import io
import re
import zipfile
from typing import Dict, Any, List

class ResumeScanner:
    def __init__(self):
        # Buzzwords list for section matching
        self.sections = {
            "education": [r"education\b", r"academic\b", r"university\b", r"college\b", r"degree\b"],
            "experience": [r"experience\b", r"employment\b", r"work history\b", r"professional path\b", r"internship\b"],
            "projects": [r"projects\b", r"personal projects\b", r"academic projects\b"],
            "skills": [r"skills\b", r"technical skills\b", r"expertise\b", r"technologies\b"]
        }

    def extract_text(self, file_content: bytes, filename: str) -> str:
        """
        Zero-dependency text extraction from TXT, DOCX, or PDF bytes.
        """
        filename_lower = filename.lower()
        if filename_lower.endswith(".txt"):
            try:
                return file_content.decode("utf-8")
            except:
                return file_content.decode("latin-1", errors="ignore")

        elif filename_lower.endswith(".docx"):
            try:
                # Word docx is a zip file containing word/document.xml
                with zipfile.ZipFile(io.BytesIO(file_content)) as docx:
                    xml_content = docx.read("word/document.xml").decode("utf-8")
                    # Strip XML tags
                    text = re.sub(r"<[^>]*>", " ", xml_content)
                    # Normalize whitespace
                    return re.sub(r"\s+", " ", text).strip()
            except Exception as e:
                # Fallback to byte scanning if zip fails
                return self._extract_ascii_from_bytes(file_content)

        elif filename_lower.endswith(".pdf"):
            # -------------------------------------------------------------------------
            # LIMITATION NOTE (Phase 4 - Model & Scanner Rigor):
            # The current byte-level ASCII regex extraction scans raw bytes for printable
            # ASCII characters without external PDF parsing libraries (maintaining the
            # zero-dependency lightweight architecture).
            #
            # KNOWN LIMITATION:
            # Modern PDF generators (LaTeX, Google Docs, Microsoft Word export, Canva)
            # compress their internal page streams using zlib/FlateDecode or embed font
            # subset encoding tables (ToUnicode CMaps). When parsing such compressed PDFs,
            # this regex scanner returns near-empty text, metadata strings, or font dictionary
            # fragments rather than the actual document text.
            #
            # See MODEL_LIMITATIONS.md for full academic analysis.
            # -------------------------------------------------------------------------
            text = self._extract_ascii_from_bytes(file_content)

            # Optional fallback: If external parser (e.g. pypdf) is installed in the environment
            # and regex extraction yielded near-empty text (< 50 chars), decompress stream.
            if len(text.strip()) < 50:
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(io.BytesIO(file_content))
                    pages_text = [p.extract_text() or "" for p in reader.pages]
                    joined = " ".join(pages_text).strip()
                    if len(joined) >= 20:
                        text = re.sub(r"\s+", " ", joined)
                except Exception:
                    pass

            return text

        else:
            return self._extract_ascii_from_bytes(file_content)

    def _extract_ascii_from_bytes(self, content: bytes) -> str:
        """Scan raw bytes for printable ASCII characters (useful as a zero-dep fallback)"""
        # Finds sequences of printable ASCII chars
        ascii_sequences = re.findall(rb"[\x20-\x7E\x0A\x0D]{4,}", content)
        text = " ".join([seq.decode("ascii", errors="ignore") for seq in ascii_sequences])
        return re.sub(r"\s+", " ", text).strip()

    def analyze_resume(self, resume_text: str, jd_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze resume text against job description, calculating ATS score and gaps.
        """
        if not resume_text or len(resume_text.strip()) < 50:
            return {
                "ats_score": 0,
                "error": "Not enough text could be extracted from this file — please upload a text-based PDF or Word document",
                "message": "Not enough text could be extracted from this file — please upload a text-based PDF or Word document",
                "matching_skills": [],
                "missing_skills": [],
                "missing_keywords": [],
                "weak_sections": [
                    "Not enough text could be extracted from this file — please upload a text-based PDF or Word document"
                ],
                "grammar_issues": [],
                "project_suggestions": [],
                "improvement_tips": [
                    "Please upload a digital, text-based PDF or Word document with selectable text."
                ]
            }

        score = 40  # Base score for submission completeness
        weak_sections = []
        matching_skills = []
        missing_skills = []
        missing_keywords = []
        
        # Parse JD required skills
        jd_skills_str = jd_details.get("required_skills") or ""
        required_skills = [s.strip().lower() for s in jd_skills_str.split(",") if s.strip()]
        if not required_skills:
            required_skills = ["python", "sql", "java", "react", "javascript", "data structures"]

        # 1. Section completeness check (max 20 points)
        resume_lower = resume_text.lower()
        sections_found = 0
        for sec_name, regexes in self.sections.items():
            found = False
            for reg in regexes:
                if re.search(reg, resume_lower):
                    found = True
                    break
            if found:
                sections_found += 1
                score += 5
            else:
                weak_sections.append(f"Consider adding a dedicated '{sec_name.capitalize()}' section to highlight your practical work.")

        # 2. Skill matching checks (max 30 points)
        skills_matched = 0
        for skill in required_skills:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, resume_lower):
                skills_matched += 1
                matching_skills.append(skill.upper())
            else:
                missing_skills.append(skill.upper())
                missing_keywords.append(skill.upper())

        if len(required_skills) > 0:
            skill_score = min(30.0, (skills_matched / len(required_skills)) * 30.0)
            score += int(skill_score)
        else:
            score += 30

        # Add suggestions if missing critical skills
        if len(missing_skills) > 3:
            weak_sections.append(f"Consider featuring key technologies relevant to this role: {', '.join(missing_skills[:3])}.")

        # 3. Format/Links check (max 10 points)
        has_links = False
        if re.search(r"github\.com", resume_lower) or re.search(r"linkedin\.com", resume_lower):
            score += 5
            has_links = True
        else:
            weak_sections.append("Include links to your GitHub and LinkedIn profiles so recruiters can see your code and background.")

        if re.search(r"\b\+?\d{10,12}\b", resume_lower) or re.search(r"\b[a-za-z0-9._%+-]+@[a-za-z0-9.-]+\.[a-za-z]{2,}\b", resume_lower):
            score += 5
        else:
            weak_sections.append("Ensure your contact email and phone number are clearly visible at the top of your resume.")

        # Final ATS calculation
        ats_score = min(100, max(0, score))

        # Project Suggestions mapping based on missing tech
        project_suggestions = []
        for ms in missing_skills:
            ms_lower = ms.lower()
            if "react" in ms_lower or "javascript" in ms_lower:
                project_suggestions.append("Develop a React client dashboard using WebSockets and Chart.js to show analytics.")
            elif "sql" in ms_lower or "dbms" in ms_lower:
                project_suggestions.append("Design a secure backend schema structure with relational SQL queries and optimization indexes.")
            elif "python" in ms_lower or "fastapi" in ms_lower:
                project_suggestions.append("Create a server-side REST API in FastAPI integrated with SQLAlchemy database operations.")
            elif "aws" in ms_lower or "docker" in ms_lower:
                project_suggestions.append("Deploy a Docker container cluster on AWS ECS with auto-scaling triggers.")

        if not project_suggestions:
            project_suggestions.append("Build a secure Relational E-Commerce transaction API utilizing JWT tokens.")

        # Grammar & Formatting checklists
        grammar_issues = [
            "Ensure capitalization of technical languages is correct (e.g. 'SQL' instead of 'sql')",
            "Action verbs check: start bullet points with active verbs like 'Developed', 'Engineered', 'Optimized'."
        ]

        improvement_tips = []
        if len(missing_skills) > 0:
            improvement_tips.append(f"Include core tools and skills you've used in coursework: {', '.join(missing_skills[:3])}.")
        if not has_links:
            improvement_tips.append("Add clickable links to your GitHub repositories and LinkedIn profile.")
        if ats_score < 70:
            improvement_tips.append("Use standard section headings (Education, Projects, Skills, Experience) so recruiters can easily find details.")

        return {
            "ats_score": ats_score,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "missing_keywords": missing_keywords[:6],
            "weak_sections": weak_sections,
            "grammar_issues": grammar_issues,
            "project_suggestions": project_suggestions[:3],
            "improvement_tips": improvement_tips[:3]
        }

def io_bytes_wrapper(content: bytes):
    """Wrapper to turn bytes into a file-like stream using io.BytesIO"""
    import io
    return io.BytesIO(content)

resume_scanner = ResumeScanner()
