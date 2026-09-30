import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import DashboardLayout from './components/DashboardLayout';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import StudentDashboard from './pages/StudentDashboard';
import StudentProfile from './pages/StudentProfile';
import StudentApplications from './pages/StudentApplications';
import StudentAiReport from './pages/StudentAiReport';
import FacultyDashboard from './pages/FacultyDashboard';
import AdminDashboard from './pages/AdminDashboard';
import AdminFaculty from './pages/AdminFaculty';
import AdminStudents from './pages/AdminStudents';
import AdminDrives from './pages/AdminDrives';
import AdminLogs from './pages/AdminLogs';
import NotFound from './pages/NotFound';
import StudentTracker from './pages/StudentTracker';
import PlacementDrives from './pages/PlacementDrives';
import AISentimentMiner from './pages/AISentimentMiner';
import ReportExporter from './pages/ReportExporter';
import ParentLogin from './pages/ParentLogin';
import ParentDashboard from './pages/ParentDashboard';
import CorrectionRequests from './pages/CorrectionRequests';
import AccessManagement from './pages/AccessManagement';
import Student360 from './pages/Student360';
import Grievances from './pages/Grievances';
import Calendar from './pages/Calendar';
import Search from './pages/Search';

// Protected Route Guard
const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRoles: string[] }> = ({ 
  children, 
  allowedRoles 
}) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gov-navy dark:border-sky-400"></div>
          <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Securing Session...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    // Redirect user to their appropriate workspace home
    if (user.role === 'admin') return <Navigate to="/admin" replace />;
    if (['faculty', 'hod', 'tnp'].includes(user.role)) return <Navigate to="/faculty-dashboard" replace />;
    if (user.role === 'parent') return <Navigate to="/parent/dashboard" replace />;
    return <Navigate to="/student" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public Gateway routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />

          {/* Secure Student Dashboard */}
          <Route 
            path="/student" 
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <DashboardLayout>
                  <StudentDashboard />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/student/profile" 
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <DashboardLayout>
                  <StudentProfile />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/student/applications" 
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <DashboardLayout>
                  <StudentApplications />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/student/ai-career-path" 
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <DashboardLayout>
                  <StudentAiReport />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          {/* Secure Faculty/Placement Officer Panel */}
          <Route 
            path="/faculty-dashboard" 
            element={
              <ProtectedRoute allowedRoles={['faculty', 'admin', 'hod', 'tnp']}>
                <DashboardLayout>
                  <FacultyDashboard />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          <Route 
            path="/student-tracker" 
            element={
              <ProtectedRoute allowedRoles={['faculty', 'admin', 'hod', 'tnp']}>
                <DashboardLayout>
                  <StudentTracker />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          <Route 
            path="/placement-drives" 
            element={
              <ProtectedRoute allowedRoles={['faculty', 'admin', 'hod', 'tnp']}>
                <DashboardLayout>
                  <PlacementDrives />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          <Route 
            path="/ai-sentiment-miner" 
            element={
              <ProtectedRoute allowedRoles={['faculty', 'admin', 'hod', 'tnp']}>
                <DashboardLayout>
                  <AISentimentMiner />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          <Route 
            path="/report-exporter" 
            element={
              <ProtectedRoute allowedRoles={['faculty', 'admin', 'hod', 'tnp']}>
                <DashboardLayout>
                  <ReportExporter />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          <Route path="/faculty" element={<Navigate to="/faculty-dashboard" replace />} />

          {/* Secure Admin Operations Control */}
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <DashboardLayout>
                  <AdminDashboard />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/dashboard" 
            element={<Navigate to="/admin" replace />} 
          />
          <Route 
            path="/admin/faculty" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <DashboardLayout>
                  <AdminFaculty />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/students" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <DashboardLayout>
                  <AdminStudents />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/drives" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <DashboardLayout>
                  <AdminDrives />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/logs" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <DashboardLayout>
                  <AdminLogs />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/reports" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <DashboardLayout>
                  <ReportExporter />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          {/* Parent Portal Routes */}
          <Route path="/parent/login" element={<ParentLogin />} />
          <Route 
            path="/parent/dashboard" 
            element={
              <ProtectedRoute allowedRoles={['parent']}>
                <DashboardLayout>
                  <ParentDashboard />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          {/* Unified Grievance Desk */}
          <Route 
            path="/grievances" 
            element={
              <ProtectedRoute allowedRoles={['student', 'faculty', 'admin', 'hod', 'tnp']}>
                <DashboardLayout>
                  <Grievances />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          {/* Correction Requests Verification */}
          <Route 
            path="/correction-requests" 
            element={
              <ProtectedRoute allowedRoles={['student', 'admin', 'faculty', 'hod', 'tnp']}>
                <DashboardLayout>
                  <CorrectionRequests />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          {/* HOD/Faculty Student 360 view */}
          <Route 
            path="/student-360/:id" 
            element={
              <ProtectedRoute allowedRoles={['faculty', 'admin', 'hod', 'tnp']}>
                <DashboardLayout>
                  <Student360 />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          {/* Access permissions console */}
          <Route 
            path="/admin/access" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <DashboardLayout>
                  <AccessManagement />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          {/* Scoped Calendar Portal */}
          <Route 
            path="/calendar" 
            element={
              <ProtectedRoute allowedRoles={['student', 'faculty', 'admin', 'parent', 'hod', 'tnp']}>
                <DashboardLayout>
                  <Calendar />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          {/* Scoped Global Search */}
          <Route 
            path="/search" 
            element={
              <ProtectedRoute allowedRoles={['faculty', 'admin', 'parent', 'hod', 'tnp']}>
                <DashboardLayout>
                  <Search />
                </DashboardLayout>
              </ProtectedRoute>
            } 
          />

          {/* Fallback Error boundaries */}
          <Route path="/404" element={<NotFound />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
      </AuthProvider>
    </Router>
  );
};

export default App;
