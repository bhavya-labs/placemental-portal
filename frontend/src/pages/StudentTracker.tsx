import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { studentService, analyticsService } from '../services/api';
import { ProfessionalTable } from '../components/ProfessionalTable';
import { CardSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import { 
  GraduationCap, PlusCircle, Trash2, Edit, Eye, Filter, 
  Upload, User, FileSpreadsheet, Download, RefreshCw, X, Check, ShieldAlert
} from 'lucide-react';
import { AccessibleModal, AccessibleTabs } from '../components/AccessibilityComponents';
import { DepartmentPlacementDetailsView } from '../components/DepartmentPlacementDetailsView';

export const StudentTracker: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlTab = searchParams.get('tab');
  const urlStatus = searchParams.get('status');
  const urlBatch = searchParams.get('batch');
  const urlDept = searchParams.get('dept_id');

  const [trackerTab, setTrackerTab] = useState<'department-placements' | 'directory'>(
    urlTab === 'directory' ? 'directory' : 'department-placements'
  );
  const [loading, setLoading] = useState(true);
  const [students, setStudents] = useState<any[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  // Filters state
  const [filterBatch, setFilterBatch] = useState<string>(urlBatch || '2026');
  const [filterDept, setFilterDept] = useState<number | undefined>(urlDept ? Number(urlDept) : undefined);
  const [filterGender, setFilterGender] = useState<string | undefined>(undefined);
  const [filterStatus, setFilterStatus] = useState<string | undefined>(urlStatus || undefined);
  const [searchQuery, setSearchQuery] = useState('');

  // Sync state if URL search parameters change externally
  useEffect(() => {
    const pStatus = searchParams.get('status');
    if (pStatus !== null && pStatus !== filterStatus) {
      setFilterStatus(pStatus || undefined);
    }
    const pBatch = searchParams.get('batch');
    if (pBatch && pBatch !== filterBatch) {
      setFilterBatch(pBatch);
    }
    const pDept = searchParams.get('dept_id');
    if (pDept && Number(pDept) !== filterDept) {
      setFilterDept(Number(pDept));
    }
    const pTab = searchParams.get('tab');
    if (pTab === 'directory' || pTab === 'department-placements') {
      if (pTab !== trackerTab) setTrackerTab(pTab);
    }
  }, [searchParams]);

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showBulkModal, setShowBulkModal] = useState(false);

  // Focus targets on modal closings
  const addBtnRef = React.useRef<HTMLButtonElement | null>(null);

  // Selected entities for edit/view
  const [selectedStudent, setSelectedStudent] = useState<any>(null);

  // Add Form state
  const [addForm, setAddForm] = useState({
    name: '',
    email: '',
    dept_id: 1,
    gender: 'Male',
    batch: '2026',
    phone: '9876543210',
    cgpa: 8.0,
    attendance: 85.0,
    backlogs: 0,
    skills: 'React, SQL, Python'
  });

  // Edit Form state
  const [editForm, setEditForm] = useState<any>({
    phone: '',
    cgpa: 0,
    attendance: 0,
    backlogs: 0,
    skills: ''
  });

  // Bulk payload text
  const [bulkInput, setBulkInput] = useState('');
  const [bulkUploading, setBulkUploading] = useState(false);
  const [bulkMsg, setBulkMsg] = useState({ text: '', isError: false });

  const loadStudents = async () => {
    setLoading(true);
    try {
      const params = {
        search: searchQuery || undefined,
        dept_id: filterDept,
        batch: filterBatch,
        gender: filterGender,
        status_filter: filterStatus,
        page: page,
        limit: pageSize
      };
      const res = await studentService.getStudents(params);
      const studentItems = Array.isArray(res?.items) ? res.items : (Array.isArray(res) ? res : []);
      setStudents(studentItems);
      setTotalCount(res?.total ?? studentItems.length);
    } catch (err) {
      console.error('Failed to load students directory', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setPage(1);
  }, [filterBatch, filterDept, filterGender, filterStatus, searchQuery]);

  useEffect(() => {
    loadStudents();
  }, [filterBatch, filterDept, filterGender, filterStatus, searchQuery, page, pageSize]);

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await studentService.createStudent({
        ...addForm,
        skills: JSON.stringify(addForm.skills.split(',').map(s => s.trim()).filter(Boolean))
      });
      alert('Student profile registered and placement preparation scores evaluated successfully!');
      setShowAddModal(false);
      loadStudents();
      // Reset form
      setAddForm({
        name: '',
        email: '',
        dept_id: 1,
        gender: 'Male',
        batch: '2026',
        phone: '9876543210',
        cgpa: 8.0,
        attendance: 85.0,
        backlogs: 0,
        skills: 'React, SQL, Python'
      });
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create student profile');
    }
  };

  const handleEditClick = (student: any) => {
    setSelectedStudent(student);
    setEditForm({
      phone: student.phone || '',
      cgpa: student.cgpa || 0,
      attendance: student.attendance || 0,
      backlogs: student.backlogs || 0,
      skills: Array.isArray(student.skills) ? student.skills.join(', ') : (student.skills || '')
    });
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudent) return;
    try {
      await studentService.updateStudent(selectedStudent.id, {
        ...editForm,
        skills: editForm.skills.split(',').map((s: string) => s.trim()).filter(Boolean)
      });
      alert('Student profile updated successfully!');
      setShowEditModal(false);
      loadStudents();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to edit student profile');
    }
  };

  const handleDeleteClick = async (studentId: number) => {
    if (!window.confirm('Are you absolutely sure you want to delete this student account? This will permanently delete their profile details and logs.')) {
      return;
    }
    try {
      await studentService.deleteStudent(studentId);
      alert('Student account successfully scrubbed.');
      loadStudents();
    } catch (err) {
      alert('Failed to delete student.');
    }
  };

  const handleViewProfileClick = async (studentId: number) => {
    try {
      const details = await studentService.getStudentById(studentId);
      setSelectedStudent(details);
      setShowProfileModal(true);
    } catch (err) {
      alert('Failed to load profile details.');
    }
  };

  const handleBulkSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBulkUploading(true);
    setBulkMsg({ text: '', isError: false });
    try {
      const payload = JSON.parse(bulkInput);
      if (!Array.isArray(payload)) {
        throw new Error('Payload must be a JSON array of students.');
      }
      const res = await studentService.bulkUpload(payload);
      setBulkMsg({ text: res.message, isError: false });
      setBulkInput('');
      loadStudents();
    } catch (err: any) {
      setBulkMsg({ 
        text: err.message || err.response?.data?.detail || 'Failed to compile JSON bulk sheets.', 
        isError: true 
      });
    } finally {
      setBulkUploading(false);
    }
  };

  // Filter local gender records if set
  const filteredStudents = React.useMemo(() => {
    if (!filterGender) return students;
    return students.filter(s => s.gender === filterGender);
  }, [students, filterGender]);

  // Columns for dynamic data tables
  const columns = [
    { header: 'Roll No', accessor: 'id', render: (row: any) => <span>#{row.id * 11}</span> },
    { header: 'Student Name', accessor: 'name' },
    { header: 'Branch', accessor: 'dept_code' },
    { header: 'CGPA', accessor: 'cgpa' },
    { header: 'Preparation Score', accessor: 'readiness_score', render: (row: any) => <span className="font-semibold">{row.readiness_score}/100</span> },
    { 
      header: 'Placement Outlook %', 
      accessor: 'placement_probability', 
      render: (row: any) => (
        <span className={`font-semibold ${(row.placement_probability * 100) >= 70 ? 'text-emerald-600' : (row.placement_probability * 100) < 40 ? 'text-red-500' : 'text-amber-500'}`}>
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
    },
    {
      header: 'Manage Actions',
      accessor: 'actions',
      sortable: false,
      render: (row: any) => (
        <div className="flex items-center gap-1.5 no-print">
          <Link
            to={`/student-360/${row.id}`}
            aria-label={`View full 360 profile for ${row.name}`}
            className="px-2 py-1 bg-sky-50 dark:bg-sky-950/40 text-gov-blue dark:text-sky-300 hover:bg-sky-100 dark:hover:bg-sky-900/60 rounded text-[10px] font-bold uppercase flex items-center gap-1 border border-sky-200 dark:border-sky-800"
            title="View Full Profile (360°)"
          >
            <User size={12} />
            <span>360° View</span>
          </Link>
          <button 
            onClick={() => handleViewProfileClick(row.id)}
            aria-label={`View profile details for ${row.name}`}
            className="p-1 text-slate-500 hover:text-gov-blue focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue rounded"
            title="Quick Summary"
          >
            <Eye size={14} />
          </button>
          <button 
            onClick={() => handleEditClick(row)}
            aria-label={`Modify records for ${row.name}`}
            className="p-1 text-slate-500 hover:text-amber-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue rounded"
            title="Edit Records"
          >
            <Edit size={14} />
          </button>
          <button 
            onClick={() => handleDeleteClick(row.id)}
            aria-label={`Scrub student account for ${row.name}`}
            className="p-1 text-slate-500 hover:text-red-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue rounded"
            title="Delete Account"
          >
            <Trash2 size={14} />
          </button>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card">
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
            <GraduationCap className="text-gov-blue shrink-0" size={24} />
            Student Tracker & Academic Directory
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium">
            Centralized registry of campus placements, academic profiles, and skill auditing reports.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            ref={addBtnRef}
            onClick={() => setShowAddModal(true)}
            className="gov-btn-primary py-2 px-4 rounded text-xs font-bold uppercase tracking-wider flex items-center gap-2"
          >
            <PlusCircle size={14} /> Add Student
          </button>
          
          <button
            onClick={() => setShowBulkModal(true)}
            className="gov-btn-secondary border border-gov-border py-2 px-4 rounded text-xs font-bold uppercase tracking-wider flex items-center gap-2 hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            <Upload size={14} /> Bulk JSON Loader
          </button>
        </div>
      </div>

      {/* View Switcher Tabs */}
      <AccessibleTabs
        tabs={[
          { id: 'department-placements', label: 'Department Placement Details', icon: <GraduationCap size={16} /> },
          { id: 'directory', label: 'All Student Directory & Records', icon: <User size={16} /> }
        ]}
        activeTab={trackerTab}
        onChange={(tab: any) => setTrackerTab(tab)}
        ariaLabel="Student Section Views"
      />

      {trackerTab === 'department-placements' && (
        <DepartmentPlacementDetailsView />
      )}

      {trackerTab === 'directory' && (
        <>
          {/* Filter widgets dock */}
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-4 rounded-lg shadow-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4 no-print">
            <div className="flex items-center gap-2">
              <Filter size={16} className="text-gov-blue" />
              <h3 className="text-xs font-bold text-slate-700 dark:text-slate-200 uppercase tracking-wider">
                Directory Query Filters
              </h3>
            </div>

            <div className="flex flex-wrap gap-4 text-xs">
              <div>
                <label htmlFor="filter-batch-select" className="block font-bold text-slate-500 uppercase mb-1">Batch Year</label>
                <select
                  id="filter-batch-select"
                  value={filterBatch}
                  onChange={(e) => setFilterBatch(e.target.value)}
                  className="border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-955 dark:border-slate-850 dark:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                >
                  <option value="2026">2026 (Active)</option>
                  <option value="2025">2025 (Graduated)</option>
                </select>
              </div>

              <div>
                <label htmlFor="filter-dept-select" className="block font-bold text-slate-500 uppercase mb-1">Branch / Department</label>
                <select
                  id="filter-dept-select"
                  value={filterDept || ''}
                  onChange={(e) => setFilterDept(e.target.value ? Number(e.target.value) : undefined)}
                  className="border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-955 dark:border-slate-850 dark:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
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

              <div>
                <label htmlFor="filter-gender-select" className="block font-bold text-slate-500 uppercase mb-1">Gender</label>
                <select
                  id="filter-gender-select"
                  value={filterGender || ''}
                  onChange={(e) => setFilterGender(e.target.value ? e.target.value : undefined)}
                  className="border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-955 dark:border-slate-850 dark:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                >
                  <option value="">All Genders</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>

              <div>
                <label htmlFor="filter-status-select" className="block font-bold text-slate-500 uppercase mb-1">Placement Status</label>
                <select
                  id="filter-status-select"
                  value={filterStatus || ''}
                  onChange={(e) => setFilterStatus(e.target.value ? e.target.value : undefined)}
                  className="border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-955 dark:border-slate-850 dark:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                >
                  <option value="">All Statuses</option>
                  <option value="Placed">Placed</option>
                  <option value="Unplaced">Unplaced</option>
                  <option value="At Risk">At Risk</option>
                </select>
              </div>
            </div>
          </div>

          {/* Active Filter Banner for Directory Tab */}
          {filterStatus && (
            <div className={`p-3 rounded-lg border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs ${
              filterStatus.toLowerCase() === 'at risk'
                ? 'bg-red-50/80 border-red-200 text-red-900 dark:bg-red-950/40 dark:border-red-900/60 dark:text-red-200'
                : filterStatus.toLowerCase() === 'placed'
                ? 'bg-emerald-50/80 border-emerald-200 text-emerald-900 dark:bg-emerald-950/40 dark:border-emerald-900/60 dark:text-emerald-200'
                : 'bg-amber-50/80 border-amber-200 text-amber-900 dark:bg-amber-950/40 dark:border-amber-900/60 dark:text-amber-200'
            }`}>
              <div className="flex items-center gap-2.5">
                <ShieldAlert className={filterStatus.toLowerCase() === 'at risk' ? 'text-red-600 dark:text-red-400' : 'text-gov-blue'} size={18} />
                <div>
                  <span className="font-bold uppercase tracking-wider">Active Filter Applied:</span>{' '}
                  <span>
                    Showing {filterStatus.toLowerCase() === 'at risk' ? 'Students At Risk (Low score)' : `${filterStatus} students`}
                    {' — '}
                    <strong>{totalCount}</strong> {totalCount === 1 ? 'student' : 'students'} found
                  </span>
                </div>
              </div>
              <button
                onClick={() => {
                  setFilterStatus(undefined);
                  const nextParams = new URLSearchParams(searchParams);
                  nextParams.delete('status');
                  setSearchParams(nextParams, { replace: true });
                }}
                className="px-3 py-1 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 rounded font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-1.5 shadow-sm transition text-xs shrink-0"
              >
                <X size={14} /> Clear Filter ({filterStatus})
              </button>
            </div>
          )}

          {/* Main Student list Table view */}
          <div className="gov-card p-4 space-y-4">
            {loading ? <TableSkeleton /> : (
              <ProfessionalTable
                columns={columns}
                data={students}
                searchPlaceholder="Search students by name, email, department..."
                exportFileName={`student_placement_registry_${filterBatch}`}
                searchValue={searchQuery}
                onSearchChange={(val) => setSearchQuery(val)}
                serverPagination={{
                  total: totalCount,
                  page: page,
                  pageSize: pageSize,
                  onPageChange: (newPage) => setPage(newPage),
                  onPageSizeChange: (newSize) => setPageSize(newSize),
                  pageSizeOptions: [20, 25, 50, 100, 200]
                }}
              />
            )}
          </div>
        </>
      )}

      {/* MODAL 1: ADD SINGLE STUDENT */}
      {showAddModal && (
        <AccessibleModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title="Add New Student Profile"
          triggerRef={addBtnRef}
        >
          <form onSubmit={handleAddSubmit} className="space-y-4 text-xs text-slate-750">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="add-name" className="block font-bold text-slate-500 uppercase">Student Full Name *</label>
                <input
                  id="add-name"
                  type="text"
                  required
                  value={addForm.name}
                  onChange={(e) => setAddForm({ ...addForm, name: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label htmlFor="add-email" className="block font-bold text-slate-500 uppercase">Official Email Address *</label>
                <input
                  id="add-email"
                  type="email"
                  required
                  value={addForm.email}
                  onChange={(e) => setAddForm({ ...addForm, email: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                  placeholder="john.doe@platform.edu"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label htmlFor="add-dept" className="block font-bold text-slate-500 uppercase">Branch</label>
                <select
                  id="add-dept"
                  value={addForm.dept_id}
                  onChange={(e) => setAddForm({ ...addForm, dept_id: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
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
                <label htmlFor="add-gender" className="block font-bold text-slate-500 uppercase">Gender</label>
                <select
                  id="add-gender"
                  value={addForm.gender}
                  onChange={(e) => setAddForm({ ...addForm, gender: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>
              <div>
                <label htmlFor="add-batch" className="block font-bold text-slate-500 uppercase">Batch</label>
                <select
                  id="add-batch"
                  value={addForm.batch}
                  onChange={(e) => setAddForm({ ...addForm, batch: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                >
                  <option value="2026">2026</option>
                  <option value="2025">2025</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4">
              <div className="col-span-2">
                <label htmlFor="add-phone" className="block font-bold text-slate-500 uppercase">Phone Number</label>
                <input
                  id="add-phone"
                  type="text"
                  value={addForm.phone}
                  onChange={(e) => setAddForm({ ...addForm, phone: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                />
              </div>
              <div>
                <label htmlFor="add-cgpa" className="block font-bold text-slate-500 uppercase">CGPA *</label>
                <input
                  id="add-cgpa"
                  type="number"
                  step="0.01"
                  min="0"
                  max="10"
                  required
                  value={addForm.cgpa}
                  onChange={(e) => setAddForm({ ...addForm, cgpa: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                />
              </div>
              <div>
                <label htmlFor="add-backlogs" className="block font-bold text-slate-500 uppercase">Backlogs</label>
                <input
                  id="add-backlogs"
                  type="number"
                  min="0"
                  required
                  value={addForm.backlogs}
                  onChange={(e) => setAddForm({ ...addForm, backlogs: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                />
              </div>
            </div>

            <div>
              <label htmlFor="add-skills" className="block font-bold text-slate-500 uppercase">Technical Skills (Comma separated)</label>
              <input
                id="add-skills"
                type="text"
                value={addForm.skills}
                onChange={(e) => setAddForm({ ...addForm, skills: e.target.value })}
                className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                placeholder="React, Java, SQL"
              />
            </div>

            <div className="flex gap-3 justify-end pt-3">
              <button 
                type="button" 
                onClick={() => setShowAddModal(false)}
                className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700"
              >
                Cancel
              </button>
              <button 
                type="submit" 
                className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy hover:bg-gov-accent border-0"
              >
                Save Profile
              </button>
            </div>
          </form>
        </AccessibleModal>
      )}

      {/* MODAL 2: EDIT STUDENT */}
      {showEditModal && selectedStudent && (
        <AccessibleModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          title={`Modify Profile - ${selectedStudent.name}`}
        >
          <form onSubmit={handleEditSubmit} className="space-y-4 text-xs text-slate-750">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="edit-cgpa" className="block font-bold text-slate-500 uppercase">CGPA (0.00 - 10.00)</label>
                <input
                  id="edit-cgpa"
                  type="number"
                  step="0.01"
                  min="0"
                  max="10"
                  required
                  value={editForm.cgpa}
                  onChange={(e) => setEditForm({ ...editForm, cgpa: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                />
              </div>
              <div>
                <label htmlFor="edit-attendance" className="block font-bold text-slate-500 uppercase">Attendance (%)</label>
                <input
                  id="edit-attendance"
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  required
                  value={editForm.attendance}
                  onChange={(e) => setEditForm({ ...editForm, attendance: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="edit-backlogs" className="block font-bold text-slate-500 uppercase">Active Backlogs</label>
                <input
                  id="edit-backlogs"
                  type="number"
                  min="0"
                  required
                  value={editForm.backlogs}
                  onChange={(e) => setEditForm({ ...editForm, backlogs: Number(e.target.value) })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                />
              </div>
              <div>
                <label htmlFor="edit-phone" className="block font-bold text-slate-500 uppercase">Phone Number</label>
                <input
                  id="edit-phone"
                  type="text"
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                />
              </div>
            </div>

            <div>
              <label htmlFor="edit-skills" className="block font-bold text-slate-500 uppercase">Skills (Comma-separated)</label>
              <textarea
                id="edit-skills"
                value={editForm.skills}
                onChange={(e) => setEditForm({ ...editForm, skills: e.target.value })}
                className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 h-16 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
              />
            </div>

            <div className="flex gap-3 justify-end pt-3">
              <button 
                type="button" 
                onClick={() => setShowEditModal(false)}
                className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-750 bg-white"
              >
                Cancel
              </button>
              <button 
                type="submit" 
                className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy hover:bg-gov-accent border-0"
              >
                Save Changes
              </button>
            </div>
          </form>
        </AccessibleModal>
      )}

      {/* MODAL 3: VIEW PROFILE PROFILE OVERLAY */}
      {showProfileModal && selectedStudent && (
        <AccessibleModal
          isOpen={showProfileModal}
          onClose={() => setShowProfileModal(false)}
          title={`Student Evaluation Portfolio - ${selectedStudent.name}`}
        >
          <div className="space-y-6 text-xs text-slate-600 dark:text-slate-400">
            <div className="flex items-center gap-4 bg-slate-50 dark:bg-slate-950 p-4 border border-gov-border dark:border-slate-850 rounded">
              <div className="bg-gov-navy text-white rounded-full w-12 h-12 flex items-center justify-center font-bold text-lg">
                {selectedStudent.name.charAt(0)}
              </div>
              <div className="space-y-0.5">
                <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200 uppercase">{selectedStudent.name}</h4>
                <p className="font-mono text-[10px] text-slate-400">{selectedStudent.email} &bull; Roll #{selectedStudent.id * 11}</p>
                <p className="font-bold text-gov-blue uppercase text-[10px]">{selectedStudent.dept_name} &bull; Batch {selectedStudent.batch}</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="bg-slate-50 dark:bg-slate-950 p-2.5 rounded border border-gov-border dark:border-slate-850">
                <span className="block text-[10px] font-bold uppercase text-slate-400">CGPA</span>
                <span className="text-sm font-extrabold text-gov-navy dark:text-slate-100">{selectedStudent.cgpa}</span>
              </div>
              <div className="bg-slate-50 dark:bg-slate-950 p-2.5 rounded border border-gov-border dark:border-slate-850">
                <span className="block text-[10px] font-bold uppercase text-slate-400">Attendance</span>
                <span className="text-sm font-extrabold text-gov-navy dark:text-slate-100">{selectedStudent.attendance}%</span>
              </div>
              <div className="bg-slate-50 dark:bg-slate-950 p-2.5 rounded border border-gov-border dark:border-slate-850">
                <span className="block text-[10px] font-bold uppercase text-slate-400">Backlogs</span>
                <span className="text-sm font-extrabold text-red-650">{selectedStudent.backlogs}</span>
              </div>
            </div>

            <div className="space-y-2">
              <h5 className="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide text-[10px] border-b border-gov-border dark:border-slate-800 pb-1">Overall Suitability Summary</h5>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 dark:bg-slate-955 p-3 rounded">
                  <p className="text-[10px] text-slate-400 uppercase font-bold">Preparation Score</p>
                  <p className="text-xl font-black text-gov-navy dark:text-slate-200 mt-1">{selectedStudent.readiness_score} / 100</p>
                </div>
                <div className="bg-slate-50 dark:bg-slate-955 p-3 rounded">
                  <p className="text-[10px] text-slate-400 uppercase font-bold">Placement Outlook</p>
                  <p className="text-xl font-black text-emerald-600 mt-1">{(selectedStudent.placement_probability * 100).toFixed(0)}%</p>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <h5 className="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide text-[10px] border-b border-gov-border dark:border-slate-800 pb-1">Coding Competency Metrics</h5>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-slate-50 dark:bg-slate-950 p-2 rounded">
                  <span className="text-[9px] block text-slate-400 font-bold">LEETCODE</span>
                  <span className="font-mono font-bold text-slate-700 dark:text-slate-300">{selectedStudent.leetcode_score || 0} solved</span>
                </div>
                <div className="bg-slate-50 dark:bg-slate-950 p-2 rounded">
                  <span className="text-[9px] block text-slate-400 font-bold">CODECHEF</span>
                  <span className="font-mono font-bold text-slate-700 dark:text-slate-300">{selectedStudent.codechef_score || 0} rating</span>
                </div>
                <div className="bg-slate-50 dark:bg-slate-950 p-2 rounded">
                  <span className="text-[9px] block text-slate-400 font-bold">HACKERRANK</span>
                  <span className="font-mono font-bold text-slate-700 dark:text-slate-300">{selectedStudent.hackerrank_score || 0} score</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <h5 className="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide text-[10px] border-b border-gov-border dark:border-slate-800 pb-1">Registered Technical Skills</h5>
              <div className="flex flex-wrap gap-1.5">
                {(() => {
                  let skillsList: string[] = [];
                  if (Array.isArray(selectedStudent.skills)) {
                    skillsList = selectedStudent.skills;
                  } else if (typeof selectedStudent.skills === 'string') {
                    try {
                      const parsed = JSON.parse(selectedStudent.skills);
                      if (Array.isArray(parsed)) skillsList = parsed;
                    } catch {
                      skillsList = selectedStudent.skills.split(',').map((s: string) => s.trim()).filter(Boolean);
                    }
                  }
                  return skillsList.length > 0 ? (
                    skillsList.map((s: string) => (
                      <span key={s} className="bg-slate-100 dark:bg-slate-800 border border-gov-border dark:border-slate-700 rounded px-2 py-0.5 font-bold uppercase text-[9px] text-slate-700 dark:text-slate-350">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-400 italic">No technical skills registered.</span>
                  );
                })()}
              </div>
            </div>
            
            <div className="flex justify-between items-center pt-2">
              <Link
                to={`/student-360/${selectedStudent.id}`}
                className="gov-btn-secondary py-1.5 px-3 uppercase tracking-wide font-semibold text-[10px] flex items-center gap-1.5 text-gov-blue hover:text-gov-navy"
              >
                <User size={12} />
                <span>Open Full 360° Assessment Profile</span>
              </Link>
              <button 
                type="button" 
                onClick={() => setShowProfileModal(false)}
                className="gov-btn-primary py-1.5 px-5 uppercase tracking-wide font-semibold text-[10px]"
              >
                Close Portfolio
              </button>
            </div>
          </div>
        </AccessibleModal>
      )}

      {/* MODAL 4: BULK JSON EXCEL LOADER */}
      {showBulkModal && (
        <AccessibleModal
          isOpen={showBulkModal}
          onClose={() => setShowBulkModal(false)}
          title="Import Student Data Sheet"
        >
          <form onSubmit={handleBulkSubmit} className="space-y-4 text-xs text-slate-750">
            <p className="text-slate-500 leading-relaxed">
              Paste a validated JSON array of student accounts. This corresponds to spreadsheet parser workflows.
            </p>

            {bulkMsg.text && (
              <div role="status" aria-live="polite" className={`p-3 rounded border font-bold uppercase ${
                bulkMsg.isError ? 'bg-red-50 text-red-800 border-red-200' : 'bg-emerald-50 text-emerald-800 border-emerald-200'
              }`}>
                {bulkMsg.text}
              </div>
            )}

            <div>
              <label htmlFor="bulk-payload-input" className="block font-bold text-slate-500 uppercase mb-1">Raw JSON Array Payload *</label>
              <textarea
                id="bulk-payload-input"
                required
                value={bulkInput}
                onChange={(e) => setBulkInput(e.target.value)}
                className="w-full h-48 p-3 font-mono text-xs border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                placeholder='[{"email":"test@platform.edu","name":"Example","department":"CSE","cgpa":8.5,"attendance":92,"backlogs":0}]'
              />
            </div>

            <div className="flex gap-3 justify-end">
              <button 
                type="button" 
                onClick={() => setShowBulkModal(false)}
                className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white"
              >
                Close
              </button>
              <button 
                type="submit" 
                disabled={bulkUploading}
                className="gov-btn-primary py-1.5 px-4 font-semibold disabled:opacity-50 text-white bg-gov-navy border-0"
              >
                {bulkUploading ? 'Uploading...' : 'Confirm Import'}
              </button>
            </div>
          </form>
        </AccessibleModal>
      )}
    </div>
  );
};

export default StudentTracker;
