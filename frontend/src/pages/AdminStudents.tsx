import React, { useState, useEffect } from 'react';
import { studentService, student360Service } from '../services/api';
import { TableSkeleton } from '../components/LoadingSkeleton';
import { 
  GraduationCap, PlusCircle, Search, Filter, Edit, Trash2, X, AlertTriangle, Eye, Upload, Download 
} from 'lucide-react';
import { ProfessionalTable } from '../components/ProfessionalTable';
import { AccessibleToast } from '../components/AccessibilityComponents';

export const AdminStudents: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [students, setStudents] = useState<any[]>([]);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  // Dialog configurations
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [isBulkOpen, setIsBulkOpen] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<any | null>(null);
  const [activeViewTab, setActiveViewTab] = useState<'profile' | 'projects' | 'other'>('profile');
  const [viewData360, setViewData360] = useState<any | null>(null);
  const [viewLoading, setViewLoading] = useState(false);
  const [viewError, setViewError] = useState<string | null>(null);
  const [viewStudentId, setViewStudentId] = useState<number | null>(null);

  // Form values
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [deptId, setDeptId] = useState<number>(1);
  const [gender, setGender] = useState('Male');
  const [batch, setBatch] = useState('2026');
  const [phone, setPhone] = useState('9876543210');
  const [cgpa, setCgpa] = useState<number>(8.0);
  const [attendance, setAttendance] = useState<number>(85.0);
  const [backlogs, setBacklogs] = useState<number>(0);
  const [skills, setSkills] = useState('Java, SQL');

  // Bulk Upload State
  const [bulkInput, setBulkInput] = useState('');
  const [bulkLoading, setBulkLoading] = useState(false);
  const [previewData, setPreviewData] = useState<any | null>(null);

  // Filters
  const [filterDept, setFilterDept] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [totalRecords, setTotalRecords] = useState(0);

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const loadStudents = async () => {
    setLoading(true);
    try {
      const res = await studentService.getStudents({
        search: searchQuery || undefined,
        dept_id: filterDept ? Number(filterDept) : undefined,
        status_filter: filterStatus || undefined,
        page: page,
        limit: pageSize
      });
      setStudents(res.items || []);
      setTotalRecords(res.total ?? (res.items ? res.items.length : 0));
    } catch (err) {
      console.error('Failed to load students database', err);
      showToast('Error fetching students records.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setPage(1);
  }, [filterDept, filterStatus, searchQuery]);

  useEffect(() => {
    loadStudents();
  }, [filterDept, filterStatus, searchQuery, page, pageSize]);

  const handleOpenAdd = () => {
    setName('');
    setEmail('');
    setDeptId(1);
    setGender('Male');
    setBatch('2026');
    setPhone('9876543210');
    setCgpa(8.0);
    setAttendance(85.0);
    setBacklogs(0);
    setSkills('Java, SQL, React');
    setIsAddOpen(true);
  };

  const safeArray = (value: any): any[] => {
    if (Array.isArray(value)) return value;
    if (typeof value === "string") {
      try {
        const parsed = JSON.parse(value);
        if (Array.isArray(parsed)) return parsed;
      } catch {}
      return value.split(",").map((s: string) => s.trim()).filter(Boolean);
    }
    return [];
  };

  const parseSkills = (skillsVal: any): string[] => {
    return safeArray(skillsVal);
  };

  const handleOpenEdit = async (std: any) => {
    try {
      const details = await studentService.getStudentById(std.id);
      setSelectedStudent(details);
      setName(details.name || '');
      setDeptId(details.dept_id || 1);
      setGender(details.gender || 'Male');
      setBatch(details.batch || '2026');
      setPhone(details.phone || '9876543210');
      setCgpa(details.cgpa);
      setAttendance(details.attendance);
      setBacklogs(details.backlogs);
      const parsed = parseSkills(details.skills);
      setSkills(parsed.join(', '));
      setIsEditOpen(true);
    } catch (err) {
      showToast('Failed to load student details for editing.', 'error');
    }
  };

  const handleOpenDelete = (std: any) => {
    setSelectedStudent(std);
    setIsDeleteOpen(true);
  };

  const handleOpenView = async (std: any) => {
    setViewStudentId(std.id);
    setViewLoading(true);
    setViewError(null);
    setViewData360(null);
    setIsViewOpen(true);
    setActiveViewTab('profile');
    try {
      const data360 = await student360Service.getStudent360(std.id);
      setViewData360(data360);
    } catch (err: any) {
      console.error(err);
      setViewError(err.response?.data?.detail || 'Unable to load student details.');
    } finally {
      setViewLoading(false);
    }
  };

  const handleRetryView = async () => {
    if (!viewStudentId) return;
    setViewLoading(true);
    setViewError(null);
    try {
      const data360 = await student360Service.getStudent360(viewStudentId);
      setViewData360(data360);
    } catch (err: any) {
      console.error(err);
      setViewError(err.response?.data?.detail || 'Unable to load student details.');
    } finally {
      setViewLoading(false);
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const skillsArr = skills.split(',').map(s => s.trim()).filter(Boolean);
      await studentService.createStudent({
        name,
        email,
        dept_id: deptId,
        gender,
        batch,
        phone,
        cgpa,
        attendance,
        backlogs,
        skills: JSON.stringify(skillsArr)
      });
      showToast('Student successfully registered!', 'success');
      setIsAddOpen(false);
      loadStudents();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to register candidate.', 'error');
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudent) return;
    try {
      const skillsArr = skills.split(',').map(s => s.trim()).filter(Boolean);
      await studentService.updateStudent(selectedStudent.id, {
        phone,
        cgpa,
        attendance,
        backlogs,
        skills: skillsArr
      });
      showToast('Student credentials updated!', 'success');
      setIsEditOpen(false);
      loadStudents();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to update credentials.', 'error');
    }
  };

  const handleDeleteSubmit = async () => {
    if (!selectedStudent) return;
    try {
      await studentService.deleteStudent(selectedStudent.id);
      showToast('Student record deleted successfully.', 'success');
      setIsDeleteOpen(false);
      loadStudents();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to remove student.', 'error');
    }
  };

  const handleBulkSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBulkLoading(true);
    try {
      const payload = JSON.parse(bulkInput);
      if (!Array.isArray(payload)) {
        throw new Error('Data payload must be a JSON array of student records.');
      }
      // Call with preview = true
      const res = await studentService.bulkUpload(payload, true);
      setPreviewData(res);
      showToast('Validation preview loaded! Please verify records before final confirmation.', 'info');
    } catch (err: any) {
      showToast(err.response?.data?.detail || err.message || 'Failed to validate JSON bulk payload.', 'error');
    } finally {
      setBulkLoading(false);
    }
  };

  const handleConfirmImport = async () => {
    setBulkLoading(true);
    try {
      const payload = JSON.parse(bulkInput);
      // Call with preview = false
      const res = await studentService.bulkUpload(payload, false);
      showToast(res.message || 'Successfully bulk imported student records!', 'success');
      setIsBulkOpen(false);
      setBulkInput('');
      setPreviewData(null);
      loadStudents();
    } catch (err: any) {
      showToast(err.response?.data?.detail || err.message || 'Failed to save imported student records.', 'error');
    } finally {
      setBulkLoading(false);
    }
  };

  const columns = [
    { header: 'Roll No', accessor: 'id', render: (row: any) => <span>#{row.id}</span> },
    { header: 'Student Name', accessor: 'name' },
    { header: 'Branch', accessor: 'dept_code' },
    { header: 'CGPA', accessor: 'cgpa' },
    { header: 'Attendance %', accessor: 'attendance', render: (row: any) => `${row.attendance}%` },
    { header: 'Backlogs', accessor: 'backlogs' },
    { header: 'Status', accessor: 'status', render: (row: any) => (
      <span className={`px-2 py-0.5 rounded font-bold uppercase text-[9px] ${
        row.status === 'Placed' ? 'bg-emerald-50 text-emerald-800 border border-emerald-250' : 'bg-amber-50 text-amber-800'
      }`}>
        {row.status}
      </span>
    )},
    { header: 'Actions', accessor: 'id', render: (row: any) => (
      <div className="flex gap-2">
        <button
          onClick={() => handleOpenView(row)}
          className="p-1 border border-gov-border rounded hover:bg-slate-100 dark:hover:bg-slate-800"
          title="View Profile Details"
        >
          <Eye size={12} className="text-slate-500" />
        </button>
        <button
          onClick={() => handleOpenEdit(row)}
          className="p-1 border border-gov-border rounded hover:bg-slate-100 dark:hover:bg-slate-800"
          title="Edit Candidate Metrics"
        >
          <Edit size={12} className="text-gov-blue" />
        </button>
        <button
          onClick={() => handleOpenDelete(row)}
          className="p-1 border border-gov-border rounded hover:bg-slate-100 dark:hover:bg-slate-800"
          title="Purge Profile"
        >
          <Trash2 size={12} className="text-red-500" />
        </button>
      </div>
    )}
  ];

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350">
      <AccessibleToast message={toast?.message || null} type={toast?.type || null} />

      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
            <GraduationCap className="text-gov-blue" size={24} />
            Institutional Student Database Directory
          </h2>
          <p className="text-[10px] text-slate-500 mt-1">
            Browse registered student profiles, verify academic criteria, modify parameters, and check student placement records.
          </p>
        </div>

        <div className="flex flex-wrap gap-2.5">
          <select
            value={filterDept}
            onChange={(e) => setFilterDept(e.target.value)}
            className="border border-gov-border rounded p-2 bg-white text-slate-700 dark:bg-slate-950 focus:outline-none focus:ring-1 focus:ring-gov-blue"
          >
            <option value="">Branch: All</option>
            <option value="1">CSE</option>
            <option value="2">IT</option>
            <option value="3">ECE</option>
            <option value="4">EEE</option>
            <option value="5">MECH</option>
            <option value="6">CIVIL</option>
          </select>
          
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="border border-gov-border rounded p-2 bg-white text-slate-700 dark:bg-slate-950 focus:outline-none focus:ring-1 focus:ring-gov-blue"
          >
            <option value="">Status: All</option>
            <option value="Placed">Placed</option>
            <option value="Unplaced">Unplaced</option>
          </select>

          <button
            onClick={() => setIsBulkOpen(true)}
            className="gov-btn-secondary border border-gov-border hover:bg-slate-50 dark:hover:bg-slate-800 py-2 px-3 rounded font-bold uppercase tracking-wider flex items-center gap-1.5"
          >
            <Upload size={14} className="text-gov-blue" /> Bulk Upload JSON
          </button>

          <button
            onClick={handleOpenAdd}
            className="gov-btn-primary py-2 px-4 rounded font-bold uppercase tracking-wider bg-gov-navy border-0 text-white flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-gov-blue"
          >
            <PlusCircle size={14} /> Add Candidate
          </button>
        </div>
      </div>

      <div className="gov-card space-y-4">
        {/* Search */}
        <div className="flex items-center gap-2 border border-gov-border rounded p-2 max-w-sm bg-white dark:bg-slate-950">
          <Search size={16} className="text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search students database by name, skills, or batch..."
            className="w-full text-xs bg-transparent focus:outline-none text-slate-800 dark:text-slate-100"
          />
        </div>

        {loading ? <TableSkeleton /> : (
          <ProfessionalTable
            columns={columns}
            data={students}
            searchPlaceholder="Search database..."
            exportFileName="students_database_export"
            serverPagination={{
              total: totalRecords,
              page: page,
              pageSize: pageSize,
              onPageChange: (newPage) => setPage(newPage),
              onPageSizeChange: (newSize) => setPageSize(newSize),
              pageSizeOptions: [20, 25, 50, 100, 200]
            }}
            hideSearch={true}
          />
        )}
      </div>

      {/* VIEW DETAILS DIALOG */}
      {isViewOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-6 rounded-lg max-w-xl w-full text-xs space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-center border-b border-gov-border dark:border-slate-850 pb-3">
              <h4 className="text-sm font-bold text-gov-navy dark:text-slate-200 uppercase tracking-wide">Student Profile Card Details</h4>
              <button type="button" onClick={() => setIsViewOpen(false)} className="text-slate-400 hover:text-slate-655 focus:outline-none">
                <X size={16} />
              </button>
            </div>

            {viewLoading ? (
              <div className="flex flex-col items-center justify-center py-12 gap-3">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gov-navy dark:border-sky-400"></div>
                <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Fetching Candidate Assessment Profile...</span>
              </div>
            ) : viewError ? (
              <div className="text-center py-8 space-y-4">
                <p className="text-red-600 dark:text-red-400 font-semibold">{viewError}</p>
                <div className="flex justify-center gap-3">
                  <button type="button" onClick={handleRetryView} className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy border-0">Retry Loading</button>
                  <button type="button" onClick={() => setIsViewOpen(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-slate-50 border border-gov-border">Close</button>
                </div>
              </div>
            ) : viewData360 ? (
              <>
                {/* Tab Navigation header */}
                <div className="flex border-b border-gov-border dark:border-slate-805 pb-1 mt-2 text-[10px] font-bold uppercase tracking-wider gap-3">
                  <button 
                    type="button"
                    onClick={() => setActiveViewTab('profile')}
                    className={`pb-1.5 focus:outline-none transition-colors border-b-2 ${
                      activeViewTab === 'profile' 
                        ? 'border-gov-blue text-gov-blue dark:text-sky-400 font-extrabold border-gov-blue' 
                        : 'border-transparent text-slate-400 hover:text-slate-600'
                    }`}
                  >
                    Profile & Academics
                  </button>
                  <button 
                    type="button"
                    onClick={() => setActiveViewTab('projects')}
                    className={`pb-1.5 focus:outline-none transition-colors border-b-2 ${
                      activeViewTab === 'projects' 
                        ? 'border-gov-blue text-gov-blue dark:text-sky-400 font-extrabold border-gov-blue' 
                        : 'border-transparent text-slate-400 hover:text-slate-600'
                }`}
                  >
                    Skills & Projects
                  </button>
                  <button 
                    type="button"
                    onClick={() => setActiveViewTab('other')}
                    className={`pb-1.5 focus:outline-none transition-colors border-b-2 ${
                      activeViewTab === 'other' 
                        ? 'border-gov-blue text-gov-blue dark:text-sky-400 font-extrabold border-gov-blue' 
                        : 'border-transparent text-slate-400 hover:text-slate-600'
                    }`}
                  >
                    Certifications & Placement
                  </button>
                </div>
                
                {activeViewTab === 'profile' && (
                  <div className="space-y-4">
                    <div>
                      <h5 className="font-bold text-slate-500 uppercase tracking-wide text-[9px] mb-2">Personal Information</h5>
                      <div className="grid grid-cols-2 gap-3 bg-slate-50 dark:bg-slate-950 p-3 border border-gov-border dark:border-slate-850 rounded">
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Full Name</span>
                          <span className="text-slate-850 dark:text-slate-200 font-bold">{viewData360.profile.name || 'Not provided'}</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Student ID / Roll No</span>
                          <span className="text-slate-850 dark:text-slate-200 font-mono font-bold">#{viewData360.profile.id}</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Email Address</span>
                          <span className="text-slate-700 dark:text-slate-350">{viewData360.profile.email || 'Not provided'}</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Phone Number</span>
                          <span className="text-slate-700 dark:text-slate-350">{viewData360.profile.phone || 'Not provided'}</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Gender</span>
                          <span className="text-slate-700 dark:text-slate-300">{viewData360.profile.gender || 'Not provided'}</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Section</span>
                          <span className="text-slate-700 dark:text-slate-300">Section {viewData360.profile.section || 'A'}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h5 className="font-bold text-slate-500 uppercase tracking-wide text-[9px] mb-2">Academics Status</h5>
                      <div className="grid grid-cols-2 gap-3 bg-slate-50 dark:bg-slate-955 p-3 border border-gov-border dark:border-slate-850 rounded">
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Academic Branch</span>
                          <span className="text-slate-700 dark:text-slate-300 font-semibold">{viewData360.profile.dept_code || 'Not provided'} ({viewData360.profile.dept_name || 'Not provided'})</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Batch / Graduation Year</span>
                          <span className="text-slate-700 dark:text-slate-300 font-semibold">{viewData360.profile.batch || 'Not provided'}</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">CGPA Metric</span>
                          <span className="text-slate-700 dark:text-slate-300 font-semibold">{viewData360.profile.cgpa !== undefined && viewData360.profile.cgpa !== null ? `${viewData360.profile.cgpa} CGPA` : 'Not provided'}</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Attendance %</span>
                          <span className="text-slate-700 dark:text-slate-300 font-semibold">{viewData360.profile.attendance !== undefined && viewData360.profile.attendance !== null ? `${viewData360.profile.attendance}%` : 'Not provided'}</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Active Backlogs</span>
                          <span className="text-slate-700 dark:text-slate-300 font-semibold">{viewData360.profile.backlogs !== undefined && viewData360.profile.backlogs !== null ? viewData360.profile.backlogs : 'Not provided'}</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Verification Status</span>
                          <span className="text-slate-700 dark:text-slate-300 font-bold uppercase">{viewData360.profile.verification_status || 'Not provided'}</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Placement Status</span>
                          <span className="text-emerald-700 dark:text-emerald-400 font-bold uppercase">{viewData360.profile.status || 'Not provided'}</span>
                        </div>
                        <div>
                          <span className="block font-bold text-slate-400 uppercase text-[9px]">Placement Preparation Score</span>
                          <span className="text-slate-700 dark:text-slate-300 font-semibold">{viewData360.profile.readiness_score !== undefined && viewData360.profile.readiness_score !== null ? `${viewData360.profile.readiness_score}/100` : 'Not provided'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeViewTab === 'projects' && (
                  <div className="space-y-4 animate-fadeIn">
                    <div>
                      <h5 className="font-bold text-slate-500 uppercase tracking-wide text-[9px] mb-2">Registered Technical Skills</h5>
                      <div className="flex flex-wrap gap-1.5 p-3 bg-slate-50 dark:bg-slate-955 border border-gov-border dark:border-slate-850 rounded">
                        {safeArray(viewData360.profile.skills).length > 0 ? (
                          safeArray(viewData360.profile.skills).map((s: string) => (
                            <span key={s} className="bg-gov-blue/5 text-gov-blue dark:bg-sky-950/20 dark:text-sky-400 px-2.5 py-0.5 rounded text-[10px] font-bold border border-gov-blue/10">
                              {s}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-400 italic">No skills registered.</span>
                        )}
                      </div>
                    </div>

                    <div>
                      <h5 className="font-bold text-slate-500 uppercase tracking-wide text-[9px] mb-2">Projects Profile</h5>
                      <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
                        {safeArray(viewData360.profile.projects).length > 0 ? (
                          safeArray(viewData360.profile.projects).map((proj: any, idx: number) => (
                            <div key={idx} className="p-3 border border-gov-border dark:border-slate-850 rounded bg-slate-50 dark:bg-slate-955 space-y-1">
                              <p className="font-bold text-slate-800 dark:text-slate-200">{proj.title || 'Untitled Project'}</p>
                              <p className="text-slate-500 leading-normal text-[10px]">{proj.description || 'No description provided.'}</p>
                              {proj.skills_used && (
                                <p className="text-[9px] text-slate-400">
                                  <span className="font-bold">Technologies/Skills:</span> {safeArray(proj.skills_used).join(', ') || 'Not provided'}
                                </p>
                              )}
                            </div>
                          ))
                        ) : (
                          <div className="text-center py-6 text-slate-400 italic border border-dashed rounded dark:border-slate-800">
                            No projects registered.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {activeViewTab === 'other' && (
                  <div className="space-y-4 animate-fadeIn">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-bold text-slate-500 uppercase tracking-wide text-[9px] mb-2">Certifications</h5>
                        <div className="space-y-2 max-h-36 overflow-y-auto pr-1">
                          {safeArray(viewData360.profile.certifications).length > 0 ? (
                            safeArray(viewData360.profile.certifications).map((cert: any, idx: number) => (
                              <div key={idx} className="p-2 border border-gov-border dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-955 flex justify-between items-center">
                                <div>
                                  <p className="font-bold text-slate-800 dark:text-slate-200">{cert.name || 'Not provided'}</p>
                                  <p className="text-[10px] text-slate-450">Issued by {cert.issuer || 'Not provided'}</p>
                                </div>
                                <span className="text-[10px] text-slate-500 font-mono">{cert.date_obtained || '—'}</span>
                              </div>
                            ))
                          ) : (
                            <div className="text-center py-4 text-slate-400 italic border border-dashed rounded dark:border-slate-800">
                              No certifications registered.
                            </div>
                          )}
                        </div>
                      </div>

                      <div>
                        <h5 className="font-bold text-slate-500 uppercase tracking-wide text-[9px] mb-2">Internships</h5>
                        <div className="space-y-2 max-h-36 overflow-y-auto pr-1">
                          {safeArray(viewData360.profile.internships).length > 0 ? (
                            safeArray(viewData360.profile.internships).map((intern: any, idx: number) => (
                              <div key={idx} className="p-2.5 border border-gov-border dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-950 space-y-1">
                                <div className="flex justify-between">
                                  <span className="font-bold text-slate-800 dark:text-slate-200">{intern.role || 'Not provided'}</span>
                                  <span className="text-[10px] text-slate-500">{intern.duration || 'Not provided'}</span>
                                </div>
                                <p className="text-[10px] text-slate-450 font-semibold">{intern.company || 'Not provided'}</p>
                                {intern.description && <p className="text-[10px] text-slate-500 leading-normal">{intern.description}</p>}
                              </div>
                            ))
                          ) : (
                            <div className="text-center py-4 text-slate-400 italic border border-dashed rounded dark:border-slate-800">
                              No internships registered.
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div>
                      <h5 className="font-bold text-slate-500 uppercase tracking-wide text-[9px] mb-2">Placement Applications</h5>
                      <div className="space-y-2 max-h-36 overflow-y-auto pr-1 font-sans">
                        {safeArray(viewData360.applications).length > 0 ? (
                          safeArray(viewData360.applications).map((app: any, idx: number) => (
                            <div key={idx} className="p-2 border border-gov-border dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
                              <div>
                                <p className="font-bold text-slate-800 dark:text-slate-200">{app.company_name} — <span className="font-semibold text-gov-blue dark:text-sky-400">{app.role}</span></p>
                                <p className="text-[9px] text-slate-400">Package: {app.package_lpa} LPA • Round: {app.current_round}</p>
                              </div>
                              <div className="text-right">
                                <span className={`px-2 py-0.5 rounded font-bold uppercase text-[8px] ${
                                  app.status === 'Placed' || app.status === 'Offered' ? 'bg-emerald-50 text-emerald-800' :
                                  app.status === 'Rejected' ? 'bg-red-50 text-red-800' : 'bg-amber-50 text-amber-800'
                                }`}>
                                  {app.status}
                                </span>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="text-center py-4 text-slate-400 italic border border-dashed rounded dark:border-slate-800">
                            No active placement applications.
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 border-t border-gov-border dark:border-slate-850 pt-3 text-[10px]">
                      <div>
                        <span className="block font-bold text-slate-400 uppercase text-[9px]">Profile Completion</span>
                        <span className={`font-bold uppercase ${viewData360.profile.profile_completed ? 'text-emerald-600 dark:text-emerald-450' : 'text-amber-600 dark:text-amber-450'}`}>
                          {viewData360.profile.profile_completed ? 'Completed' : 'Incomplete'}
                        </span>
                      </div>
                      <div>
                        <span className="block font-bold text-slate-400 uppercase text-[9px]">Resume Document Reference</span>
                        <span className="text-slate-500 dark:text-slate-400 truncate block font-mono">{viewData360.profile.resume_path || 'Not uploaded'}</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-end pt-2 border-t border-gov-border dark:border-slate-850">
                  <button type="button" onClick={() => setIsViewOpen(false)} className="gov-btn-secondary py-1.5 px-5 font-semibold text-slate-700 bg-slate-50 border border-gov-border hover:bg-slate-100 transition-colors">Close Dialog</button>
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}

      {/* ADD DIALOG MODAL */}
      {isAddOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-6 rounded-lg max-w-lg w-full text-xs space-y-4">
            <div className="flex justify-between items-center border-b border-gov-border dark:border-slate-850 pb-3">
              <h4 className="text-sm font-bold text-gov-navy dark:text-slate-200 uppercase">Register New Student</h4>
              <button onClick={() => setIsAddOpen(false)} className="text-slate-400 hover:text-slate-650">
                <X size={16} />
              </button>
            </div>
            
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="std-name" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Full Name *</label>
                  <input
                    id="std-name"
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none focus:ring-1 focus:ring-gov-blue"
                    placeholder="Amit Patel"
                  />
                </div>
                <div>
                  <label htmlFor="std-email" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Email Address *</label>
                  <input
                    id="std-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none focus:ring-1 focus:ring-gov-blue"
                    placeholder="amit@student.edu"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label htmlFor="std-dept" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Branch *</label>
                  <select
                    id="std-dept"
                    value={deptId}
                    onChange={(e) => setDeptId(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 focus:outline-none"
                  >
                    <option value="1">CSE</option>
                    <option value="2">IT</option>
                    <option value="3">ECE</option>
                    <option value="4">EEE</option>
                    <option value="5">MECH</option>
                    <option value="6">CIVIL</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="std-gender" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Gender</label>
                  <select
                    id="std-gender"
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 focus:outline-none"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="std-phone" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Phone No *</label>
                  <input
                    id="std-phone"
                    type="text"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label htmlFor="std-cgpa" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Cumulative CGPA *</label>
                  <input
                    id="std-cgpa"
                    type="number"
                    step="0.01"
                    min="0"
                    max="10"
                    required
                    value={cgpa}
                    onChange={(e) => setCgpa(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="std-attendance" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Attendance % *</label>
                  <input
                    id="std-attendance"
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    required
                    value={attendance}
                    onChange={(e) => setAttendance(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="std-backlogs" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Backlogs *</label>
                  <input
                    id="std-backlogs"
                    type="number"
                    min="0"
                    required
                    value={backlogs}
                    onChange={(e) => setBacklogs(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="std-skills" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Technical Skills (Comma-Separated)</label>
                <input
                  id="std-skills"
                  type="text"
                  value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  placeholder="React, Java, SQL, Python"
                />
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setIsAddOpen(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border">Cancel</button>
                <button type="submit" className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy border-0">Add Student</button>
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
              <h4 className="text-sm font-bold text-gov-navy dark:text-slate-200 uppercase">Modify Student Credentials</h4>
              <button onClick={() => setIsEditOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={16} />
              </button>
            </div>
            
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="edit-std-phone" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Phone No</label>
                  <input
                    id="edit-std-phone"
                    type="text"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-std-cgpa" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">CGPA Score</label>
                  <input
                    id="edit-std-cgpa"
                    type="number"
                    step="0.01"
                    required
                    value={cgpa}
                    onChange={(e) => setCgpa(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="edit-std-attendance" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Attendance %</label>
                  <input
                    id="edit-std-attendance"
                    type="number"
                    step="0.1"
                    required
                    value={attendance}
                    onChange={(e) => setAttendance(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-std-backlogs" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Backlogs count</label>
                  <input
                    id="edit-std-backlogs"
                    type="number"
                    required
                    value={backlogs}
                    onChange={(e) => setBacklogs(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="edit-std-skills" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Technical Skills (Comma-Separated)</label>
                <input
                  id="edit-std-skills"
                  type="text"
                  value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 focus:outline-none"
                />
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setIsEditOpen(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border">Cancel</button>
                <button type="submit" className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy border-0">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELETE DIALOG MODAL */}
      {isDeleteOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-805 p-6 rounded-lg max-w-sm w-full text-xs space-y-4">
            <div className="flex items-start gap-3">
              <div className="bg-red-50 p-2 rounded-full text-red-650 shrink-0">
                <AlertTriangle size={20} />
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-slate-850 dark:text-slate-200 uppercase">Purge Student Record</h4>
                <p className="text-slate-500 leading-normal">
                  Are you absolutely sure you want to delete <span className="font-semibold text-slate-700 dark:text-slate-300">{selectedStudent?.name}</span>? This will permanently erase their credentials and resume entries from database blocks.
                </p>
              </div>
            </div>

            <div className="flex gap-3 justify-end pt-2">
              <button onClick={() => setIsDeleteOpen(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border">Cancel</button>
              <button onClick={handleDeleteSubmit} className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-red-650 border-0 hover:bg-red-700">Delete student</button>
            </div>
          </div>
        </div>
      )}

      {/* BULK UPLOAD MODAL */}
      {isBulkOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-6 rounded-lg max-w-2xl w-full text-xs space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-gov-border dark:border-slate-850 pb-3">
              <h4 className="text-sm font-bold text-gov-navy dark:text-slate-200 uppercase">
                {previewData ? 'Bulk Import Validation Preview' : 'Bulk Student Import Sheets'}
              </h4>
              <button onClick={() => { setIsBulkOpen(false); setPreviewData(null); }} className="text-slate-400 hover:text-slate-655">
                <X size={16} />
              </button>
            </div>
            
            {!previewData ? (
              <form onSubmit={handleBulkSubmit} className="space-y-4">
                <div>
                  <label htmlFor="bulk-json-area" className="block font-bold text-slate-500 uppercase mb-1">Student JSON Array Data</label>
                  <textarea
                    id="bulk-json-area"
                    required
                    value={bulkInput}
                    onChange={(e) => setBulkInput(e.target.value)}
                    className="w-full h-44 p-3 border border-gov-border rounded dark:bg-slate-950 font-mono text-[10px] focus:outline-none focus:ring-1 focus:ring-gov-blue"
                    placeholder={`[
  {
    "name": "Amit Sharma",
    "email": "amit.sharma@student.edu",
    "dept_id": 1,
    "cgpa": 8.2,
    "attendance": 89.0,
    "backlogs": 0,
    "gender": "Male",
    "batch": "2026",
    "skills": ["Java", "SQL"]
  }
]`}
                  />
                </div>

                <div className="flex gap-3 justify-end pt-2">
                  <button type="button" onClick={() => setIsBulkOpen(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border">Cancel</button>
                  <button
                    type="submit"
                    disabled={bulkLoading || !bulkInput}
                    className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy border-0 flex items-center gap-1.5"
                  >
                    {bulkLoading ? 'Validating...' : 'Validate Payload'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                {/* Stats cards */}
                <div className="grid grid-cols-4 gap-4 text-center">
                  <div className="bg-slate-50 dark:bg-slate-955 border border-slate-200 dark:border-slate-800 p-2.5 rounded">
                    <span className="block font-bold text-slate-400 uppercase text-[8px]">Total Rows</span>
                    <span className="text-sm font-bold text-slate-850 dark:text-slate-100">{previewData.total}</span>
                  </div>
                  <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-250 p-2.5 rounded text-emerald-800 dark:text-emerald-400">
                    <span className="block font-bold uppercase text-[8px]">Valid (Ready)</span>
                    <span className="text-sm font-bold">{previewData.valid}</span>
                  </div>
                  <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-250 p-2.5 rounded text-amber-800 dark:text-amber-400">
                    <span className="block font-bold uppercase text-[8px]">Duplicates</span>
                    <span className="text-sm font-bold">{previewData.duplicates}</span>
                  </div>
                  <div className="bg-red-50 dark:bg-red-950/20 border border-red-250 p-2.5 rounded text-red-800 dark:text-red-400">
                    <span className="block font-bold uppercase text-[8px]">Invalid Rows</span>
                    <span className="text-sm font-bold">{previewData.invalid}</span>
                  </div>
                </div>

                {/* Validation detailed logs */}
                <div className="space-y-2">
                  <span className="block font-bold text-slate-500 uppercase tracking-wide">Validation Audit Logs</span>
                  <div className="border border-gov-border dark:border-slate-800 rounded overflow-hidden max-h-56 overflow-y-auto">
                    <table className="w-full text-[10px]">
                      <thead className="bg-slate-100 dark:bg-slate-950 font-bold border-b border-gov-border dark:border-slate-800">
                        <tr>
                          <th className="p-2 text-left">Row</th>
                          <th className="p-2 text-left">Student Name</th>
                          <th className="p-2 text-left">Email</th>
                          <th className="p-2 text-left">Status</th>
                          <th className="p-2 text-left font-medium">Rejection Reason</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-150 dark:divide-slate-850">
                        {previewData.items.map((item: any, index: number) => (
                          <tr key={index} className={item.status === 'Invalid' ? 'bg-red-50/20' : item.status === 'Duplicate' ? 'bg-amber-50/20' : ''}>
                            <td className="p-2 font-mono">#{item.row}</td>
                            <td className="p-2 font-semibold">{item.name || '—'}</td>
                            <td className="p-2">{item.email}</td>
                            <td className="p-2">
                              <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase ${
                                item.status === 'Valid' ? 'bg-emerald-50 text-emerald-800' :
                                item.status === 'Duplicate' ? 'bg-amber-50 text-amber-800' :
                                'bg-red-50 text-red-800'
                              }`}>
                                {item.status}
                              </span>
                            </td>
                            <td className={`p-2 font-medium ${item.status !== 'Valid' ? 'text-red-655 dark:text-red-400' : 'text-slate-400'}`}>
                              {item.reason || 'Record is clean and ready.'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="flex gap-3 justify-end pt-2 border-t border-gov-border dark:border-slate-850">
                  <button
                    type="button"
                    onClick={() => setPreviewData(null)}
                    className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border"
                  >
                    Go Back & Edit
                  </button>
                  <button
                    onClick={handleConfirmImport}
                    disabled={previewData.valid === 0 || bulkLoading}
                    className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-emerald-650 border-0 hover:bg-emerald-700 flex items-center gap-1.5"
                  >
                    {bulkLoading ? 'Processing...' : `Confirm Import [${previewData.valid} Records]`}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default AdminStudents;
