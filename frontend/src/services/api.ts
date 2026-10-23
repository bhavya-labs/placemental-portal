import axios from 'axios';

const resolveApiBaseUrl = (): string => {
  // 1. Explicit build-time or runtime environment variable takes highest precedence
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // 2. Automated fallback when deployed on GitHub Pages domain
  if (typeof window !== 'undefined' && window.location.hostname.endsWith('github.io')) {
    return 'https://placement-portal-n570.onrender.com';
  }
  // 3. Local Vite development mode
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000';
  }
  // 4. Unified single-origin production deployment fallback
  return '';
};

const API_BASE_URL = resolveApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60s timeout to allow Render container to wake up from cold standby
});

// Auto-inject JWT token to all requests if present in localStorage
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle session timeouts/unauthorized access and format technical errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status;
      if (status === 401) {
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');
        let userRole = '';
        if (storedUser) {
          try {
            const parsed = JSON.parse(storedUser);
            userRole = parsed.role || '';
          } catch {
            // ignore JSON parse error
          }
        }

        // Only redirect if the user had an active stored token in localStorage
        // Prevents unauthenticated background calls on public landing pages from triggering redirect loops
        if (storedToken) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          const basePath = (typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL)
            ? import.meta.env.BASE_URL.replace(/\/$/, '')
            : '';
          const loginTarget = `${basePath}${userRole === 'parent' ? '/parent/login' : '/login'}`;
          if (window.location.pathname !== loginTarget) {
            window.location.href = loginTarget;
          }
        }

        if (error.response.data) {
          const detail = error.response.data.detail;
          if (detail === "Token has expired" || detail === "Signature has expired" || String(detail).toLowerCase().includes("jwt")) {
            error.response.data.detail = "Your session has expired. Please sign in again.";
          }
        }
      } else if (status === 403) {
        const oldDetail = error.response.data?.detail || "";
        if (!oldDetail.includes("locked") && !oldDetail.includes("correction")) {
          error.response.data = error.response.data || {};
          error.response.data.detail = "You do not have permission to access this information.";
        }
      } else if (status === 422) {
        error.response.data = error.response.data || {};
        error.response.data.detail = "The information entered could not be processed. Please check the details.";
      } else if (status >= 500) {
        error.response.data = error.response.data || {};
        error.response.data.detail = "Something went wrong while processing your request. Please try again.";
      }
    } else {
      error.message = "Something went wrong while processing your request. Please try again.";
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (credentials: any) => {
    const response = await api.post('/api/auth/login', credentials);
    return response.data;
  },
  getProfile: async () => {
    const response = await api.get('/api/auth/profile');
    return response.data;
  },
  getFaculties: async () => {
    const response = await api.get('/api/auth/faculty');
    return response.data;
  },
  createFaculty: async (data: any) => {
    const response = await api.post('/api/auth/faculty', data);
    return response.data;
  },
  updateFaculty: async (id: number, data: any) => {
    const response = await api.put(`/api/auth/faculty/${id}`, data);
    return response.data;
  },
  deleteFaculty: async (id: number) => {
    const response = await api.delete(`/api/auth/faculty/${id}`);
    return response.data;
  }
};

export const studentService = {
  getStudents: async (params: any) => {
    const response = await api.get('/api/students', { params });
    return response.data;
  },
  getStudentById: async (id: number) => {
    const response = await api.get(`/api/students/${id}`);
    return response.data;
  },
  updateStudent: async (id: number, data: any) => {
    const response = await api.put(`/api/students/${id}`, data);
    return response.data;
  },
  createStudent: async (data: any) => {
    const response = await api.post('/api/students', data);
    return response.data;
  },
  deleteStudent: async (id: number) => {
    const response = await api.delete(`/api/students/${id}`);
    return response.data;
  },
  bulkUpload: async (payload: any[], preview: boolean = false) => {
    const response = await api.post(`/api/students/bulk-upload?preview=${preview}`, payload);
    return response.data;
  },
  getDepartmentPlacementDetails: async (params?: any) => {
    const response = await api.get('/api/students/department-placement-details', { params });
    return response.data;
  }
};

