import React, { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { studentService, applicationService, aiService } from '../services/api';
import { CardSkeleton } from '../components/LoadingSkeleton';
import { 
  Award, Brain, Star, Briefcase, ShieldAlert, CheckCircle2, 
  X, FileText, Calendar, ArrowUpRight 
} from 'lucide-react';
import confetti from 'canvas-confetti';

export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [studentDetails, setStudentDetails] = useState<any>(null);
  const [aiReport, setAiReport] = useState<any>(null);
  const [applications, setApplications] = useState<any[]>([]);

  const loadData = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const details = await studentService.getStudentById(user.id);
      setStudentDetails(details);

      const report = await aiService.getStudentReport(user.id);
      setAiReport(report);

      const apps = await applicationService.getStudentApplications(user.id);
      setApplications(apps);

      if (details.status === 'Placed') {
        confetti({
          particleCount: 150,
          spread: 80,
          origin: { y: 0.6 }
        });
      }
    } catch (err) {
      console.error('Failed to load dashboard metrics', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const roundToPercent = (val: number | null | undefined) => {
    if (val === null || val === undefined) return '0%';
    return `${Math.round(val * 100)}%`;
  };

  const getPreparationStanding = () => {
    if (!studentDetails) return { tier: 'In Review', color: 'slate', subtext: 'Evaluating profile' };
    const status = studentDetails.status;
    const backlogs = studentDetails.backlogs ?? 0;
    const cgpa = studentDetails.cgpa ?? 0;
    const attendance = studentDetails.attendance ?? 0;
    const readiness = studentDetails.readiness_score ?? 0;

    // 1. Placed students (status == 'Placed') -> always "On Track"
    if (status === 'Placed') {
      return {
        tier: 'On Track',
        color: 'emerald',
        subtext: 'Placement secured • Keep skills sharp'
      };
    }

    // 2. Unplaced students with hard red flags -> always "Action Recommended"
    if (backlogs > 2 || cgpa < 6.0 || attendance < 75.0) {
      return {
        tier: 'Action Recommended',
        color: 'amber',
        subtext: 'Targeted focus areas identified below'
      };
    }

    // 3. Remaining unplaced+qualified students:
    // Ranked dynamically against unplaced+qualified cohort pool.
    // Top ~15% (percentile >= 85 or readiness >= dynamic 85th percentile cutoff) -> "On Track", rest -> "Making Progress"
    const percentile = aiReport?.cohort_percentile;
    const cutoff = aiReport?.cohort_readiness_cutoff ?? 87.14;

    const isTopTier = percentile !== undefined && percentile !== null
      ? percentile >= 85.0
      : readiness >= cutoff;

    if (isTopTier) {
      return {
        tier: 'On Track',
        color: 'emerald',
        subtext: 'Top cohort standing • Strong profile for upcoming drives'
      };
    }

    return {
      tier: 'Making Progress',
      color: 'blue',
      subtext: 'Steady path • Follow recommended actions'
    };
  };

  const standing = getPreparationStanding();

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350">
      
      {/* Welcome banner */}
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card">
        <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
          <Brain className="text-gov-blue" size={24} />
          Student Career Workspace
        </h2>
        <p className="text-[10px] text-slate-500 mt-1">
          Welcome back, {studentDetails?.name || user?.name || 'Student'}. Track your placement preparation, explore personalized recommendations, and apply for open campus drives.
        </p>
      </div>

      {loading || !studentDetails || !aiReport ? <CardSkeleton /> : (
        <>
          {/* KPI metrics row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="gov-card flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Cumulative CGPA</p>
                <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">{studentDetails.cgpa}</p>
                <p className="text-[10px] text-slate-500 mt-1">Active Backlogs: {studentDetails.backlogs}</p>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                <Award size={20} />
              </div>
            </div>

            <div className="gov-card flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Placement Preparation Score</p>
                <div className="flex items-baseline gap-1 mt-1">
                  <p className="text-2xl font-bold text-gov-navy dark:text-slate-200">{studentDetails.readiness_score}</p>
                  <span className="text-[10px] text-slate-500">/100</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-1">Profile Complete: {studentDetails.profile_completed ? '100%' : 'Partial'}</p>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                <Brain size={20} />
              </div>
            </div>

            <div className="gov-card flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Preparation Standing</p>
                <div className="mt-1 flex items-center gap-1.5">
                  <span className={`inline-block w-2.5 h-2.5 rounded-full ${
                    standing.color === 'emerald' ? 'bg-emerald-500' :
                    standing.color === 'blue' ? 'bg-blue-500' : 'bg-amber-500'
                  }`} />
                  <p className="text-xl font-bold text-gov-navy dark:text-slate-200">
                    {standing.tier}
                  </p>
                </div>
                <p className="text-[10px] text-slate-500 mt-1">{standing.subtext}</p>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                <Star size={20} />
              </div>
            </div>

            <div className="gov-card flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Active Applications</p>
                <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">{applications.length}</p>
                <p className="text-[10px] text-slate-500 mt-1">Status: Process Running</p>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                <Briefcase size={20} />
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            
            {/* AI Explanation block & Warnings (Left) */}
            <div className="md:col-span-2 space-y-6">
              
              {aiReport.at_risk && (
                <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900 rounded-lg p-5 flex items-start gap-4">
                  <ShieldAlert size={24} className="text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-bold text-amber-800 dark:text-amber-400 uppercase tracking-wider">Your Placement Preparation Needs Attention</h4>
                    <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                      Here are the key areas that could improve your recruitment prospects: <span className="font-semibold">{aiReport.risk_reason || 'adding hands-on projects and strengthening core technical skills'}</span>. Explore the action items below to boost your preparation.
                    </p>
                  </div>
                </div>
              )}

              {/* Status Box */}
              {studentDetails.status === 'Placed' && (
                <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-250 dark:border-emerald-900 rounded-lg p-5 flex items-start gap-4">
                  <CheckCircle2 size={24} className="text-emerald-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-bold text-emerald-800 dark:text-emerald-400 uppercase tracking-wider">Congratulations! Candidate Status: Placed</h4>
                    <p className="text-xs text-emerald-700 dark:text-emerald-300 mt-1">
                      You have successfully secured an institutional offer block! Keep learning and preparation schedules active for upcoming premium packages.
                    </p>
                  </div>
                </div>
              )}

              {/* AI Details */}
              <div className="gov-card space-y-4">
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <Brain size={18} className="text-gov-blue" />
                  Placement Preparation Analysis
                </h3>
                <p className="text-xs text-slate-650 dark:text-slate-450 leading-relaxed bg-slate-50 dark:bg-slate-950 p-4 rounded border border-gov-border dark:border-slate-850">
                  {aiReport.explanation}
                </p>

                {/* Profile quality metrics list */}
                <div className="space-y-3 pt-2">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-350 uppercase">Your Preparation Checklist</h4>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="flex items-center gap-2">
                      {studentDetails.cgpa >= 7.5 ? (
                        <CheckCircle2 size={14} className="text-emerald-500 shrink-0" />
                      ) : (
                        <X size={14} className="text-red-500 shrink-0" />
                      )}
                      <span>Good academic standing (CGPA &ge; 7.5)</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {studentDetails.attendance >= 80 ? (
                        <CheckCircle2 size={14} className="text-emerald-500 shrink-0" />
                      ) : (
                        <X size={14} className="text-red-500 shrink-0" />
                      )}
                      <span>Consistent attendance (&ge; 80%)</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {(() => {
                        const skillsLen = Array.isArray(studentDetails.skills)
                          ? studentDetails.skills.length
                          : (typeof studentDetails.skills === 'string'
                              ? (studentDetails.skills.startsWith('[') ? (JSON.parse(studentDetails.skills) || []).length : studentDetails.skills.split(',').filter(Boolean).length)
                              : 0);
                        return (
                          <>
                            {skillsLen >= 6 ? (
                              <CheckCircle2 size={14} className="text-emerald-500 shrink-0" />
                            ) : (
                              <X size={14} className="text-red-500 shrink-0" />
                            )}
                            <span>Technical skills listed ({skillsLen} of 6 recommended)</span>
                          </>
                        );
                      })()}
                    </div>

                    <div className="flex items-center gap-2">
                      {studentDetails.backlogs === 0 ? (
                        <CheckCircle2 size={14} className="text-emerald-500 shrink-0" />
                      ) : (
                        <X size={14} className="text-red-500 shrink-0" />
                      )}
                      <span>All subjects cleared (0 active backlogs)</span>
                    </div>
                  </div>
                </div>
              </div>

            </div>

            {/* Resume scan gauge (Right) */}
            <div className="gov-card h-fit space-y-4">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <FileText size={18} className="text-gov-blue" />
                Resume Completeness
              </h3>

              <div className="flex flex-col items-center justify-center py-4 space-y-2">
                <div className="relative flex items-center justify-center">
                  <svg className="w-24 h-24">
                    <circle className="text-slate-200 dark:text-slate-800" strokeWidth="6" stroke="currentColor" fill="transparent" r="40" cx="48" cy="48" />
                    <circle className="text-gov-blue" strokeWidth="6" strokeDasharray={251.2} strokeDashoffset={251.2 - (251.2 * aiReport.resume_quality.score) / 100} strokeLinecap="round" stroke="currentColor" fill="transparent" r="40" cx="48" cy="48" />
                  </svg>
                  <span className="absolute text-xl font-extrabold text-gov-navy dark:text-slate-100">{aiReport.resume_quality.score}%</span>
                </div>
                <p className="text-xs text-slate-500 font-bold uppercase">Resume Completeness</p>
              </div>

              <div className="space-y-2 border-t border-gov-border dark:border-slate-850 pt-3">
                <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase">Suggestions to Strengthen Your Resume</h4>
                <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-1.5 list-disc pl-4">
                  {aiReport.resume_quality.suggestions && aiReport.resume_quality.suggestions.map((sug: string, i: number) => (
                    <li key={i}>{sug}</li>
                  ))}
                </ul>
              </div>
            </div>

          </div>
        </>
      )}

    </div>
  );
};

export default StudentDashboard;
