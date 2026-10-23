import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { parentService } from '../services/api';
import { 
  GraduationCap, Briefcase, Calendar, Bell, ClipboardList, CheckCircle2, 
  XCircle, AlertTriangle, ShieldAlert, Award, FileText
} from 'lucide-react';

export const ParentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChildData = async () => {
      try {
        const res = await parentService.getChildData();
        setData(res);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load child details. Session expired.');
      } finally {
        setLoading(false);
      }
    };
    fetchChildData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gov-navy dark:border-sky-400"></div>
          <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Loading child profile metrics...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-6">
        <div className="bg-white dark:bg-slate-900 border border-red-200 rounded p-6 max-w-md w-full shadow-card text-center space-y-4">
          <ShieldAlert size={48} className="text-red-500 mx-auto" />
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Parent Access Error</h2>
          <p className="text-sm text-slate-500">{error || 'Session could not be verified.'}</p>
          <button
            onClick={() => navigate('/parent/login')}
            className="gov-btn-primary w-full"
          >
            Return to Parent Login
          </button>
        </div>
      </div>
    );
  }

  const { student, applications, attendance, notifications } = data;

  // Determine eligibility status and specific pending criteria
  const unmetRequirements: string[] = [];
  if (student.cgpa < 6.0) {
    unmetRequirements.push(`CGPA is ${student.cgpa.toFixed(2)} (min 6.00)`);
  }
  if (student.backlogs > 0) {
    unmetRequirements.push(`${student.backlogs} active backlog${student.backlogs > 1 ? 's' : ''} to clear`);
  }
  if (student.attendance < 75.0) {
    unmetRequirements.push(`Attendance is ${student.attendance.toFixed(1)}% (min 75.0%)`);
  }
  const isEligible = unmetRequirements.length === 0;

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Top Welcome Title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-gov-navy text-white p-6 rounded-lg shadow-card">
        <div>
          <h1 className="text-xl font-bold uppercase tracking-wide">Child Career Tracker</h1>
          <p className="text-xs text-slate-350">Academic Performance & Placement Progress</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg px-4 py-2 text-right">
            <p className="text-[10px] text-slate-400 uppercase font-semibold">Active Ward</p>
            <p className="text-sm font-bold">{student.name} ({student.id})</p>
          </div>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* CGPA */}
        <div className="gov-card flex items-center gap-4">
          <div className="p-3 bg-gov-light dark:bg-slate-800 text-gov-blue dark:text-sky-400 rounded-lg">
            <GraduationCap size={24} />
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Cumulative CGPA</p>
            <p className="text-lg font-bold text-slate-800 dark:text-slate-100">{student.cgpa.toFixed(2)}</p>
          </div>
        </div>

        {/* Attendance */}
        <div className="gov-card flex items-center gap-4">
          <div className="p-3 bg-gov-light dark:bg-slate-800 text-emerald-500 rounded-lg">
            <ClipboardList size={24} />
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Academic Attendance</p>
            <p className="text-lg font-bold text-slate-800 dark:text-slate-100">{student.attendance.toFixed(1)}%</p>
          </div>
        </div>

        {/* Backlogs */}
        <div className="gov-card flex items-center gap-4">
          <div className={`p-3 rounded-lg ${student.backlogs > 0 ? 'bg-red-50 text-red-500 dark:bg-red-950/20' : 'bg-gov-light dark:bg-slate-800 text-gov-navy'}`}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Active Backlogs</p>
            <p className="text-lg font-bold text-slate-800 dark:text-slate-100">{student.backlogs}</p>
          </div>
        </div>

        {/* Eligibility Status */}
        <div className="gov-card flex items-start gap-4">
          <div className={`p-3 rounded-lg mt-0.5 ${isEligible ? 'bg-emerald-50 text-emerald-500 dark:bg-emerald-950/20' : 'bg-amber-50 text-amber-500 dark:bg-amber-950/20'}`}>
            <Award size={24} />
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Placement Eligibility</p>
            <p className={`text-sm font-bold ${isEligible ? 'text-emerald-700 dark:text-emerald-400' : 'text-amber-700 dark:text-amber-400'}`}>
              {isEligible ? 'Requirements Met' : 'Requirements Pending'}
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">
              {isEligible ? 'Eligible for open campus drives' : unmetRequirements.join(' • ')}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Applications Tracker & Placement Attendance */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Applications list */}
          <div className="gov-card">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <Briefcase size={20} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Recruitment Applications ({applications.length})</h2>
            </div>
            {applications.length === 0 ? (
              <div className="text-center py-6 text-slate-400 text-xs">No recruitment applications submitted yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="gov-table-th">Company</th>
                      <th className="gov-table-th">Role</th>
                      <th className="gov-table-th">Package (LPA)</th>
                      <th className="gov-table-th">Current Round</th>
                      <th className="gov-table-th">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {applications.map((app: any, idx: number) => (
                      <tr key={idx}>
                        <td className="gov-table-td font-semibold">{app.company_name}</td>
                        <td className="gov-table-td">{app.role}</td>
                        <td className="gov-table-td">{app.package_lpa} LPA</td>
                        <td className="gov-table-td text-xs font-semibold">{app.current_round}</td>
                        <td className="gov-table-td">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                            app.status === 'Selected' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400' :
                            app.status === 'Rejected' ? 'bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400' :
                            'bg-blue-50 text-blue-700 dark:bg-blue-950/20 dark:text-blue-400'
                          }`}>
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

          {/* Activity attendance list */}
          <div className="gov-card">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <Calendar size={20} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Placement Activities Attendance</h2>
            </div>
            {attendance.length === 0 ? (
              <div className="text-center py-6 text-slate-400 text-xs">No placement training sessions registered.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="gov-table-th">Activity Name</th>
                      <th className="gov-table-th">Type</th>
                      <th className="gov-table-th">Date</th>
                      <th className="gov-table-th">Status</th>
                      <th className="gov-table-th">Remarks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attendance.map((att: any, idx: number) => (
                      <tr key={idx}>
                        <td className="gov-table-td font-semibold text-xs">{att.activity_name}</td>
                        <td className="gov-table-td text-xs capitalize">{att.activity_type.toLowerCase()}</td>
                        <td className="gov-table-td text-xs">{att.date}</td>
                        <td className="gov-table-td">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                            att.status === 'PRESENT' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400' :
                            'bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400'
                          }`}>
                            {att.status}
                          </span>
                        </td>
                        <td className="gov-table-td text-xs text-slate-500">{att.remarks || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>

        {/* Right Column: Notifications & Student metadata */}
        <div className="space-y-6">
          
          {/* Notifications feed */}
          <div className="gov-card">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <Bell size={20} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Placement Notifications</h2>
            </div>
            {notifications.length === 0 ? (
              <div className="text-center py-6 text-slate-400 text-xs">No alerts posted recently.</div>
            ) : (
              <div className="space-y-4 max-h-[350px] overflow-y-auto pr-2">
                {notifications.map((notif: any, idx: number) => (
                  <div key={idx} className="border-l-4 border-gov-blue pl-3 py-1 space-y-1 bg-slate-50 dark:bg-slate-900 rounded-r p-2">
                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200">{notif.title}</p>
                    <p className="text-[11px] text-slate-500">{notif.message}</p>
                    <p className="text-[9px] text-slate-400 font-medium">
                      {new Date(notif.created_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Locked fields info */}
          <div className="gov-card bg-slate-50 dark:bg-slate-900 border border-slate-200/50">
            <div className="flex items-center gap-2 pb-3 mb-3 border-b border-gov-border dark:border-slate-800">
              <FileText size={18} className="text-gov-blue" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-750 dark:text-slate-300">Verified Profile Info</h3>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Full Name:</span>
                <span className="font-semibold">{student.name} 🔒</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Roll Number:</span>
                <span className="font-semibold">{student.id} 🔒</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Department:</span>
                <span className="font-semibold">{student.dept_code} — {student.dept_name} 🔒</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Hiring Status:</span>
                <span className="font-bold text-gov-blue">{student.status} 🔒</span>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};

export default ParentDashboard;
