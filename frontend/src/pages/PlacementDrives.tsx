import React, { useState, useEffect } from 'react';
import { driveService, applicationService } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { TableSkeleton } from '../components/LoadingSkeleton';
import { 
  Briefcase, PlusCircle, Calendar, MapPin, DollarSign, Award, Clock, 
  Users, Trash2, Edit, ChevronRight, X, User, ExternalLink, Filter, Search,
  Download, FileSpreadsheet, Brain
} from 'lucide-react';
import { AccessibleModal } from '../components/AccessibilityComponents';
import { DriveFeedbackReportModal } from '../components/DriveFeedbackReportModal';

const generateJobId = () => 'JD-' + Math.floor(1000 + Math.random() * 9000) + '-' + Date.now().toString().slice(-4);

export const PlacementDrives: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [drives, setDrives] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  const [selectedDriveId, setSelectedDriveId] = useState<number | null>(null);
  const [selectedDriveDetails, setSelectedDriveDetails] = useState<any | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [feedbackModalDriveId, setFeedbackModalDriveId] = useState<number | null>(null);

  // Filters and Categories
  const [statusFilter, setStatusFilter] = useState<string>(''); // All, Active, Upcoming, Completed
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Add Drive form toggle
  const [showAddModal, setShowAddModal] = useState(false);
  const [showAddCompanyModal, setShowAddCompanyModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);

  // Form states
  const [newCompany, setNewCompany] = useState({
    name: '',
    industry: '',
    website: '',
    description: ''
  });

  const [newDrive, setNewDrive] = useState({
    company_id: 0,
    role: '',
    package_lpa: 6.5,
    location: 'Hyderabad',
    cgpa_cutoff: 7.0,
    allowed_depts: 'CSE,IT,ECE',
    allowed_backlogs: 0,
    bond_details: 'No Bond',
    selection_process: 'Aptitude -> Technical -> HR',
    interview_date: new Date().toISOString().split('T')[0],
    deadline: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString().split('T')[0],
    status: 'DRAFT',
    batch: '2026',
    min_attendance: 75,
    job_id: generateJobId(),
    responsibilities: 'Core software engineering development and team collaboration.',
    required_skills: 'React, Node.js, SQL',
    preferred_skills: 'AWS, Docker',
    job_type: 'Full-Time',
    work_mode: 'Onsite',
    openings_count: 5,
    hiring_process: 'Online test -> Coding round -> HR',
    company_logo: 'https://logo.clearbit.com/google.com'
  });

  const [editForm, setEditForm] = useState<any>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const comps = await driveService.getCompanies();
      setCompanies(comps);
      if (comps.length > 0 && newDrive.company_id === 0) {
        setNewDrive(prev => ({ ...prev, company_id: comps[0].id }));
      }

      const drivesList = await driveService.getDrives();
      setDrives(drivesList);
    } catch (err) {
      console.error('Failed to load placement drives data', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDetails = async (id: number) => {
    setLoadingDetails(true);
    try {
      const details = await driveService.getDriveDetails(id);
      setSelectedDriveDetails(details);
    } catch (err) {
      console.error('Failed to load drive details', err);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleExportDriveCSV = () => {
    if (!selectedDriveDetails || !selectedDriveDetails.applied_list) return;
    const exportRows = selectedDriveDetails.applied_list.map((app: any) => ({
      "Student Name": app.name,
      "Roll Number": app.student_id,
      "Email": app.email,
      "Department": app.dept_code,
      "Batch": app.batch,
      "CGPA": app.cgpa,
      "Attendance": app.attendance,
      "Backlogs": app.backlogs,
      "Company": selectedDriveDetails.company_name,
      "Job Role": selectedDriveDetails.role,
      "LPA": selectedDriveDetails.package_lpa,
      "Application Date": app.applied_date,
      "Interview Date": selectedDriveDetails.interview_date,
      "Process Round": app.current_round,
      "Application Status": app.status,
      "Joining Status": app.joining_status
    }));

    if (exportRows.length === 0) return;
    const headers = Object.keys(exportRows[0]).join(',');
    const csvContent = "data:text/csv;charset=utf-8,\uFEFF" + [
      headers,
      ...exportRows.map((row: any) => 
        Object.values(row).map(val => `"${String(val !== null && val !== undefined ? val : '').replace(/"/g, '""')}"`).join(',')
      )
    ].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `applications_${selectedDriveDetails.company_name.replace(/\s+/g, '_')}_${selectedDriveDetails.role.replace(/\s+/g, '_')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportDriveExcel = () => {
    if (!selectedDriveDetails || !selectedDriveDetails.applied_list) return;
    const exportRows = selectedDriveDetails.applied_list.map((app: any) => ({
      "Student Name": app.name,
      "Roll Number": app.student_id,
      "Email": app.email,
      "Department": app.dept_code,
      "Batch": app.batch,
      "CGPA": app.cgpa,
      "Attendance": app.attendance,
      "Backlogs": app.backlogs,
      "Company": selectedDriveDetails.company_name,
      "Job Role": selectedDriveDetails.role,
      "LPA": selectedDriveDetails.package_lpa,
      "Application Date": app.applied_date,
      "Interview Date": selectedDriveDetails.interview_date,
      "Process Round": app.current_round,
      "Application Status": app.status,
      "Joining Status": app.joining_status
    }));

    if (exportRows.length === 0) return;
    const headers = Object.keys(exportRows[0]).join('\t');
    const excelContent = "data:application/vnd.ms-excel;charset=utf-8,\uFEFF" + [
      headers,
      ...exportRows.map((row: any) => 
        Object.values(row).map(val => String(val !== null && val !== undefined ? val : '').replace(/\t/g, ' ')).join('\t')
      )
    ].join("\n");
    const encodedUri = encodeURI(excelContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `applications_${selectedDriveDetails.company_name.replace(/\s+/g, '_')}_${selectedDriveDetails.role.replace(/\s+/g, '_')}.xls`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedDriveId) {
      loadDetails(selectedDriveId);
    } else {
      setSelectedDriveDetails(null);
    }
  }, [selectedDriveId]);

  const handleAddCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await driveService.createCompany(newCompany);
      alert('Company Registered Successfully!');
      setShowAddCompanyModal(false);
      setNewCompany({ name: '', industry: '', website: '', description: '' });
      loadData();
      if (created) {
        setNewDrive(prev => ({ ...prev, company_id: created.id }));
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to register company.');
    }
  };

  const handleAddDrive = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await driveService.createDrive(newDrive);
      alert('Placement Drive scheduled and logged to recruitment calendar!');
      setShowAddModal(false);
      setNewDrive(prev => ({
        ...prev,
        role: '',
        job_id: generateJobId(),
        package_lpa: 6.5,
        cgpa_cutoff: 7.0,
        allowed_backlogs: 0
      }));
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to schedule placement drive.');
    }
  };

  const handleOpenAddDriveModal = () => {
    setNewDrive(prev => ({
      ...prev,
      job_id: generateJobId()
    }));
    setShowAddModal(true);
  };

  const handleEditClick = (drive: any) => {
    const matchedCompanyId = drive.company_id;
    setEditForm({
      id: drive.id,
      company_id: matchedCompanyId,
      role: drive.role || '',
      package_lpa: drive.package_lpa || 6.5,
      location: drive.location || 'Hyderabad',
      cgpa_cutoff: drive.cgpa_cutoff || 7.0,
      allowed_depts: drive.allowed_depts || 'CSE,IT,ECE',
      allowed_backlogs: drive.allowed_backlogs || 0,
      bond_details: drive.bond_details || 'No Bond',
      selection_process: drive.selection_process || 'Aptitude -> Technical -> HR',
      interview_date: drive.interview_date || '',
      deadline: drive.deadline || '',
      status: drive.status || 'DRAFT',
      batch: drive.batch || '2026',
      min_attendance: drive.min_attendance || 75,
      job_id: drive.job_id || '',
      responsibilities: drive.responsibilities || '',
      required_skills: drive.required_skills || '',
      preferred_skills: drive.preferred_skills || '',
      job_type: drive.job_type || 'Full-Time',
      work_mode: drive.work_mode || 'Onsite',
      openings_count: drive.openings_count || 5,
      hiring_process: drive.hiring_process || '',
      company_logo: drive.company_logo || ''
    });
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editForm) return;
    if (!editForm.company_id || editForm.company_id <= 0) {
      alert('Error: Placement drive is missing a valid company association.');
      return;
    }
    try {
      await driveService.updateDrive(editForm.id, editForm);
      alert('Placement drive specifications updated!');
      setShowEditModal(false);
      loadData();
      if (selectedDriveId === editForm.id) {
        loadDetails(editForm.id);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to modify drive records.');
    }
  };

  const handleDeleteDrive = async (id: number) => {
    if (user?.role !== 'admin') {
      alert('Elevated action: Only administrators have permissions to delete placement drives.');
      return;
    }
    if (!window.confirm('Are you sure you want to delete this placement drive? All applications and interview schedules mapping to this drive will be scrubbed.')) {
      return;
    }
    try {
      await driveService.deleteDrive(id);
      alert('Drive record deleted.');
      setSelectedDriveId(null);
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete drive record.');
    }
  };

  const handleStatusUpdate = async (applicationId: number, status: 'Selected' | 'Rejected' | 'Shortlisted', round: string) => {
    try {
      await applicationService.updateStatus(applicationId, {
        status,
        current_round: round,
        joining_status: status === 'Selected' ? 'Accepted' : 'Pending'
      });
      alert(`Candidate status updated to ${status}!`);
      if (selectedDriveId) loadDetails(selectedDriveId);
    } catch (err) {
      alert('Failed to update candidate application status.');
    }
  };

  // Filter drives list based on status category & search
  const filteredDrives = drives.filter(d => {
    const matchesSearch = d.company_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          d.role.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === '' || d.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="grid md:grid-cols-3 gap-6 text-xs text-slate-700 dark:text-slate-350">
      
      {/* Drives list pane (Left 2 columns) */}
      <div className="md:col-span-2 space-y-6">
        
        {/* Header Block */}
        <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
              <Calendar className="text-gov-blue" size={20} />
              Placement Calendars & Recruitment Drives
            </h2>
            <p className="text-[10px] text-slate-500 mt-0.5">
              Review current and upcoming campus placement drive schedules.
            </p>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={handleOpenAddDriveModal}
              className="gov-btn-primary py-2 px-3 rounded uppercase font-bold flex items-center gap-1 bg-gov-navy hover:bg-gov-accent border-0 text-white"
            >
              <PlusCircle size={14} /> Schedule Drive
            </button>
            <button
              onClick={() => setShowAddCompanyModal(true)}
              className="gov-btn-secondary border border-gov-border py-2 px-3 rounded uppercase font-bold flex items-center gap-1 hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              <PlusCircle size={14} /> Register Recruiter
            </button>
          </div>
        </div>

        {/* Filter bar */}
        <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-4 rounded-lg shadow-card flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 text-slate-400" size={14} />
            <input
              type="text"
              placeholder="Search drives by company or hiring role..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-2 text-xs border border-gov-border rounded dark:bg-slate-950 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Filter size={14} className="text-gov-blue" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-955 dark:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
            >
              <option value="">All Drives Status</option>
              <option value="DRAFT">DRAFT</option>
              <option value="PUBLISHED">PUBLISHED</option>
              <option value="REGISTRATION_OPEN">REGISTRATION_OPEN</option>
              <option value="REGISTRATION_CLOSED">REGISTRATION_CLOSED</option>
              <option value="ASSESSMENT">ASSESSMENT</option>
              <option value="INTERVIEW">INTERVIEW</option>
              <option value="RESULT_DECLARED">RESULT_DECLARED</option>
              <option value="COMPLETED">COMPLETED</option>
            </select>
          </div>
        </div>

        {/* Drives card listings */}
        {loading ? <TableSkeleton /> : filteredDrives.length === 0 ? (
          <div className="gov-card text-center py-12 text-slate-450 uppercase font-bold">
            No placement drives scheduled matching these filters.
          </div>
        ) : (
          <div className="space-y-4">
            {filteredDrives.map((d) => (
              <div 
                key={d.id} 
                className={`border rounded p-4 flex justify-between items-center transition-all bg-white dark:bg-slate-900 cursor-pointer ${
                  selectedDriveId === d.id 
                    ? 'border-gov-blue ring-1 ring-gov-blue' 
                    : 'border-gov-border dark:border-slate-800 hover:border-slate-400'
                }`}
                onClick={() => setSelectedDriveId(d.id)}
              >
                <div className="flex gap-4 items-center">
                  {d.company_logo ? (
                    <img 
                      src={d.company_logo} 
                      alt={`${d.company_name} Logo`}
                      className="w-10 h-10 rounded border border-gov-border dark:border-slate-800 object-contain p-1 bg-white"
                      onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
                    />
                  ) : (
                    <div className="w-10 h-10 rounded border border-gov-border dark:border-slate-800 bg-slate-100 flex items-center justify-center font-bold text-slate-400">
                      {d.company_name.charAt(0)}
                    </div>
                  )}
                  <div className="space-y-0.5">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                      {d.company_name} &bull; {d.status}
                    </p>
                    <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase">{d.role}</h4>
                    <p className="text-[10px] text-slate-500">
                      Salary: <span className="font-semibold text-slate-700 dark:text-slate-300">{d.package_lpa} LPA</span> &bull; 
                      CGPA Cutoff: <span className="font-semibold text-slate-700 dark:text-slate-300">{d.cgpa_cutoff}</span> &bull; 
                      Branches: <span className="font-semibold text-slate-700 dark:text-slate-300">{d.allowed_depts}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => setFeedbackModalDriveId(d.id)}
                    className="p-1 text-slate-450 hover:text-gov-blue rounded focus:outline-none"
                    title="View Interview Intelligence Report"
                  >
                    <Brain size={14} />
                  </button>
                  <button
                    onClick={() => handleEditClick(d)}
                    className="p-1 text-slate-450 hover:text-amber-500 rounded focus:outline-none"
                    title="Edit Drive Settings"
                  >
                    <Edit size={14} />
                  </button>
                  {user?.role === 'admin' && (
                    <button
                      onClick={() => handleDeleteDrive(d.id)}
                      className="p-1 text-slate-450 hover:text-red-500 rounded focus:outline-none"
                      title="Scrub Drive"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                  <ChevronRight size={16} className="text-slate-400" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected drive detailed information (Right 1 column) */}
      <div className="space-y-6">
        <div className="gov-card h-fit space-y-5">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide border-b border-gov-border dark:border-slate-850 pb-2 flex items-center gap-2">
            <Users size={16} className="text-gov-blue" />
            Drive Information Desk
          </h3>

          {!selectedDriveDetails ? (
            <div className="text-center py-12 text-slate-400 italic">
              Select a placement schedule on the left to audit applicants and eligibility criteria.
            </div>
          ) : loadingDetails ? (
            <TableSkeleton />
          ) : (
            <div className="space-y-5 text-xs">
              
              {/* Drive profile header */}
              <div className="flex gap-3 items-center">
                {selectedDriveDetails.company_logo && (
                  <img 
                    src={selectedDriveDetails.company_logo} 
                    alt="Logo"
                    className="w-12 h-12 rounded border border-gov-border p-1 bg-white object-contain"
                  />
                )}
                <div>
                  <h4 className="font-extrabold text-slate-800 dark:text-slate-100 uppercase leading-snug">
                    {selectedDriveDetails.role}
                  </h4>
                  <p className="text-[10px] text-slate-450 font-bold uppercase">
                    {selectedDriveDetails.company_name}
                  </p>
                </div>
              </div>

              {/* Interview Intelligence Report Trigger */}
              <button
                onClick={() => setFeedbackModalDriveId(selectedDriveDetails.id)}
                className="w-full flex items-center justify-between p-2.5 rounded-lg border border-gov-blue/30 bg-gov-blue/5 hover:bg-gov-blue/10 dark:bg-gov-blue/10 dark:hover:bg-gov-blue/20 text-gov-navy dark:text-gov-accent transition-all group focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
              >
                <div className="flex items-center gap-2">
                  <Brain size={16} className="text-gov-blue group-hover:scale-110 transition-transform" />
                  <div className="text-left">
                    <span className="block font-bold text-[11px] uppercase tracking-wide">
                      Interview Intelligence Report
                    </span>
                    <span className="block text-[9px] text-slate-500 dark:text-slate-400">
                      Aggregated questions, difficulty & advice
                    </span>
                  </div>
                </div>
                <ChevronRight size={14} className="text-slate-400 group-hover:translate-x-0.5 transition-transform" />
              </button>

              {/* Recruitment parameters */}
              <div className="grid grid-cols-2 gap-3.5 bg-slate-50 dark:bg-slate-950 border border-gov-border dark:border-slate-850 p-3 rounded text-[11px]">
                <div className="flex items-center gap-2">
                  <DollarSign size={14} className="text-gov-blue shrink-0" />
                  <div>
                    <span className="block text-[9px] text-slate-450 uppercase font-bold">Salary</span>
                    <span className="font-bold text-slate-700 dark:text-slate-300">{selectedDriveDetails.package_lpa} LPA</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin size={14} className="text-gov-blue shrink-0" />
                  <div>
                    <span className="block text-[9px] text-slate-450 uppercase font-bold">Location</span>
                    <span className="font-bold text-slate-700 dark:text-slate-300">{selectedDriveDetails.location}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Award size={14} className="text-gov-blue shrink-0" />
                  <div>
                    <span className="block text-[9px] text-slate-450 uppercase font-bold">CGPA Cutoff</span>
                    <span className="font-bold text-slate-700 dark:text-slate-300">&ge; {selectedDriveDetails.cgpa_cutoff}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Clock size={14} className="text-gov-blue shrink-0" />
                  <div>
                    <span className="block text-[9px] text-slate-450 uppercase font-bold">Deadline</span>
                    <span className="font-bold text-red-650">{selectedDriveDetails.deadline}</span>
                  </div>
                </div>
              </div>

              {/* JD description summary */}
              <div className="space-y-1.5">
                <p className="font-bold text-[10px] text-slate-500 uppercase tracking-wider">Job Specifications</p>
                <div className="space-y-1 p-2.5 border border-gov-border dark:border-slate-850 rounded">
                  <p><strong>Job Type:</strong> {selectedDriveDetails.job_type} &bull; {selectedDriveDetails.work_mode}</p>
                  <p><strong>Allowed Backlogs:</strong> &le; {selectedDriveDetails.allowed_backlogs}</p>
                  <p><strong>Required Skills:</strong> {selectedDriveDetails.required_skills}</p>
                  <p><strong>Interview Date:</strong> {selectedDriveDetails.interview_date}</p>
                  <p><strong>Bond Details:</strong> {selectedDriveDetails.bond_details || 'No Bond Specified'}</p>
                </div>
              </div>

              {/* Selection pipeline timeline */}
              <div className="space-y-1.5">
                <p className="font-bold text-[10px] text-slate-500 uppercase tracking-wider">Hiring Process Timeline</p>
                <div className="p-2.5 border border-gov-border dark:border-slate-850 rounded text-gov-blue font-mono font-bold">
                  {selectedDriveDetails.hiring_process}
                </div>
              </div>

              {/* Applied list accordion */}
              <div className="space-y-3">
                <div className="flex justify-between items-center mt-2 mb-2">
                  <p className="font-bold text-[10px] text-slate-500 uppercase tracking-wider">Applied Candidates ({selectedDriveDetails.applied_list?.length || 0})</p>
                  {selectedDriveDetails.applied_list && selectedDriveDetails.applied_list.length > 0 && (
                    <div className="flex gap-2">
                      <button
                        onClick={handleExportDriveCSV}
                        className="bg-gov-navy hover:bg-slate-800 text-white font-bold py-1 px-2 rounded text-[9px] uppercase transition-all flex items-center gap-1 focus:outline-none"
                        title="Export CSV"
                      >
                        <Download size={10} /> CSV
                      </button>
                      <button
                        onClick={handleExportDriveExcel}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-1 px-2 rounded text-[9px] uppercase transition-all flex items-center gap-1 focus:outline-none"
                        title="Export Excel"
                      >
                        <FileSpreadsheet size={10} /> Excel
                      </button>
                    </div>
                  )}
                </div>
                
                {(!selectedDriveDetails.applied_list || selectedDriveDetails.applied_list.length === 0) ? (
                  <div className="text-center py-6 text-slate-400 italic border border-dashed rounded">
                    No student applications filed for this drive yet.
                  </div>
                ) : (
                  <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                    {selectedDriveDetails.applied_list.map((app: any) => (
                      <div key={app.application_id} className="border border-gov-border dark:border-slate-850 rounded p-2.5 space-y-2 bg-slate-50 dark:bg-slate-950">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-bold text-slate-800 dark:text-slate-200">{app.name} ({app.dept_code})</p>
                            <p className="text-[10px] text-slate-450">CGPA: {app.cgpa} &bull; Status: <span className="font-bold uppercase text-[9px]">{app.status}</span></p>
                          </div>
                        </div>

                        {/* Status updating actions */}
                        <div className="flex gap-2 justify-end pt-1">
                          <button
                            onClick={() => handleStatusUpdate(app.application_id, 'Selected', 'HR')}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-1 px-2.5 rounded text-[10px] uppercase transition-all"
                          >
                            Select
                          </button>
                          <button
                            onClick={() => handleStatusUpdate(app.application_id, 'Rejected', 'Rejected')}
                            className="bg-red-600 hover:bg-red-700 text-white font-bold py-1 px-2.5 rounded text-[10px] uppercase transition-all"
                          >
                            Reject
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>
          )}
        </div>
      </div>

      {/* MODAL 1: ADD DRIVE CALENDAR */}
      {showAddModal && (
        <AccessibleModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title="Schedule New Placement Drive"
        >
          <form onSubmit={handleAddDrive} className="space-y-4 text-xs text-slate-750">
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="add-drive-company" className="block font-bold text-slate-500 uppercase">Recruiting Company *</label>
                <select
                  id="add-drive-company"
                  required
                  value={newDrive.company_id}
                  onChange={(e) => setNewDrive({ ...newDrive, company_id: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                >
                  {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              
              <div>
                <label htmlFor="add-drive-role" className="block font-bold text-slate-500 uppercase">Hiring Designation *</label>
                <input
                  id="add-drive-role"
                  type="text"
                  required
                  value={newDrive.role}
                  onChange={(e) => setNewDrive({ ...newDrive, role: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                  placeholder="Software Engineer"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label htmlFor="add-drive-package" className="block font-bold text-slate-500 uppercase">CTC (LPA) *</label>
                <input
                  id="add-drive-package"
                  type="number"
                  step="0.1"
                  required
                  value={newDrive.package_lpa}
                  onChange={(e) => setNewDrive({ ...newDrive, package_lpa: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none"
                />
              </div>
              <div>
                <label htmlFor="add-drive-cgpa" className="block font-bold text-slate-500 uppercase">CGPA Cutoff *</label>
                <input
                  id="add-drive-cgpa"
                  type="number"
                  step="0.01"
                  required
                  value={newDrive.cgpa_cutoff}
                  onChange={(e) => setNewDrive({ ...newDrive, cgpa_cutoff: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none"
                />
              </div>
              <div>
                <label htmlFor="add-drive-backlogs" className="block font-bold text-slate-500 uppercase">Max Backlogs *</label>
                <input
                  id="add-drive-backlogs"
                  type="number"
                  required
                  value={newDrive.allowed_backlogs}
                  onChange={(e) => setNewDrive({ ...newDrive, allowed_backlogs: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="add-drive-depts" className="block font-bold text-slate-500 uppercase">Allowed Branches *</label>
                <input
                  id="add-drive-depts"
                  type="text"
                  required
                  value={newDrive.allowed_depts}
                  onChange={(e) => setNewDrive({ ...newDrive, allowed_depts: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none"
                  placeholder="CSE,IT,ECE"
                />
              </div>
              <div>
                <label htmlFor="add-drive-location" className="block font-bold text-slate-500 uppercase">Location *</label>
                <input
                  id="add-drive-location"
                  type="text"
                  required
                  value={newDrive.location}
                  onChange={(e) => setNewDrive({ ...newDrive, location: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="add-drive-date" className="block font-bold text-slate-500 uppercase">Interview Date *</label>
                <input
                  id="add-drive-date"
                  type="date"
                  required
                  value={newDrive.interview_date}
                  onChange={(e) => setNewDrive({ ...newDrive, interview_date: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
              <div>
                <label htmlFor="add-drive-deadline" className="block font-bold text-slate-500 uppercase">Apply Deadline *</label>
                <input
                  id="add-drive-deadline"
                  type="date"
                  required
                  value={newDrive.deadline}
                  onChange={(e) => setNewDrive({ ...newDrive, deadline: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label htmlFor="add-drive-batch" className="block font-bold text-slate-500 uppercase">Target Batch *</label>
                <input
                  id="add-drive-batch"
                  type="text"
                  required
                  value={newDrive.batch}
                  onChange={(e) => setNewDrive({ ...newDrive, batch: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
              <div>
                <label htmlFor="add-drive-attendance" className="block font-bold text-slate-500 uppercase">Min Attendance % *</label>
                <input
                  id="add-drive-attendance"
                  type="number"
                  required
                  value={newDrive.min_attendance}
                  onChange={(e) => setNewDrive({ ...newDrive, min_attendance: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
              <div>
                <label htmlFor="add-drive-status" className="block font-bold text-slate-500 uppercase">Initial Status *</label>
                <select
                  id="add-drive-status"
                  value={newDrive.status}
                  onChange={(e) => setNewDrive({ ...newDrive, status: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 dark:text-slate-100"
                >
                  <option value="DRAFT">DRAFT</option>
                  <option value="PUBLISHED">PUBLISHED</option>
                  <option value="REGISTRATION_OPEN">REGISTRATION_OPEN</option>
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="add-drive-req" className="block font-bold text-slate-500 uppercase">Required Technical Skills</label>
              <input
                id="add-drive-req"
                type="text"
                value={newDrive.required_skills}
                onChange={(e) => setNewDrive({ ...newDrive, required_skills: e.target.value })}
                className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                placeholder="Python, React, Django"
              />
            </div>

            <div>
              <label htmlFor="add-drive-resp" className="block font-bold text-slate-500 uppercase">Job Description Summary</label>
              <textarea
                id="add-drive-resp"
                value={newDrive.responsibilities}
                onChange={(e) => setNewDrive({ ...newDrive, responsibilities: e.target.value })}
                className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 h-16"
                placeholder="Core development tasks..."
              />
            </div>

            <div className="flex gap-3 justify-end pt-2">
              <button type="button" onClick={() => setShowAddModal(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold bg-white text-slate-700">Cancel</button>
              <button type="submit" className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy border-0">Schedule</button>
            </div>
          </form>
        </AccessibleModal>
      )}

      {/* MODAL 2: REGISTER COMPANY */}
      {showAddCompanyModal && (
        <AccessibleModal
          isOpen={showAddCompanyModal}
          onClose={() => setShowAddCompanyModal(false)}
          title="Register Corporate Partner"
        >
          <form onSubmit={handleAddCompany} className="space-y-4 text-xs text-slate-755">
            <div>
              <label htmlFor="reg-company-name" className="block font-bold text-slate-500 uppercase">Company Name *</label>
              <input
                id="reg-company-name"
                type="text"
                required
                value={newCompany.name}
                onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
                className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                placeholder="Amazon"
              />
            </div>

            <div>
              <label htmlFor="reg-company-industry" className="block font-bold text-slate-500 uppercase">Industry Domain *</label>
              <input
                id="reg-company-industry"
                type="text"
                required
                value={newCompany.industry}
                onChange={(e) => setNewCompany({ ...newCompany, industry: e.target.value })}
                className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                placeholder="Cloud Infrastructure"
              />
            </div>

            <div>
              <label htmlFor="reg-company-website" className="block font-bold text-slate-500 uppercase">Company Website URL</label>
              <input
                id="reg-company-website"
                type="url"
                value={newCompany.website}
                onChange={(e) => setNewCompany({ ...newCompany, website: e.target.value })}
                className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                placeholder="https://amazon.jobs"
              />
            </div>

            <div>
              <label htmlFor="reg-company-desc" className="block font-bold text-slate-500 uppercase">Company Description</label>
              <textarea
                id="reg-company-desc"
                value={newCompany.description}
                onChange={(e) => setNewCompany({ ...newCompany, description: e.target.value })}
                className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 h-16"
              />
            </div>

            <div className="flex gap-3 justify-end pt-2">
              <button type="button" onClick={() => setShowAddCompanyModal(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold bg-white text-slate-700">Cancel</button>
              <button type="submit" className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy border-0">Register</button>
            </div>
          </form>
        </AccessibleModal>
      )}

      {/* MODAL 3: EDIT DRIVE */}
      {showEditModal && editForm && (
        <AccessibleModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          title={`Modify Drive Settings - ${editForm.job_id}`}
        >
          <form onSubmit={handleEditSubmit} className="space-y-4 text-xs text-slate-755">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="edit-drive-role" className="block font-bold text-slate-500 uppercase">Hiring Role *</label>
                <input
                  id="edit-drive-role"
                  type="text"
                  required
                  value={editForm.role}
                  onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
              <div>
                <label htmlFor="edit-drive-status" className="block font-bold text-slate-500 uppercase">Drive Status</label>
                <select
                  id="edit-drive-status"
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 dark:text-slate-100"
                >
                  <option value="DRAFT">DRAFT</option>
                  <option value="PUBLISHED">PUBLISHED</option>
                  <option value="Active">Active</option>
                  <option value="REGISTRATION_OPEN">REGISTRATION_OPEN</option>
                  <option value="REGISTRATION_CLOSED">REGISTRATION_CLOSED</option>
                  <option value="ASSESSMENT">ASSESSMENT</option>
                  <option value="INTERVIEW">INTERVIEW</option>
                  <option value="RESULT_DECLARED">RESULT_DECLARED</option>
                  <option value="COMPLETED">COMPLETED</option>
                  <option value="ARCHIVED">ARCHIVED</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label htmlFor="edit-drive-package" className="block font-bold text-slate-500 uppercase">CTC (LPA)</label>
                <input
                  id="edit-drive-package"
                  type="number"
                  step="0.1"
                  required
                  value={editForm.package_lpa}
                  onChange={(e) => setEditForm({ ...editForm, package_lpa: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
              <div>
                <label htmlFor="edit-drive-cgpa" className="block font-bold text-slate-500 uppercase">CGPA Cutoff</label>
                <input
                  id="edit-drive-cgpa"
                  type="number"
                  step="0.01"
                  required
                  value={editForm.cgpa_cutoff}
                  onChange={(e) => setEditForm({ ...editForm, cgpa_cutoff: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
              <div>
                <label htmlFor="edit-drive-backlogs" className="block font-bold text-slate-500 uppercase">Backlog Cutoff</label>
                <input
                  id="edit-drive-backlogs"
                  type="number"
                  required
                  value={editForm.allowed_backlogs}
                  onChange={(e) => setEditForm({ ...editForm, allowed_backlogs: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="edit-drive-depts" className="block font-bold text-slate-500 uppercase">Allowed Branches</label>
                <input
                  id="edit-drive-depts"
                  type="text"
                  required
                  value={editForm.allowed_depts}
                  onChange={(e) => setEditForm({ ...editForm, allowed_depts: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
              <div>
                <label htmlFor="edit-drive-location" className="block font-bold text-slate-500 uppercase">Location</label>
                <input
                  id="edit-drive-location"
                  type="text"
                  required
                  value={editForm.location}
                  onChange={(e) => setEditForm({ ...editForm, location: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="edit-drive-date" className="block font-bold text-slate-500 uppercase">Interview Date *</label>
                <input
                  id="edit-drive-date"
                  type="date"
                  required
                  value={editForm.interview_date}
                  onChange={(e) => setEditForm({ ...editForm, interview_date: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
              <div>
                <label htmlFor="edit-drive-deadline" className="block font-bold text-slate-500 uppercase">Apply Deadline *</label>
                <input
                  id="edit-drive-deadline"
                  type="date"
                  required
                  value={editForm.deadline}
                  onChange={(e) => setEditForm({ ...editForm, deadline: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="edit-drive-batch" className="block font-bold text-slate-500 uppercase">Target Batch *</label>
                <input
                  id="edit-drive-batch"
                  type="text"
                  required
                  value={editForm.batch}
                  onChange={(e) => setEditForm({ ...editForm, batch: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
              <div>
                <label htmlFor="edit-drive-attendance" className="block font-bold text-slate-500 uppercase">Min Attendance % *</label>
                <input
                  id="edit-drive-attendance"
                  type="number"
                  required
                  value={editForm.min_attendance}
                  onChange={(e) => setEditForm({ ...editForm, min_attendance: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
                />
              </div>
            </div>

            <div>
              <label htmlFor="edit-drive-req" className="block font-bold text-slate-500 uppercase">Required Technical Skills</label>
              <input
                id="edit-drive-req"
                type="text"
                value={editForm.required_skills}
                onChange={(e) => setEditForm({ ...editForm, required_skills: e.target.value })}
                className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100"
              />
            </div>

            <div>
              <label htmlFor="edit-drive-resp" className="block font-bold text-slate-500 uppercase">Job Description Summary</label>
              <textarea
                id="edit-drive-resp"
                value={editForm.responsibilities}
                onChange={(e) => setEditForm({ ...editForm, responsibilities: e.target.value })}
                className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 h-16"
              />
            </div>

            <div className="flex gap-3 justify-end pt-2">
              <button type="button" onClick={() => setShowEditModal(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold bg-white text-slate-700">Cancel</button>
              <button type="submit" className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy border-0">Save Settings</button>
            </div>
          </form>
        </AccessibleModal>
      )}

      {/* Aggregated Drive Feedback Report Modal */}
      <DriveFeedbackReportModal
        isOpen={feedbackModalDriveId !== null}
        onClose={() => setFeedbackModalDriveId(null)}
        driveId={feedbackModalDriveId}
        driveTitle={
          drives.find(d => d.id === feedbackModalDriveId)
            ? `${drives.find(d => d.id === feedbackModalDriveId).company_name} — ${drives.find(d => d.id === feedbackModalDriveId).role}`
            : undefined
        }
      />

    </div>
  );
};

export default PlacementDrives;
