import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { student360Service } from '../services/api';
import { 
  GraduationCap, Briefcase, Calendar, MessageSquare, Brain, Clock, 
  ChevronLeft, Award, BookOpen, User, CheckCircle2, AlertCircle, FileText
} from 'lucide-react';

export const Student360: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const studentId = parseInt(id || '0');

  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (studentId > 0) {
      fetchStudentData();
    } else {
      setError('Invalid student account ID.');
      setLoading(false);
    }
  }, [studentId]);

  const fetchStudentData = async () => {
    try {
      setLoading(true);
      const res = await student360Service.getStudent360(studentId);
      setData(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Access denied. You do not have permissions to view this student profile.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gov-navy dark:border-sky-400"></div>
          <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Compiling candidate metrics...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 text-center space-y-4 max-w-md mx-auto">
        <AlertCircle size={48} className="text-red-500 mx-auto" />
        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Access Restricted</h2>
        <p className="text-sm text-slate-500">{error || 'Failed to load candidate files.'}</p>
        <button onClick={() => navigate(-1)} className="gov-btn-secondary w-full">
          Go Back
        </button>
      </div>
    );
  }

  const { profile, applications, interviews, activity_attendance, feedbacks, timeline, eligibility } = data;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header Navigation */}
      <div className="flex items-center justify-between pb-4 border-b border-gov-border dark:border-slate-850">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-gov-blue transition-colors focus:outline-none"
        >
          <ChevronLeft size={16} />
          <span>Back to Tracker</span>
        </button>
        <span className="text-xs bg-slate-100 text-slate-650 px-3 py-1 rounded dark:bg-slate-900">
          360° Officer Assessment Portal
        </span>
      </div>

      {/* Main Candidate Card */}
      <div className="bg-gov-navy text-white p-6 rounded-lg shadow-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center font-bold text-xl uppercase border border-white/20">
            {profile.name.charAt(0)}
          </div>
          <div>
            <h1 className="text-lg font-bold uppercase tracking-wide">{profile.name}</h1>
            <p className="text-xs text-slate-350">{profile.dept_code} Department • Roll Number: #{profile.id} • Section {profile.section || 'A'}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg px-4 py-2 text-right">
            <p className="text-[10px] text-slate-400 uppercase font-semibold">Verification status</p>
            <p className="text-xs font-bold tracking-wide uppercase">{profile.verification_status}</p>
          </div>
          <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg px-4 py-2 text-right">
            <p className="text-[10px] text-slate-400 uppercase font-semibold">Placement status</p>
            <p className="text-xs font-bold text-gov-blue uppercase bg-white px-2 py-0.5 rounded shadow-sm">{profile.status}</p>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="gov-card flex items-center gap-3.5">
          <div className="p-2.5 bg-gov-light dark:bg-slate-800 text-gov-blue dark:text-sky-400 rounded-lg">
            <GraduationCap size={22} />
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Cumulative CGPA</p>
            <p className="text-base font-bold text-slate-850 dark:text-slate-100">{profile.cgpa.toFixed(2)}</p>
          </div>
        </div>

        <div className="gov-card flex items-center gap-3.5">
          <div className="p-2.5 bg-gov-light dark:bg-slate-800 text-emerald-500 rounded-lg">
            <BookOpen size={22} />
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Attendance Rate</p>
            <p className="text-base font-bold text-slate-850 dark:text-slate-100">{profile.attendance.toFixed(1)}%</p>
          </div>
        </div>

        <div className="gov-card flex items-center gap-3.5">
          <div className="p-2.5 bg-gov-light dark:bg-slate-800 text-amber-500 rounded-lg">
            <AlertCircle size={22} />
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Active Backlogs</p>
            <p className="text-base font-bold text-slate-850 dark:text-slate-100">{profile.backlogs}</p>
          </div>
        </div>

        <div className="gov-card flex items-center gap-3.5">
          <div className="p-2.5 bg-gov-light dark:bg-slate-800 text-indigo-500 rounded-lg">
            <Brain size={22} />
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Placement Preparation Score</p>
            <p className="text-base font-bold text-slate-850 dark:text-slate-100">{profile.readiness_score}%</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Timelines and Active Applications */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Applications list */}
          <div className="gov-card">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <Briefcase size={18} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Recruitment Applications ({applications.length})</h2>
            </div>
            {applications.length === 0 ? (
              <div className="text-center py-6 text-slate-400 text-xs">No placement applications reported.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="gov-table-th">Company</th>
                      <th className="gov-table-th">Job Role</th>
                      <th className="gov-table-th">Package</th>
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
                        <td className="gov-table-td font-semibold text-xs">{app.current_round}</td>
                        <td className="gov-table-td">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                            app.status === 'Selected' ? 'bg-emerald-50 text-emerald-700' :
                            app.status === 'Rejected' ? 'bg-red-50 text-red-700' :
                            'bg-blue-50 text-blue-700'
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

          {/* Activity Attendance & Workshops */}
          <div className="gov-card">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <Calendar size={18} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Placement Activities Attendance</h2>
            </div>
            {activity_attendance.length === 0 ? (
              <div className="text-center py-6 text-slate-400 text-xs">No placement activities registered.</div>
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
                    {activity_attendance.map((att: any, idx: number) => (
                      <tr key={idx}>
                        <td className="gov-table-td font-semibold text-xs">{att.activity_name}</td>
                        <td className="gov-table-td text-xs capitalize">{att.activity_type.toLowerCase()}</td>
                        <td className="gov-table-td text-xs">{new Date(att.date).toLocaleDateString()}</td>
                        <td className="gov-table-td">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                            att.status === 'PRESENT' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
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

          {/* Timeline events flow */}
          <div className="gov-card">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <Clock size={18} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Student Placement Timeline</h2>
            </div>
            
            {timeline.length === 0 ? (
              <div className="text-center py-6 text-slate-400 text-xs">No timeline events compiled.</div>
            ) : (
              <div className="relative pl-6 border-l-2 border-slate-200 dark:border-slate-800 space-y-6">
                {timeline.map((event: any, idx: number) => (
                  <div key={idx} className="relative">
                    <span className={`absolute -left-[31px] top-0.5 w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 ${
                      event.type === 'activity' ? 'bg-blue-500' :
                      event.type === 'application' ? 'bg-emerald-500' :
                      'bg-indigo-500'
                    }`} />
                    <div className="space-y-1">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-bold text-slate-800 dark:text-slate-200">{event.title}</span>
                        <span className="text-slate-400 font-mono">{event.date}</span>
                      </div>
                      <p className="text-[11px] text-slate-500">
                        Status: <span className="font-semibold">{event.status}</span> {event.remarks && `• ${event.remarks}`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* AI Recommendations and Feedbacks */}
        <div className="space-y-6">
          
          {/* AI analytics report summary card */}
          <div className="gov-card bg-indigo-50/50 border border-indigo-100/50 dark:bg-slate-900 dark:border-slate-800">
            <div className="flex items-center gap-2 pb-3 mb-3 border-b border-gov-border dark:border-slate-800">
              <Brain size={18} className="text-indigo-650" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-750 dark:text-slate-300">Placement Preparation Recommendations</h3>
            </div>
            
            <div className="space-y-4 text-xs">
              <div>
                <p className="font-bold text-slate-700 dark:text-slate-400 uppercase text-[9px] tracking-wider mb-1">Placement Insights</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-slate-200 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-indigo-500 h-full" 
                      style={{ width: `${profile.placement_probability * 100}%` }}
                    />
                  </div>
                  <span className="font-bold">{(profile.placement_probability * 100).toFixed(1)}%</span>
                </div>
              </div>

              <div>
                {profile.ai_recommendations && (() => {
                  let recs = profile.ai_recommendations;
                  if (typeof recs === 'string') {
                    try {
                      recs = JSON.parse(recs);
                    } catch (e) {
                      recs = {};
                    }
                  }
                  const tips = Array.isArray(recs?.improvement_tips) ? recs.improvement_tips : [];
                  if (tips.length === 0) return <p className="text-slate-400 text-[10px]">No specific improvement suggestions currently noted.</p>;
                  return (
                    <ul className="list-disc pl-4 space-y-1.5 text-slate-650 dark:text-slate-350">
                      {tips.map((tip: string, idx: number) => (
                        <li key={idx}>{tip}</li>
                      ))}
                    </ul>
                  );
                })()}

              </div>
            </div>
          </div>

          {/* Drive Eligibility matching status (Req 11) */}
          <div className="gov-card space-y-4">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <Award size={18} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Placement Drive Eligibility</h2>
            </div>

            {!eligibility || eligibility.length === 0 ? (
              <div className="text-center py-6 text-slate-400 text-xs">No active company drives mapped.</div>
            ) : (
              <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2">
                {eligibility.map((el: any, idx: number) => (
                  <div key={idx} className="border border-gov-border dark:border-slate-800 p-3 rounded space-y-2 bg-slate-50 dark:bg-slate-900">
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="font-bold text-slate-850 dark:text-slate-200">{el.company_name}</span>
                      <span className={`px-2 py-0.5 rounded-full font-bold uppercase text-[8px] ${
                        el.is_eligible ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                      }`}>
                        {el.is_eligible ? 'Qualified' : 'Ineligible'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 font-medium">Role: <span className="font-semibold text-slate-700 dark:text-slate-300">{el.role}</span></p>
                    
                    {!el.is_eligible && el.reasons && el.reasons.length > 0 && (
                      <div className="text-[10px] text-red-650 bg-red-50/50 dark:bg-red-950/20 dark:text-red-400 p-1.5 rounded space-y-0.5">
                        <strong className="block text-[8px] uppercase tracking-wide">Eligibility Blocker:</strong>
                        <ul className="list-disc pl-3">
                          {el.reasons.map((r: string, rIdx: number) => (
                            <li key={rIdx}>{r}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Student feedbacks list */}
          <div className="gov-card">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-gov-border dark:border-slate-800">
              <MessageSquare size={18} className="text-gov-blue" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Candidate Feedbacks</h2>
            </div>

            {feedbacks.length === 0 ? (
              <div className="text-center py-6 text-slate-400 text-xs">No feedback forms filed.</div>
            ) : (
              <div className="space-y-4 max-h-[350px] overflow-y-auto pr-2">
                {feedbacks.map((fb: any, idx: number) => (
                  <div key={idx} className="border border-gov-border dark:border-slate-800 p-3 rounded space-y-2 bg-slate-50 dark:bg-slate-900">
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="font-bold text-slate-800 dark:text-slate-200">{fb.company_name}</span>
                      <span className={`px-2 py-0.5 rounded-full font-bold ${
                        fb.sentiment_score > 0.15 ? 'bg-emerald-50 text-emerald-700' :
                        fb.sentiment_score < -0.15 ? 'bg-red-50 text-red-700' :
                        'bg-slate-100 text-slate-600'
                      }`}>
                        Feedback: {fb.sentiment_score > 0.15 ? 'Positive' : fb.sentiment_score < -0.15 ? 'Negative' : 'Neutral'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300">"{fb.experience_text}"</p>
                    <p className="text-[10px] text-slate-400">Difficulty: {fb.difficulty_rating}/5</p>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
};

export default Student360;
