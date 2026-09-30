import React, { useState, useEffect } from 'react';
import { driveService } from '../services/api';
import { CardSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import { 
  Briefcase, PlusCircle, Search, Filter, Edit, Trash2, X, AlertTriangle, Calendar 
} from 'lucide-react';
import { AccessibleToast } from '../components/AccessibilityComponents';

export const AdminDrives: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [drives, setDrives] = useState<any[]>([]);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  // Dialog configurations
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedDrive, setSelectedDrive] = useState<any | null>(null);

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

  const loadDrives = async () => {
    setLoading(true);
    try {
      const data = await driveService.getDrives();
      setDrives(data);
    } catch (err) {
      console.error('Failed to load drives', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDrives();
  }, []);

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
      await driveService.deleteDrive(selectedDrive.id);
      showToast('Placement drive purged from active lists.', 'success');
      setIsDeleteOpen(false);
      loadDrives();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to delete drive.', 'error');
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

      {loading ? <CardSkeleton /> : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {drives.map((drive) => (
            <div key={drive.id} className="gov-card flex flex-col justify-between space-y-4 hover:border-slate-300">
              <div className="space-y-2">
                <div className="flex justify-between items-start">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">{drive.company_name}</span>
                  <span className={`px-2 py-0.5 rounded font-bold uppercase text-[9px] ${
                    ['REGISTRATION_OPEN', 'PUBLISHED'].includes(drive.status)
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-250' 
                      : 'bg-slate-100 text-slate-500'
                  }`}>
                    {drive.status}
                  </span>
                </div>

                <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase leading-snug">
                  {drive.role}
                </h4>

                <div className="space-y-1.5 text-slate-500 pt-1 text-[11px]">
                  <p>CTC Package: <span className="font-semibold text-slate-700 dark:text-slate-300">{drive.package_lpa} LPA</span></p>
                  <p>Location: <span className="font-semibold text-slate-700 dark:text-slate-300">{drive.location}</span></p>
                  <p>Min CGPA Cutoff: <span className="font-semibold text-slate-700 dark:text-slate-300">{drive.cgpa_cutoff}</span></p>
                  <p>Allowed Backlogs: <span className="font-semibold text-slate-700 dark:text-slate-300">{drive.allowed_backlogs}</span></p>
                  <p className="flex items-center gap-1"><Calendar size={11} /> Deadline: {drive.deadline}</p>
                </div>
              </div>

              <div className="flex gap-2 pt-2 border-t border-gov-border dark:border-slate-850">
                <button
                  onClick={() => handleOpenEdit(drive)}
                  className="gov-btn-secondary py-1.5 w-full flex justify-center items-center gap-1 border border-gov-border hover:bg-slate-50 dark:hover:bg-slate-800 font-bold uppercase text-[10px]"
                >
                  <Edit size={12} /> Edit Criteria
                </button>
                <button
                  onClick={() => handleOpenDelete(drive)}
                  className="gov-btn-secondary py-1.5 w-full flex justify-center items-center gap-1 border border-red-200 hover:bg-red-50 text-red-650 font-bold uppercase text-[10px]"
                >
                  <Trash2 size={12} /> Purge
                </button>
              </div>
            </div>
          ))}
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
                    <option value="PUBLISHED">PUBLISHED</option>
                    <option value="REGISTRATION_OPEN">REGISTRATION_OPEN</option>
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

      {/* DELETE DIALOG MODAL */}
      {isDeleteOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-805 p-6 rounded-lg max-w-sm w-full text-xs space-y-4">
            <div className="flex items-start gap-3">
              <div className="bg-red-50 p-2 rounded-full text-red-650 shrink-0">
                <AlertTriangle size={20} />
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-slate-850 dark:text-slate-200 uppercase">Confirm Drive Purging</h4>
                <p className="text-slate-500 leading-normal">
                  Are you absolutely sure you want to delete the placement drive for <span className="font-semibold text-slate-700 dark:text-slate-350">{selectedDrive?.company_name} ({selectedDrive?.role})</span>? All candidate job applications filed under this drive will be deleted.
                </p>
              </div>
            </div>

            <div className="flex gap-3 justify-end pt-2">
              <button onClick={() => setIsDeleteOpen(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border">Cancel</button>
              <button onClick={handleDeleteSubmit} className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-red-600 border-0 hover:bg-red-700">Delete Drive</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default AdminDrives;
