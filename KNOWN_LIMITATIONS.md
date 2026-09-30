# Known Architectural Limitations & Production Roadmap

This document provides a transparent engineering disclosure of simulated components, architectural trade-offs, boundary conditions, and untested areas within the Placement Portal codebase. Each limitation is documented alongside its current implementation reality, rationale, and recommended remediation roadmap for enterprise production deployment.

---

## Table of Contents

1. [Telephony & SMS Gateway Simulation](#1-telephony--sms-gateway-simulation)
2. [Administrative Database Snapshot Backup Simulation](#2-administrative-database-snapshot-backup-simulation)
3. [Resume Optical Character Recognition (OCR) Boundaries](#3-resume-optical-character-recognition-ocr-boundaries)
4. [Resume Binary Document Retention vs. Metadata Indexing](#4-resume-binary-document-retention-vs-metadata-indexing)
5. [Database Engine Concurrency & SQLite Ceilings](#5-database-engine-concurrency--sqlite-ceilings)
6. [Synchronous Bulk Student Ingestion Scale](#6-synchronous-bulk-student-ingestion-scale)
7. [Assistive Technology & Hardware Screen-Reader Validation](#7-assistive-technology--hardware-screen-reader-validation)
8. [Client-Side Offline Fallback Mock Datasets](#8-client-side-offline-fallback-mock-datasets)

---

## 1. Telephony & SMS Gateway Simulation

### Current Implementation
- **Location**: [`backend/app/routers/parents.py`](file:///d:/placement%20portal/backend/app/routers/parents.py#L33-L46)
- **Status**: Simulated (Standard Output Log)
- **Description**: The Parent Portal authentication relies on a One-Time Password (OTP) verification flow. In the current codebase, the `SMSProvider` base class is backed by two implementations:
  - `DevelopmentSMSProvider`: Formats and logs the plaintext 6-digit OTP directly to server `stdout` (`[SMS SIMULATOR - DEV] OTP for parent {phone}: {otp}`) to enable instantaneous testing and inspection without incurring vendor API credits.
  - `ProductionSMSProvider`: Simulates dispatch by masking the token and logging delivery confirmation (`[SMS DISPATCH - PROD] OTP dispatched successfully to {phone}`).
- **Impact**: Real SMS messages are not transmitted over cellular telecom networks. Live parents cannot receive OTPs on physical handsets unless an external telephony gateway is plugged in.

### Production Remediation & Future Work
- Implement a gateway adapter subclass (e.g. `TwilioSMSProvider`, `AWSSNSProvider`, or `GupshupSMSProvider`) adhering to the `SMSProvider.send_otp(phone, otp)` interface.
- Store vendor API keys (`SMS_API_KEY`, `SMS_SENDER_ID`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`) in encrypted environment variables or secrets managers (AWS Secrets Manager / HashiCorp Vault).
- Implement webhook status callbacks to verify cellular carrier delivery reports (DLR).

---

## 2. Administrative Database Snapshot Backup Simulation

### Current Implementation
- **Location**: [`frontend/src/pages/AdminLogs.tsx`](file:///d:/placement%20portal/frontend/src/pages/AdminLogs.tsx#L43-L52)
- **Status**: UI Simulation
- **Description**: In the Audit Logs and System Administration interface, the "Trigger Snapshot Backup" button initiates a 1.5-second timer (`setTimeout`), toggles a loading spinner, and displays an administrative notification:
  > *Database backup successfully completed! Snapshot: 'backups/backup_YYYY-MM-DD.sql' (2.4 MB) written to local disk.*
- **Impact**: While the user interface feedback loop, audit logging, and authorization guards are functional, there is no underlying backend endpoint generating a physical `.sql` dump or copying the database file to an archive volume.

### Production Remediation & Future Work
- Create an authenticated administrative endpoint: `POST /api/admin/backups/snapshot`.
- Utilize the native engine backup APIs:
  - For SQLite: `sqlite3.Connection.backup()` to create a consistent, non-blocking online snapshot.
  - For PostgreSQL: Subprocess call to `pg_dump -Fc` or volume-level snapshots via cloud storage APIs.
- Stream generated compressed snapshots (`.sql.gz` or `.dump`) to encrypted cloud object storage (Amazon S3 / Google Cloud Storage) with lifecycle expiration policies.

---

## 3. Resume Optical Character Recognition (OCR) Boundaries

### Current Implementation
- **Location**: [`backend/app/ml/resume_scanner.py`](file:///d:/placement%20portal/backend/app/ml/resume_scanner.py#L83-L105), [`backend/app/routers/ai.py`](file:///d:/placement%20portal/backend/app/routers/ai.py#L411-L418)
- **Status**: Text-Layer Extraction Only (Zero-OCR)
- **Description**: The ATS resume parser extracts text from uploaded PDF and DOCX files using Python byte-stream readers (`pypdf`, `pdfplumber`, `docx2txt`). If a student uploads a scanned photograph, raster image, or photocopy embedded inside a PDF without an underlying digital text layer, extracted character count is near zero.
- **Handling**: Rather than fabricating placeholder text, the parser validates that extracted text meets a minimum threshold of 50 characters. If fewer than 50 characters are extracted, the API returns an explicit HTTP 400 error:
  > *"Not enough text could be extracted from this file — please upload a text-based PDF or Word document"*
- **Impact**: Candidates uploading scanned physical documents cannot be scored until they provide a digital document with selectable fonts.

### Production Remediation & Future Work
- Bundle an OCR processing pipeline using `pytesseract` (backed by the native Google Tesseract OCR engine) or cloud document intelligence (AWS Textract / Google Cloud Vision API).
- Route scanned documents to an asynchronous worker queue that renders PDF pages as high-resolution images, executes image binarization/deskewing, and performs multi-column optical character recognition.

---

## 4. Resume Binary Document Retention vs. Metadata Indexing

### Current Implementation
- **Location**: [`backend/app/routers/ai.py`](file:///d:/placement%20portal/backend/app/routers/ai.py#L438-L445)
- **Status**: In-Memory Parsing with Structured SQL Storage
- **Description**: When a candidate uploads a resume file:
  1. The binary stream is ingested in memory (`content = await file.read()`).
  2. Extracted text, computed ATS score, and granular section breakdowns are serialized into the `Student` relational table (`resume_text`, `resume_ats_score`, `resume_analysis_json`).
  3. A logical path string (`resumes/{student_id}_{filename}`) is written to `Student.resume_path`.
- **Impact**: The physical binary file (`.pdf` or `.docx`) is not persisted to a permanent filesystem folder or cloud object storage bucket. The portal stores the parsed text and structured analysis, but recruiters cannot download the original formatted graphic layout PDF.

### Production Remediation & Future Work
- Configure Amazon S3 or MinIO blob storage.
- Save uploaded binary files with unique UUID keys (`s3://placement-portal-resumes/{batch}/{student_id}/{uuid}.pdf`).
- Expose secure, time-limited presigned URLs (`GET /api/students/{id}/resume/download`) allowing placement officers and recruiters to inspect original formatted resumes.

---

## 5. Database Engine Concurrency & SQLite Ceilings

### Current Implementation
- **Location**: [`backend/app/database.py`](file:///d:/placement%20portal/backend/app/database.py), `placement_portal.db`
- **Status**: Single-File Embedded RDBMS (SQLite 3)
- **Description**: The platform currently executes on SQLite with Write-Ahead Logging (WAL) and indexed schemas (Compound indices on `applications(student_id, drive_id)`, `students(batch, dept_id)`, `feedbacks(interview_id)`).
- **Concurrency Characteristics**:
  - Read operations: Highly performant, concurrent, and thread-safe.
  - Write operations: Constrained by SQLite's database-level write lock. If hundreds of candidates simultaneously submit applications or interview feedbacks in the final minutes before a drive deadline, requests may encounter `sqlite3.OperationalError: database is locked`.
- **Impact**: Adequate for single-institution demonstrations, development environments, and moderate departmental cohorts, but unsuitable for multi-tenant enterprise deployments under high write bursts.

### Production Remediation & Future Work
- Transition to a managed PostgreSQL cluster (Amazon RDS / Cloud SQL) by simply updating the connection string in `.env`:
  ```env
  DATABASE_URL=postgresql+psycopg2://user:password@db-cluster.internal:5432/placement_portal
  ```
- Because all models are defined via SQLAlchemy ORM with standard types and managed via Alembic revisions, zero application code refactoring is required.
- Enable connection pooling via `QueuePool` with `pool_size=20` and `max_overflow=30`.

---

## 6. Synchronous Bulk Student Ingestion Scale

### Current Implementation
- **Location**: [`backend/app/routers/students.py`](file:///d:/placement%20portal/backend/app/routers/students.py#L225-L290), [`frontend/src/pages/AdminDashboard.tsx`](file:///d:/placement%20portal/frontend/src/pages/AdminDashboard.tsx#L30-L53)
- **Status**: Synchronous Single-Transaction Processing
- **Description**: The Admin "Bulk Import Records" feature accepts a JSON array of student profiles. The backend parses each record, verifies unique user email constraints, creates `User` and `Student` rows, and invokes `predictor.train_model(db)` synchronously before returning the HTTP response.
- **Operational Boundary**: Batches of 50 to 500 students execute smoothly in 1–3 seconds. Ingesting multi-thousand records (> 5,000 students) in a single synchronous HTTP request risks web server timeout (Uvicorn / Nginx 60s gateway timeouts) and monopolizes CPU cores during model refitting.

### Production Remediation & Future Work
- Decouple batch parsing into an asynchronous background task queue using Celery or ARQ with Redis:
  1. The API immediately returns an ingestion job ID (`{"job_id": "job_9843", "status": "QUEUED"}`).
  2. A worker pool ingests records in chunks of 500 using SQLAlchemy bulk insertions (`bulk_insert_mappings`).
  3. The Random Forest model is retrained once upon completion of the entire batch.
  4. Real-time progress is streamed to the administrator's browser via WebSockets or Server-Sent Events (SSE).

---

## 7. Assistive Technology & Hardware Screen-Reader Validation

### Current Implementation
- **Location**: [`frontend/src/components/AccessibilityComponents.tsx`](file:///d:/placement%20portal/frontend/src/components/AccessibilityComponents.tsx)
- **Status**: Automated DOM Testing Passed; Physical Device Testing Pending
- **Description**: The frontend incorporates WCAG 2.1 AA compliant elements:
  - `AccessibleModal`: Traps Tab / Shift+Tab keyboard focus within active dialogs, binds Escape dismissal, and restores focus to triggering controls upon unmounting.
  - `AccessibleChart`: Exposes semantic HTML `<table>` data tables with assistive captions for screen-reader users behind visual Recharts canvas graphs.
  - High-contrast color palette, explicit ARIA role attributes, and aria-live status regions.
- **Testing Reality**: Accessibility compliance has been verified programmatically using Node.js DOM unit tests (`scratch/test_modal_focus.cjs`, 6/6 tests passing). However, manual audits with physical screen-reading software (NVDA, JAWS, Apple VoiceOver, Android TalkBack) across multiple operating systems have not been conducted.

### Production Remediation & Future Work
- Conduct live user accessibility sessions with visually impaired test participants.
- Execute formal audits using NVDA on Windows and VoiceOver on macOS/iOS.
- Integrate automated accessibility regression testing into CI/CD pipelines using Axe-Core / Playwright Accessibility testing suites (`@axe-core/playwright`).

---

## 8. Client-Side Offline Fallback Mock Datasets

### Current Implementation
- **Location**: [`frontend/src/pages/LandingPage.tsx`](file:///d:/placement%20portal/frontend/src/pages/LandingPage.tsx#L44-L49), [`frontend/src/pages/AISentimentMiner.tsx`](file:///d:/placement%20portal/frontend/src/pages/AISentimentMiner.tsx#L45-L65)
- **Status**: Network Disconnection Safeguards
- **Description**: When the backend API is online, live database records are fetched and rendered. However, both pages wrap their initial data fetches in `try/catch` blocks that catch connection dropouts or 500 server errors:
  - `LandingPage.tsx`: Populates 4 sample placement drives (`Google`, `Microsoft`, `TCS`, `Goldman Sachs`) if the public drive endpoint is unreachable.
  - `AISentimentMiner.tsx`: Populates 3 mock candidate feedback cards if the NLP sentiment analytics endpoint fails.
- **Purpose & Impact**: Designed as defensive UI stopgaps so prospective visitors do not encounter a completely blank white screen during server reboots or offline demonstration setups. However, administrators inspecting the interface while the backend is down might mistakenly view mock drives as live institutional data.

### Production Remediation & Future Work
- Replace mock data fallbacks with an explicit, high-visibility "Offline / Reconnecting" banner component that informs users of transient backend downtime without displaying fabricated drive information.
- Utilize React Query or SWR with IndexedDB persistence for offline-first caching of previously fetched live institutional data.

---

## Summary Matrix

| Limitation Area | Current State | Risk Level | Target Resolution Architecture |
| :--- | :--- | :---: | :--- |
| **SMS Telephony** | Console simulation | Low (Dev) / High (Prod) | Twilio / AWS SNS gateway adapter |
| **Snapshot Backup** | UI timer simulation | Low | `POST /api/admin/backups` + S3 archival |
| **PDF OCR** | Rejects image PDFs (< 50 chars) | Medium | Tesseract OCR / AWS Textract async worker |
| **Resume Storage** | In-memory text extraction | Medium | S3 / MinIO blob storage with presigned URLs |
| **Database Concurrency** | SQLite file lock | High (at peak) | Managed PostgreSQL + QueuePool |
| **Bulk Import Scale** | Synchronous (< 500 records) | Medium | Celery / Redis worker + WebSockets |
| **Screen Reader Verification**| Automated DOM tests | Low | NVDA & VoiceOver physical audit |
| **Offline UI Fallbacks** | Sample mock cards on error | Low | Dedicated Offline State Banner |
