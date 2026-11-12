import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { correctionService, studentService } from '../services/api';
import { 
  ClipboardList, CheckCircle2, XCircle, AlertCircle, FileText, Send, 
  UserCheck, ShieldAlert, ChevronLeft, ChevronRight, Filter, RotateCcw
} from 'lucide-react';

export const CorrectionRequests: React.FC = () => {
  const { user } = useAuth();
  
  const [requests, setRequests] = useState<any[]>([]);
  const [studentProfile, setStudentProfile] = useState<any | null>(null);
  
  // Form fields
  const [field, setField] = useState('CGPA');
  const [currentVal, setCurrentVal] = useState('');
  const [requestedVal, setRequestedVal] = useState('');
  const [reason, setReason] = useState('');
  
  // State and filter controls
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'Pending' | 'Approved' | 'Rejected'>('ALL');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 8;

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [actioningId, setActioningId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchRequests();
    if (user?.role === 'student') {
      fetchStudentProfile();
    }
  }, []);

  const fetchRequests = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await correctionService.getRequests();
      setRequests(Array.isArray(res) ? res : []);
    } catch (err: any) {
      setError('Failed to load profile correction requests.');
    } finally {
      setLoading(false);
    }
  };

  const fetchStudentProfile = async () => {
    if (!user) return;
    try {
      const res = await studentService.getStudentById(user.id);
      setStudentProfile(res);
      autofillCurrentValue(field, res);
    } catch (err) {
      console.error('Failed to load student profile.');
    }
  };

  const autofillCurrentValue = (selectedField: string, profile: any) => {
    if (!profile) return;
    const f = selectedField.toLowerCase();
    if (f === 'cgpa') setCurrentVal(profile.cgpa?.toString() || '');
    else if (f === 'attendance' || f === 'academic attendance') setCurrentVal(profile.attendance?.toString() || '');
    else if (f === 'backlogs') setCurrentVal(profile.backlogs?.toString() || '0');
    else if (f === 'name') setCurrentVal(profile.name || '');
    else if (f === 'section') setCurrentVal(profile.section || 'A');
    else if (f === 'batch' || f === 'year') setCurrentVal(profile.batch || '');
    else if (f === 'email') setCurrentVal(profile.email || '');
    else if (f === 'branch' || f === 'department') setCurrentVal(profile.dept_code || '');
  };

  const handleFieldChange = (val: string) => {
    setField(val);
    if (studentProfile) {
      autofillCurrentValue(val, studentProfile);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requestedVal || !reason) {
      setError('Please complete all form fields.');
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      await correctionService.submitRequest({
        field,
        current_value: currentVal,
        requested_value: requestedVal,
        reason
      });
      setSuccess('Correction request successfully submitted for Admin verification.');
      setRequestedVal('');
      setReason('');
      fetchRequests();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit correction request.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAction = async (id: number, status: 'Approved' | 'Rejected') => {
    try {
      setActioningId(id);
      setError(null);
      await correctionService.actionRequest(id, status);
      setSuccess(`Request #${id} successfully ${status.toLowerCase()}!`);
      fetchRequests();
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to ${status.toLowerCase()} request.`);
    } finally {
      setActioningId(null);
    }
  };

  // Filter requests by status
  const filteredRequests = requests.filter(req => {
    if (statusFilter === 'ALL') return true;
    return req.status === statusFilter;
  });

  // Calculate pagination
  const totalPages = Math.ceil(filteredRequests.length / pageSize) || 1;
  const safePage = Math.min(Math.max(currentPage, 1), totalPages);
  const startIndex = (safePage - 1) * pageSize;
  const paginatedRequests = filteredRequests.slice(startIndex, startIndex + pageSize);

  const handleStatusFilterChange = (filter: 'ALL' | 'Pending' | 'Approved' | 'Rejected') => {
    setStatusFilter(filter);
    setCurrentPage(1);
  };

  return (
    <div className="space-y-6 w-full max-w-7xl mx-auto px-4 sm:px-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold uppercase tracking-wide flex items-center gap-2">
            <ClipboardList className="text-gov-blue" size={24} />
            Profile Correction Registry
          </h1>
          <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mt-0.5">
            Verify, review, and synchronize official student academic parameters
          </p>
        </div>
        <button
          onClick={fetchRequests}
          disabled={loading}
          className="gov-btn-secondary py-1.5 px-3 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider"
          title="Refresh Requests"
        >
          <RotateCcw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded p-3 text-xs text-red-700 dark:text-red-300 flex items-start gap-2 animate-fadeIn">
          <AlertCircle size={14} className="shrink-0 mt-0.5" />
          <span className="flex-1">{error}</span>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
            <XCircle size={14} />
          </button>
        </div>
      )}

      {success && (
        <div className="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-250 dark:border-emerald-800 rounded p-3 text-xs text-emerald-700 dark:text-emerald-300 flex items-start gap-2 animate-fadeIn">
          <CheckCircle2 size={14} className="shrink-0 mt-0.5 text-emerald-500" />
          <span className="flex-1">{success}</span>
          <button onClick={() => setSuccess(null)} className="text-emerald-500 hover:text-emerald-700">
            <XCircle size={14} />
          </button>
        </div>
      )}

      {/* Grid Layout: Form (Student Only) + Table Board */}
      <div className={`grid grid-cols-1 ${user?.role === 'student' ? 'lg:grid-cols-3' : 'lg:grid-cols-1'} gap-6 w-full`}>
        
        {/* Submit Form (Only for Student) */}
        {user?.role === 'student' && (
          <div className="gov-card h-fit lg:col-span-1">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <Send size={18} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">File Correction Request</h2>
            </div>
            
            <form className="space-y-4 text-xs" onSubmit={handleSubmit}>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Select Field to Correct
                </label>
                <select
                  value={field}
                  onChange={(e) => handleFieldChange(e.target.value)}
                  className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2 text-xs focus:outline-none"
                >
                  <option value="Name">Student Name</option>
                  <option value="CGPA">Academic CGPA</option>
                  <option value="Attendance">Academic Attendance %</option>
                  <option value="Backlogs">Active Backlogs</option>
                  <option value="Section">Section Assignment</option>
                  <option value="Batch">Graduation Batch Year</option>
                  <option value="Branch">Department Branch</option>
                  <option value="Email">Official College Email</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Current Registered Value
                </label>
                <input
                  type="text"
                  value={currentVal}
                  disabled
                  className="w-full mt-1 bg-slate-50 border border-gov-border dark:bg-slate-950/60 dark:text-slate-400 dark:border-slate-800 rounded p-2 text-xs font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Correct / Requested Value *
                </label>
                <input
                  type="text"
                  value={requestedVal}
                  onChange={(e) => setRequestedVal(e.target.value)}
                  required
                  placeholder="Enter the correct value"
                  className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2 text-xs focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Reason for Request *
                </label>
                <textarea
                  rows={3}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  required
                  placeholder="Describe why this value needs update (e.g. sem results re-valuation)"
                  className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2 text-xs focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="gov-btn-primary w-full py-2 font-bold uppercase tracking-wider text-xs bg-gov-navy border-0 text-white"
              >
                {submitting ? 'Submitting Request...' : 'Submit to Admin Review'}
              </button>
            </form>
          </div>
        )}

        {/* Requests Table Board */}
        <div className={`gov-card ${user?.role === 'student' ? 'lg:col-span-2' : 'lg:col-span-3 w-full'}`}>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
            <div className="flex items-center gap-2">
              <ClipboardList size={18} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">
                {user?.role === 'admin' ? 'Administrative Verification Queue' : 'My Verification Requests'}
              </h2>
            </div>

            {/* Filter Tabs */}
            <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
              {(['ALL', 'Pending', 'Approved', 'Rejected'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => handleStatusFilterChange(tab)}
                  className={`px-2.5 py-1 rounded font-bold uppercase tracking-wider transition-colors ${
                    statusFilter === tab
                      ? 'bg-gov-navy text-white'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                  }`}
                >
                  {tab === 'ALL' ? `All (${requests.length})` : `${tab} (${requests.filter(r => r.status === tab).length})`}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
              <div className="w-6 h-6 border-2 border-gov-blue border-t-transparent rounded-full animate-spin"></div>
              <span className="text-xs uppercase tracking-wider font-semibold">Loading verification requests...</span>
            </div>
          ) : filteredRequests.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs font-semibold uppercase tracking-wider flex flex-col items-center gap-2">
              <FileText size={32} className="text-slate-300 dark:text-slate-700" />
              <p>No profile correction requests reported for this filter.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="overflow-x-auto -mx-4 sm:mx-0 border border-gov-border dark:border-slate-800 rounded">
                <table className="w-full text-left border-collapse min-w-[700px]">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-850 text-slate-600 dark:text-slate-300 text-[10px] uppercase font-bold tracking-wider">
                      {user?.role === 'admin' && <th className="p-2.5">Student ID</th>}
                      <th className="p-2.5">Field</th>
                      <th className="p-2.5">Current Value</th>
                      <th className="p-2.5">Requested Value</th>
                      <th className="p-2.5 min-w-[180px]">Reason</th>
                      <th className="p-2.5">Status</th>
                      {user?.role === 'admin' && <th className="p-2.5 text-center">Actions</th>}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gov-border dark:divide-slate-800 text-xs">
                    {paginatedRequests.map((req) => (
                      <tr key={req.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                        {user?.role === 'admin' && (
                          <td className="p-2.5 font-bold text-slate-800 dark:text-slate-200">
                            #{req.student_id}
                          </td>
                        )}
                        <td className="p-2.5 font-bold uppercase text-slate-700 dark:text-slate-300">{req.field}</td>
                        <td className="p-2.5 text-red-600 dark:text-red-400 font-mono text-[11px]">{req.current_value}</td>
                        <td className="p-2.5 text-emerald-600 dark:text-emerald-400 font-mono text-[11px] font-bold">{req.requested_value}</td>
                        <td className="p-2.5 text-slate-600 dark:text-slate-300 text-[11px] max-w-xs break-words" title={req.reason}>
                          {req.reason}
                        </td>
                        <td className="p-2.5 whitespace-nowrap">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                            req.status === 'Approved' ? 'bg-emerald-50 text-emerald-700 border-emerald-250 dark:bg-emerald-950/30 dark:text-emerald-300' :
                            req.status === 'Rejected' ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:text-red-300' :
                            'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-300'
                          }`}>
                            {req.status}
                          </span>
                        </td>
                        {user?.role === 'admin' && (
                          <td className="p-2.5 text-center whitespace-nowrap">
                            {req.status === 'Pending' ? (
                              <div className="flex gap-2 justify-center">
                                <button
                                  onClick={() => handleAction(req.id, 'Approved')}
                                  disabled={actioningId === req.id}
                                  className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded text-[11px] font-bold uppercase tracking-wider flex items-center gap-1 transition-colors"
                                  title="Approve Request"
                                >
                                  <CheckCircle2 size={12} /> Approve
                                </button>
                                <button
                                  onClick={() => handleAction(req.id, 'Rejected')}
                                  disabled={actioningId === req.id}
                                  className="px-2.5 py-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded text-[11px] font-bold uppercase tracking-wider flex items-center gap-1 transition-colors"
                                  title="Reject Request"
                                >
                                  <XCircle size={12} /> Reject
                                </button>
                              </div>
                            ) : (
                              <span className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider">Processed</span>
                            )}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex flex-col sm:flex-row justify-between items-center gap-3 pt-3 border-t border-gov-border dark:border-slate-800 text-xs">
                  <div className="text-slate-500 font-semibold text-[11px]">
                    Showing <span className="font-bold text-slate-700 dark:text-slate-300">{startIndex + 1}</span> to{' '}
                    <span className="font-bold text-slate-700 dark:text-slate-300">
                      {Math.min(startIndex + pageSize, filteredRequests.length)}
                    </span>{' '}
                    of <span className="font-bold text-slate-700 dark:text-slate-300">{filteredRequests.length}</span> requests
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={safePage === 1}
                      className="px-2 py-1 rounded border border-gov-border dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1 text-[11px] font-bold uppercase"
                    >
                      <ChevronLeft size={14} /> Prev
                    </button>

                    <div className="flex items-center gap-1 px-2">
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
                        <button
                          key={p}
                          onClick={() => setCurrentPage(p)}
                          className={`w-7 h-7 rounded text-[11px] font-bold transition-colors ${
                            safePage === p
                              ? 'bg-gov-navy text-white'
                              : 'border border-gov-border dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                          }`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>

                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={safePage === totalPages}
                      className="px-2 py-1 rounded border border-gov-border dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1 text-[11px] font-bold uppercase"
                    >
                      Next <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default CorrectionRequests;
