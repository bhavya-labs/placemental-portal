import React, { useState, useEffect } from 'react';
import api from '../services/api'; // Axios instance directly
import { 
  Shield, CheckCircle2, XCircle, AlertCircle, Trash2, Key, Users,
  FolderLock, UserCheck, ShieldAlert
} from 'lucide-react';

export const AccessManagement: React.FC = () => {
  const [permissions, setPermissions] = useState<any[]>([]);
  const [requests, setRequests] = useState<any[]>([]);
  
  // Grant Form fields
  const [targetUserId, setTargetUserId] = useState('');
  const [module, setModule] = useState('Student Performance');
  const [scope, setScope] = useState('DEPARTMENT');
  const [scopeValue, setScopeValue] = useState('CSE');
  const [action, setAction] = useState('VIEW');
  const [duration, setDuration] = useState(7);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchPermissionsData();
  }, []);

  const fetchPermissionsData = async () => {
    try {
      setLoading(true);
      const [permRes, reqRes] = await Promise.all([
        api.get('/api/permissions'),
        api.get('/api/permissions/requests')
      ]);
      setPermissions(permRes.data);
      setRequests(reqRes.data);
    } catch (err) {
      setError('Failed to load access permissions registry.');
    } finally {
      setLoading(false);
    }
  };

  const handleGrant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetUserId || !scopeValue || !action) {
      setError('Please complete all permission details.');
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      await api.post('/api/permissions/grant', {
        user_id: parseInt(targetUserId),
        module,
        scope,
        scope_value: scopeValue,
        action,
        duration_days: duration
      });
      setSuccess('Access scope successfully granted to user account.');
      setTargetUserId('');
      setScopeValue('');
      fetchPermissionsData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to grant permission scope.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevoke = async (id: number) => {
    try {
      setError(null);
      await api.post(`/api/permissions/revoke/${id}`);
      setSuccess('Permission scope successfully revoked.');
      fetchPermissionsData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to revoke permission.');
    }
  };

  const handleRequestAction = async (id: number, status: 'Approved' | 'Rejected') => {
    try {
      setError(null);
      await api.put(`/api/permissions/requests/${id}/action`, { status });
      setSuccess(`Access request successfully ${status.toLowerCase()}!`);
      fetchPermissionsData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process access request.');
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-xl font-bold uppercase tracking-wide">Admin Access & RBAC Control</h1>
        <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
          Grant granular permission scopes and audit active credentials
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
        
        {/* Grant permission console form */}
        <div className="gov-card h-fit">
          <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
            <Key size={18} className="text-gov-blue" />
            <h2 className="text-sm font-bold uppercase tracking-wider">Grant User Scope</h2>
          </div>
          
          <form className="space-y-4" onSubmit={handleGrant}>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                Target User ID
              </label>
              <input
                type="number"
                value={targetUserId}
                onChange={(e) => setTargetUserId(e.target.value)}
                required
                placeholder="Enter account user ID"
                className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                Module
              </label>
              <select
                value={module}
                onChange={(e) => setModule(e.target.value)}
                className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
              >
                <option value="Student Performance">Student Performance</option>
                <option value="Placement Drives">Placement Drives & Analytics</option>
                <option value="Analytics">Analytics Dashboard</option>
                <option value="Access Control">Access Control Configuration</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                Scope Type
              </label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value)}
                className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
              >
                <option value="ALL_STUDENTS">All Students (ALL)</option>
                <option value="DEPARTMENT">Specific Department</option>
                <option value="SECTION">Specific Section</option>
                <option value="ASSIGNED_STUDENTS">Assigned Mentored Candidates</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                Scope Match Value
              </label>
              <input
                type="text"
                value={scopeValue}
                onChange={(e) => setScopeValue(e.target.value)}
                required
                placeholder="e.g. CSE, ECE, Section A"
                className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                Authorized Actions
              </label>
              <input
                type="text"
                value={action}
                onChange={(e) => setAction(e.target.value)}
                required
                placeholder="e.g. VIEW, EDIT, EXPORT"
                className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                Duration (Days)
              </label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value))}
                required
                min={1}
                max={365}
                className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="gov-btn-primary w-full"
            >
              {submitting ? 'Granting Permissions...' : 'Grant Scope'}
            </button>
          </form>
        </div>

        {/* Requests & Permissions audit board list */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Faculty Access Requests board */}
          <div className="gov-card">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <Users size={18} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Faculty Scope Requests</h2>
            </div>
            
            {requests.length === 0 ? (
              <div className="text-center py-6 text-slate-400 text-xs">No pending coordinator scope requests.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="gov-table-th">User ID</th>
                      <th className="gov-table-th">Module</th>
                      <th className="gov-table-th">Scope</th>
                      <th className="gov-table-th">Action</th>
                      <th className="gov-table-th">Reason</th>
                      <th className="gov-table-th">Status</th>
                      <th className="gov-table-th text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {requests.map((req) => (
                      <tr key={req.id}>
                        <td className="gov-table-td">#{req.user_id}</td>
                        <td className="gov-table-td text-xs font-semibold">{req.module}</td>
                        <td className="gov-table-td text-xs font-mono">{req.scope}:{req.scope_value || '—'}</td>
                        <td className="gov-table-td text-xs font-bold">{req.action}</td>
                        <td className="gov-table-td text-xs max-w-xs truncate" title={req.reason}>{req.reason}</td>
                        <td className="gov-table-td">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                            req.status === 'Approved' ? 'bg-emerald-50 text-emerald-700' :
                            req.status === 'Rejected' ? 'bg-red-50 text-red-700' :
                            'bg-amber-50 text-amber-700'
                          }`}>
                            {req.status}
                          </span>
                        </td>
                        <td className="gov-table-td text-center">
                          {req.status === 'Pending' ? (
                            <div className="flex gap-1.5 justify-center">
                              <button
                                onClick={() => handleRequestAction(req.id, 'Approved')}
                                className="px-2 py-0.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded text-[10px] font-bold"
                              >
                                Grant
                              </button>
                              <button
                                onClick={() => handleRequestAction(req.id, 'Rejected')}
                                className="px-2 py-0.5 bg-red-500 hover:bg-red-650 text-white rounded text-[10px] font-bold"
                              >
                                Deny
                              </button>
                            </div>
                          ) : (
                            <span className="text-slate-400 text-xs">Processed</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Active permissions list */}
          <div className="gov-card">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <FolderLock size={18} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Active Permissions Registry</h2>
            </div>
            
            {permissions.length === 0 ? (
              <div className="text-center py-6 text-slate-400 text-xs">No active granular permission records.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="gov-table-th">User ID</th>
                      <th className="gov-table-th">Module</th>
                      <th className="gov-table-th">Scope</th>
                      <th className="gov-table-th">Actions</th>
                      <th className="gov-table-th">Expiry Date</th>
                      <th className="gov-table-th">Status</th>
                      <th className="gov-table-th text-center">Revoke</th>
                    </tr>
                  </thead>
                  <tbody>
                    {permissions.map((perm) => (
                      <tr key={perm.id}>
                        <td className="gov-table-td font-semibold">#{perm.user_id}</td>
                        <td className="gov-table-td text-xs font-semibold">{perm.module}</td>
                        <td className="gov-table-td text-xs font-mono">{perm.scope}:{perm.scope_value || 'ALL'}</td>
                        <td className="gov-table-td text-xs font-bold text-gov-blue">{perm.action}</td>
                        <td className="gov-table-td text-xs">{new Date(perm.expiry_date).toLocaleDateString()}</td>
                        <td className="gov-table-td">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                            perm.status === 'Active' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'
                          }`}>
                            {perm.status}
                          </span>
                        </td>
                        <td className="gov-table-td text-center">
                          {perm.status === 'Active' ? (
                            <button
                              onClick={() => handleRevoke(perm.id)}
                              className="text-red-500 hover:text-red-700 transition-colors p-1"
                              title="Revoke Permission"
                            >
                              <Trash2 size={16} />
                            </button>
                          ) : (
                            <span className="text-slate-350">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
};

export default AccessManagement;
