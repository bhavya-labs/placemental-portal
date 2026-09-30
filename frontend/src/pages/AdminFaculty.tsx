import React, { useState, useEffect } from 'react';
import { authService } from '../services/api';
import { CardSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import { 
  Users, PlusCircle, Search, Filter, Edit, Trash2, X, AlertTriangle, Key 
} from 'lucide-react';
import { ProfessionalTable } from '../components/ProfessionalTable';
import { AccessibleToast } from '../components/AccessibilityComponents';

export const AdminFaculty: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [faculties, setFaculties] = useState<any[]>([]);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  // Dialog configurations
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedFaculty, setSelectedFaculty] = useState<any | null>(null);

  // Form values
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [deptId, setDeptId] = useState<number>(1);
  const [designation, setDesignation] = useState('Assistant Professor');

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const loadFaculties = async () => {
    setLoading(true);
    try {
      const data = await authService.getFaculties();
      setFaculties(data);
    } catch (err) {
      console.error('Failed to load faculties list', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFaculties();
  }, []);

  const handleOpenAdd = () => {
    setName('');
    setEmail('');
    setPassword('');
    setDeptId(1);
    setDesignation('Assistant Professor');
    setIsAddOpen(true);
  };

  const generateRandomPassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%&*';
    let generated = '';
    for (let i = 0; i < 12; i++) {
      generated += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setPassword(generated);
  };

  const handleOpenEdit = (fac: any) => {
    setSelectedFaculty(fac);
    setName(fac.name);
    setDeptId(fac.dept_id);
    setDesignation(fac.designation);
    setIsEditOpen(true);
  };

  const handleOpenDelete = (fac: any) => {
    setSelectedFaculty(fac);
    setIsDeleteOpen(true);
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) {
      showToast('Please specify an initial password or click generate.', 'error');
      return;
    }
    try {
      await authService.createFaculty({
        name,
        email,
        password,
        dept_id: deptId,
        designation
      });
      showToast('Faculty coordinator account successfully created!', 'success');
      setIsAddOpen(false);
      loadFaculties();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to register faculty.', 'error');
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFaculty) return;
    try {
      await authService.updateFaculty(selectedFaculty.id, {
        name,
        dept_id: deptId,
        designation
      });
      showToast('Faculty configurations updated!', 'success');
      setIsEditOpen(false);
      loadFaculties();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to update details.', 'error');
    }
  };

  const handleDeleteSubmit = async () => {
    if (!selectedFaculty) return;
    try {
      await authService.deleteFaculty(selectedFaculty.id);
      showToast('Faculty account deleted successfully.', 'success');
      setIsDeleteOpen(false);
      loadFaculties();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to delete account.', 'error');
    }
  };

  const columns = [
    { header: 'ID', accessor: 'id' },
    { header: 'Name', accessor: 'name' },
    { header: 'Email', accessor: 'email' },
    { header: 'Department', accessor: 'dept_name' },
    { header: 'Designation', accessor: 'designation' },
    { header: 'Actions', accessor: 'id', render: (row: any) => (
      <div className="flex gap-2">
        <button
          onClick={() => handleOpenEdit(row)}
          className="p-1 border border-gov-border rounded hover:bg-slate-100 dark:hover:bg-slate-800"
          title="Edit Details"
        >
          <Edit size={12} className="text-gov-blue" />
        </button>
        <button
          onClick={() => handleOpenDelete(row)}
          className="p-1 border border-gov-border rounded hover:bg-slate-100 dark:hover:bg-slate-800"
          title="Delete Account"
        >
          <Trash2 size={12} className="text-red-500" />
        </button>
      </div>
    )}
  ];

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-355">
      <AccessibleToast message={toast?.message || null} type={toast?.type || null} />

      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
            <Users className="text-gov-blue" size={24} />
            Faculty Accounts Registry
          </h2>
          <p className="text-[10px] text-slate-500 mt-1">
            Create, update, and manage coordinator designations and system permissions for departments.
          </p>
        </div>

        <button
          onClick={handleOpenAdd}
          className="gov-btn-primary py-2 px-4 rounded font-bold uppercase tracking-wider bg-gov-navy border-0 text-white flex items-center gap-1.5"
        >
          <PlusCircle size={14} /> Add Coordinator
        </button>
      </div>

      {loading ? <TableSkeleton /> : (
        <div className="gov-card">
          <ProfessionalTable
            columns={columns}
            data={faculties}
            searchPlaceholder="Search faculty database by name, email, or division..."
            exportFileName="faculty_members_registry"
          />
        </div>
      )}

      {/* ADD DIALOG MODAL */}
      {isAddOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-6 rounded-lg max-w-md w-full text-xs space-y-4">
            <div className="flex justify-between items-center border-b border-gov-border dark:border-slate-850 pb-3">
              <h4 className="text-sm font-bold text-gov-navy dark:text-slate-200 uppercase">Register Department Coordinator</h4>
              <button onClick={() => setIsAddOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={16} />
              </button>
            </div>
            
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label htmlFor="fac-name" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Full Name *</label>
                <input
                  id="fac-name"
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:text-slate-100 focus:outline-none"
                  placeholder="Prof. Ramesh Babu"
                />
              </div>

              <div>
                <label htmlFor="fac-email" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Email Address *</label>
                <input
                  id="fac-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:text-slate-100 focus:outline-none"
                  placeholder="ramesh@university.edu"
                />
              </div>

              <div>
                <div className="flex justify-between items-center">
                  <label htmlFor="fac-password" className="block font-bold text-slate-650 dark:text-slate-400 uppercase flex items-center gap-1">
                    <Key size={12} className="text-gov-blue" />
                    Initial Password *
                  </label>
                  <button
                    type="button"
                    onClick={generateRandomPassword}
                    className="text-[10px] font-bold text-gov-blue hover:underline focus:outline-none uppercase tracking-wider"
                  >
                    + Generate Random
                  </button>
                </div>
                <input
                  id="fac-password"
                  type="text"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:text-slate-100 focus:outline-none font-mono"
                  placeholder="Leave blank to enter custom password or click Generate"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="fac-dept" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Department *</label>
                  <select
                    id="fac-dept"
                    value={deptId}
                    onChange={(e) => setDeptId(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 focus:outline-none"
                  >
                    <option value="1">Computer Science (CSE)</option>
                    <option value="2">Information Tech (IT)</option>
                    <option value="3">Electronics (ECE)</option>
                    <option value="4">Electrical (EEE)</option>
                    <option value="5">Mechanical (MECH)</option>
                    <option value="6">Civil (CIVIL)</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="fac-designation" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Designation *</label>
                  <input
                    id="fac-designation"
                    type="text"
                    required
                    value={designation}
                    onChange={(e) => setDesignation(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:text-slate-100 focus:outline-none"
                    placeholder="Assistant Professor"
                  />
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setIsAddOpen(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border">Cancel</button>
                <button type="submit" className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy border-0">Register Account</button>
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
              <h4 className="text-sm font-bold text-gov-navy dark:text-slate-200 uppercase">Modify Coordinator Settings</h4>
              <button onClick={() => setIsEditOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={16} />
              </button>
            </div>
            
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label htmlFor="edit-fac-name" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Full Name *</label>
                <input
                  id="edit-fac-name"
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="edit-fac-dept" className="block font-bold text-slate-655 dark:text-slate-400 uppercase">Department</label>
                  <select
                    id="edit-fac-dept"
                    value={deptId}
                    onChange={(e) => setDeptId(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 focus:outline-none"
                  >
                    <option value="1">Computer Science (CSE)</option>
                    <option value="2">Information Tech (IT)</option>
                    <option value="3">Electronics (ECE)</option>
                    <option value="4">Electrical (EEE)</option>
                    <option value="5">Mechanical (MECH)</option>
                    <option value="6">Civil (CIVIL)</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="edit-fac-designation" className="block font-bold text-slate-650 dark:text-slate-400 uppercase">Designation</label>
                  <input
                    id="edit-fac-designation"
                    type="text"
                    required
                    value={designation}
                    onChange={(e) => setDesignation(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 focus:outline-none"
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
                <h4 className="text-sm font-bold text-slate-850 dark:text-slate-200 uppercase">Confirm Coordinator Removal</h4>
                <p className="text-slate-500 leading-normal">
                  Are you absolutely sure you want to delete the faculty account for <span className="font-semibold text-slate-700 dark:text-slate-300">{selectedFaculty?.name}</span>? This action is permanent.
                </p>
              </div>
            </div>

            <div className="flex gap-3 justify-end pt-2">
              <button onClick={() => setIsDeleteOpen(false)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border">Cancel</button>
              <button onClick={handleDeleteSubmit} className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-red-600 border-0 hover:bg-red-700">Delete Account</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default AdminFaculty;
