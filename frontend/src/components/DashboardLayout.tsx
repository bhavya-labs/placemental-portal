import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { 
  LayoutDashboard, User, Briefcase, FileSpreadsheet, Brain, 
  Settings, LogOut, Menu, X, Bell, Globe, ChevronDown, Database,
  GraduationCap, ClipboardList, ShieldAlert, History, Search, Calendar
} from 'lucide-react';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [lang, setLang] = useState('English');

  if (!user) return null;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Role-based links config
  const linksByRole: Record<string, { label: string; path: string; icon: React.ReactNode }[]> = {
    student: [
      { label: 'My Dashboard', path: '/student', icon: <LayoutDashboard size={18} /> },
      { label: 'My Profile', path: '/student/profile', icon: <User size={18} /> },
      { label: 'Applications', path: '/student/applications', icon: <Briefcase size={18} /> },
      { label: 'Career Guidance', path: '/student/ai-career-path', icon: <Brain size={18} /> },
      { label: 'Placement Calendar', path: '/calendar', icon: <Calendar size={18} /> },
      { label: 'Correction Requests', path: '/correction-requests', icon: <ClipboardList size={18} /> },
      { label: 'Grievances', path: '/grievances', icon: <ShieldAlert size={18} /> },
    ],
    faculty: [
      { label: 'Faculty Dashboard', path: '/faculty-dashboard', icon: <LayoutDashboard size={18} /> },
      { label: 'Student Tracker', path: '/student-tracker', icon: <GraduationCap size={18} /> },
      { label: 'Placement Drives', path: '/placement-drives', icon: <Briefcase size={18} /> },
      { label: 'Interview Feedback Analysis', path: '/ai-sentiment-miner', icon: <Brain size={18} /> },
      { label: 'Placement Calendar', path: '/calendar', icon: <Calendar size={18} /> },
      { label: 'Global Search', path: '/search', icon: <Search size={18} /> },
      { label: 'Grievances', path: '/grievances', icon: <ShieldAlert size={18} /> },
      { label: 'Report Exporter', path: '/report-exporter', icon: <FileSpreadsheet size={18} /> },
    ],
    admin: [
      { label: 'Admin Dashboard', path: '/admin', icon: <LayoutDashboard size={18} /> },
      { label: 'Faculty Accounts', path: '/admin/faculty', icon: <User size={18} /> },
      { label: 'Student Records', path: '/admin/students', icon: <GraduationCap size={18} /> },
      { label: 'Placement & Drives', path: '/admin/drives', icon: <Briefcase size={18} /> },
      { label: 'Placement Calendar', path: '/calendar', icon: <Calendar size={18} /> },
      { label: 'Global Search', path: '/search', icon: <Search size={18} /> },
      { label: 'Correction Requests', path: '/correction-requests', icon: <ClipboardList size={18} /> },
      { label: 'Access Control', path: '/admin/access', icon: <History size={18} /> },
      { label: 'Grievance queue', path: '/grievances', icon: <ShieldAlert size={18} /> },
      { label: 'System Logs & Data', path: '/admin/logs', icon: <Database size={18} /> },
    ],
    parent: [
      { label: 'Child Dashboard', path: '/parent/dashboard', icon: <LayoutDashboard size={18} /> },
      { label: 'Placement Calendar', path: '/calendar', icon: <Calendar size={18} /> },
      { label: 'Global Search', path: '/search', icon: <Search size={18} /> },
    ],
    hod: [
      { label: 'HOD Dashboard', path: '/faculty-dashboard', icon: <LayoutDashboard size={18} /> },
      { label: 'Student Tracker', path: '/student-tracker', icon: <GraduationCap size={18} /> },
      { label: 'Placement Drives', path: '/placement-drives', icon: <Briefcase size={18} /> },
      { label: 'Interview Feedback Analysis', path: '/ai-sentiment-miner', icon: <Brain size={18} /> },
      { label: 'Placement Calendar', path: '/calendar', icon: <Calendar size={18} /> },
      { label: 'Global Search', path: '/search', icon: <Search size={18} /> },
      { label: 'Grievances', path: '/grievances', icon: <ShieldAlert size={18} /> },
      { label: 'Report Exporter', path: '/report-exporter', icon: <FileSpreadsheet size={18} /> },
    ],
    tnp: [
      { label: 'TNP Dashboard', path: '/faculty-dashboard', icon: <LayoutDashboard size={18} /> },
      { label: 'Student Tracker', path: '/student-tracker', icon: <GraduationCap size={18} /> },
      { label: 'Placement Drives', path: '/placement-drives', icon: <Briefcase size={18} /> },
      { label: 'Interview Feedback Analysis', path: '/ai-sentiment-miner', icon: <Brain size={18} /> },
      { label: 'Placement Calendar', path: '/calendar', icon: <Calendar size={18} /> },
      { label: 'Global Search', path: '/search', icon: <Search size={18} /> },
      { label: 'Grievances', path: '/grievances', icon: <ShieldAlert size={18} /> },
      { label: 'Report Exporter', path: '/report-exporter', icon: <FileSpreadsheet size={18} /> },
    ]
  };

  const navLinks = linksByRole[user.role] || [];

  return (
    <div className="min-h-screen flex bg-gov-light dark:bg-gov-dark">
      {/* Sidebar - Desktop */}
      <aside className="w-64 bg-gov-navy text-slate-100 hidden md:flex flex-col border-r border-slate-800 shrink-0 sticky top-0 h-screen z-20">
        {/* APCFSS Government Portal Logo Section */}
        <div className="p-5 border-b border-slate-800 bg-slate-950 flex items-center gap-3">
          <div className="bg-white p-1 rounded-full text-gov-navy flex items-center justify-center">
            <GraduationCap size={24} />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wide uppercase leading-tight">Placement</h1>
            <p className="text-[10px] text-slate-400">Portal</p>
          </div>
        </div>

        {/* Sidebar Nav links */}
        <nav aria-label="Primary Navigation" className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          <div className="text-[10px] text-slate-455 font-semibold px-3 uppercase tracking-wider mb-2">
            Navigation Menu
          </div>
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <button
                key={link.label}
                onClick={() => navigate(link.path)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-white ${
                  isActive 
                    ? 'bg-gov-blue text-white shadow-sm' 
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <span aria-hidden="true">{link.icon}</span>
                <span>{link.label}</span>
              </button>
            );
          })}
        </nav>

        {/* User Footer Profile */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="bg-gov-blue text-white w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm uppercase shrink-0">
              {user.name.charAt(0)}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-white truncate">{user.name}</p>
              <p className="text-[10px] text-slate-400 capitalize truncate">{user.role}</p>
            </div>
          </div>
          <button 
            onClick={handleLogout}
            aria-label="Log Out"
            className="text-slate-400 hover:text-red-400 transition-colors p-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-white rounded"
            title="Log Out"
          >
            <LogOut size={16} aria-hidden="true" />
          </button>
        </div>
      </aside>

      {/* Sidebar - Mobile Navigation Menu Overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 md:hidden">
          <aside className="w-64 bg-gov-navy text-slate-100 flex flex-col h-full animate-slide-in">
            <div className="p-5 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-white p-1 rounded-full text-gov-navy flex items-center justify-center">
                  <GraduationCap size={20} aria-hidden="true" />
                </div>
                <h1 className="text-sm font-bold uppercase leading-tight">Placement Portal</h1>
              </div>
              <button 
                onClick={() => setMobileOpen(false)} 
                aria-label="Close Mobile Navigation Menu"
                className="text-slate-400 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-white rounded p-1"
              >
                <X size={20} aria-hidden="true" />
              </button>
            </div>

            <nav aria-label="Mobile Navigation" className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
              {navLinks.map((link) => {
                const isActive = location.pathname === link.path;
                return (
                  <button
                    key={link.label}
                    onClick={() => {
                      navigate(link.path);
                      setMobileOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-white ${
                      isActive 
                        ? 'bg-gov-blue text-white' 
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    }`}
                  >
                    <span aria-hidden="true">{link.icon}</span>
                    <span>{link.label}</span>
                  </button>
                );
              })}
            </nav>

            <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="bg-gov-blue text-white w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm uppercase">
                  {user.name.charAt(0)}
                </div>
                <div>
                  <p className="text-xs font-semibold text-white">{user.name}</p>
                  <p className="text-[10px] text-slate-400 capitalize">{user.role}</p>
                </div>
              </div>
              <button 
                onClick={handleLogout} 
                aria-label="Log Out"
                className="text-slate-400 hover:text-red-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-white rounded p-1"
              >
                <LogOut size={16} aria-hidden="true" />
              </button>
            </div>
          </aside>
        </div>
      )}

      {/* Main content wrapper */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Sticky Top Header */}
        <header className="h-16 bg-white dark:bg-slate-900 border-b border-gov-border dark:border-slate-800 flex items-center justify-between px-6 sticky top-0 z-10 no-print">
          {/* Menu button & Title */}
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setMobileOpen(true)}
              aria-label="Open Mobile Navigation Menu"
              className="p-1 text-slate-600 dark:text-slate-300 md:hidden hover:bg-slate-100 dark:hover:bg-slate-800 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
            >
              <Menu size={20} aria-hidden="true" />
            </button>
            
            <div className="hidden sm:block">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
                Placement Cell Portal
              </span>
              <h2 className="text-sm font-semibold text-gov-navy dark:text-slate-200 uppercase">
                {user.role === 'student' ? 'Student Workspace' : user.role === 'parent' ? 'Parent Portal' : user.role === 'faculty' ? 'Officer Control Panel' : 'System Administration'}
              </h2>
            </div>
          </div>

          {/* Right Header Panel widgets */}
          <div className="flex items-center gap-5">
            {/* Lang translator */}
            <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800 px-2 py-1.5 rounded cursor-pointer transition-colors">
              <Globe size={14} className="text-gov-blue" />
              <span>{lang}</span>
              <ChevronDown size={12} />
            </div>

            {/* Current system status marker */}
            <div className="hidden md:flex items-center gap-1.5 bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full text-[10px] font-semibold dark:bg-emerald-950/30 dark:text-emerald-400 border border-emerald-200/50 dark:border-emerald-900/30">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 pulse-glow"></span>
              <span>System Services Active</span>
            </div>

            {/* Notification bell */}
            <button 
              aria-label="Notifications"
              className="text-slate-600 dark:text-slate-300 hover:text-gov-blue dark:hover:text-white transition-colors relative p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
            >
              <Bell size={18} aria-hidden="true" />
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" aria-hidden="true"></span>
            </button>

            {/* Short Divider */}
            <div className="h-6 w-px bg-slate-200 dark:bg-slate-800"></div>

            {/* User Profile Info */}
            <div className="flex items-center gap-3">
              <div className="hidden lg:block text-right">
                <p className="text-xs font-bold text-slate-800 dark:text-slate-200">{user.name}</p>
                <p className="text-[10px] text-slate-500 font-medium capitalize">{user.role} Account</p>
              </div>
              <div className="bg-gov-navy text-white w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm shadow-premium select-none">
                {user.name.charAt(0)}
              </div>
            </div>
          </div>
        </header>

        {/* Dynamic page main content body */}
        <main className="flex-1 p-6 overflow-y-auto print-expand">
          {children}
        </main>
      </div>
    </div>
  );
};
export default DashboardLayout;
