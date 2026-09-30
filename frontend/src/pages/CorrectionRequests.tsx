import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { correctionService, studentService } from '../services/api';
import { 
  ClipboardList, CheckCircle2, XCircle, AlertCircle, FileText, Send, 
  UserCheck, ShieldAlert
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
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchRequests();
    if (user.role === 'student') {
      fetchStudentProfile();
    }
  }, []);

  const fetchRequests = async () => {
    try {
      setLoading(true);
      const res = await correctionService.getRequests();
      setRequests(res);
    } catch (err: any) {
      setError('Failed to load correction requests.');
    } finally {
      setLoading(false);
    }
  };

  const fetchStudentProfile = async () => {
    try {
      const res = await studentService.getStudentById(user.id);
      setStudentProfile(res);
      // Autofill current value
      autofillCurrentValue(field, res);
    } catch (err) {
      console.error('Failed to load student profile.');
    }
  };

  const autofillCurrentValue = (selectedField: string, profile: any) => {
    if (!profile) return;
    const f = selectedField.toLowerCase();
    if (f === 'cgpa') setCurrentVal(profile.cgpa.toString());
    else if (f === 'attendance' || f === 'academic attendance') setCurrentVal(profile.attendance.toString());
    else if (f === 'backlogs') setCurrentVal(profile.backlogs.toString());
    else if (f === 'name') setCurrentVal(profile.name);
    else if (f === 'section') setCurrentVal(profile.section || 'A');
    else if (f === 'batch' || f === 'year') setCurrentVal(profile.batch);
    else if (f === 'email') setCurrentVal(profile.email);
    else if (f === 'branch' || f === 'department') setCurrentVal(profile.dept_code);
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
      setError(null);
      await correctionService.actionRequest(id, status);
      setSuccess(`Request successfully ${status.toLowerCase()}!`);
      fetchRequests();
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to ${status.toLowerCase()} request.`);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-xl font-bold uppercase tracking-wide">Profile Correction Portal</h1>
        <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
          Verify and modify official academic parameter registries
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-xs text-red-700 flex items-start gap-2">
          <AlertCircle size={14} className="shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="bg-emerald-50 border border-emerald-250 rounded p-3 text-xs text-emerald-700 flex items-start gap-2">
          <CheckCircle2 size={14} className="shrink-0 mt-0.5 text-emerald-500" />
          <span>{success}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Submit Form (Only for Student) */}
        {user.role === 'student' && (
          <div className="gov-card h-fit">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <Send size={18} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">File Correction Request</h2>
            </div>
            
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Select Field to Correct
                </label>
                <select
                  value={field}
                  onChange={(e) => handleFieldChange(e.target.value)}
                  className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
                >
                  <option value="Name">Student Name</option>
                  <option value="CGPA">Academic CGPA</option>
                  <option value="Attendance">Academic Attendance</option>
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
                  className="w-full mt-1 bg-slate-50 border border-gov-border dark:bg-slate-950 dark:text-slate-100 dark:border-slate-800 rounded p-2.5 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Correct/Requested Value
                </label>
                <input
                  type="text"
                  value={requestedVal}
                  onChange={(e) => setRequestedVal(e.target.value)}
                  required
                  placeholder="Enter the correct value"
                  className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Reason for Request
                </label>
                <textarea
                  rows={3}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  required
                  placeholder="Describe why this value needs update (e.g. sem results re-valuation)"
                  className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="gov-btn-primary w-full"
              >
                {submitting ? 'Submitting Request...' : 'Submit to Admin Review'}
              </button>
            </form>
          </div>
        )}

        {/* Requests Table Board */}
        <div className={`gov-card lg:col-span-${user.role === 'student' ? '2' : '3'}`}>
          <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
            <ClipboardList size={18} className="text-gov-blue" />
            <h2 className="text-sm font-bold uppercase tracking-wider">
              {user.role === 'admin' ? 'Pending Verification Requests' : 'My Verification Requests'}
            </h2>
          </div>

          {loading ? (
            <div className="text-center py-6 text-slate-400 text-xs">Loading requests...</div>
          ) : requests.length === 0 ? (
            <div className="text-center py-6 text-slate-400 text-xs">No profile correction requests reported.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    {user.role === 'admin' && <th className="gov-table-th">Student ID</th>}
                    <th className="gov-table-th">Field</th>
                    <th className="gov-table-th">Current Value</th>
                    <th className="gov-table-th">Requested Value</th>
                    <th className="gov-table-th">Reason</th>
                    <th className="gov-table-th">Status</th>
                    {user.role === 'admin' && <th className="gov-table-th text-center">Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {requests.map((req) => (
                    <tr key={req.id}>
                      {user.role === 'admin' && <td className="gov-table-td font-semibold">#{req.student_id}</td>}
                      <td className="gov-table-td font-bold uppercase text-xs">{req.field}</td>
                      <td className="gov-table-td text-red-500 font-mono text-xs">{req.current_value}</td>
                      <td className="gov-table-td text-emerald-500 font-mono text-xs font-bold">{req.requested_value}</td>
                      <td className="gov-table-td max-w-xs truncate text-xs" title={req.reason}>{req.reason}</td>
                      <td className="gov-table-td">
                        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                          req.status === 'Approved' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20' :
                          req.status === 'Rejected' ? 'bg-red-50 text-red-700 dark:bg-red-950/20' :
                          'bg-amber-50 text-amber-700 dark:bg-amber-950/20'
                        }`}>
                          {req.status}
                        </span>
                      </td>
                      {user.role === 'admin' && (
                        <td className="gov-table-td text-center">
                          {req.status === 'Pending' ? (
                            <div className="flex gap-2 justify-center">
                              <button
                                onClick={() => handleAction(req.id, 'Approved')}
                                className="px-2 py-1 bg-emerald-500 hover:bg-emerald-600 text-white rounded text-xs font-bold"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => handleAction(req.id, 'Rejected')}
                                className="px-2 py-1 bg-red-500 hover:bg-red-650 text-white rounded text-xs font-bold"
                              >
                                Reject
                              </button>
                            </div>
                          ) : (
                            <span className="text-slate-400 text-xs">Processed</span>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default CorrectionRequests;
