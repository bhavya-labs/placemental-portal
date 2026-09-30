import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { driveService, applicationService, studentService } from '../services/api';
import { CardSkeleton } from '../components/LoadingSkeleton';
import { 
  Briefcase, Check, Calendar, MapPin, Clock, Star, 
  X, HelpCircle, ArrowUpRight, Compass, ShieldAlert, Award
} from 'lucide-react';
import { AccessibleToast } from '../components/AccessibilityComponents';

export const StudentApplications: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [studentDetails, setStudentDetails] = useState<any>(null);
  const [drives, setDrives] = useState<any[]>([]);
  const [applications, setApplications] = useState<any[]>([]);
  const [interviews, setInterviews] = useState<any[]>([]);
  
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [expandedDriveId, setExpandedDriveId] = useState<number | null>(null);

  // Feedback modal states
  const [feedbackInterviewId, setFeedbackInterviewId] = useState<number | null>(null);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackQuestions, setFeedbackQuestions] = useState('');
  const [feedbackDifficulty, setFeedbackDifficulty] = useState(3);
  const [feedbackPrepTime, setFeedbackPrepTime] = useState('1 week');

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const loadData = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const details = await studentService.getStudentById(user.id);
      setStudentDetails(details);

      const activeDrives = await driveService.getDrives('Active');
      setDrives(activeDrives);

      const apps = await applicationService.getStudentApplications(user.id);
      setApplications(apps);

      const ivs = await applicationService.getStudentInterviews(user.id);
      setInterviews(Array.isArray(ivs) ? ivs : []);
    } catch (err) {
      console.error('Failed to load applications data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const handleApply = async (driveId: number) => {
    try {
      await applicationService.apply(driveId);
      showToast('Application successfully registered for this drive!', 'success');
      loadData();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Application submission failed.', 'error');
    }
  };

  const handleWithdraw = async (applicationId: number) => {
    if (!window.confirm('Are you sure you want to withdraw your application for this placement drive?')) {
      return;
    }
    try {
      await applicationService.withdrawApplication(applicationId);
      showToast('Application successfully withdrawn.', 'success');
      loadData();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to withdraw application.', 'error');
    }
  };

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackInterviewId) return;
    try {
      await applicationService.submitFeedback(feedbackInterviewId, {
        experience_text: feedbackText,
        questions_asked: feedbackQuestions,
        difficulty_rating: feedbackDifficulty,
        preparation_time: feedbackPrepTime,
        suggestions: 'Keep practicing DSA questions.'
      });
      showToast('Thank you! Your interview feedback has been submitted successfully.', 'success');
      setFeedbackInterviewId(null);
      setFeedbackText('');
      setFeedbackQuestions('');
      loadData();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to submit experience feedback.', 'error');
    }
  };

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350">
      <AccessibleToast message={toast?.message || null} type={toast?.type || null} />

      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card">
        <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
          <Briefcase className="text-gov-blue" size={24} />
          My Applications & Active Placement Drives
        </h2>
        <p className="text-[10px] text-slate-500 mt-1">
          Apply to open placement drives, check role requirements, and share your interview experiences.
        </p>
      </div>

      {loading || !studentDetails ? <CardSkeleton /> : (
        <div className="grid md:grid-cols-3 gap-6">
          
          {/* Active drives to apply to */}
          <div className="md:col-span-2 space-y-4">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Compass size={18} className="text-gov-blue" />
              Active Institutional Drives
            </h3>

            {drives.length === 0 ? (
              <div className="gov-card text-center py-12 text-slate-400 font-bold uppercase">
                No active placement drives found.
              </div>
            ) : (
              <div className="space-y-4">
                {drives.map((drive) => {
                  const appliedApp = applications.find(a => a.drive_id === drive.id);
                  const isApplied = !!appliedApp;

                  // Check eligibility locally for helper info
                  const allowedDepts = drive.allowed_depts.split(',').map((d: string) => d.trim().toUpperCase());
                  const isDeptEligible = allowedDepts.includes('ALL') || allowedDepts.includes(studentDetails.dept_code.toUpperCase());
                  const isCgpaEligible = studentDetails.cgpa >= drive.cgpa_cutoff;
                  const isBacklogEligible = studentDetails.backlogs <= drive.allowed_backlogs;
                  const isEligible = isDeptEligible && isCgpaEligible && isBacklogEligible;

                  return (
                    <React.Fragment key={drive.id}>
                      <div className={`gov-card flex flex-col sm:flex-row justify-between sm:items-center gap-4 hover:border-slate-350 transition-all ${
                        !isEligible && !isApplied ? 'opacity-75 border-red-200 bg-red-50/10' : ''
                      }`}>
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold text-slate-450 uppercase">{drive.company_name}</span>
                            <span className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded text-[10px] font-bold">
                              {drive.package_lpa} LPA
                            </span>
                          </div>

                          <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase leading-snug">
                            {drive.role}
                          </h4>

                          <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-[10px] text-slate-500">
                            <span className="flex items-center gap-1"><MapPin size={12} /> {drive.location}</span>
                            <span className="flex items-center gap-1"><Clock size={12} /> Cutoff: {drive.cgpa_cutoff} CGPA</span>
                            <span className="flex items-center gap-1"><Calendar size={12} /> Deadline: {drive.deadline}</span>
                          </div>

                          <button
                            onClick={() => setExpandedDriveId(expandedDriveId === drive.id ? null : drive.id)}
                            className="text-[11px] font-bold text-gov-blue dark:text-sky-400 uppercase hover:underline mt-2 inline-block"
                          >
                            {expandedDriveId === drive.id ? 'Hide Details' : 'View Job Specifications'}
                          </button>
                        </div>

                        <div className="shrink-0 flex items-center">
                          {isApplied ? (
                            <div className="text-right">
                              <span className="inline-flex items-center gap-1 px-3 py-1 rounded bg-slate-100 text-slate-850 text-xs font-bold uppercase border border-gov-border">
                                <Check size={12} className="text-emerald-600" /> {appliedApp.status}
                              </span>
                              <p className="text-[10px] text-slate-400 mt-1 uppercase">Round: {appliedApp.current_round}</p>
                              {appliedApp.status === 'Applied' && (
                                <button
                                  onClick={() => handleWithdraw(appliedApp.id)}
                                  className="mt-1 text-[10px] font-semibold text-red-600 hover:text-red-800 hover:underline block ml-auto"
                                >
                                  Withdraw
                                </button>
                              )}
                            </div>
                          ) : !isEligible ? (
                            <div className="text-right">
                              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-red-50 text-red-750 text-[10px] font-bold uppercase border border-red-200">
                                <ShieldAlert size={12} /> Ineligible
                              </span>
                            </div>
                          ) : (
                            <button
                              onClick={() => handleApply(drive.id)}
                              className="gov-btn-primary uppercase text-xs px-4 py-2 font-bold bg-gov-navy border-0 text-white"
                            >
                              Apply Now
                            </button>
                          )}
                        </div>
                      </div>

                      {expandedDriveId === drive.id && (
                        <div className="bg-slate-50 dark:bg-slate-900/60 p-4 border-x border-b border-gov-border dark:border-slate-800 rounded-b-lg -mt-4 text-xs space-y-3 animate-fadeIn">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <h5 className="font-bold text-gov-navy dark:text-sky-400 uppercase">Responsibilities Summary</h5>
                              <p className="text-slate-650 dark:text-slate-400 leading-relaxed mt-1">
                                {drive.responsibilities}
                              </p>
                            </div>
                            <div>
                              <h5 className="font-bold text-gov-navy dark:text-sky-400 uppercase">Recruitment Process</h5>
                              <p className="text-slate-650 dark:text-slate-400 leading-relaxed mt-1">
                                {drive.hiring_process}
                              </p>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 border-t border-slate-200 dark:border-slate-800 pt-3">
                            <div>
                              <span className="font-bold block text-slate-400 uppercase text-[9px]">Job Type</span>
                              <span className="text-slate-700 dark:text-slate-300 font-semibold">{drive.job_type}</span>
                            </div>
                            <div>
                              <span className="font-bold block text-slate-400 uppercase text-[9px]">Work Mode</span>
                              <span className="text-slate-700 dark:text-slate-300 font-semibold">{drive.work_mode}</span>
                            </div>
                            <div>
                              <span className="font-bold block text-slate-400 uppercase text-[9px]">Openings</span>
                              <span className="text-slate-700 dark:text-slate-300 font-semibold">{drive.openings_count} spots</span>
                            </div>
                            <div>
                              <span className="font-bold block text-slate-400 uppercase text-[9px]">Cutoff Criteria</span>
                              <span className="text-slate-700 dark:text-slate-300 font-semibold">&le; {drive.allowed_backlogs} backlogs</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            )}
          </div>

          {/* Feedback & Interviews timeline (Right column) */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Calendar size={18} className="text-gov-blue" />
              Interview Timeline & Feedback
            </h3>

            {/* Submitting experiences feedback card */}
            <div className="gov-card space-y-4">
              <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase">Interview Experiences & Feedback</h4>
              <p className="text-slate-500 leading-relaxed text-[11px]">
                Log feedback from your active or completed interview rounds to compile question guides and prep insights.
              </p>
              
              {interviews.length === 0 ? (
                <div className="p-3 border border-dashed border-gov-border rounded bg-slate-50 dark:bg-slate-950 text-slate-400 text-center text-[10px]">
                  No interview rounds scheduled yet. You can submit feedback once an interview is scheduled.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {interviews.map((iv) => (
                    <div key={iv.id} className="p-2.5 border border-gov-border dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-950 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div>
                        <p className="font-bold text-slate-800 dark:text-slate-200 uppercase">{iv.company_name} — {iv.round_name}</p>
                        <p className="text-[10px] text-slate-500">{iv.role} &bull; Status: {iv.status}</p>
                      </div>
                      {iv.has_feedback ? (
                        <span className="bg-emerald-50 text-emerald-800 border border-emerald-250 px-2.5 py-1 rounded text-[10px] font-bold uppercase self-start sm:self-auto">
                          Feedback Logged
                        </span>
                      ) : (
                        <button
                          onClick={() => setFeedbackInterviewId(iv.id)}
                          className="gov-btn-primary bg-gov-navy hover:bg-slate-800 text-white text-[10px] font-bold uppercase py-1 px-3 rounded shrink-0 self-start sm:self-auto"
                        >
                          Submit Review
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Applications history tracker */}
            <div className="gov-card space-y-3">
              <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase">Application Tracker</h4>
              
              {applications.length === 0 ? (
                <p className="text-slate-400 italic">No job applications filed yet.</p>
              ) : (
                <div className="space-y-2">
                  {applications.map((app) => (
                    <div key={app.id} className="p-2 border border-gov-border dark:border-slate-850 rounded bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
                      <div>
                        <p className="font-bold text-slate-800 dark:text-slate-200 uppercase">{app.company_name}</p>
                        <p className="text-[9px] text-slate-450">{app.role}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-350 px-2 py-0.5 rounded text-[9px] font-bold uppercase">
                          {app.status}
                        </span>
                        {app.status === 'Applied' && (
                          <button
                            onClick={() => handleWithdraw(app.id)}
                            className="px-2 py-0.5 text-[9px] font-bold text-red-600 hover:text-red-800 border border-red-200 hover:border-red-400 rounded uppercase bg-red-50/50"
                            title="Withdraw application"
                          >
                            Withdraw
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>

        </div>
      )}

      {/* FEEDBACK MODAL DIALOG */}
      {feedbackInterviewId && (() => {
        const targetInterview = interviews.find(iv => iv.id === feedbackInterviewId);
        return (
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-6 rounded-lg max-w-md w-full text-xs space-y-4">
              <div className="flex justify-between items-center border-b border-gov-border dark:border-slate-850 pb-3">
                <h4 className="text-sm font-bold text-gov-navy dark:text-slate-200 uppercase">
                  {targetInterview ? `${targetInterview.company_name} (${targetInterview.round_name}) Review` : 'Interview Experience Review'}
                </h4>
                <button onClick={() => setFeedbackInterviewId(null)} className="text-slate-400 hover:text-slate-650">
                  <X size={16} />
                </button>
              </div>
            
            <form onSubmit={handleFeedbackSubmit} className="space-y-4">
              <div>
                <label htmlFor="fb-exp-desc" className="block font-bold text-slate-600 dark:text-slate-400 uppercase">Experience description *</label>
                <textarea
                  id="fb-exp-desc"
                  required
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  className="mt-1 w-full p-2 border border-gov-border rounded h-20 dark:bg-slate-950 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-gov-blue"
                  placeholder="Explain round flow, panel behavior, coding tests, etc."
                />
              </div>
              
              <div>
                <label htmlFor="fb-questions-asked" className="block font-bold text-slate-600 dark:text-slate-400 uppercase">Questions Asked (Comma-Separated) *</label>
                <input
                  id="fb-questions-asked"
                  type="text"
                  required
                  value={feedbackQuestions}
                  onChange={(e) => setFeedbackQuestions(e.target.value)}
                  className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-gov-blue"
                  placeholder="What is Left Join? Reversing LinkedList..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="fb-difficulty" className="block font-bold text-slate-600 dark:text-slate-400 uppercase">Difficulty Rating (1-5)</label>
                  <select
                    id="fb-difficulty"
                    value={feedbackDifficulty}
                    onChange={(e) => setFeedbackDifficulty(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-gov-border rounded bg-white dark:bg-slate-955 focus:outline-none"
                  >
                    <option value="1">1 - Very Easy</option>
                    <option value="2">2 - Easy</option>
                    <option value="3">3 - Moderate</option>
                    <option value="4">4 - Hard</option>
                    <option value="5">5 - Very Hard</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="fb-prep-time" className="block font-bold text-slate-600 dark:text-slate-400 uppercase">Preparation Duration</label>
                  <input
                    id="fb-prep-time"
                    type="text"
                    required
                    value={feedbackPrepTime}
                    onChange={(e) => setFeedbackPrepTime(e.target.value)}
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:text-slate-100 focus:outline-none"
                    placeholder="e.g. 2 weeks"
                  />
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setFeedbackInterviewId(null)} className="gov-btn-secondary py-1.5 px-4 font-semibold text-slate-700 bg-white border border-gov-border">Cancel</button>
                <button type="submit" className="gov-btn-primary py-1.5 px-4 font-semibold text-white bg-gov-navy border-0">Submit feedback</button>
              </div>
            </form>
          </div>
        </div>
      ); })()}

    </div>
  );
};

export default StudentApplications;
