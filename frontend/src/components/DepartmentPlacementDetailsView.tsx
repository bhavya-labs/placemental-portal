import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { studentService } from '../services/api';
import { CardSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import { 
  GraduationCap, Users, Briefcase, Award, CheckCircle2, 
  XCircle, Filter, Search, User, FileSpreadsheet, AlertCircle, RefreshCw,
  AlertTriangle, X
} from 'lucide-react';

interface DepartmentPlacementDetailsViewProps {
  initialDeptId?: number;
  initialBatch?: string;
}

export const DepartmentPlacementDetailsView: React.FC<DepartmentPlacementDetailsViewProps> = ({
  initialDeptId,
  initialBatch = '2026'
}) => {
  const { user } = useAuth();
  const userDeptId = user?.faculty_profile?.dept_id;
  const isDeptScoped = user?.role === 'faculty' && userDeptId && !user?.permissions?.includes('ALL_DEPT');

  const [searchParams, setSearchParams] = useSearchParams();
  const urlStatus = searchParams.get('status');
  const urlBatch = searchParams.get('batch');
  const urlDept = searchParams.get('dept_id');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedDept, setSelectedDept] = useState<number>(() => {
    if (isDeptScoped && userDeptId) return userDeptId;
    if (urlDept) return Number(urlDept);
    return initialDeptId || userDeptId || 1;
  });
  const [selectedBatch, setSelectedBatch] = useState<string>(urlBatch || initialBatch);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>(urlStatus || '');
  const [driveParticipation, setDriveParticipation] = useState<string>('');
  const [selectedSection, setSelectedSection] = useState<string>('');

  // Pagination
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);

  // Data states
  const [deptInfo, setDeptInfo] = useState<{ id: number; name: string; code: string } | null>(null);
  const [summary, setSummary] = useState<{
    total_students: number;
    placed_students: number;
    unplaced_students: number;
    at_risk_students?: number;
    placement_percentage: number;
    students_participated: number;
    students_not_participated: number;
    total_applications: number;
    total_selections: number;
  } | null>(null);
  const [availableSections, setAvailableSections] = useState<string[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);

  // Sync state if URL search parameters change externally
  useEffect(() => {
    const pStatus = searchParams.get('status') || '';
    if (pStatus !== statusFilter) {
      setStatusFilter(pStatus);
    }
    const pBatch = searchParams.get('batch');
    if (pBatch && pBatch !== selectedBatch) {
      setSelectedBatch(pBatch);
    }
    const pDept = searchParams.get('dept_id');
    if (pDept && !isDeptScoped && Number(pDept) !== selectedDept) {
      setSelectedDept(Number(pDept));
    }
  }, [searchParams]);

  const handleStatusChange = (newStatus: string) => {
    setStatusFilter(newStatus);
    const newParams = new URLSearchParams(searchParams);
    if (newStatus) {
      newParams.set('status', newStatus);
    } else {
      newParams.delete('status');
    }
    setSearchParams(newParams, { replace: true });
  };

  const fetchPlacementDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await studentService.getDepartmentPlacementDetails({
        dept_id: selectedDept,
        batch: selectedBatch,
        section: selectedSection || undefined,
        status_filter: statusFilter || undefined,
        drive_participation: driveParticipation || undefined,
        search: searchQuery.trim() || undefined,
        page: page,
        limit: pageSize
      });

      setDeptInfo(res.department || null);
      setSummary(res.summary || null);
      setAvailableSections(res.available_sections || []);
      setStudents(res.items || []);
      setTotalCount(res.total || 0);
    } catch (err: any) {
      console.error('Failed to load department placement details', err);
      setError(err.response?.data?.detail || 'Failed to retrieve department placement details.');
      setStudents([]);
      setSummary(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isDeptScoped && userDeptId && selectedDept !== userDeptId) {
      setSelectedDept(userDeptId);
    }
  }, [isDeptScoped, userDeptId]);

  useEffect(() => {
    setPage(1);
  }, [selectedDept, selectedBatch, searchQuery, statusFilter, driveParticipation, selectedSection]);

  useEffect(() => {
    fetchPlacementDetails();
  }, [selectedDept, selectedBatch, searchQuery, statusFilter, driveParticipation, selectedSection, page, pageSize]);

  const totalPages = Math.ceil(totalCount / pageSize) || 1;

  const handleExportCSV = () => {
    if (!students || students.length === 0) return;
    const headers = [
      'Roll No', 'Student Name', 'Branch', 'Section', 'CGPA', 'Attendance %',
      'Backlogs', 'Placement Preparation Score', 'Placement Status',
      'Drives Applied', 'Interviews Attended', 'Selections/Offers', 'Active Applications'
    ];
    const rows = students.map(s => [
      `"${s.roll_no}"`,
      `"${s.name}"`,
      `"${s.branch}"`,
      `"${s.section}"`,
      s.cgpa,
      s.attendance,
      s.backlogs,
      s.placement_preparation_score,
      `"${s.status}"`,
      s.drives_applied_count,
      s.interviews_attended_count,
      s.selections_count,
      s.active_applications_count
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${deptInfo?.code || 'DEPT'}_student_placement_details_${selectedBatch}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Filters Bar */}
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-4 rounded-lg shadow-card space-y-3">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-gov-blue" />
            <div>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">
                Department Placement Filters
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Filter students and metrics for your authorized academic department.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleExportCSV}
              disabled={students.length === 0}
              className="gov-btn-secondary border border-gov-border py-1.5 px-3 rounded text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50"
              title="Export current table to CSV"
            >
              <FileSpreadsheet size={14} /> Export CSV
            </button>
            <button
              onClick={fetchPlacementDetails}
              className="p-1.5 text-slate-500 hover:text-gov-blue hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition"
              title="Refresh placement data"
            >
              <RefreshCw size={15} />
            </button>
          </div>
        </div>

        {/* Filter Selectors Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 text-xs pt-2 border-t border-gov-border/60 dark:border-slate-800">
          {/* Department Selector */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="dept-filter-select" className="font-bold text-slate-600 dark:text-slate-300 uppercase">
                Department
              </label>
              {isDeptScoped && (
                <span className="text-[9px] font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-1 rounded">
                  Scoped
                </span>
              )}
            </div>
            <select
              id="dept-filter-select"
              value={selectedDept}
              onChange={(e) => setSelectedDept(Number(e.target.value))}
              disabled={isDeptScoped}
              className={`w-full border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-950 dark:border-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-gov-blue ${
                isDeptScoped ? 'opacity-90 cursor-not-allowed bg-slate-50 dark:bg-slate-900' : ''
              }`}
            >
              {isDeptScoped ? (
                <option value={userDeptId}>
                  {user?.faculty_profile?.dept_name || 'My Department'} ({user?.faculty_profile?.dept_code || 'Dept'})
                </option>
              ) : (
                <>
                  <option value="1">Computer Science & Engineering (CSE)</option>
                  <option value="2">Information Technology (IT)</option>
                  <option value="3">Electronics & Communication (ECE)</option>
                  <option value="4">Electrical & Electronics (EEE)</option>
                  <option value="5">Mechanical Engineering (MECH)</option>
                  <option value="6">Civil Engineering (CIVIL)</option>
                </>
              )}
            </select>
          </div>

          {/* Batch Selector */}
          <div>
            <label htmlFor="batch-filter-select" className="block font-bold text-slate-600 dark:text-slate-300 uppercase mb-1">
              Graduating Batch
            </label>
            <select
              id="batch-filter-select"
              value={selectedBatch}
              onChange={(e) => setSelectedBatch(e.target.value)}
              className="w-full border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-950 dark:border-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-gov-blue"
            >
              <option value="2026">2026 (Final Year)</option>
              <option value="2025">2025 (Graduated)</option>
            </select>
          </div>

          {/* Section Selector */}
          <div>
            <label htmlFor="section-filter-select" className="block font-bold text-slate-600 dark:text-slate-300 uppercase mb-1">
              Section
            </label>
            <select
              id="section-filter-select"
              value={selectedSection}
              onChange={(e) => setSelectedSection(e.target.value)}
              className="w-full border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-950 dark:border-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-gov-blue"
            >
              <option value="">All Sections</option>
              {availableSections.map(sec => (
                <option key={sec} value={sec}>Section {sec}</option>
              ))}
            </select>
          </div>

          {/* Placement Status Selector */}
          <div>
            <label htmlFor="status-filter-select" className="block font-bold text-slate-600 dark:text-slate-300 uppercase mb-1">
              Placement Status
            </label>
            <select
              id="status-filter-select"
              value={statusFilter}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="w-full border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-950 dark:border-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-gov-blue"
            >
              <option value="">All Statuses</option>
              <option value="Placed">Placed</option>
              <option value="Unplaced">Unplaced</option>
              <option value="At Risk">Students At Risk (Low Score)</option>
            </select>
          </div>

          {/* Drive Participation Selector */}
          <div>
            <label htmlFor="participation-filter-select" className="block font-bold text-slate-600 dark:text-slate-300 uppercase mb-1">
              Drive Participation
            </label>
            <select
              id="participation-filter-select"
              value={driveParticipation}
              onChange={(e) => setDriveParticipation(e.target.value)}
              className="w-full border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-950 dark:border-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-gov-blue"
            >
              <option value="">All Students</option>
              <option value="applied">Attended / Applied</option>
              <option value="not_applied">Not Attended / Applied</option>
            </select>
          </div>
        </div>

        {/* Search Bar */}
        <div className="pt-2">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by student name, roll number, or email..."
              className="w-full pl-9 pr-4 py-1.5 text-xs border border-gov-border rounded bg-white dark:bg-slate-950 dark:border-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-gov-blue"
            />
          </div>
        </div>
      </div>

      {/* DEPARTMENT-LEVEL SUMMARY CARDS */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : error ? (
        <div className="gov-card p-6 border-l-4 border-l-red-500 bg-red-50/50 dark:bg-red-950/20 text-center space-y-2">
          <div className="flex items-center justify-center gap-2 text-red-600 dark:text-red-400 font-bold text-sm">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
          <p className="text-xs text-slate-500">
            Please ensure you have authorization for this department or request elevated department access.
          </p>
        </div>
      ) : summary ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {/* Card 1: Total Students */}
          <div 
            onClick={() => handleStatusChange('')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleStatusChange('')}
            className={`gov-card p-3 border-l-4 border-l-gov-blue cursor-pointer transition hover:shadow-md ${
              !statusFilter ? 'ring-2 ring-gov-blue/50' : ''
            }`}
            title="Click to view all students"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total</span>
              <Users size={14} className="text-gov-blue" />
            </div>
            <p className="text-xl font-bold text-slate-800 dark:text-slate-100 mt-1">{summary.total_students}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">{deptInfo?.code || 'Dept'} Batch {selectedBatch}</p>
          </div>

          {/* Card 2: Placed Students */}
          <div 
            onClick={() => handleStatusChange(statusFilter.toLowerCase() === 'placed' ? '' : 'Placed')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleStatusChange(statusFilter.toLowerCase() === 'placed' ? '' : 'Placed')}
            className={`gov-card p-3 border-l-4 border-l-emerald-500 cursor-pointer transition hover:shadow-md ${
              statusFilter.toLowerCase() === 'placed' ? 'ring-2 ring-emerald-500 bg-emerald-50/40 dark:bg-emerald-950/30' : ''
            }`}
            title="Click to filter Placed students"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Placed</span>
              <CheckCircle2 size={14} className="text-emerald-500" />
            </div>
            <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{summary.placed_students}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">{summary.placement_percentage}% placed</p>
          </div>

          {/* Card 3: Unplaced Students */}
          <div 
            onClick={() => handleStatusChange(statusFilter.toLowerCase() === 'unplaced' ? '' : 'Unplaced')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleStatusChange(statusFilter.toLowerCase() === 'unplaced' ? '' : 'Unplaced')}
            className={`gov-card p-3 border-l-4 border-l-amber-500 cursor-pointer transition hover:shadow-md ${
              statusFilter.toLowerCase() === 'unplaced' ? 'ring-2 ring-amber-500 bg-amber-50/40 dark:bg-amber-950/30' : ''
            }`}
            title="Click to filter Unplaced students"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Unplaced</span>
              <XCircle size={14} className="text-amber-500" />
            </div>
            <p className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1">{summary.unplaced_students}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Seeking placement</p>
          </div>

          {/* Card 4: Students At Risk (Low score) */}
          <div 
            onClick={() => handleStatusChange(statusFilter.toLowerCase() === 'at risk' ? '' : 'At Risk')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleStatusChange(statusFilter.toLowerCase() === 'at risk' ? '' : 'At Risk')}
            className={`gov-card p-3 border-l-4 border-l-red-500 cursor-pointer transition hover:shadow-md ${
              statusFilter.toLowerCase() === 'at risk' ? 'ring-2 ring-red-500 bg-red-50/50 dark:bg-red-950/30' : ''
            }`}
            title="Click to view Students At Risk"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">At Risk</span>
              <AlertTriangle size={14} className="text-red-500" />
            </div>
            <p className="text-xl font-bold text-red-600 dark:text-red-400 mt-1">{summary.at_risk_students ?? 0}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Needs intervention</p>
          </div>

          {/* Card 5: Attended / Applied to Drives */}
          <div className="gov-card p-3 border-l-4 border-l-sky-500">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Drive Active</span>
              <Briefcase size={14} className="text-sky-500" />
            </div>
            <p className="text-xl font-bold text-sky-600 dark:text-sky-400 mt-1">{summary.students_participated}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Applied to drives</p>
          </div>

          {/* Card 6: Not Attended / Applied to Any Drive */}
          <div className="gov-card p-3 border-l-4 border-l-purple-500">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Zero Drives</span>
              <AlertCircle size={14} className="text-purple-500" />
            </div>
            <p className="text-xl font-bold text-purple-600 dark:text-purple-400 mt-1">{summary.students_not_participated}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Not yet applied</p>
          </div>

          {/* Card 7: Total Applications */}
          <div className="gov-card p-3 border-l-4 border-l-indigo-500">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Applications</span>
              <FileSpreadsheet size={14} className="text-indigo-500" />
            </div>
            <p className="text-xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">{summary.total_applications}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Total submissions</p>
          </div>

          {/* Card 8: Total Selections / Offers */}
          <div className="gov-card p-3 border-l-4 border-l-teal-500">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Offers Made</span>
              <Award size={14} className="text-teal-500" />
            </div>
            <p className="text-xl font-bold text-teal-600 dark:text-teal-400 mt-1">{summary.total_selections}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Selected candidates</p>
          </div>
        </div>
      ) : null}

      {/* STUDENT PLACEMENT DETAILS TABLE */}
      <div className="gov-card p-4 space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div>
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
              <GraduationCap className="text-gov-blue" size={18} />
              {deptInfo ? `${deptInfo.name} (${deptInfo.code})` : 'Department'} Student Placement Records
            </h4>
            <p className="text-[11px] text-slate-500">
              Showing {students.length} of {totalCount} matching student placement records
            </p>
          </div>
        </div>

        {/* Visual Indication: Active Filter Applied Banner */}
        {statusFilter && (
          <div className={`p-3 rounded-lg border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs ${
            statusFilter.toLowerCase() === 'at risk'
              ? 'bg-red-50/80 border-red-200 text-red-900 dark:bg-red-950/40 dark:border-red-900/60 dark:text-red-200'
              : statusFilter.toLowerCase() === 'placed'
              ? 'bg-emerald-50/80 border-emerald-200 text-emerald-900 dark:bg-emerald-950/40 dark:border-emerald-900/60 dark:text-emerald-200'
              : 'bg-amber-50/80 border-amber-200 text-amber-900 dark:bg-amber-950/40 dark:border-amber-900/60 dark:text-amber-200'
          }`}>
            <div className="flex items-center gap-2.5">
              {statusFilter.toLowerCase() === 'at risk' ? (
                <AlertTriangle className="text-red-600 dark:text-red-400 shrink-0" size={18} />
              ) : (
                <Filter className="text-gov-blue shrink-0" size={18} />
              )}
              <div>
                <span className="font-bold uppercase tracking-wider">Active Filter Applied:</span>{' '}
                <span className="font-medium">
                  {statusFilter.toLowerCase() === 'at risk'
                    ? 'Showing Students At Risk (Low Placement Preparation Score)'
                    : `Showing ${statusFilter} students`}
                  {' — '}
                  <strong className="font-bold">{totalCount}</strong> {totalCount === 1 ? 'student' : 'students'} found
                </span>
              </div>
            </div>
            <button
              onClick={() => handleStatusChange('')}
              className="px-3 py-1 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 rounded font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-1.5 shadow-sm transition text-xs shrink-0"
              title="Clear filter and view all students"
            >
              <X size={14} /> Clear Filter ({statusFilter})
            </button>
          </div>
        )}

        {loading ? (
          <TableSkeleton />
        ) : students.length === 0 ? (
          <div className="py-12 text-center text-slate-500 space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
              {statusFilter.toLowerCase() === 'at risk' ? (
                <CheckCircle2 size={24} className="text-emerald-500" />
              ) : (
                <Users size={24} />
              )}
            </div>
            <div className="space-y-1">
              <p className="text-sm font-bold text-slate-700 dark:text-slate-200">
                {statusFilter.toLowerCase() === 'at risk'
                  ? 'No Students At Risk Found'
                  : 'No student placement records found'}
              </p>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                {statusFilter.toLowerCase() === 'at risk'
                  ? 'Great news! There are currently no students identified as At Risk in this department and batch.'
                  : 'No students match your current filter selections. Try adjusting your department, section, or search filters.'}
              </p>
            </div>
            {statusFilter && (
              <div>
                <button
                  onClick={() => handleStatusChange('')}
                  className="px-3 py-1.5 bg-gov-blue text-white rounded text-xs font-semibold hover:bg-gov-navy transition inline-flex items-center gap-1.5"
                >
                  <X size={14} /> Clear Active Filter
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-gov-border dark:border-slate-800 bg-slate-50 dark:bg-slate-850/50 text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                  <th className="py-2.5 px-3">Roll No</th>
                  <th className="py-2.5 px-3">Student Name</th>
                  <th className="py-2.5 px-3">Branch / Sec</th>
                  <th className="py-2.5 px-3 text-center">CGPA</th>
                  <th className="py-2.5 px-3 text-center">Attendance</th>
                  <th className="py-2.5 px-3 text-center">Backlogs</th>
                  <th className="py-2.5 px-3 text-center">Placement Prep</th>
                  <th className="py-2.5 px-3 text-center">Placement Status</th>
                  <th className="py-2.5 px-3 text-center">Drives Applied</th>
                  <th className="py-2.5 px-3 text-center">Interviews</th>
                  <th className="py-2.5 px-3 text-center">Selections</th>
                  <th className="py-2.5 px-3 text-center">Active Apps</th>
                  <th className="py-2.5 px-3 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gov-border/60 dark:divide-slate-800">
                {students.map((student) => {
                  const isPlaced = (student.status || '').toLowerCase() === 'placed';
                  const prepScore = student.placement_preparation_score ?? 0;
                  const prepColor = prepScore >= 70 ? 'text-emerald-600' : prepScore < 40 ? 'text-red-500' : 'text-amber-500';

                  return (
                    <tr 
                      key={student.id} 
                      className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      {/* Roll Number */}
                      <td className="py-2.5 px-3 font-mono font-semibold text-gov-navy dark:text-slate-200">
                        {student.roll_no}
                      </td>

                      {/* Student Name */}
                      <td className="py-2.5 px-3">
                        <div className="font-semibold text-slate-800 dark:text-slate-100">{student.name}</div>
                        <div className="text-[10px] text-slate-400">{student.email}</div>
                      </td>

                      {/* Branch / Section */}
                      <td className="py-2.5 px-3">
                        <span className="font-semibold text-slate-700 dark:text-slate-300">{student.branch}</span>
                        <span className="text-slate-400 ml-1">Sec-{student.section}</span>
                      </td>

                      {/* CGPA */}
                      <td className="py-2.5 px-3 text-center font-bold text-slate-700 dark:text-slate-200">
                        {student.cgpa.toFixed(2)}
                      </td>

                      {/* Attendance */}
                      <td className="py-2.5 px-3 text-center">
                        <span className={`font-semibold ${student.attendance < 75 ? 'text-red-600 font-bold' : 'text-slate-700 dark:text-slate-200'}`}>
                          {student.attendance.toFixed(1)}%
                        </span>
                      </td>

                      {/* Backlogs */}
                      <td className="py-2.5 px-3 text-center">
                        <span className={`font-semibold ${student.backlogs > 0 ? 'text-red-600' : 'text-slate-500'}`}>
                          {student.backlogs}
                        </span>
                      </td>

                      {/* Placement Preparation Score */}
                      <td className="py-2.5 px-3 text-center">
                        <span className={`font-bold ${prepColor}`}>
                          {prepScore}/100
                        </span>
                      </td>

                      {/* Placement Status */}
                      <td className="py-2.5 px-3 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          isPlaced 
                            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300' 
                            : 'bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-300'
                        }`}>
                          {student.status}
                        </span>
                      </td>

                      {/* Number of placement drives attended/applied */}
                      <td className="py-2.5 px-3 text-center font-semibold text-slate-700 dark:text-slate-200">
                        {student.drives_applied_count}
                      </td>

                      {/* Number of interviews attended */}
                      <td className="py-2.5 px-3 text-center font-semibold text-slate-700 dark:text-slate-200">
                        {student.interviews_attended_count}
                      </td>

                      {/* Number of selections/offers */}
                      <td className="py-2.5 px-3 text-center">
                        <span className={`font-bold ${student.selections_count > 0 ? 'text-teal-600 dark:text-teal-400' : 'text-slate-400'}`}>
                          {student.selections_count}
                        </span>
                      </td>

                      {/* Active applications */}
                      <td className="py-2.5 px-3 text-center font-semibold text-slate-700 dark:text-slate-200">
                        {student.active_applications_count}
                      </td>

                      {/* Actions */}
                      <td className="py-2.5 px-3 text-center">
                        <Link
                          to={`/student-360/${student.id}`}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-sky-50 dark:bg-sky-950/40 text-gov-blue dark:text-sky-300 hover:bg-sky-100 dark:hover:bg-sky-900/60 rounded text-[10px] font-bold uppercase border border-sky-200 dark:border-sky-800"
                          title="View Full Student 360° Profile"
                        >
                          <User size={11} />
                          <span>360°</span>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div className="flex flex-col sm:flex-row justify-between items-center gap-3 pt-3 border-t border-gov-border dark:border-slate-800 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => setPageSize(Number(e.target.value))}
              className="border border-gov-border rounded p-1 bg-white text-slate-700 dark:bg-slate-950 dark:border-slate-800 dark:text-slate-200"
            >
              <option value="10">10</option>
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
            <span>
              Page {page} of {totalPages}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-2.5 py-1 border border-gov-border rounded hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed font-medium"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-2.5 py-1 border border-gov-border rounded hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed font-medium"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
