import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { analyticsService, studentService, driveService, aiService, permissionService } from '../services/api';
import { ProfessionalTable } from '../components/ProfessionalTable';
import { CardSkeleton, ChartSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, Legend
} from 'recharts';
import { 
  Users, Briefcase, TrendingUp, AlertTriangle, Filter, Download, 
  Brain, FileSpreadsheet, PieChart as PieIcon, BarChart2, BookOpen, Calendar,
  Printer, Smile, Meh, Frown, PlusCircle, ChevronRight, GraduationCap,
  KeyRound, ShieldCheck, CheckCircle2, AlertCircle, Clock
} from 'lucide-react';
import { AccessibleTabs, AccessibleChart, AccessibleModal } from '../components/AccessibilityComponents';
import { DepartmentPlacementDetailsView } from '../components/DepartmentPlacementDetailsView';
import { DriveFeedbackReportModal } from '../components/DriveFeedbackReportModal';

export const FacultyDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const userDeptId = user?.faculty_profile?.dept_id;
  const isDeptScoped = user?.role === 'faculty' && userDeptId && !user?.permissions?.includes('ALL_DEPT');

  const [activeTab, setActiveTab] = useState<'analytics' | 'students' | 'drives' | 'company-analytics' | 'sentiment' | 'ai-insights' | 'exporter'>('analytics');
  const [loading, setLoading] = useState(true);
  const [feedbackReportDriveId, setFeedbackReportDriveId] = useState<number | null>(null);
  const [selectedDriveForReport, setSelectedDriveForReport] = useState<string>('');
  
  // Dynamic filter states - default to faculty member's department if scoped
  const [filterDept, setFilterDept] = useState<number | undefined>(userDeptId);
  const [filterBatch, setFilterBatch] = useState<string>('2026');
  const [filterGender, setFilterGender] = useState<string | undefined>(undefined);

  // Data states
  const [stats, setStats] = useState<any>(null);
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  const [students, setStudents] = useState<any[]>([]);
  const [drives, setDrives] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  const [sentimentData, setSentimentData] = useState<any>(null);

  // Forms states
  const [showAddDrive, setShowAddDrive] = useState(false);
  const [showAddCompany, setShowAddCompany] = useState(false);
  const [newCompany, setNewCompany] = useState({ name: '', industry: '', website: '', description: '' });
  const [newDrive, setNewDrive] = useState({ 
    company_id: 0, 
    role: '', 
    package_lpa: 0, 
    location: '', 
    cgpa_cutoff: 0.0, 
    allowed_depts: 'CSE,IT', 
    allowed_backlogs: 0, 
    bond_details: 'No Bond', 
    selection_process: 'Aptitude -> Technical -> HR', 
    interview_date: '', 
    deadline: '',
    job_id: '',
    responsibilities: '',
    required_skills: '',
    preferred_skills: '',
    job_type: 'Full-Time',
    work_mode: 'Onsite',
    openings_count: 5,
    hiring_process: 'Aptitude -> Technical -> HR',
    company_logo: ''
  });

  // Exporter states
  const [exportType, setExportType] = useState<string>('student');
  const [exportDept, setExportDept] = useState<number | undefined>(undefined);
  const [exportData, setExportData] = useState<any[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Job Description Intelligence States
  const [selectedCompanyAnalyticsId, setSelectedCompanyAnalyticsId] = useState<number | null>(null);
  const [companyAnalyticsData, setCompanyAnalyticsData] = useState<any | null>(null);
  const [loadingCompanyAnalytics, setLoadingCompanyAnalytics] = useState(false);
  const [aiInsightsData, setAiInsightsData] = useState<any | null>(null);
  const [loadingAiInsights, setLoadingAiInsights] = useState(false);

  // Permission Request States
  const [showAccessModal, setShowAccessModal] = useState(false);
  const [submittingAccess, setSubmittingAccess] = useState(false);
  const [accessSuccess, setAccessSuccess] = useState<string | null>(null);
  const [accessError, setAccessError] = useState<string | null>(null);
  const [accessForm, setAccessForm] = useState({
    module: 'Placement Drives',
    scope: 'DEPARTMENT',
    scope_value: 'CSE',
    action: 'VIEW',
    duration_days: 7,
    reason: ''
  });
  const [myRequests, setMyRequests] = useState<any[]>([]);
  const [loadingRequests, setLoadingRequests] = useState(false);

  const loadMyRequests = async () => {
    setLoadingRequests(true);
    try {
      const data = await permissionService.getRequests();
      setMyRequests(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load permission requests', err);
    } finally {
      setLoadingRequests(false);
    }
  };

  const handleAccessSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessForm.reason.trim()) {
      setAccessError('Please provide an academic justification reason for your request.');
      return;
    }
    setSubmittingAccess(true);
    setAccessSuccess(null);
    setAccessError(null);
    try {
      await permissionService.submitRequest({
        ...accessForm,
        duration_days: Number(accessForm.duration_days)
      });
      setAccessSuccess('Access scope request submitted successfully to administrators.');
      setAccessForm(prev => ({ ...prev, reason: '' }));
      loadMyRequests();
    } catch (err: any) {
      setAccessError(err.response?.data?.detail || 'Failed to submit access request.');
    } finally {
      setSubmittingAccess(false);
    }
  };

  // Fetch metrics depending on active filters
  const loadDashboardStats = async () => {
    setLoading(true);
    setDashboardError(null);
    try {
      const filters = {
        dept_id: filterDept,
        batch: filterBatch,
        gender: filterGender
      };
      const data = await analyticsService.getDashboardStats(filters);
      setStats(data);
    } catch (err: any) {
      console.error('Failed to load dashboard metrics', err);
      setDashboardError(err.response?.data?.detail || 'Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userDeptId && filterDept === undefined) {
      setFilterDept(userDeptId);
    }
  }, [userDeptId]);

  // Fetch static data (companies, drives, student list, NLP sentiment)
  const loadStaticData = async () => {
    try {
      const studentList = await studentService.getStudents({ limit: 1000, batch: filterBatch });
      const studentItems = Array.isArray(studentList?.items) ? studentList.items : (Array.isArray(studentList) ? studentList : []);
      setStudents(studentItems);

      const drivesList = await driveService.getDrives();
      setDrives(drivesList);

      const comps = await driveService.getCompanies();
      setCompanies(comps);
      if (comps.length > 0) {
        setNewDrive(prev => ({ ...prev, company_id: comps[0].id }));
      }

      const sentiment = await aiService.getFeedbackSentiment();
      setSentimentData(sentiment);
    } catch (err) {
      console.error('Failed to load static datasets', err);
    }
  };

  useEffect(() => {
    loadDashboardStats();
  }, [filterDept, filterBatch, filterGender]);

  useEffect(() => {
    loadStaticData();
  }, [filterBatch]);

  // Handle adding a new company
  const handleAddCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await driveService.createCompany(newCompany);
      alert('Company added successfully!');
      setNewCompany({ name: '', industry: '', website: '', description: '' });
      setShowAddCompany(false);
      loadStaticData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add company');
    }
  };

  // Handle scheduling a drive
  const handleAddDrive = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await driveService.createDrive(newDrive);
      alert('Placement drive scheduled successfully!');
      setShowAddDrive(false);
      loadStaticData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to schedule drive');
    }
  };

  // Fetch preview report data
  const handlePreviewReport = async () => {
    setPreviewLoading(true);
    try {
      const data = await analyticsService.getReportData(exportType, exportDept, filterBatch);
      setExportData(data);
    } catch (err) {
      alert('Failed to preview report.');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  // Columns for Student table
  const studentColumns = [
    { header: 'Roll No', accessor: 'id', render: (row: any) => <span>#{row.id * 11}</span> },
    { header: 'Student Name', accessor: 'name' },
    { header: 'Branch', accessor: 'dept_code' },
    { header: 'CGPA', accessor: 'cgpa' },
    { header: 'Placement Preparation', accessor: 'readiness_score', render: (row: any) => <span className="font-semibold">{row.readiness_score}/100</span> },
    { 
      header: 'Placement Outlook %', 
      accessor: 'placement_probability', 
      render: (row: any) => (
        <span className={`font-semibold ${row.placement_probability >= 0.7 ? 'text-emerald-600' : row.placement_probability < 0.4 ? 'text-red-500' : 'text-amber-500'}`}>
          {(row.placement_probability * 100).toFixed(0)}%
        </span>
      )
    },
    { 
      header: 'Placement Status', 
      accessor: 'status', 
      render: (row: any) => (
        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
          row.status === 'Placed' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : row.status === 'At Risk' ? 'bg-red-50 text-red-800 border border-red-200' : 'bg-amber-50 text-amber-800 border border-amber-200'
        }`}>
          {row.status}
        </span>
      ) 
    }
  ];

  // Recharts color list
  const COLORS = ['#0F2942', '#328CC1', '#D9B310', '#B45309', '#0D9488', '#4F46E5'];

  const loadCompanyAnalytics = async (companyId: number) => {
    setLoadingCompanyAnalytics(true);
    try {
      const data = await analyticsService.getCompanyAnalytics(companyId);
      setCompanyAnalyticsData(data);
    } catch (err) {
      console.error("Failed to load company analytics", err);
    } finally {
      setLoadingCompanyAnalytics(false);
    }
  };

  const loadAiInsights = async () => {
    setLoadingAiInsights(true);
    try {
      const data = await aiService.getAIInsights();
      setAiInsightsData(data);
    } catch (err) {
      console.error("Failed to load AI insights", err);
    } finally {
      setLoadingAiInsights(false);
    }
  };

  // Sort companies so recruiters with active drives appear first
  const sortedCompanies = useMemo(() => {
    if (!companies || companies.length === 0) return [];
    const activeCompanyIds = new Set(drives.map((d: any) => d.company_id));
    return [...companies].sort((a, b) => {
      const aHas = activeCompanyIds.has(a.id) ? 1 : 0;
      const bHas = activeCompanyIds.has(b.id) ? 1 : 0;
      if (aHas !== bHas) return bHas - aHas; // Active drives prioritized
      return a.name.localeCompare(b.name);
    });
  }, [companies, drives]);

  useEffect(() => {
    if (isDeptScoped && userDeptId && filterDept !== userDeptId) {
      setFilterDept(userDeptId);
    }
  }, [isDeptScoped, userDeptId]);

  useEffect(() => {
    if (sortedCompanies && sortedCompanies.length > 0) {
      if (!selectedCompanyAnalyticsId || !sortedCompanies.some(c => c.id === selectedCompanyAnalyticsId)) {
        setSelectedCompanyAnalyticsId(sortedCompanies[0].id);
      }
    }
  }, [sortedCompanies, selectedCompanyAnalyticsId]);

  useEffect(() => {
    if (selectedCompanyAnalyticsId) {
      loadCompanyAnalytics(selectedCompanyAnalyticsId);
    }
  }, [selectedCompanyAnalyticsId]);

  useEffect(() => {
    if (activeTab === 'ai-insights') {
      loadAiInsights();
    }
  }, [activeTab]);

  return (
    <div className="space-y-6">
      {/* Filters Dock */}
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-4 rounded-lg shadow-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4 no-print">
        <div className="flex items-center justify-between w-full md:w-auto gap-4">
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-gov-blue" />
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">
              Portal Analytics Filters
            </h3>
          </div>
          <button
            onClick={() => {
              setShowAccessModal(true);
              loadMyRequests();
            }}
            className="gov-btn-primary py-1.5 px-3 bg-gov-navy text-white rounded flex items-center gap-1.5 hover:bg-slate-800 text-xs font-semibold shrink-0"
            title="Request elevated module permissions or department scope"
          >
            <KeyRound size={13} />
            Request Access Scope
          </button>
        </div>

        <div className="flex flex-wrap gap-4 text-xs">
          <div>
            <label className="block font-bold text-slate-500 uppercase mb-1">Batch Year</label>
            <select
              value={filterBatch}
              onChange={(e) => setFilterBatch(e.target.value)}
              className="border border-gov-border rounded p-2 bg-white text-slate-700 dark:bg-slate-950 dark:border-slate-850 dark:text-slate-200 focus:outline-none"
            >
              <option value="2026">2026 (Active)</option>
              <option value="2025">2025 (Graduated)</option>
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block font-bold text-slate-500 uppercase">Department</label>
              {isDeptScoped && (
                <span className="text-[9px] font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-1 rounded ml-1">
                  Scoped
                </span>
              )}
            </div>
            <select
              value={filterDept || ''}
              onChange={(e) => setFilterDept(e.target.value ? Number(e.target.value) : undefined)}
              disabled={isDeptScoped}
              className={`border border-gov-border rounded p-2 bg-white text-slate-700 dark:bg-slate-950 dark:border-slate-850 dark:text-slate-200 focus:outline-none ${isDeptScoped ? 'opacity-90 cursor-not-allowed' : ''}`}
              title={isDeptScoped ? "Department filter is scoped to your assigned faculty department. Submit an access scope request for cross-department data." : "Select department to filter"}
            >
              {isDeptScoped ? (
                <option value={userDeptId}>
                  {user?.faculty_profile?.dept_name || 'My Department'} ({user?.faculty_profile?.dept_code || 'Dept'})
                </option>
              ) : (
                <>
                  <option value="">All Departments</option>
                  <option value="1">Computer Science (CSE)</option>
                  <option value="2">Information Tech (IT)</option>
                  <option value="3">Electronics (ECE)</option>
                  <option value="4">Electrical (EEE)</option>
                  <option value="5">Mechanical (MECH)</option>
                  <option value="6">Civil (CIVIL)</option>
                </>
              )}
            </select>
          </div>

          <div>
            <label className="block font-bold text-slate-500 uppercase mb-1">Student Gender</label>
            <select
              value={filterGender || ''}
              onChange={(e) => setFilterGender(e.target.value ? e.target.value : undefined)}
              className="border border-gov-border rounded p-2 bg-white text-slate-700 dark:bg-slate-950 dark:border-slate-850 dark:text-slate-200 focus:outline-none"
            >
              <option value="">All Genders</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <AccessibleTabs
        tabs={[
          { id: 'analytics', label: 'Analytics Dashboard', icon: <PieIcon size={16} /> },
          { id: 'students', label: 'Department Student Placements', icon: <GraduationCap size={16} /> },
          { id: 'sentiment', label: 'Drive Feedback & Reviews', icon: <Smile size={16} /> },
          { id: 'company-analytics', label: 'Company Analytics', icon: <BarChart2 size={16} /> },
          { id: 'ai-insights', label: 'Institutional Insights', icon: <TrendingUp size={16} /> }
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
        ariaLabel="Placement Officer Portal Sections"
      />

      {/* TAB 1: ANALYTICS DASHBOARD */}
      {activeTab === 'analytics' && (
        <div id="panel-analytics" role="tabpanel" aria-labelledby="tab-analytics" className="space-y-6">
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)}
            </div>
          ) : dashboardError ? (
            <div className="gov-card p-6 border-l-4 border-l-red-500 bg-red-50/50 dark:bg-red-950/20 text-center space-y-3">
              <div className="flex items-center justify-center gap-2 text-red-600 dark:text-red-400 font-bold text-sm">
                <AlertCircle size={20} />
                <span>{dashboardError}</span>
              </div>
              <button
                onClick={loadDashboardStats}
                className="px-4 py-2 bg-gov-navy text-white text-xs font-semibold rounded hover:bg-slate-800 transition"
              >
                Retry Loading Metrics
              </button>
            </div>
          ) : stats ? (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 no-print">
                <div 
                  onClick={() => navigate(`/student-tracker?status=Placed&batch=${filterBatch}${filterDept ? `&dept_id=${filterDept}` : ''}`)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      navigate(`/student-tracker?status=Placed&batch=${filterBatch}${filterDept ? `&dept_id=${filterDept}` : ''}`);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  className="gov-card border-l-4 border-l-emerald-500 cursor-pointer hover:shadow-md hover:border-emerald-600 transition group relative focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
                  title="Click to view all Placed students in the Student Tracker"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Overall Placement Percentage</p>
                    <span className="text-emerald-500 opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all">
                      <ChevronRight size={16} />
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">{stats.placement_percentage}%</p>
                  <div className="flex items-center justify-between mt-1 text-[10px]">
                    <p className="text-emerald-600">Placed: {stats.placed_students} / {stats.total_students}</p>
                    <span className="font-bold text-emerald-600 dark:text-emerald-400 group-hover:underline flex items-center gap-0.5">
                      View {stats.placed_students} Students &rarr;
                    </span>
                  </div>
                </div>
                
                <div className="gov-card">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Highest Package Offered</p>
                  <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">{stats.highest_package} LPA</p>
                  <p className="text-[10px] text-slate-500 mt-1">Direct from database records</p>
                </div>

                <div className="gov-card">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Average Package (LPA)</p>
                  <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">{stats.average_package} LPA</p>
                  <p className="text-[10px] text-slate-500 mt-1">Median Package: {stats.median_package} LPA</p>
                </div>

                <div 
                  onClick={() => navigate(`/student-tracker?status=At%20Risk&batch=${filterBatch}${filterDept ? `&dept_id=${filterDept}` : ''}`)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      navigate(`/student-tracker?status=At%20Risk&batch=${filterBatch}${filterDept ? `&dept_id=${filterDept}` : ''}`);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  className="gov-card border-l-4 border-l-red-500 cursor-pointer hover:shadow-md hover:border-red-600 transition group relative focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 bg-red-50/20 dark:bg-red-950/10"
                  title="Click to view all At Risk students in the Student Tracker"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Students At Risk (Low score)</p>
                    <span className="text-red-500 opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all">
                      <ChevronRight size={16} />
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{stats.at_risk_count}</p>
                  <div className="flex items-center justify-between mt-1 text-[10px]">
                    <p className="text-slate-500">Needs urgent attention</p>
                    <span className="font-bold text-red-600 dark:text-red-400 group-hover:underline flex items-center gap-0.5">
                      View {stats.at_risk_count} Students &rarr;
                    </span>
                  </div>
                </div>
              </div>

              {/* Charts grid */}
              <div className="grid md:grid-cols-2 gap-6 no-print">
                {/* Branch hiring bar chart */}
                <div className="gov-card flex flex-col justify-between h-80">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase mb-4">Branch-wise Placement %</h4>
                  <div className="flex-1 min-h-0">
                    <ResponsiveContainer width="100%" height="100%">
                      {!Array.isArray(stats.branch_hiring) || stats.branch_hiring.length === 0 ? (
                        <div className="h-full flex items-center justify-center text-slate-400 text-xs font-semibold">
                          No branch placement records found for current filters.
                        </div>
                      ) : (
                        <BarChart data={stats.branch_hiring}>
                          <XAxis dataKey="dept_code" tick={{ fontSize: 10 }} />
                          <YAxis tick={{ fontSize: 10 }} />
                          <Tooltip />
                          <Bar dataKey="percentage" name="Placement Rate" fill="#0F2942" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      )}
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Monthly trend line chart */}
                <div className="gov-card flex flex-col justify-between h-80">
                  <AccessibleChart
                    title="Monthly Placement Timeline"
                    description="Placement timelines show count of students registered and placed dynamically per month."
                    data={Array.isArray(stats.monthly_trend) ? stats.monthly_trend : []}
                    keys={[{ dataKey: 'placements', label: 'Students Placed' }]}
                    labelKey="month"
                  >
                    <ResponsiveContainer width="100%" height="100%">
                      {!Array.isArray(stats.monthly_trend) || stats.monthly_trend.length === 0 ? (
                        <div className="h-full flex items-center justify-center text-slate-400 text-xs font-semibold">
                          No monthly placement timelines recorded for current filters.
                        </div>
                      ) : (
                        <LineChart data={stats.monthly_trend}>
                          <XAxis dataKey="month" tick={{ fontSize: 10 }} />
                          <YAxis tick={{ fontSize: 10 }} />
                          <Tooltip />
                          <Line type="monotone" dataKey="placements" name="Students Placed" stroke="#328CC1" strokeWidth={2} activeDot={{ r: 6 }} />
                        </LineChart>
                      )}
                    </ResponsiveContainer>
                  </AccessibleChart>
                </div>
              </div>

              {/* Second row of charts */}
              <div className="grid md:grid-cols-3 gap-6 no-print">
                {/* Gender distribution */}
                <div className="gov-card flex flex-col justify-between h-80">
                  <AccessibleChart
                    title="Gender Placement Ratios"
                    description="Gender-wise allocation ratios for offer distribution."
                    data={Array.isArray(stats.gender_stats) ? stats.gender_stats : []}
                    keys={[{ dataKey: 'placed', label: 'Placed Count' }]}
                    labelKey="gender"
                  >
                    <ResponsiveContainer width="100%" height="100%">
                      {!Array.isArray(stats.gender_stats) || stats.gender_stats.length === 0 ? (
                        <div className="h-full flex items-center justify-center text-slate-400 text-xs font-semibold">
                          No gender statistics available for this selection.
                        </div>
                      ) : (
                        <PieChart>
                          <Pie
                            data={stats.gender_stats}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={70}
                            paddingAngle={5}
                            dataKey="placed"
                            nameKey="gender"
                            label={({ gender, percentage }) => `${gender}: ${percentage}%`}
                          >
                            {stats.gender_stats.map((entry: any, index: number) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      )}
                    </ResponsiveContainer>
                  </AccessibleChart>
                </div>

                {/* Placement pipeline funnel */}
                <div className="gov-card flex flex-col justify-between h-80 md:col-span-2">
                  <AccessibleChart
                    title="Recruitment Pipeline Funnel"
                    description="Funnel showing total student count transitioning across selection stages."
                    data={Array.isArray(stats.funnel_data) ? stats.funnel_data : []}
                    keys={[{ dataKey: 'count', label: 'Candidates Count' }]}
                    labelKey="stage"
                  >
                    <ResponsiveContainer width="100%" height="100%">
                      {!Array.isArray(stats.funnel_data) || stats.funnel_data.length === 0 ? (
                        <div className="h-full flex items-center justify-center text-slate-400 text-xs font-semibold">
                          No candidate recruitment funnel activity reported.
                        </div>
                      ) : (
                        <BarChart data={stats.funnel_data} layout="vertical">
                          <XAxis type="number" tick={{ fontSize: 10 }} />
                          <YAxis dataKey="stage" type="category" tick={{ fontSize: 10 }} width={120} />
                          <Tooltip />
                          <Bar dataKey="count" fill="#328CC1" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      )}
                    </ResponsiveContainer>
                  </AccessibleChart>
                </div>
              </div>

            </>
          ) : (
            <div className="gov-card p-8 text-center text-slate-400 text-xs font-semibold">
              No analytics data available for the selected filters.
            </div>
          )}
        </div>
      )}

      {/* TAB 2: DEPARTMENT STUDENT PLACEMENT DETAILS */}
      {activeTab === 'students' && (
        <div id="panel-students" role="tabpanel" aria-labelledby="tab-students" className="space-y-6 no-print">
          <DepartmentPlacementDetailsView initialDeptId={filterDept} initialBatch={filterBatch} />
        </div>
      )}

      {/* TAB 3: PLACEMENT DRIVES */}
      {activeTab === 'drives' && (
        <div id="panel-drives" role="tabpanel" aria-labelledby="tab-drives" className="grid md:grid-cols-3 gap-6 no-print">
          {/* Drives schedule list */}
          <div className="gov-card md:col-span-2 space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-gov-border dark:border-slate-800">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Calendar size={18} className="text-gov-blue" />
                Active Placement Schedules
              </h3>
              <button
                onClick={() => setShowAddDrive(!showAddDrive)}
                className="gov-btn-primary py-1 px-3 text-xs font-bold uppercase tracking-wide flex items-center gap-1.5"
              >
                <PlusCircle size={14} /> Schedule Drive
              </button>
            </div>

            {showAddDrive && (
              <form onSubmit={handleAddDrive} className="bg-slate-50 dark:bg-slate-950 p-4 border border-gov-border dark:border-slate-850 rounded-lg text-xs space-y-4">
                <h4 className="font-bold text-slate-700 dark:text-slate-300 uppercase">Create Recruitment Calendar Event</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="add-drive-company" className="block font-bold text-slate-500 uppercase">Recruiting Company <span className="text-red-500">*</span></label>
                    <select
                      id="add-drive-company"
                      required
                      aria-required="true"
                      value={newDrive.company_id}
                      onChange={(e) => setNewDrive({ ...newDrive, company_id: Number(e.target.value) })}
                      className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                    >
                      {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label htmlFor="add-drive-role" className="block font-bold text-slate-500 uppercase">Hiring Role <span className="text-red-500">*</span></label>
                    <input
                      id="add-drive-role"
                      type="text"
                      required
                      aria-required="true"
                      value={newDrive.role}
                      onChange={(e) => setNewDrive({ ...newDrive, role: e.target.value })}
                      className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                      placeholder="e.g. Associate Software Engineer"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label htmlFor="add-drive-package" className="block font-bold text-slate-500 uppercase">Salary Package (LPA) <span className="text-red-500">*</span></label>
                    <input
                      id="add-drive-package"
                      type="number"
                      step="0.1"
                      required
                      aria-required="true"
                      value={newDrive.package_lpa}
                      onChange={(e) => setNewDrive({ ...newDrive, package_lpa: Number(e.target.value) })}
                      className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                    />
                  </div>
                  <div>
                    <label htmlFor="add-drive-cgpa" className="block font-bold text-slate-500 uppercase">CGPA Cutoff <span className="text-red-500">*</span></label>
                    <input
                      id="add-drive-cgpa"
                      type="number"
                      step="0.01"
                      required
                      aria-required="true"
                      value={newDrive.cgpa_cutoff}
                      onChange={(e) => setNewDrive({ ...newDrive, cgpa_cutoff: Number(e.target.value) })}
                      className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                    />
                  </div>
                  <div>
                    <label htmlFor="add-drive-backlogs" className="block font-bold text-slate-500 uppercase">Backlog Cutoff <span className="text-red-500">*</span></label>
                    <input
                      id="add-drive-backlogs"
                      type="number"
                      required
                      aria-required="true"
                      value={newDrive.allowed_backlogs}
                      onChange={(e) => setNewDrive({ ...newDrive, allowed_backlogs: Number(e.target.value) })}
                      className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="add-drive-depts" className="block font-bold text-slate-500 uppercase">Allowed Departments <span className="text-red-500">*</span></label>
                    <input
                      id="add-drive-depts"
                      type="text"
                      required
                      aria-required="true"
                      value={newDrive.allowed_depts}
                      onChange={(e) => setNewDrive({ ...newDrive, allowed_depts: e.target.value })}
                      className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                      placeholder="e.g. CSE,IT,ECE"
                    />
                  </div>
                  <div>
                    <label htmlFor="add-drive-location" className="block font-bold text-slate-500 uppercase">Recruitment Location <span className="text-red-500">*</span></label>
                    <input
                      id="add-drive-location"
                      type="text"
                      required
                      aria-required="true"
                      value={newDrive.location}
                      onChange={(e) => setNewDrive({ ...newDrive, location: e.target.value })}
                      className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                      placeholder="e.g. Hyderabad"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="add-drive-date" className="block font-bold text-slate-500 uppercase">Interview Date <span className="text-red-500">*</span></label>
                    <input
                      id="add-drive-date"
                      type="date"
                      required
                      aria-required="true"
                      value={newDrive.interview_date}
                      onChange={(e) => setNewDrive({ ...newDrive, interview_date: e.target.value })}
                      className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                    />
                  </div>
                  <div>
                    <label htmlFor="add-drive-deadline" className="block font-bold text-slate-500 uppercase">Application Deadline <span className="text-red-500">*</span></label>
                    <input
                      id="add-drive-deadline"
                      type="date"
                      required
                      aria-required="true"
                      value={newDrive.deadline}
                      onChange={(e) => setNewDrive({ ...newDrive, deadline: e.target.value })}
                      className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                    />
                  </div>
                </div>

                 <div className="border-t border-gov-border dark:border-slate-800 pt-3 space-y-3">
                  <h5 className="font-bold text-slate-700 dark:text-slate-300 uppercase text-[10px]">Job Description Specifications</h5>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="add-drive-jobid" className="block font-bold text-slate-500 uppercase">Job ID</label>
                      <input
                        id="add-drive-jobid"
                        type="text"
                        value={newDrive.job_id}
                        onChange={(e) => setNewDrive({ ...newDrive, job_id: e.target.value })}
                        className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                        placeholder="e.g. JD-2026-001"
                      />
                    </div>
                    <div>
                      <label htmlFor="add-drive-funnel" className="block font-bold text-slate-500 uppercase">Hiring Funnel Outline</label>
                      <input
                        id="add-drive-funnel"
                        type="text"
                        value={newDrive.hiring_process}
                        onChange={(e) => setNewDrive({ ...newDrive, hiring_process: e.target.value })}
                        className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                        placeholder="e.g. Online MCQ -> Coding test -> Technical -> HR"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label htmlFor="add-drive-type" className="block font-bold text-slate-500 uppercase">Job Type</label>
                      <select
                        id="add-drive-type"
                        value={newDrive.job_type}
                        onChange={(e) => setNewDrive({ ...newDrive, job_type: e.target.value })}
                        className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                      >
                        <option value="Full-Time">Full-Time</option>
                        <option value="Internship">Internship</option>
                      </select>
                    </div>
                    <div>
                      <label htmlFor="add-drive-mode" className="block font-bold text-slate-500 uppercase">Work Mode</label>
                      <select
                        id="add-drive-mode"
                        value={newDrive.work_mode}
                        onChange={(e) => setNewDrive({ ...newDrive, work_mode: e.target.value })}
                        className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                      >
                        <option value="Onsite">Onsite</option>
                        <option value="Hybrid">Hybrid</option>
                        <option value="Remote">Remote</option>
                      </select>
                    </div>
                    <div>
                      <label htmlFor="add-drive-openings" className="block font-bold text-slate-500 uppercase">Openings Count</label>
                      <input
                        id="add-drive-openings"
                        type="number"
                        value={newDrive.openings_count}
                        onChange={(e) => setNewDrive({ ...newDrive, openings_count: Number(e.target.value) })}
                        className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="add-drive-req-skills" className="block font-bold text-slate-500 uppercase">Required Skills (Comma-Separated)</label>
                      <input
                        id="add-drive-req-skills"
                        type="text"
                        value={newDrive.required_skills}
                        onChange={(e) => setNewDrive({ ...newDrive, required_skills: e.target.value })}
                        className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                        placeholder="React, SQL, Java..."
                      />
                    </div>
                    <div>
                      <label htmlFor="add-drive-pref-skills" className="block font-bold text-slate-500 uppercase">Preferred Skills (Comma-Separated)</label>
                      <input
                        id="add-drive-pref-skills"
                        type="text"
                        value={newDrive.preferred_skills}
                        onChange={(e) => setNewDrive({ ...newDrive, preferred_skills: e.target.value })}
                        className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                        placeholder="AWS, Docker..."
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="add-drive-responsibilities" className="block font-bold text-slate-500 uppercase">Role Summary & Responsibilities</label>
                    <textarea
                      id="add-drive-responsibilities"
                      value={newDrive.responsibilities}
                      onChange={(e) => setNewDrive({ ...newDrive, responsibilities: e.target.value })}
                      className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 h-16 text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                      placeholder="Enter core responsibilities..."
                    />
                  </div>

                  <div>
                    <label htmlFor="add-drive-logo" className="block font-bold text-slate-500 uppercase">Company Logo URL Link</label>
                    <input
                      id="add-drive-logo"
                      type="text"
                      value={newDrive.company_logo}
                      onChange={(e) => setNewDrive({ ...newDrive, company_logo: e.target.value })}
                      className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                      placeholder="e.g. https://logo.clearbit.com/google.com"
                    />
                  </div>
                </div>

                <div className="flex gap-3 justify-end pt-2">
                  <button type="button" onClick={() => setShowAddDrive(false)} className="gov-btn-secondary py-1 px-3 font-semibold">Cancel</button>
                  <button type="submit" className="gov-btn-primary py-1 px-3 font-semibold">Schedule Calendar</button>
                </div>
              </form>
            )}

            <div className="space-y-4">
              {drives.map((d) => (
                <div key={d.id} className="border border-gov-border dark:border-slate-800 rounded p-4 flex justify-between items-center bg-white dark:bg-slate-900">
                  <div className="space-y-1">
                    <p className="text-[10px] font-bold text-slate-400 uppercase">{d.company_name} &bull; {d.status}</p>
                    <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase">{d.role}</h4>
                    <p className="text-[10px] text-slate-500">Package: {d.package_lpa} LPA &bull; Cutoff: {d.cgpa_cutoff} CGPA &bull; Allowed: {d.allowed_depts}</p>
                  </div>
                  <ChevronRight size={16} className="text-slate-400" />
                </div>
              ))}
            </div>
          </div>

          {/* Add Company card */}
          <div className="gov-card space-y-4 h-fit">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <PlusCircle size={18} className="text-gov-blue" />
              Register Recruiters
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Add corporate partners to the institutional placement list before scheduling recruiting drives.
            </p>

            <form onSubmit={handleAddCompany} className="space-y-3 text-xs">
              <div>
                <label htmlFor="reg-company-name" className="block font-bold text-slate-500 uppercase">Company Name <span className="text-red-500">*</span></label>
                <input
                  id="reg-company-name"
                  type="text"
                  required
                  aria-required="true"
                  value={newCompany.name}
                  onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-950 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                  placeholder="Google"
                />
              </div>

              <div>
                <label htmlFor="reg-company-industry" className="block font-bold text-slate-500 uppercase">Industry Domain <span className="text-red-500">*</span></label>
                <input
                  id="reg-company-industry"
                  type="text"
                  required
                  aria-required="true"
                  value={newCompany.industry}
                  onChange={(e) => setNewCompany({ ...newCompany, industry: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-950 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                  placeholder="Product Tech"
                />
              </div>

              <div>
                <label htmlFor="reg-company-website" className="block font-bold text-slate-500 uppercase">Company Website</label>
                <input
                  id="reg-company-website"
                  type="url"
                  value={newCompany.website}
                  onChange={(e) => setNewCompany({ ...newCompany, website: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded bg-white text-slate-800 dark:bg-slate-955 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                  placeholder="https://google.com"
                />
              </div>

              <button
                type="submit"
                className="gov-btn-primary w-full py-2.5 font-bold uppercase tracking-wider focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
              >
                Register Recruiter
              </button>
            </form>
          </div>
        </div>
      )}

      {/* TAB 4: STUDENT FEEDBACK ANALYSIS */}
      {activeTab === 'sentiment' && (
        <div id="panel-sentiment" role="tabpanel" aria-labelledby="tab-sentiment" className="space-y-6 no-print">
          {/* Drive Selector Bar for Consolidated Drive Feedback Report */}
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-4 rounded-lg shadow-card flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
            <div className="flex items-center gap-2">
              <Brain size={18} className="text-gov-blue" />
              <div>
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide">
                  Consolidated Placement Drive Feedback Report
                </h4>
                <p className="text-[11px] text-slate-500">
                  Select a recruitment drive to aggregate questions, topics, difficulty distribution, and candidate suggestions.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto">
              <select
                value={selectedDriveForReport}
                onChange={(e) => setSelectedDriveForReport(e.target.value)}
                className="border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-950 dark:text-slate-200 text-xs focus:outline-none focus:ring-1 focus:ring-gov-blue w-full sm:w-64"
              >
                <option value="">-- Select Placement Drive --</option>
                {drives.map((d: any) => (
                  <option key={d.id} value={d.id}>
                    {d.company_name} — {d.role} (#{d.id})
                  </option>
                ))}
              </select>
              <button
                onClick={() => {
                  if (selectedDriveForReport) {
                    setFeedbackReportDriveId(Number(selectedDriveForReport));
                  }
                }}
                disabled={!selectedDriveForReport}
                className="gov-btn-primary py-1.5 px-3 rounded uppercase font-bold text-[10px] flex items-center gap-1.5 bg-gov-navy hover:bg-slate-800 text-white shrink-0 shadow-sm disabled:opacity-50"
                title="Open Consolidated Feedback Report"
              >
                <Brain size={13} /> View Consolidated Report
              </button>
            </div>
          </div>

          {(!sentimentData) ? <CardSkeleton /> : (
            <>
              {/* sentiment metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="gov-card flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Average Interview Difficulty</p>
                    <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">{sentimentData.average_difficulty} / 5.0</p>
                    <p className="text-[10px] text-slate-500 mt-1">Based on student feedback reviews</p>
                  </div>
                  <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                    <BookOpen size={20} />
                  </div>
                </div>

                <div className="gov-card flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Feedbacks Collected</p>
                    <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">{sentimentData.total_feedbacks}</p>
                    <p className="text-[10px] text-slate-500 mt-1">Interview feedback monitoring active</p>
                  </div>
                  <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                    <Users size={20} />
                  </div>
                </div>

                <div className="gov-card flex flex-col justify-between">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Interview Feedback Distribution</p>
                  <div className="space-y-1.5 text-[11px]">
                    <div className="flex justify-between font-bold text-slate-600 dark:text-slate-300">
                      <span className="flex items-center gap-1"><Smile size={14} className="text-emerald-500" /> Positive: {sentimentData.sentiment_summary.positive_pct}%</span>
                      <span className="flex items-center gap-1"><Meh size={14} className="text-amber-500" /> Neutral: {sentimentData.sentiment_summary.neutral_pct}%</span>
                      <span className="flex items-center gap-1"><Frown size={14} className="text-red-500" /> Negative: {sentimentData.sentiment_summary.negative_pct}%</span>
                    </div>
                    {/* Sentiment bar */}
                    <div className="w-full bg-slate-200 h-2 rounded overflow-hidden flex">
                      <div className="bg-emerald-500" style={{ width: `${sentimentData.sentiment_summary.positive_pct}%` }}></div>
                      <div className="bg-amber-400" style={{ width: `${sentimentData.sentiment_summary.neutral_pct}%` }}></div>
                      <div className="bg-red-500" style={{ width: `${sentimentData.sentiment_summary.negative_pct}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Word Cloud and Common rejection reasons */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* CSS Based dynamic word cloud */}
                <div className="gov-card space-y-4">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Student Interview Word Cloud</h4>
                  <p className="text-[11px] text-slate-500 leading-normal">
                    Aggregated keywords extracted from experiences describing questions asked in technical rounds.
                  </p>
                  <div className="border border-gov-border dark:border-slate-800 rounded p-6 bg-slate-50 dark:bg-slate-950 flex flex-wrap gap-x-4 gap-y-3 justify-center items-center h-48 overflow-y-auto">
                    {sentimentData.word_cloud.map((w: any, idx: number) => {
                      const sizes = ['text-[11px]', 'text-xs', 'text-sm', 'text-base', 'text-lg', 'text-xl', 'text-2xl'];
                      const fontClass = sizes[Math.min(w.value, sizes.length - 1)];
                      const colors = ['text-slate-500', 'text-slate-700', 'text-gov-blue', 'text-gov-navy', 'text-sky-500'];
                      const colorClass = colors[idx % colors.length];

                      return (
                        <span key={idx} className={`${fontClass} ${colorClass} font-bold capitalize select-none cursor-help hover:underline`} title={`Occurrences: ${w.value}`}>
                          {w.text}
                        </span>
                      );
                    })}
                  </div>
                </div>

                {/* Common rejection reasons */}
                <div className="gov-card space-y-4">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Top 5 Interview Blockers & Skill Improvement Areas</h4>
                  <p className="text-[11px] text-slate-500 leading-normal">
                    Technical topics identified where students failed to clear interview rounds.
                  </p>
                  <div className="space-y-3">
                    {sentimentData.common_bottlenecks.map((bot: any, idx: number) => (
                      <div key={idx} className="flex justify-between items-center border-b border-gov-border dark:border-slate-800 pb-2.5 last:border-0 last:pb-0 text-xs">
                        <span className="font-semibold text-slate-700 dark:text-slate-300">{bot.bottleneck}</span>
                        <span className="bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400 px-2 py-0.5 rounded text-[10px] font-bold">
                          {bot.count} cases
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* TAB 5: REPORTS EXPORTER */}
      {activeTab === 'exporter' && (
        <div id="panel-exporter" role="tabpanel" aria-labelledby="tab-exporter" className="space-y-6 print-expand">
          {/* Exporter Config dock */}
          <div className="gov-card space-y-4 no-print">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <FileSpreadsheet size={18} className="text-gov-blue" />
              Configure Custom Institution Report Builder
            </h3>
            
            <div className="flex flex-wrap gap-4 text-xs">
              <div>
                <label htmlFor="export-category-select" className="block font-bold text-slate-500 uppercase mb-1">Report Category</label>
                <select
                  id="export-category-select"
                  value={exportType}
                  onChange={(e) => {
                    setExportType(e.target.value);
                    setExportData([]);
                  }}
                  className="border border-gov-border rounded p-2 bg-white text-slate-800 dark:bg-slate-950 dark:border-slate-800 dark:text-slate-200 focus:outline-none"
                >
                  <option value="student">Student Performance & Preparation</option>
                  <option value="company">Registered Recruiters & Packages</option>
                  <option value="placement">Placement Applications Outcomes</option>
                  <option value="ai">Placement Preparation Assessment Sheet</option>
                </select>
              </div>

              <div>
                <label htmlFor="export-branch-select" className="block font-bold text-slate-500 uppercase mb-1">Branch Filter</label>
                <select
                  id="export-branch-select"
                  value={exportDept || ''}
                  onChange={(e) => setExportDept(e.target.value ? Number(e.target.value) : undefined)}
                  className="border border-gov-border rounded p-2 bg-white text-slate-800 dark:bg-slate-950 dark:border-slate-800 dark:text-slate-200 focus:outline-none"
                >
                  <option value="">All Branches</option>
                  <option value="1">Computer Science (CSE)</option>
                  <option value="2">Information Tech (IT)</option>
                  <option value="3">Electronics (ECE)</option>
                  <option value="4">Electrical (EEE)</option>
                  <option value="5">Mechanical (MECH)</option>
                  <option value="6">Civil (CIVIL)</option>
                </select>
              </div>

              <div className="flex items-end gap-3">
                <button
                  onClick={handlePreviewReport}
                  className="gov-btn-primary py-2 px-4 font-bold uppercase tracking-wide flex items-center gap-1.5"
                >
                  Preview Report
                </button>
                
                {exportData.length > 0 && (
                  <button
                    onClick={handlePrint}
                    className="gov-btn-secondary py-2 px-4 font-bold uppercase tracking-wide flex items-center gap-1.5 hover:bg-slate-50 border border-gov-border"
                  >
                    <Printer size={14} className="text-gov-blue" />
                    <span>Print Report / Save PDF</span>
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Report Preview grid */}
          {exportData.length > 0 && (
            <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 rounded-lg p-8 shadow-card space-y-6 print-expand">
              {/* Header logo for printed reports */}
              <div className="flex justify-between items-center border-b-2 border-slate-900 dark:border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                  <div className="bg-slate-900 dark:bg-slate-800 text-white p-2 rounded-full flex items-center justify-center">
                    <GraduationCap size={32} />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
                      Placement Portal
                    </h2>
                    <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
                      Official Institutional Evaluation Report
                    </p>
                  </div>
                </div>
                <div className="text-right text-xs text-slate-500 font-semibold space-y-0.5">
                  <p>BATCH: {filterBatch}</p>
                  <p>DATE: {new Date().toLocaleDateString()}</p>
                  <p className="text-[10px] text-slate-400">REPORT CODE: REP-{exportType.toUpperCase()}-026</p>
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                  Report Type: {exportType === 'student' ? 'Student Performance Audit' : exportType === 'company' ? 'Recruiter Relations & Packages' : exportType === 'placement' ? 'Placement Application Summary' : 'Career Assessment Report'}
                </h3>
                <p className="text-xs text-slate-500 leading-normal">
                  The following records represent the compiled database snapshot for evaluation purposes. Authenticated by College Placement Director.
                </p>
              </div>

              {/* Data Table */}
              <div className="overflow-x-auto border border-slate-300 dark:border-slate-800 rounded">
                <table className="min-w-full divide-y divide-slate-300 dark:divide-slate-800 text-left text-xs">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-800">
                      {Object.keys(exportData[0]).map((key, i) => (
                        <th key={i} className="px-4 py-3 font-bold uppercase tracking-wider text-slate-700 dark:text-slate-350 border-b border-slate-350 dark:border-slate-750">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {exportData.map((row, rIdx) => (
                      <tr key={rIdx} className={rIdx % 2 === 1 ? 'bg-slate-50/40 dark:bg-slate-900/40' : ''}>
                        {Object.values(row).map((val: any, cIdx) => (
                          <td key={cIdx} className="px-4 py-3 text-slate-600 dark:text-slate-400 font-medium">
                            {val ?? '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Printed Signature line */}
              <div className="pt-16 flex justify-between items-center text-xs font-semibold text-slate-500">
                <div className="text-center">
                  <div className="h-0.5 w-40 bg-slate-300 mx-auto mb-1"></div>
                  <p>Prepared by Coordinator</p>
                </div>
                <div className="text-center">
                  <div className="h-0.5 w-40 bg-slate-300 mx-auto mb-1"></div>
                  <p>Chief Placement Officer Sign</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB: COMPANY-SPECIFIC ANALYTICS */}
      {activeTab === 'company-analytics' && (
        <div id="panel-company-analytics" role="tabpanel" aria-labelledby="tab-company-analytics" className="space-y-6">
          <div className="gov-card flex flex-col sm:flex-row justify-between sm:items-center gap-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">Recruiter Specific Analytics</h3>
              <p className="text-xs text-slate-500">Query detailed selection records, department hiring ratios, and rejection reasons per partner company.</p>
            </div>
            
            <div className="shrink-0 flex items-center gap-2">
              <label htmlFor="company-analytics-select" className="text-[10px] font-bold text-slate-500 uppercase">Select Partner:</label>
              <select
                id="company-analytics-select"
                value={selectedCompanyAnalyticsId || ''}
                onChange={(e) => setSelectedCompanyAnalyticsId(Number(e.target.value))}
                className="p-2 border border-gov-border rounded text-xs dark:bg-slate-950 dark:border-slate-800 dark:text-slate-100 font-bold focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
              >
                {sortedCompanies.map(c => {
                  const hasDrives = drives.some((d: any) => d.company_id === c.id);
                  return (
                    <option key={c.id} value={c.id}>
                      {c.name} {hasDrives ? '★ (Active Drives)' : '(No Drives Scheduled)'}
                    </option>
                  );
                })}
              </select>
            </div>
          </div>

          {loadingCompanyAnalytics || !companyAnalyticsData ? (
            <div className="h-64 flex items-center justify-center text-xs text-slate-400 bg-white dark:bg-slate-900 border rounded border-gov-border dark:border-slate-800">
              Generating applicant funnel charts...
            </div>
          ) : (
            <div className="space-y-6">
              {/* KPI cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="gov-card">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Applicants</span>
                  <span className="text-2xl font-black text-gov-navy dark:text-slate-200 mt-1 block">{companyAnalyticsData.total_applicants}</span>
                  <span className="text-[10px] text-slate-400">Applications submitted</span>
                </div>
                <div className="gov-card">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Selected Candidates</span>
                  <span className="text-2xl font-black text-emerald-600 mt-1 block">{companyAnalyticsData.selected_students}</span>
                  <span className="text-[10px] text-slate-400">Offer rollouts count</span>
                </div>
                <div className="gov-card">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Avg CGPA of Selected</span>
                  <span className="text-2xl font-black text-gov-navy dark:text-slate-200 mt-1 block">{companyAnalyticsData.avg_cgpa_selected || "N/A"}</span>
                  <span className="text-[10px] text-slate-400">Academic average cutoff check</span>
                </div>
                <div className="gov-card">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Offer Acceptance Rate</span>
                  <span className="text-2xl font-black text-indigo-600 mt-1 block">{companyAnalyticsData.offer_acceptance_rate}%</span>
                  <span className="text-[10px] text-slate-400">Student enrollment percentage</span>
                </div>
              </div>

              {/* Funnel chart and details */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 gov-card space-y-4">
                  <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase">Department Hiring Breakdown</h4>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={companyAnalyticsData.department_hiring}>
                        <XAxis dataKey="dept_code" stroke="#64748B" fontSize={11} tickLine={false} />
                        <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                        <Tooltip />
                        <Bar dataKey="hires" fill="#0F2942" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="gov-card space-y-3">
                    <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase">Top Skills Recruited</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {companyAnalyticsData.top_skills_hired && companyAnalyticsData.top_skills_hired.length > 0 ? (
                        companyAnalyticsData.top_skills_hired.map((s: string) => (
                          <span key={s} className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-1 rounded text-[10px] font-bold uppercase border border-gov-border dark:border-slate-700">
                            {s}
                          </span>
                        ))
                      ) : (
                        <span className="text-[11px] text-slate-400">Data insufficient.</span>
                      )}
                    </div>
                  </div>

                  <div className="gov-card space-y-3">
                    <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase text-red-700 dark:text-red-400">Primary Rejection Bottlenecks</h4>
                    <ul className="list-disc pl-4 text-xs text-slate-600 dark:text-slate-400 space-y-1.5">
                      {companyAnalyticsData.rejection_reasons && companyAnalyticsData.rejection_reasons.length > 0 ? (
                        companyAnalyticsData.rejection_reasons.map((r: string, idx: number) => (
                          <li key={idx} className="leading-snug">{r}</li>
                        ))
                      ) : (
                        <li>Technical interview feedback records pending.</li>
                      )}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB: INSTITUTIONAL PLACEMENT INSIGHTS */}
      {activeTab === 'ai-insights' && (
        <div id="panel-ai-insights" role="tabpanel" aria-labelledby="tab-ai-insights" className="space-y-6">
          {loadingAiInsights || !aiInsightsData ? (
            <div className="h-64 flex items-center justify-center text-xs text-slate-400 bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 rounded">
              Compiling system assessments and feedback transcripts...
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Leaderboard and Demand column */}
              <div className="space-y-6">
                {/* Leaderboard */}
                <div className="gov-card space-y-4">
                  <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-1">
                    <TrendingUp size={14} className="text-gov-blue" />
                    Branch Preparation Rankings
                  </h4>
                  <div className="space-y-3 text-xs">
                    {aiInsightsData.branch_readiness_avg && aiInsightsData.branch_readiness_avg.map((b: any, idx: number) => (
                      <div key={b.dept_code} className="flex justify-between items-center bg-slate-50 dark:bg-slate-950 p-2 border border-gov-border dark:border-slate-850 rounded">
                        <div className="flex items-center gap-2">
                          <span className="font-extrabold text-gov-navy dark:text-sky-400">#{idx + 1}</span>
                          <span className="font-bold text-slate-700 dark:text-slate-300 uppercase">{b.dept_code}</span>
                        </div>
                        <span className="font-bold text-gov-blue dark:text-sky-500">{b.avg_readiness} Avg</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Most Demanded skills */}
                <div className="gov-card space-y-4">
                  <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-1">
                    <Brain size={14} className="text-gov-blue" />
                    Market Technologies Demand
                  </h4>
                  <div className="space-y-3">
                    {aiInsightsData.demanded_skills && aiInsightsData.demanded_skills.map((s: any) => (
                      <div key={s.skill} className="space-y-1">
                        <div className="flex justify-between text-[10px] font-bold text-slate-500 uppercase">
                          <span>{s.skill}</span>
                          <span>{s.demand_count} drives</span>
                        </div>
                        <div className="h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gov-blue dark:bg-sky-500 transition-all duration-500"
                            style={{ width: `${Math.min(100, (s.demand_count / 15) * 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Likely Selected and Risk lists */}
              <div className="lg:col-span-2 space-y-6">
                {/* Likely selected nominees */}
                <div className="gov-card space-y-3">
                  <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase text-emerald-700 dark:text-emerald-400">
                    Strong Placement Prospects
                  </h4>
                  <p className="text-[10px] text-slate-500 leading-normal">These candidates have demonstrated strong preparation and profile alignment for upcoming recruiters.</p>
                  
                  <div className="border border-gov-border dark:border-slate-800 rounded overflow-hidden">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-950 font-bold border-b border-gov-border dark:border-slate-800 uppercase text-slate-500">
                          <th className="p-2.5">Name</th>
                          <th className="p-2.5 text-center">Branch</th>
                          <th className="p-2.5 text-center">CGPA</th>
                          <th className="p-2.5 text-right">Placement Outlook %</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gov-border dark:divide-slate-800">
                        {aiInsightsData.students_likely_selected && aiInsightsData.students_likely_selected.map((s: any) => (
                          <tr key={s.id} className="hover:bg-slate-50 dark:hover:bg-slate-950/20">
                            <td className="p-2.5 font-bold text-slate-800 dark:text-slate-300">{s.name}</td>
                            <td className="p-2.5 text-center font-semibold text-slate-600 dark:text-slate-400">{s.dept_code}</td>
                            <td className="p-2.5 text-center text-slate-600 dark:text-slate-400">{s.cgpa}</td>
                            <td className="p-2.5 text-right font-black text-emerald-600">{s.probability}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Students at Risk */}
                <div className="gov-card space-y-3">
                  <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase text-red-700 dark:text-red-400">
                    Active Placement Risk Flags
                  </h4>
                  <p className="text-[10px] text-slate-500 leading-normal">Candidates flagged as placement risks due to active backlogs, low CGPAs, or lower technical preparation scores.</p>
                  
                  <div className="border border-gov-border dark:border-slate-800 rounded overflow-hidden">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-950 font-bold border-b border-gov-border dark:border-slate-800 uppercase text-slate-500">
                          <th className="p-2.5">Name</th>
                          <th className="p-2.5 text-center">Branch</th>
                          <th className="p-2.5 text-center">CGPA</th>
                          <th className="p-2.5 text-right">Preparation Score</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gov-border dark:divide-slate-800">
                        {aiInsightsData.students_at_risk && aiInsightsData.students_at_risk.map((s: any) => (
                          <tr key={s.id} className="hover:bg-slate-50 dark:hover:bg-slate-950/20">
                            <td className="p-2.5 font-bold text-slate-800 dark:text-slate-300">{s.name}</td>
                            <td className="p-2.5 text-center font-semibold text-slate-600 dark:text-slate-400">{s.dept_code}</td>
                            <td className="p-2.5 text-center text-slate-600 dark:text-slate-400">{s.cgpa}</td>
                            <td className="p-2.5 text-right font-bold text-red-600">{s.readiness_score} / 100</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Request Access Scope Modal */}
      <AccessibleModal
        isOpen={showAccessModal}
        onClose={() => {
          setShowAccessModal(false);
          setAccessSuccess(null);
          setAccessError(null);
        }}
        title="Request Elevated Module Scope & Permissions"
        maxWidth="max-w-3xl"
      >
        <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350">
          <p className="text-slate-500 leading-normal">
            Submit an access request to administrators to temporarily or permanently expand your module permissions (e.g. cross-department access, write/create permissions on placement schedules).
          </p>

          {accessSuccess && (
            <div className="bg-emerald-50 border border-emerald-250 text-emerald-800 p-3 rounded flex items-center gap-2 font-semibold">
              <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
              <span>{accessSuccess}</span>
            </div>
          )}

          {accessError && (
            <div className="bg-red-50 border border-red-250 text-red-800 p-3 rounded flex items-center gap-2 font-semibold">
              <AlertCircle size={16} className="text-red-600 shrink-0" />
              <span>{accessError}</span>
            </div>
          )}

          <form onSubmit={handleAccessSubmit} className="space-y-4 bg-slate-50 dark:bg-slate-950 p-4 border border-gov-border dark:border-slate-850 rounded">
            <h4 className="font-bold uppercase text-[11px] text-slate-800 dark:text-slate-200 border-b border-gov-border dark:border-slate-800 pb-2">
              New Permission Scope Application
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-bold text-slate-600 dark:text-slate-400 uppercase text-[10px] mb-1">
                  Target Module *
                </label>
                <select
                  value={accessForm.module}
                  onChange={(e) => setAccessForm(prev => ({ ...prev, module: e.target.value }))}
                  className="w-full border border-gov-border rounded p-2 bg-white dark:bg-slate-900 dark:border-slate-800 dark:text-slate-200 focus:outline-none"
                >
                  <option value="Placement Drives">Placement Drives</option>
                  <option value="Student Performance">Student Performance</option>
                  <option value="Analytics">Analytics</option>
                  <option value="Activities & Attendance">Activities & Attendance</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-600 dark:text-slate-400 uppercase text-[10px] mb-1">
                  Requested Action *
                </label>
                <select
                  value={accessForm.action}
                  onChange={(e) => setAccessForm(prev => ({ ...prev, action: e.target.value }))}
                  className="w-full border border-gov-border rounded p-2 bg-white dark:bg-slate-900 dark:border-slate-800 dark:text-slate-200 focus:outline-none"
                >
                  <option value="VIEW">VIEW (Read-only)</option>
                  <option value="EDIT">EDIT (Modify existing records)</option>
                  <option value="CREATE">CREATE (Register new entries)</option>
                  <option value="DELETE">DELETE (Remove records)</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-600 dark:text-slate-400 uppercase text-[10px] mb-1">
                  Scope Type *
                </label>
                <select
                  value={accessForm.scope}
                  onChange={(e) => setAccessForm(prev => ({ ...prev, scope: e.target.value }))}
                  className="w-full border border-gov-border rounded p-2 bg-white dark:bg-slate-900 dark:border-slate-800 dark:text-slate-200 focus:outline-none"
                >
                  <option value="DEPARTMENT">DEPARTMENT (Specific Department)</option>
                  <option value="SECTION">SECTION (Specific Section)</option>
                  <option value="ALL">ALL (Institutional Scope)</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-600 dark:text-slate-400 uppercase text-[10px] mb-1">
                  Scope Target / Value *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CSE, IT, ECE, Section-A"
                  value={accessForm.scope_value}
                  onChange={(e) => setAccessForm(prev => ({ ...prev, scope_value: e.target.value }))}
                  className="w-full border border-gov-border rounded p-2 bg-white dark:bg-slate-900 dark:border-slate-800 dark:text-slate-200 focus:outline-none"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block font-bold text-slate-600 dark:text-slate-400 uppercase text-[10px] mb-1">
                  Duration (Days) *
                </label>
                <input
                  type="number"
                  min={1}
                  max={365}
                  required
                  value={accessForm.duration_days}
                  onChange={(e) => setAccessForm(prev => ({ ...prev, duration_days: Number(e.target.value) }))}
                  className="w-full border border-gov-border rounded p-2 bg-white dark:bg-slate-900 dark:border-slate-800 dark:text-slate-200 focus:outline-none"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block font-bold text-slate-600 dark:text-slate-400 uppercase text-[10px] mb-1">
                  Academic Justification & Reason *
                </label>
                <textarea
                  required
                  rows={2}
                  placeholder="Explain why this elevated scope or cross-department access is required..."
                  value={accessForm.reason}
                  onChange={(e) => setAccessForm(prev => ({ ...prev, reason: e.target.value }))}
                  className="w-full border border-gov-border rounded p-2 bg-white dark:bg-slate-900 dark:border-slate-800 dark:text-slate-200 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="submit"
                disabled={submittingAccess}
                className="gov-btn-primary px-4 py-2 bg-gov-navy text-white rounded font-bold text-xs flex items-center gap-1.5 hover:bg-slate-800"
              >
                <KeyRound size={13} />
                {submittingAccess ? 'Submitting Application...' : 'Submit Access Request'}
              </button>
            </div>
          </form>

          {/* Previous Requests Table */}
          <div className="space-y-3">
            <h4 className="font-bold uppercase text-[11px] text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
              <Clock size={14} className="text-gov-blue" />
              My Access Requests Status
            </h4>

            {loadingRequests ? (
              <p className="text-slate-400 italic py-2">Loading previous requests...</p>
            ) : myRequests.length === 0 ? (
              <p className="text-slate-400 italic py-2">No previous scope requests filed.</p>
            ) : (
              <div className="overflow-x-auto border border-gov-border dark:border-slate-800 rounded">
                <table className="w-full text-left text-[11px]">
                  <thead className="bg-slate-100 dark:bg-slate-900 border-b border-gov-border dark:border-slate-800 uppercase font-bold text-slate-500">
                    <tr>
                      <th className="p-2">ID</th>
                      <th className="p-2">Module</th>
                      <th className="p-2">Scope</th>
                      <th className="p-2">Action</th>
                      <th className="p-2">Duration</th>
                      <th className="p-2">Status</th>
                      <th className="p-2">Justification</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gov-border dark:divide-slate-800">
                    {myRequests.map((req) => (
                      <tr key={req.id}>
                        <td className="p-2 font-mono">#{req.id}</td>
                        <td className="p-2 font-semibold">{req.module}</td>
                        <td className="p-2 font-mono">{req.scope}:{req.scope_value || '—'}</td>
                        <td className="p-2 font-bold text-gov-blue">{req.action}</td>
                        <td className="p-2">{req.duration_days} days</td>
                        <td className="p-2">
                          <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                            req.status === 'Approved' ? 'bg-emerald-50 text-emerald-700' :
                            req.status === 'Rejected' ? 'bg-red-50 text-red-700' :
                            'bg-amber-50 text-amber-700'
                          }`}>
                            {req.status}
                          </span>
                        </td>
                        <td className="p-2 text-slate-500 max-w-xs truncate" title={req.reason}>{req.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </AccessibleModal>
      
      {/* Consolidated Drive Feedback Report Modal */}
      <DriveFeedbackReportModal
        isOpen={feedbackReportDriveId !== null}
        onClose={() => setFeedbackReportDriveId(null)}
        driveId={feedbackReportDriveId}
        driveTitle={
          drives.find(d => d.id === feedbackReportDriveId)
            ? `${drives.find(d => d.id === feedbackReportDriveId).company_name} — ${drives.find(d => d.id === feedbackReportDriveId).role}`
            : undefined
        }
      />
    </div>
  );
};
export default FacultyDashboard;
