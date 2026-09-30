import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { grievanceService } from '../services/api';
import { 
  ShieldAlert, CheckCircle2, AlertTriangle, AlertCircle, FileText, Send, 
  MessageSquareCode, HelpCircle
} from 'lucide-react';

export const Grievances: React.FC = () => {
  const { user } = useAuth();
  
  const [grievances, setGrievances] = useState<any[]>([]);
  const [category, setCategory] = useState('Attendance issue');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  
  // Resolve dialog state
  const [activeGrievanceId, setActiveGrievanceId] = useState<number | null>(null);
  const [resolutionRemarks, setResolutionRemarks] = useState('');
  const [statusAction, setStatusAction] = useState('RESOLVED');

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchGrievances();
  }, []);

  const fetchGrievances = async () => {
    try {
      setLoading(true);
      const res = await grievanceService.getGrievances();
      setGrievances(res);
    } catch (err: any) {
      setError('Failed to load issue tickets registry.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !description) {
      setError('Please fill in issue title and description.');
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      await grievanceService.submitGrievance({
        category,
        title,
        description
      });
      setSuccess('Issue ticket filed successfully. Placement cell team will contact you shortly.');
      setTitle('');
      setDescription('');
      fetchGrievances();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit issue ticket.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleResolve = async (id: number) => {
    if (!resolutionRemarks) {
      setError('Please input resolution remarks.');
      return;
    }
    try {
      setError(null);
      await grievanceService.resolveGrievance(id, statusAction, resolutionRemarks);
      setSuccess('Issue status modified successfully.');
      setActiveGrievanceId(null);
      setResolutionRemarks('');
      fetchGrievances();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update issue ticket.');
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-xl font-bold uppercase tracking-wide">Issue & Grievance Desk</h1>
        <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
          Report placement issues and track official resolution reports
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
        
        {/* Report form (Only for student) */}
        {user.role === 'student' && (
          <div className="gov-card h-fit">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <Send size={18} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Submit Issue Ticket</h2>
            </div>
            
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Issue Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
                >
                  <option value="Attendance issue">Attendance parameter issue</option>
                  <option value="Eligibility issue">Company drive eligibility mismatch</option>
                  <option value="Application issue">Application submission error</option>
                  <option value="Interview issue">Scheduled Interview conflict</option>
                  <option value="Placement process issue">Recruitment process grievance</option>
                  <option value="Technical issue">Technical platform glitch</option>
                  <option value="Other">Other general issues</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Short Summary / Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  placeholder="e.g. Attendance shows 71% instead of 78%"
                  className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Detailed Description
                </label>
                <textarea
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                  placeholder="Provide precise details to help coordinators verify and fix this issue..."
                  className="w-full mt-1 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded p-2.5 text-sm"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="gov-btn-primary w-full"
              >
                {submitting ? 'Filing Ticket...' : 'File Issue Ticket'}
              </button>
            </form>
          </div>
        )}

        {/* Grievances list board */}
        <div className={`gov-card lg:col-span-${user.role === 'student' ? '2' : '3'}`}>
          <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
            <MessageSquareCode size={18} className="text-gov-blue" />
            <h2 className="text-sm font-bold uppercase tracking-wider">
              {user.role === 'student' ? 'My Filed Issue Tickets' : 'Student Grievance Queue'}
            </h2>
          </div>

          {loading ? (
            <div className="text-center py-6 text-slate-400 text-xs">Loading issue queue...</div>
          ) : grievances.length === 0 ? (
            <div className="text-center py-6 text-slate-400 text-xs">No issue tickets registered.</div>
          ) : (
            <div className="space-y-4">
              {grievances.map((gr) => (
                <div key={gr.id} className="border border-gov-border dark:border-slate-800 p-4 rounded-lg bg-slate-50 dark:bg-slate-900 space-y-3">
                  <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 text-xs">
                    <div>
                      <span className="bg-slate-200 dark:bg-slate-800 text-slate-650 px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider mr-2">
                        {gr.category}
                      </span>
                      {user.role !== 'student' && (
                        <span className="font-bold text-slate-600">Student ID #{gr.student_id}</span>
                      )}
                    </div>
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold self-start ${
                      gr.status === 'RESOLVED' ? 'bg-emerald-50 text-emerald-700' :
                      gr.status === 'UNDER_REVIEW' ? 'bg-amber-50 text-amber-700' :
                      'bg-red-50 text-red-700'
                    }`}>
                      {gr.status}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-xs font-bold text-slate-850 dark:text-slate-200">{gr.title}</h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">{gr.description}</p>
                  </div>

                  {gr.resolution_remarks && (
                    <div className="bg-emerald-50/40 border border-emerald-100 p-2.5 rounded text-[11px] text-emerald-800">
                      <p className="font-semibold">Resolution Remarks:</p>
                      <p className="mt-0.5">{gr.resolution_remarks}</p>
                    </div>
                  )}

                  {user.role !== 'student' && gr.status !== 'RESOLVED' && (
                    <div className="pt-2 border-t border-gov-border dark:border-slate-800">
                      {activeGrievanceId === gr.id ? (
                        <div className="space-y-3">
                          <div className="flex gap-4">
                            <select
                              value={statusAction}
                              onChange={(e) => setStatusAction(e.target.value)}
                              className="border border-gov-border dark:border-slate-850 dark:bg-slate-900 rounded p-1.5 text-xs font-semibold"
                            >
                              <option value="RESOLVED">RESOLVED</option>
                              <option value="UNDER_REVIEW">UNDER REVIEW</option>
                            </select>
                            <input
                              type="text"
                              value={resolutionRemarks}
                              onChange={(e) => setResolutionRemarks(e.target.value)}
                              placeholder="Input resolution remarks"
                              required
                              className="flex-1 border border-gov-border dark:border-slate-850 dark:bg-slate-900 rounded p-1.5 text-xs"
                            />
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleResolve(gr.id)}
                              className="px-3 py-1 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded text-xs"
                            >
                              Confirm update
                            </button>
                            <button
                              onClick={() => setActiveGrievanceId(null)}
                              className="px-3 py-1 bg-slate-200 text-slate-700 rounded text-xs font-bold"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => {
                            setActiveGrievanceId(gr.id);
                            setStatusAction(gr.status === 'OPEN' ? 'UNDER_REVIEW' : 'RESOLVED');
                          }}
                          className="px-3 py-1 bg-gov-blue hover:bg-gov-accent text-white font-bold rounded text-xs"
                        >
                          Process Ticket
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default Grievances;
