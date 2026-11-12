import React, { useState, useEffect } from 'react';
import { driveService } from '../services/api';
import { CardSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import { 
  Briefcase, PlusCircle, Search, Filter, Edit, Trash2, X, AlertTriangle, Calendar, Archive, Eye,
  ChevronLeft, ChevronRight, RotateCcw, MapPin, Building2, Clock, CheckCircle2, XCircle
} from 'lucide-react';
import { AccessibleToast } from '../components/AccessibilityComponents';

export const AdminDrives: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [drives, setDrives] = useState<any[]>([]);
  const [tab, setTab] = useState<'active' | 'archived'>('active');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [regStatusFilter, setRegStatusFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Pagination state
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(9);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(0);

  // Dialog configurations
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isInspectOpen, setIsInspectOpen] = useState(false);
  const [selectedDrive, setSelectedDrive] = useState<any | null>(null);
  const [inspectDrive, setInspectDrive] = useState<any | null>(null);

  // Form values
  const [companyName, setCompanyName] = useState('');
  const [role, setRole] = useState('');
  const [packageLpa, setPackageLpa] = useState<number>(6.5);
  const [location, setLocation] = useState('Hyderabad');
  const [cgpaCutoff, setCgpaCutoff] = useState<number>(7.0);
  const [allowedDepts, setAllowedDepts] = useState('CSE, IT, ECE');
  const [allowedBacklogs, setAllowedBacklogs] = useState<number>(0);
  const [interviewDate, setInterviewDate] = useState('2026-09-10');
  const [deadline, setDeadline] = useState('2026-08-31');
  const [status, setStatus] = useState('DRAFT');
  const [batch, setBatch] = useState('2026');
  const [minAttendance, setMinAttendance] = useState<number>(75);

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const loadDrives = async (page = currentPage, activeTab: 'active' | 'archived' = tab) => {
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: pageSize,
        status_filter: activeTab === 'archived' ? 'ARCHIVED' : undefined,
      };
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (deptFilter && deptFilter !== 'ALL') params.dept = deptFilter;
      if (locationFilter.trim()) params.location = locationFilter.trim();
      if (regStatusFilter && regStatusFilter !== 'ALL') params.reg_status = regStatusFilter;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const res = await driveService.getDrives(params);
      if (res && res.items !== undefined) {
        setDrives(res.items);
        setTotalCount(res.total || 0);
        setTotalPages(res.total_pages || 0);
      } else if (Array.isArray(res)) {
        setDrives(res);
        setTotalCount(res.length);
        setTotalPages(Math.ceil(res.length / pageSize) || 1);
      } else {
        setDrives([]);
        setTotalCount(0);
        setTotalPages(0);
      }
    } catch (err) {
      console.error('Failed to load drives', err);
      showToast('Failed to load placement drives.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (newTab: 'active' | 'archived') => {
    setTab(newTab);
    setCurrentPage(1);
  };

  const handleClearAllFilters = () => {
    setSearchQuery('');
    setDeptFilter('');
    setLocationFilter('');
    setRegStatusFilter('');
    setDateFrom('');
    setDateTo('');
    setCurrentPage(1);
  };

  const hasActiveFilters = Boolean(
    searchQuery.trim() ||
    (deptFilter && deptFilter !== 'ALL') ||
    locationFilter.trim() ||
    (regStatusFilter && regStatusFilter !== 'ALL') ||
    dateFrom ||
    dateTo
  );

  useEffect(() => {
    const timer = setTimeout(() => {
      loadDrives(currentPage, tab);
    }, 250);
    return () => clearTimeout(timer);
  }, [currentPage, pageSize, tab, deptFilter, locationFilter, regStatusFilter, dateFrom, dateTo, searchQuery]);

  const handleOpenInspect = async (drv: any) => {
    try {
      const details = await driveService.getDriveDetails(drv.id);
      setInspectDrive(details);
      setIsInspectOpen(true);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to load drive details.', 'error');
    }
  };

  const handleOpenAdd = () => {
    setCompanyName('');
    setRole('');
    setPackageLpa(6.5);
    setLocation('Hyderabad');
    setCgpaCutoff(7.0);
    setAllowedDepts('CSE, IT, ECE');
    setAllowedBacklogs(0);
    setInterviewDate(new Date().toISOString().split('T')[0]);
    setDeadline(new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString().split('T')[0]);
    setStatus('DRAFT');
    setBatch('2026');
    setMinAttendance(75);
    setIsAddOpen(true);
  };

  const handleOpenEdit = (drv: any) => {
    setSelectedDrive(drv);
    setCompanyName(drv.company_name);
    setRole(drv.role);
    setPackageLpa(drv.package_lpa);
    setLocation(drv.location);
    setCgpaCutoff(drv.cgpa_cutoff);
    setAllowedDepts(drv.allowed_depts);
    setAllowedBacklogs(drv.allowed_backlogs);
    setInterviewDate(drv.interview_date || new Date().toISOString().split('T')[0]);
    setDeadline(drv.deadline);
    setStatus(drv.status);
    setBatch(drv.batch || '2026');
    setMinAttendance(drv.min_attendance || 75);
    setIsEditOpen(true);
  };

  const handleOpenDelete = (drv: any) => {
    setSelectedDrive(drv);
    setIsDeleteOpen(true);
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await driveService.createDrive({
        company_name: companyName,
        role,
        package_lpa: packageLpa,
        location,
        cgpa_cutoff: cgpaCutoff,
        allowed_depts: allowedDepts,
        allowed_backlogs: allowedBacklogs,
        interview_date: interviewDate,
        deadline,
        status,
        batch,
        min_attendance: minAttendance,
        responsibilities: 'Collaborate with cross-functional development panels to audit features.',
        hiring_process: 'Round 1 (DSA MCQs) -> Coding Test -> Technical Panel -> HR Discussion'
      });
      showToast('Placement drive constructed and open for applications!', 'success');
      setIsAddOpen(false);
      loadDrives();
    } catch (err: any) {
      const errMsg = Array.isArray(err.response?.data?.detail)
        ? err.response.data.detail.map((d: any) => `${d.loc ? d.loc.slice(1).join('.') + ': ' : ''}${d.msg}`).join(', ')
        : (err.response?.data?.detail || 'Failed to schedule placement drive.');
      showToast(errMsg, 'error');
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDrive) return;
    try {
      await driveService.updateDrive(selectedDrive.id, {
        company_name: companyName,
        role,
        package_lpa: packageLpa,
        location,
        cgpa_cutoff: cgpaCutoff,
        allowed_depts: allowedDepts,
        allowed_backlogs: allowedBacklogs,
        interview_date: interviewDate,
        deadline,
        status,
        batch,
        min_attendance: minAttendance,
        responsibilities: selectedDrive.responsibilities || 'General software engineer roles.',
        hiring_process: selectedDrive.hiring_process || 'Coding round -> Interviews'
      });
      showToast('Drive criteria parameters modified successfully!', 'success');
      setIsEditOpen(false);
      loadDrives();
    } catch (err: any) {
      const errMsg = Array.isArray(err.response?.data?.detail)
        ? err.response.data.detail.map((d: any) => `${d.loc ? d.loc.slice(1).join('.') + ': ' : ''}${d.msg}`).join(', ')
        : (err.response?.data?.detail || 'Failed to modify drive parameters.');
      showToast(errMsg, 'error');
    }
  };

  const handleDeleteSubmit = async () => {
    if (!selectedDrive) return;
    try {
      const res = await driveService.deleteDrive(selectedDrive.id);
      showToast(res.message || 'Drive action executed successfully.', 'success');
      setIsDeleteOpen(false);
      loadDrives(currentPage, tab);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to remove drive.', 'error');
    }
  };

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350">
      <AccessibleToast message={toast?.message || null} type={toast?.type || null} />

      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
            <Briefcase className="text-gov-blue" size={24} />
            Institutional Placement Drives Control
          </h2>
          <p className="text-[10px] text-slate-500 mt-1">
            Configure ongoing recruitment drives, package matrices, Allowed branches, and application timelines.
          </p>
        </div>

        <button
          onClick={handleOpenAdd}
          className="gov-btn-primary py-2 px-4 rounded font-bold uppercase tracking-wider bg-gov-navy border-0 text-white flex items-center gap-1.5"
        >
          <PlusCircle size={14} /> Schedule Drive
        </button>
      </div>

      {/* TABS: ACTIVE vs ARCHIVED */}
      <div className="flex border-b border-gov-border dark:border-slate-800 gap-4">
        <button
          onClick={() => handleTabChange('active')}
          className={`pb-2.5 font-bold uppercase tracking-wider text-xs flex items-center gap-1.5 transition-colors border-b-2 ${
            tab === 'active'
              ? 'border-gov-blue text-gov-blue dark:text-sky-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
          }`}
        >
          <Briefcase size={14} /> Active & Scheduled Drives
        </button>
        <button
          onClick={() => handleTabChange('archived')}
          className={`pb-2.5 font-bold uppercase tracking-wider text-xs flex items-center gap-1.5 transition-colors border-b-2 ${
            tab === 'archived'
              ? 'border-gov-blue text-gov-blue dark:text-sky-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
          }`}
        >
          <Archive size={14} /> Archived Drives
        </button>
      </div>

      {/* SEARCH AND FILTER CONTROLS BAR */}
      <div className="gov-card space-y-3 p-4">
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center">
          {/* Search bar */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={14} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search by company name, job role, or Job ID..."
              className="w-full pl-9 pr-8 py-2 border border-gov-border dark:border-slate-800 rounded bg-white dark:bg-slate-950 text-xs focus:outline-none"
            />
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setCurrentPage(1);
                }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                title="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Department Filter */}
          <div className="min-w-[140px]">
            <select
              value={deptFilter}
              onChange={(e) => {
                setDeptFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full py-2 px-2.5 border border-gov-border dark:border-slate-800 rounded bg-white dark:bg-slate-950 text-xs focus:outline-none font-semibold"
            >
              <option value="">All Departments</option>
              <option value="CSE">CSE</option>
              <option value="ECE">ECE</option>
              <option value="IT">IT</option>
              <option value="MECH">MECH</option>
              <option value="CIVIL">CIVIL</option>
              <option value="EEE">EEE</option>
            </select>
          </div>

          {/* Registration Status Filter */}
          <div className="min-w-[150px]">
            <select
              value={regStatusFilter}
              onChange={(e) => {
                setRegStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full py-2 px-2.5 border border-gov-border dark:border-slate-800 rounded bg-white dark:bg-slate-950 text-xs focus:outline-none font-semibold"
            >
              <option value="">All Registrations</option>
              <option value="OPEN">Registration Open</option>
              <option value="CLOSED">Registration Closed</option>
            </select>
          </div>
        </div>

        {/* Secondary Filter Row: Location and Date Range */}
        <div className="flex flex-col sm:flex-row flex-wrap items-center gap-3 pt-1 border-t border-gov-border/60 dark:border-slate-800/60">
          <div className="relative flex-1 min-w-[180px]">
            <MapPin className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" size={12} />
            <input
              type="text"
              value={locationFilter}
              onChange={(e) => {
                setLocationFilter(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Filter by location (e.g. Hyderabad)..."
              className="w-full pl-8 pr-7 py-1.5 border border-gov-border dark:border-slate-800 rounded bg-white dark:bg-slate-950 text-[11px] focus:outline-none"
            />
            {locationFilter && (
              <button
                onClick={() => {
                  setLocationFilter('');
                  setCurrentPage(1);
                }}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X size={12} />
              </button>
            )}
          </div>

          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-500">
            <Calendar size={12} className="text-slate-400" />
            <span>Interview Dates:</span>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setCurrentPage(1);
              }}
              className="py-1 px-1.5 border border-gov-border dark:border-slate-800 rounded bg-white dark:bg-slate-950 text-[11px] focus:outline-none"
              title="Interview Date From"
            />
            <span>to</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value);
                setCurrentPage(1);
              }}
              className="py-1 px-1.5 border border-gov-border dark:border-slate-800 rounded bg-white dark:bg-slate-950 text-[11px] focus:outline-none"
              title="Interview Date To"
            />
          </div>
        </div>

        {/* ACTIVE FILTER BADGES */}
        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-gov-border/60 dark:border-slate-800/60 text-[11px]">
            <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">Active Filters:</span>
            {searchQuery.trim() && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-sky-50 text-sky-800 border border-sky-200 dark:bg-sky-950/40 dark:text-sky-300 font-semibold">
                Search: "{searchQuery.trim()}"
                <button onClick={() => { setSearchQuery(''); setCurrentPage(1); }} className="hover:text-sky-950">
                  <X size={10} />
                </button>
              </span>
            )}
            {deptFilter && deptFilter !== 'ALL' && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-50 text-purple-800 border border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 font-semibold">
                Dept: {deptFilter}
                <button onClick={() => { setDeptFilter(''); setCurrentPage(1); }} className="hover:text-purple-950">
                  <X size={10} />
                </button>
              </span>
            )}
            {regStatusFilter && regStatusFilter !== 'ALL' && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 font-semibold">
                Reg: {regStatusFilter === 'OPEN' ? 'Open' : 'Closed'}
                <button onClick={() => { setRegStatusFilter(''); setCurrentPage(1); }} className="hover:text-emerald-950">
                  <X size={10} />
                </button>
              </span>
            )}
            {locationFilter.trim() && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 font-semibold">
                Location: {locationFilter.trim()}
                <button onClick={() => { setLocationFilter(''); setCurrentPage(1); }} className="hover:text-amber-950">
                  <X size={10} />
                </button>
              </span>
            )}
            {dateFrom && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-800 border border-slate-300 dark:bg-slate-800 dark:text-slate-300 font-semibold">
                From: {dateFrom}
                <button onClick={() => { setDateFrom(''); setCurrentPage(1); }} className="hover:text-slate-950">
                  <X size={10} />
                </button>
              </span>
            )}
            {dateTo && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-800 border border-slate-300 dark:bg-slate-800 dark:text-slate-300 font-semibold">
                To: {dateTo}
                <button onClick={() => { setDateTo(''); setCurrentPage(1); }} className="hover:text-slate-950">
                  <X size={10} />
                </button>
              </span>
            )}
            <button
              onClick={handleClearAllFilters}
              className="text-red-650 hover:text-red-800 font-bold uppercase tracking-wider text-[10px] ml-auto flex items-center gap-1"
            >
              <RotateCcw size={10} /> Clear all filters
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <CardSkeleton />
      ) : drives.length === 0 ? (
        <div className="gov-card text-center py-12 text-slate-450 uppercase font-bold flex flex-col items-center justify-center gap-2">
          <Briefcase size={32} className="text-slate-300 dark:text-slate-700" />
          <p>
            {hasActiveFilters
              ? 'No placement drives match the current search and filter criteria.'
              : tab === 'archived'
              ? 'No archived placement drives found.'
              : 'No active or scheduled placement drives found.'}
          </p>
          {hasActiveFilters && (
            <button
              onClick={handleClearAllFilters}
              className="mt-2 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded font-bold uppercase text-[10px] flex items-center gap-1.5 tracking-wider"
            >
              <RotateCcw size={12} /> Reset filters
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {drives.map((drive) => {
              const getStatusBadge = (st: string) => {
                switch (st) {
                  case 'REGISTRATION_OPEN':
                  case 'PUBLISHED':
                  case 'Active':
                    return 'bg-emerald-50 text-emerald-800 border border-emerald-250 dark:bg-emerald-950/40 dark:text-emerald-300';
                  case 'SCHEDULED':
                  case 'Upcoming':
                    return 'bg-sky-50 text-sky-800 border border-sky-200 dark:bg-sky-950/40 dark:text-sky-300';
                  case 'REGISTRATION_CLOSED':
                    return 'bg-amber-50 text-amber-800 border border-amber-250 dark:bg-amber-950/40 dark:text-amber-300';
                  case 'ONGOING':
                  case 'ASSESSMENT':
                  case 'INTERVIEW':
                    return 'bg-purple-50 text-purple-800 border border-purple-200 dark:bg-purple-950/40 dark:text-purple-300';
                  case 'COMPLETED':
                  case 'Completed':
                    return 'bg-slate-100 text-slate-700 border border-slate-300 dark:bg-slate-800 dark:text-slate-300';
                  case 'ARCHIVED':
                    return 'bg-zinc-100 text-zinc-700 border border-zinc-300 dark:bg-zinc-800 dark:text-zinc-300';
                  default:
                    return 'bg-slate-100 text-slate-500 border border-slate-200 dark:bg-slate-800 dark:text-slate-400';
                }
              };

              return (
                <div key={drive.id} className="gov-card flex flex-col justify-between space-y-4 hover:border-slate-300">
                  <div className="space-y-2">
                    <div className="flex justify-between items-start gap-2">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">{drive.company_name}</span>
                      <div className="flex flex-col items-end gap-1">
                        <span className={`px-2 py-0.5 rounded font-bold uppercase text-[9px] ${getStatusBadge(drive.status)}`}>
                          {drive.status}
                        </span>
                        {drive.effective_status && drive.effective_status !== drive.status && (
                          <span className="text-[8px] font-semibold text-amber-600 dark:text-amber-400">
                            ({drive.effective_status})
                          </span>
                        )}
                      </div>
                    </div>

                    <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase leading-snug">
                      {drive.role}
                    </h4>

                    <div className="space-y-1.5 text-slate-500 pt-1 text-[11px]">
                      {drive.job_id && (
                        <p className="font-mono text-[10px] text-slate-400">ID: {drive.job_id}</p>
                      )}
                      <p>CTC Package: <span className="font-semibold text-slate-700 dark:text-slate-300">{drive.package_lpa} LPA</span></p>
                      <p>Location: <span className="font-semibold text-slate-700 dark:text-slate-300">{drive.location}</span></p>
                      <p>Min CGPA Cutoff: <span className="font-semibold text-slate-700 dark:text-slate-300">{drive.cgpa_cutoff}</span></p>
                      <p>Allowed Branches: <span className="font-semibold text-slate-700 dark:text-slate-300">{drive.allowed_depts || 'ALL'}</span></p>
                      <p>Allowed Backlogs: <span className="font-semibold text-slate-700 dark:text-slate-300">{drive.allowed_backlogs}</span></p>
                      <p className="flex items-center gap-1"><Calendar size={11} /> Deadline: {drive.deadline}</p>
                    </div>
                  </div>

                  <div className="flex gap-2 pt-2 border-t border-gov-border dark:border-slate-850">
                    <button
                      onClick={() => handleOpenInspect(drive)}
                      className="gov-btn-secondary py-1.5 w-full flex justify-center items-center gap-1 border border-gov-border hover:bg-slate-50 dark:hover:bg-slate-800 font-bold uppercase text-[10px]"
                      title="Inspect Details"
                    >
                      <Eye size={12} /> Inspect
                    </button>
                    <button
                      onClick={() => handleOpenEdit(drive)}
                      className="gov-btn-secondary py-1.5 w-full flex justify-center items-center gap-1 border border-gov-border hover:bg-slate-50 dark:hover:bg-slate-800 font-bold uppercase text-[10px]"
                      title="Edit Criteria"
                    >
                      <Edit size={12} /> Edit
                    </button>
                    {tab === 'active' && (
                      <button
                        onClick={() => handleOpenDelete(drive)}
                        className="gov-btn-secondary py-1.5 w-full flex justify-center items-center gap-1 border border-red-200 hover:bg-red-50 text-red-650 font-bold uppercase text-[10px]"
                        title="Archive or Delete"
                      >
                        <Trash2 size={12} /> Remove
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* RESPONSIVE PAGINATION BAR */}
          {totalCount > 0 && (
            <div className="gov-card flex flex-col sm:flex-row justify-between items-center gap-4 py-3 text-xs">
              <div className="text-slate-500 font-semibold text-[11px] flex items-center gap-2">
                <span>
                  Showing <span className="font-bold text-slate-700 dark:text-slate-200">{(currentPage - 1) * pageSize + 1}</span> to{' '}
                  <span className="font-bold text-slate-700 dark:text-slate-200">{Math.min(currentPage * pageSize, totalCount)}</span> of{' '}
                  <span className="font-bold text-slate-700 dark:text-slate-200">{totalCount}</span> drives
                </span>
                <span className="text-slate-300 dark:text-slate-700">|</span>
                <label className="flex items-center gap-1">
                  <span>Show</span>
                  <select
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setCurrentPage(1);
                    }}
                    className="border border-gov-border dark:border-slate-800 bg-white dark:bg-slate-950 rounded px-1.5 py-0.5 text-[11px] font-bold"
                  >
                    <option value={6}>6</option>
                    <option value={9}>9</option>
                    <option value={15}>15</option>
                    <option value={30}>30</option>
                  </select>
                  <span>per page</span>
                </label>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage <= 1}
                  className="px-2.5 py-1 rounded border border-gov-border dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1 text-[11px] font-bold uppercase transition-colors"
                >
                  <ChevronLeft size={14} /> Prev
                </button>

                <span className="px-3 py-1 text-[11px] font-bold text-slate-600 dark:text-slate-300">
                  Page {currentPage} of {totalPages || 1}
                </span>

                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage >= totalPages}
                  className="px-2.5 py-1 rounded border border-gov-border dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1 text-[11px] font-bold uppercase transition-colors"
                >
                  Next <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SCHEDULE DIALOG MODAL */}
      {isAddOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-6 rounded-lg max-w-md w-full text-xs space-y-4">
            <div className="flex justify-between items-center border-b border-gov-border dark:border-slate-850 pb-3">
              <h4 className="text-sm font-bold text-gov-navy dark:text-slate-200 uppercase">Schedule Recruitment Drive</h4>
              <button onClick={() => setIsAddOpen(false)} className="text-slate-400 hover:text-slate-650">
                <X size={16} />
              </button>
            </div>
            
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="drv-comp" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Company Name *</label>
                  <input
                    id="drv-comp"
                    type="text"
                    required
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                    placeholder="e.g. TCS"
                  />
                </div>
                <div>
                  <label htmlFor="drv-role" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Job Role / Title *</label>
                  <input
                    id="drv-role"
                    type="text"
                    required
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 focus:outline-none"
                    placeholder="e.g. Systems Engineer"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label htmlFor="drv-package" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Package (LPA) *</label>
                  <input
                    id="drv-package"
                    type="number"
                    step="0.1"
                    required
                    value={packageLpa}
                    onChange={(e) => setPackageLpa(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="drv-location" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Work Location *</label>
                  <input
                    id="drv-location"
                    type="text"
                    required
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="drv-cgpa" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Min CGPA *</label>
                  <input
                    id="drv-cgpa"
                    type="number"
                    step="0.1"
                    required
                    value={cgpaCutoff}
                    onChange={(e) => setCgpaCutoff(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="drv-backlogs" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Max Allowed Backlogs</label>
                  <input
                    id="drv-backlogs"
                    type="number"
                    required
                    value={allowedBacklogs}
                    onChange={(e) => setAllowedBacklogs(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="drv-interview-date" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Interview Date *</label>
                  <input
                    id="drv-interview-date"
                    type="date"
                    required
                    value={interviewDate}
                    onChange={(e) => setInterviewDate(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="drv-deadline" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Deadline Date *</label>
                  <input
                    id="drv-deadline"
                    type="date"
                    required
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="drv-depts" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Allowed Branches (Comma-Separated)</label>
                <input
                  id="drv-depts"
                  type="text"
                  required
                  value={allowedDepts}
                  onChange={(e) => setAllowedDepts(e.target.value)}
                  className="mt-1.5 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  placeholder="CSE, IT, ECE"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label htmlFor="drv-batch" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Batch *</label>
                  <input
                    id="drv-batch"
                    type="text"
                    required
                    value={batch}
                    onChange={(e) => setBatch(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="drv-min-att" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Min Attendance *</label>
                  <input
                    id="drv-min-att"
                    type="number"
                    required
                    value={minAttendance}
                    onChange={(e) => setMinAttendance(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="drv-status" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Status *</label>
                  <select
                    id="drv-status"
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-950 focus:outline-none"
                  >
                    <option value="DRAFT">DRAFT</option>
                    <option value="SCHEDULED">SCHEDULED (Upcoming)</option>
                    <option value="REGISTRATION_OPEN">REGISTRATION_OPEN</option>
                    <option value="PUBLISHED">PUBLISHED</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setIsAddOpen(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border">Cancel</button>
                <button type="submit" className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy border-0">Schedule Drive</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT DIALOG MODAL */}
      {isEditOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-805 p-6 rounded-lg max-w-md w-full text-xs space-y-4">
            <div className="flex justify-between items-center border-b border-gov-border dark:border-slate-850 pb-3">
              <h4 className="text-sm font-bold text-gov-navy dark:text-slate-200 uppercase">Modify Recruitment Settings</h4>
              <button onClick={() => setIsEditOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={16} />
              </button>
            </div>
            
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="edit-drv-comp" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Company Name</label>
                  <input
                    id="edit-drv-comp"
                    type="text"
                    required
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-drv-role" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Job Role</label>
                  <input
                    id="edit-drv-role"
                    type="text"
                    required
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label htmlFor="edit-drv-package" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Package (LPA)</label>
                  <input
                    id="edit-drv-package"
                    type="number"
                    step="0.1"
                    required
                    value={packageLpa}
                    onChange={(e) => setPackageLpa(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-drv-location" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Location</label>
                  <input
                    id="edit-drv-location"
                    type="text"
                    required
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-drv-cgpa" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Min CGPA</label>
                  <input
                    id="edit-drv-cgpa"
                    type="number"
                    step="0.1"
                    required
                    value={cgpaCutoff}
                    onChange={(e) => setCgpaCutoff(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label htmlFor="edit-drv-backlogs" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Allowed Backlogs</label>
                  <input
                    id="edit-drv-backlogs"
                    type="number"
                    required
                    value={allowedBacklogs}
                    onChange={(e) => setAllowedBacklogs(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-drv-interview-date" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Interview Date *</label>
                  <input
                    id="edit-drv-interview-date"
                    type="date"
                    required
                    value={interviewDate}
                    onChange={(e) => setInterviewDate(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-drv-deadline" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Deadline Date *</label>
                  <input
                    id="edit-drv-deadline"
                    type="date"
                    required
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-drv-status" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Status</label>
                  <select
                    id="edit-drv-status"
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 focus:outline-none"
                  >
                    <option value="DRAFT">DRAFT</option>
                    <option value="SCHEDULED">SCHEDULED (Upcoming)</option>
                    <option value="REGISTRATION_OPEN">REGISTRATION_OPEN</option>
                    <option value="REGISTRATION_CLOSED">REGISTRATION_CLOSED</option>
                    <option value="ONGOING">ONGOING</option>
                    <option value="ASSESSMENT">ASSESSMENT</option>
                    <option value="INTERVIEW">INTERVIEW</option>
                    <option value="RESULT_DECLARED">RESULT_DECLARED</option>
                    <option value="COMPLETED">COMPLETED</option>
                    <option value="ARCHIVED">ARCHIVED</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="edit-drv-batch" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Batch *</label>
                  <input
                    id="edit-drv-batch"
                    type="text"
                    required
                    value={batch}
                    onChange={(e) => setBatch(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-drv-min-att" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Min Attendance % *</label>
                  <input
                    id="edit-drv-min-att"
                    type="number"
                    required
                    value={minAttendance}
                    onChange={(e) => setMinAttendance(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setIsEditOpen(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border">Cancel</button>
                <button type="submit" className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy border-0">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELETE / ARCHIVE DIALOG MODAL */}
      {isDeleteOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-6 rounded-lg max-w-md w-full text-xs space-y-4">
            <div className="flex items-start gap-3">
              <div className="bg-amber-50 dark:bg-amber-950/40 p-2 rounded-full text-amber-600 shrink-0">
                <AlertTriangle size={20} />
              </div>
              <div className="space-y-1.5">
                <h4 className="text-sm font-bold text-slate-850 dark:text-slate-200 uppercase">Confirm Drive Archival or Removal</h4>
                <p className="text-slate-600 dark:text-slate-400 leading-normal">
                  Are you sure you want to proceed with removal for <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedDrive?.company_name} ({selectedDrive?.role})</span>?
                </p>
                <div className="bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 p-3 rounded text-[11px] text-blue-900 dark:text-blue-300 space-y-1">
                  <p className="font-bold">Institutional Safety Rule:</p>
                  <p className="leading-relaxed">
                    Placement drives with existing candidate applications or activities are <strong>safely archived</strong> rather than hard-deleted to preserve all historical records, evaluations, and student records. Only drives with zero associated records will be permanently deleted.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex gap-3 justify-end pt-2 border-t border-gov-border dark:border-slate-850">
              <button onClick={() => setIsDeleteOpen(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border">Cancel</button>
              <button onClick={handleDeleteSubmit} className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-red-600 border-0 hover:bg-red-700">Confirm Action</button>
            </div>
          </div>
        </div>
      )}

      {/* INSPECT DETAILS DIALOG MODAL */}
      {isInspectOpen && inspectDrive && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-6 rounded-lg max-w-2xl w-full text-xs space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-gov-border dark:border-slate-850 pb-3">
              <div>
                <h4 className="text-sm font-bold text-gov-navy dark:text-slate-200 uppercase flex items-center gap-2">
                  <Briefcase size={16} className="text-gov-blue" />
                  {inspectDrive.company_name} — {inspectDrive.role}
                </h4>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Drive ID: #{inspectDrive.id} | Status: <span className="font-bold text-slate-700 dark:text-slate-300">{inspectDrive.status}</span>
                  {inspectDrive.effective_status && inspectDrive.effective_status !== inspectDrive.status && ` (Effective: ${inspectDrive.effective_status})`}
                </p>
              </div>
              <button onClick={() => setIsInspectOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={16} />
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 dark:bg-slate-950 p-3 rounded border border-gov-border dark:border-slate-850">
              <div>
                <span className="block text-[9px] uppercase font-bold text-slate-400">Package</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">{inspectDrive.package_lpa} LPA</span>
              </div>
              <div>
                <span className="block text-[9px] uppercase font-bold text-slate-400">Location</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">{inspectDrive.location}</span>
              </div>
              <div>
                <span className="block text-[9px] uppercase font-bold text-slate-400">Min CGPA</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">{inspectDrive.cgpa_cutoff}</span>
              </div>
              <div>
                <span className="block text-[9px] uppercase font-bold text-slate-400">Allowed Backlogs</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">&le; {inspectDrive.allowed_backlogs}</span>
              </div>
              <div>
                <span className="block text-[9px] uppercase font-bold text-slate-400">Allowed Branches</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">{inspectDrive.allowed_depts}</span>
              </div>
              <div>
                <span className="block text-[9px] uppercase font-bold text-slate-400">Min Attendance</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">{inspectDrive.min_attendance}%</span>
              </div>
              <div>
                <span className="block text-[9px] uppercase font-bold text-slate-400">Deadline</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">{inspectDrive.deadline}</span>
              </div>
              <div>
                <span className="block text-[9px] uppercase font-bold text-slate-400">Interview Date</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">{inspectDrive.interview_date}</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <h5 className="font-bold uppercase text-[11px] text-slate-700 dark:text-slate-300">
                  Candidate Applications ({inspectDrive.students_applied?.length || 0})
                </h5>
                <span className="text-[10px] text-slate-400">
                  Eligible Students: {inspectDrive.students_eligible_count ?? 'N/A'}
                </span>
              </div>

              {(!inspectDrive.students_applied || inspectDrive.students_applied.length === 0) ? (
                <p className="text-slate-400 italic py-2 text-[11px]">No applications recorded for this drive.</p>
              ) : (
                <div className="border border-gov-border dark:border-slate-800 rounded overflow-hidden max-h-48 overflow-y-auto">
                  <table className="w-full text-left">
                    <thead className="bg-slate-100 dark:bg-slate-800 text-[10px] uppercase font-bold text-slate-600 dark:text-slate-300">
                      <tr>
                        <th className="p-2">Name</th>
                        <th className="p-2">Branch</th>
                        <th className="p-2">CGPA</th>
                        <th className="p-2">Round</th>
                        <th className="p-2">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gov-border dark:divide-slate-800 text-[11px]">
                      {inspectDrive.students_applied.map((app: any) => (
                        <tr key={app.application_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                          <td className="p-2 font-semibold text-slate-800 dark:text-slate-200">{app.name}</td>
                          <td className="p-2">{app.dept_code}</td>
                          <td className="p-2">{app.cgpa}</td>
                          <td className="p-2">{app.current_round}</td>
                          <td className="p-2">
                            <span className="px-1.5 py-0.5 rounded font-bold uppercase text-[9px] bg-slate-100 dark:bg-slate-800">
                              {app.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-3 border-t border-gov-border dark:border-slate-850">
              <button
                onClick={() => setIsInspectOpen(false)}
                className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default AdminDrives;