export const driveService = {
  getCompanies: async () => {
    const response = await api.get('/api/companies');
    return response.data;
  },
  createCompany: async (data: any) => {
    const response = await api.post('/api/companies', data);
    return response.data;
  },
  getPublicActiveDrives: async () => {
    const response = await api.get('/api/public/active-drives');
    return response.data;
  },
  getDrives: async (statusFilter?: string) => {
    const response = await api.get('/api/drives', {
      params: statusFilter ? { status_filter: statusFilter } : {}
    });
    return response.data;
  },
  createDrive: async (data: any) => {
    const response = await api.post('/api/drives', data);
    return response.data;
  },
  getDriveDetails: async (id: number) => {
    const response = await api.get(`/api/drives/${id}`);
    return response.data;
  },
  updateDrive: async (id: number, data: any) => {
    const response = await api.put(`/api/drives/${id}`, data);
    return response.data;
  },
  deleteDrive: async (id: number) => {
    const response = await api.delete(`/api/drives/${id}`);
    return response.data;
  },
  deleteCompany: async (id: number) => {
    const response = await api.delete(`/api/companies/${id}`);
    return response.data;
  },
  getEligibleStudents: async (driveId: number) => {
    const response = await api.get(`/api/drives/${driveId}/eligible-students`);
    return response.data;
  }
};

export const applicationService = {
  apply: async (driveId: number) => {
    const response = await api.post('/api/applications', { drive_id: driveId });
    return response.data;
  },
  withdrawApplication: async (applicationId: number) => {
    const response = await api.delete(`/api/applications/${applicationId}`);
    return response.data;
  },
  getStudentApplications: async (studentId: number) => {
    const response = await api.get(`/api/applications/student/${studentId}`);
    return response.data;
  },
  updateStatus: async (applicationId: number, data: { status: string; current_round: string; joining_status?: string; remarks?: string }) => {
    const response = await api.put(`/api/applications/${applicationId}/status`, data);
    return response.data;
  },
  scheduleInterview: async (data: { application_id: number; round_name: string; interview_date: string; remarks?: string }) => {
    const response = await api.post('/api/interviews', data);
    return response.data;
  },
  getStudentInterviews: async (studentId: number) => {
    const response = await api.get(`/api/interviews/student/${studentId}`);
    return response.data;
  },
  submitFeedback: async (interviewId: number, data: any) => {
    const response = await api.post(`/api/interviews/${interviewId}/feedback`, data);
    return response.data;
  }
};

export const analyticsService = {
  getDashboardStats: async (filters: { dept_id?: number; batch?: string; gender?: string } = {}) => {
    const response = await api.get('/api/analytics/dashboard', { params: filters });
    return response.data;
  },
  getReportData: async (reportType: string, deptId?: number, batch?: string) => {
    const response = await api.get('/api/analytics/reports', {
      params: { report_type: reportType, dept_id: deptId, batch }
    });
    return response.data;
  },
  getCompanyAnalytics: async (companyId: number) => {
    const response = await api.get(`/api/analytics/company/${companyId}`);
    return response.data;
  }
};

export const aiService = {
  getStudentReport: async (studentId: number) => {
    const response = await api.get(`/api/ai/student-report/${studentId}`);
    return response.data;
  },
  getFeedbackSentiment: async () => {
    const response = await api.get('/api/ai/feedback-sentiment');
    return response.data;
  },
  getFeedbacks: async () => {
    const response = await api.get('/api/ai/feedbacks');
    return response.data;
  },
  uploadResume: async (formData: FormData) => {
    const response = await api.post('/api/ai/resume/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },
  getJobMatch: async (driveId: number) => {
    const response = await api.get(`/api/ai/job-match/${driveId}`);
    return response.data;
  },
  getPrepRoadmap: async (driveId: number) => {
    const response = await api.get(`/api/ai/prep-roadmap/${driveId}`);
    return response.data;
  },
  getAIInsights: async () => {
    const response = await api.get('/api/ai/insights');
    return response.data;
  },
  getDriveFeedbackSummary: async (driveId: number) => {
    const response = await api.get(`/api/ai/drives/${driveId}/feedback-summary`);
    return response.data;
  }
};

export const careerPathService = {
  getStudentReport: async (studentId: number) => {
    const response = await api.get(`/api/ai/student-report/${studentId}`);
    return response.data;
  },
  getPrepRoadmap: async (driveId: number) => {
    const response = await api.get(`/api/ai/prep-roadmap/${driveId}`);
    return response.data;
  }
};

export const parentService = {
  requestOtp: async (rollNumber: number, mobileNumber: string) => {
    const response = await api.post('/api/parent/request-otp', { roll_number: rollNumber, mobile_number: mobileNumber });
    return response.data;
  },
  verifyOtp: async (rollNumber: number, mobileNumber: string, otp: string) => {
    const response = await api.post('/api/parent/verify-otp', { roll_number: rollNumber, mobile_number: mobileNumber, otp });
    return response.data;
  },
  getChildData: async () => {
    const response = await api.get('/api/parent/child');
    return response.data;
  }
};

export const correctionService = {
  submitRequest: async (data: { field: string; current_value: string; requested_value: string; reason: string }) => {
    const response = await api.post('/api/students/correction-requests', data);
    return response.data;
  },
  getRequests: async () => {
    const response = await api.get('/api/students/correction-requests');
    return response.data;
  },
  actionRequest: async (id: number, status: string) => {
    const response = await api.put(`/api/students/correction-requests/${id}/action`, { status });
    return response.data;
  }
};

export const activityService = {
  getActivities: async (driveId?: number) => {
    const response = await api.get('/api/activities', {
      params: driveId ? { placement_drive_id: driveId } : {}
    });
    return response.data;
  },
  createActivity: async (data: any) => {
    const response = await api.post('/api/activities', data);
    return response.data;
  },
  updateActivity: async (id: number, data: any) => {
    const response = await api.put(`/api/activities/${id}`, data);
    return response.data;
  },
  deleteActivity: async (id: number) => {
    const response = await api.delete(`/api/activities/${id}`);
    return response.data;
  },
  getAttendance: async (activityId: number) => {
    const response = await api.get(`/api/activities/${activityId}/attendance`);
    return response.data;
  },
  markAttendance: async (activityId: number, payload: any[]) => {
    const response = await api.post(`/api/activities/${activityId}/attendance`, payload);
    return response.data;
  }
};

export const attendanceService = {
  getAcademicAttendance: async (studentId: number) => {
    const response = await api.get(`/api/attendance/academic/${studentId}`);
    return response.data;
  },
  getActivityAttendance: async (studentId: number) => {
    const response = await api.get(`/api/attendance/activity/student/${studentId}`);
    return response.data;
  }
};

export const grievanceService = {
  submitGrievance: async (data: { category: string; title: string; description: string }) => {
    const response = await api.post('/api/grievances', data);
    return response.data;
  },
  getGrievances: async () => {
    const response = await api.get('/api/grievances');
    return response.data;
  },
  resolveGrievance: async (id: number, status: string, remarks?: string) => {
    const response = await api.put(`/api/grievances/${id}/status`, null, {
      params: { status, remarks }
    });
    return response.data;
  }
};

export const student360Service = {
  getTimeline: async (studentId?: number) => {
    const response = await api.get('/api/students/timeline', {
      params: studentId ? { student_id: studentId } : {}
    });
    return response.data;
  },
  getStudent360: async (studentId: number) => {
    const response = await api.get(`/api/students/360/${studentId}`);
    return response.data;
  }
};

export const feedbackIntelService = {
  getActivityReport: async (activityId: number) => {
    const response = await api.get(`/api/feedback/report/${activityId}`);
    return response.data;
  },
  getDriveReport: async (driveId: number) => {
    const response = await api.get(`/api/feedback/report/drive/${driveId}`);
    return response.data;
  },
  getComparison: async () => {
    const response = await api.get('/api/feedback/comparison');
    return response.data;
  }
};

export const permissionService = {
  getPermissions: async () => {
    const response = await api.get('/api/permissions');
    return response.data;
  },
  grantPermission: async (data: any) => {
    const response = await api.post('/api/permissions/grant', data);
    return response.data;
  },
  revokePermission: async (id: number) => {
    const response = await api.post(`/api/permissions/revoke/${id}`);
    return response.data;
  },
  getRequests: async () => {
    const response = await api.get('/api/permissions/requests');
    return response.data;
  },
  submitRequest: async (data: {
    module: string;
    scope: string;
    scope_value: string;
    action: string;
    duration_days: number;
    reason: string;
  }) => {
    const response = await api.post('/api/permissions/requests', data);
    return response.data;
  },
  actionRequest: async (id: number, status: 'Approved' | 'Rejected') => {
    const response = await api.put(`/api/permissions/requests/${id}/action`, { status });
    return response.data;
  }
};

export default api;
