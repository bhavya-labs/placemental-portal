import React, { useState, useEffect } from 'react';
import { aiService } from '../services/api';
import { 
  Brain, Star, Smile, Meh, Frown, AlertCircle, X, CheckCircle2, 
  HelpCircle, Lightbulb, ShieldAlert, Users, BookOpen, Layers,
  MessageSquare, Award, Check
} from 'lucide-react';

interface DriveFeedbackReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  driveId: number | null;
  driveTitle?: string;
}

export const DriveFeedbackReportModal: React.FC<DriveFeedbackReportModalProps> = ({
  isOpen,
  onClose,
  driveId,
  driveTitle
}) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && driveId) {
      fetchReport(driveId);
    } else {
      setData(null);
      setError(null);
    }
  }, [isOpen, driveId]);

  const fetchReport = async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await aiService.getDriveFeedbackSummary(id);
      setData(res);
    } catch (err: any) {
      console.error('Failed to fetch drive feedback report', err);
      setError(err.response?.data?.detail || 'Failed to retrieve aggregated drive feedback.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="feedback-modal-title"
      className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-3 sm:p-4 animate-fadeIn"
    >
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 rounded-lg shadow-premium max-w-4xl w-full flex flex-col max-h-[92vh] text-xs text-slate-700 dark:text-slate-350">
        
        {/* Modal Header */}
        <header className="p-4 border-b border-gov-border dark:border-slate-800 flex items-center justify-between bg-slate-50/70 dark:bg-slate-950/70">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-gov-blue/10 text-gov-blue dark:text-gov-accent shrink-0">
              <Brain size={20} />
            </div>
            <div>
              <h3 id="feedback-modal-title" className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide">
                Consolidated Placement Drive Feedback Report
              </h3>
              <p className="text-[11px] text-slate-500 font-medium">
                {data?.company_name ? `${data.company_name} — ${data.role}` : driveTitle || 'Aggregated Interview Feedback'}
                {data?.package_lpa ? ` • ${data.package_lpa} LPA` : ''}
                {data?.location ? ` • ${data.location}` : ''}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="text-slate-400 hover:text-slate-600 dark:hover:text-white p-1 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
          >
            <X size={18} />
          </button>
        </header>

        {/* Modal Body */}
        <div className="flex-1 p-5 overflow-y-auto space-y-6">
          {loading ? (
            <div className="py-20 text-center space-y-3">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gov-blue border-t-transparent"></div>
              <p className="font-bold text-slate-700 dark:text-slate-300 text-xs">
                Compiling and aggregating student interview feedback records...
              </p>
              <p className="text-[10px] text-slate-400">
                Consolidating questions, topics, difficulty ratings, and candidate suggestions.
              </p>
            </div>
          ) : error ? (
            <div className="p-5 rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-400 space-y-3 text-center">
              <div className="flex items-center justify-center gap-2 font-bold text-sm">
                <AlertCircle size={18} />
                Failed to load consolidated feedback report
              </div>
              <p className="text-xs">{error}</p>
              <button
                onClick={() => driveId && fetchReport(driveId)}
                className="px-4 py-1.5 bg-gov-navy text-white rounded text-xs font-semibold hover:bg-slate-800 transition"
              >
                Retry
              </button>
            </div>
          ) : !data ? null : (!data.has_feedback || data.total_feedbacks === 0) ? (
            /* Clean Empty State: No feedback recorded for this drive */
            <div className="py-12 px-6 text-center space-y-4">
              <div className="mx-auto w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400">
                <MessageSquare size={24} />
              </div>
              <div className="space-y-1">
                <h4 className="font-bold text-slate-800 dark:text-slate-200 text-sm uppercase tracking-wide">
                  No Feedback Logged Yet
                </h4>
                <p className="text-slate-500 dark:text-slate-400 text-xs max-w-md mx-auto">
                  {data.message || 'No candidate interview feedback records have been logged for this recruitment drive yet.'}
                </p>
              </div>

              {data.participation && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-w-lg mx-auto pt-4 border-t border-gov-border dark:border-slate-800">
                  <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded border border-gov-border dark:border-slate-800 text-center">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase">Registered Applicants</span>
                    <span className="text-base font-black text-slate-700 dark:text-slate-200">{data.participation.total_applicants}</span>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded border border-gov-border dark:border-slate-800 text-center">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase">Interview Attendees</span>
                    <span className="text-base font-black text-slate-700 dark:text-slate-200">{data.participation.attended_students_count}</span>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded border border-gov-border dark:border-slate-800 text-center col-span-2 sm:col-span-1">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase">Feedback Submissions</span>
                    <span className="text-base font-black text-slate-700 dark:text-slate-200">0</span>
                  </div>
                </div>
              )}

              <div className="pt-2">
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded font-semibold text-xs"
                >
                  Close
                </button>
              </div>
            </div>
          ) : (
            /* Consolidated Report with all 7 Required Sections */
            <div className="space-y-6">

              {/* Preliminary warning if < 5 feedbacks */}
              {data.total_feedbacks < 5 && (
                <div className="p-3 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 rounded-lg flex items-center gap-2.5 text-amber-800 dark:text-amber-300 text-[11px]">
                  <AlertCircle size={16} className="shrink-0 text-amber-600 dark:text-amber-400" />
                  <span>
                    <strong>Preliminary Feedback Report:</strong> Aggregated from {data.total_feedbacks} candidate submissions. Analysis will become statistically comprehensive as additional students log feedback.
                  </span>
                </div>
              )}

              {/* SECTION 1: PARTICIPATION METRICS */}
              <div className="space-y-2">
                <h4 className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Users size={14} className="text-gov-blue" />
                  1. Participation & Candidate Engagement
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="bg-slate-50 dark:bg-slate-950 border border-gov-border dark:border-slate-800 p-3 rounded-lg">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Interview Attendees</span>
                    <span className="text-xl font-black text-gov-navy dark:text-slate-100 mt-0.5 block">
                      {data.participation?.attended_students_count ?? data.total_feedbacks}
                    </span>
                    <span className="text-[10px] text-slate-500">Participating candidates</span>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-950 border border-gov-border dark:border-slate-800 p-3 rounded-lg">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Feedback Responses</span>
                    <span className="text-xl font-black text-gov-navy dark:text-slate-100 mt-0.5 block">
                      {data.total_feedbacks}
                    </span>
                    <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">Logged submissions</span>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-950 border border-gov-border dark:border-slate-800 p-3 rounded-lg">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Response Rate</span>
                    <span className="text-xl font-black text-gov-navy dark:text-slate-100 mt-0.5 block">
                      {data.participation?.response_rate_pct ?? 100}%
                    </span>
                    <span className="text-[10px] text-slate-500">Of interviewed students</span>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-950 border border-gov-border dark:border-slate-800 p-3 rounded-lg">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Applied</span>
                    <span className="text-xl font-black text-gov-navy dark:text-slate-100 mt-0.5 block">
                      {data.participation?.total_applicants ?? data.total_feedbacks}
                    </span>
                    <span className="text-[10px] text-slate-500">Drive applicants</span>
                  </div>
                </div>
              </div>

              {/* SECTION 2: OVERALL INTERVIEW EXPERIENCE */}
              <div className="space-y-2">
                <h4 className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Star size={14} className="text-amber-500" />
                  2. Overall Interview Experience
                </h4>
                
                {data.experience_summary && (
                  <div className="p-3.5 bg-gov-blue/5 border border-gov-blue/20 rounded-lg text-slate-700 dark:text-slate-300 text-xs leading-relaxed font-medium">
                    {data.experience_summary}
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Rating Score */}
                  <div className="bg-slate-50 dark:bg-slate-950 border border-gov-border dark:border-slate-800 p-3.5 rounded-lg flex items-center justify-between">
                    <div>
                      <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Average Candidate Rating</span>
                      <div className="flex items-baseline gap-1.5 mt-1">
                        <span className="text-2xl font-black text-gov-navy dark:text-slate-100">{data.average_rating || 3.0}</span>
                        <span className="text-slate-400 text-xs font-semibold">/ 5.0</span>
                      </div>
                    </div>
                    <div className="flex gap-0.5 text-amber-500">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star key={i} size={14} fill={i < Math.round(data.average_rating || 3) ? 'currentColor' : 'none'} />
                      ))}
                    </div>
                  </div>

                  {/* Feedback Tone Distribution */}
                  <div className="bg-slate-50 dark:bg-slate-950 border border-gov-border dark:border-slate-800 p-3.5 rounded-lg space-y-2">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Overall Feedback Tone</span>
                    <div className="flex justify-between text-[11px] font-bold">
                      <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                        <Smile size={12} /> Positive: {data.sentiment_summary?.positive_pct ?? 0}%
                      </span>
                      <span className="text-amber-600 dark:text-amber-400 flex items-center gap-1">
                        <Meh size={12} /> Neutral: {data.sentiment_summary?.neutral_pct ?? 0}%
                      </span>
                      <span className="text-red-600 dark:text-red-400 flex items-center gap-1">
                        <Frown size={12} /> Negative: {data.sentiment_summary?.negative_pct ?? 0}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden flex">
                      <div className="bg-emerald-500" style={{ width: `${data.sentiment_summary?.positive_pct || 0}%` }}></div>
                      <div className="bg-amber-400" style={{ width: `${data.sentiment_summary?.neutral_pct || 0}%` }}></div>
                      <div className="bg-red-500" style={{ width: `${data.sentiment_summary?.negative_pct || 0}%` }}></div>
                    </div>
                  </div>
                </div>

                {/* Common Observations / Themes */}
                {data.themes && data.themes.length > 0 && (
                  <div className="border border-gov-border dark:border-slate-800 rounded-lg p-3 bg-white dark:bg-slate-900 space-y-2">
                    <span className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider">Common Observations</span>
                    <div className="grid sm:grid-cols-2 gap-2">
                      {data.themes.map((theme: any, idx: number) => (
                        <div key={idx} className="p-2.5 rounded border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 space-y-1">
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-slate-800 dark:text-slate-200 text-[11px]">{theme.theme}</span>
                            <span className="bg-slate-200 dark:bg-slate-800 px-1.5 py-0.2 rounded text-[9px] font-bold text-slate-600 dark:text-slate-350">
                              {theme.student_count} candidates
                            </span>
                          </div>
                          <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-snug">{theme.consolidated_explanation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* SECTION 3: DIFFICULTY DISTRIBUTION */}
              <div className="space-y-2">
                <h4 className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Layers size={14} className="text-gov-blue" />
                  3. Interview Difficulty Distribution
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3 rounded-lg border border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/40 dark:bg-emerald-950/20">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-bold uppercase text-emerald-800 dark:text-emerald-300">Easy (1-2)</span>
                      <span className="font-bold text-emerald-600 text-xs">
                        {data.difficulty_distribution?.easy_pct ?? 0}%
                      </span>
                    </div>
                    <span className="text-xl font-black text-emerald-700 dark:text-emerald-300 block mt-1">
                      {data.difficulty_distribution?.easy ?? 0} candidates
                    </span>
                  </div>

                  <div className="p-3 rounded-lg border border-amber-200 dark:border-amber-900/40 bg-amber-50/40 dark:bg-amber-950/20">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-bold uppercase text-amber-800 dark:text-amber-300">Moderate (3)</span>
                      <span className="font-bold text-amber-600 text-xs">
                        {data.difficulty_distribution?.moderate_pct ?? 0}%
                      </span>
                    </div>
                    <span className="text-xl font-black text-amber-700 dark:text-amber-300 block mt-1">
                      {data.difficulty_distribution?.moderate ?? 0} candidates
                    </span>
                  </div>

                  <div className="p-3 rounded-lg border border-red-200 dark:border-red-900/40 bg-red-50/40 dark:bg-red-950/20">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-bold uppercase text-red-800 dark:text-red-300">Difficult (4-5)</span>
                      <span className="font-bold text-red-600 text-xs">
                        {data.difficulty_distribution?.difficult_pct ?? 0}%
                      </span>
                    </div>
                    <span className="text-xl font-black text-red-700 dark:text-red-300 block mt-1">
                      {data.difficulty_distribution?.difficult ?? 0} candidates
                    </span>
                  </div>
                </div>
              </div>

              {/* SECTION 4: COMMON INTERVIEW AREAS */}
              {data.common_interview_areas && data.common_interview_areas.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <BookOpen size={14} className="text-gov-blue" />
                    4. Common Interview Domains & Core Subject Areas
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {data.common_interview_areas.map((area: any, idx: number) => (
                      <div 
                        key={idx} 
                        className="p-2.5 rounded border border-gov-border dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between"
                      >
                        <span className="font-bold text-slate-800 dark:text-slate-200 text-[11px] truncate" title={area.area}>
                          {area.area}
                        </span>
                        <span className="bg-gov-blue/10 text-gov-blue dark:text-gov-accent px-1.5 py-0.5 rounded text-[9px] font-bold shrink-0">
                          {area.count} ({area.percentage}%)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* SECTION 5: TOPICS ASKED */}
              {data.topic_distribution && data.topic_distribution.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Layers size={14} className="text-gov-blue" />
                    5. Aggregate Topics Reported by Students
                  </h4>
                  <div className="border border-gov-border dark:border-slate-800 rounded-lg p-3 bg-white dark:bg-slate-900 space-y-2">
                    <div className="grid sm:grid-cols-2 gap-2">
                      {data.topic_distribution.map((item: any, idx: number) => (
                        <div 
                          key={idx} 
                          className="flex items-center justify-between p-2 rounded bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-850"
                        >
                          <span className="font-medium text-slate-700 dark:text-slate-300 text-[11px]">{item.topic}</span>
                          <span className="bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded font-bold text-[9px]">
                            {item.count} {item.count === 1 ? 'mention' : 'mentions'} ({item.percentage}%)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* SECTION 6: COMMONLY REPORTED QUESTIONS ASKED */}
              <div className="space-y-2">
                <h4 className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <HelpCircle size={14} className="text-gov-blue" />
                  6. Frequently Asked Interview Questions (Normalized & Grouped)
                </h4>
                {(!data.top_questions || data.top_questions.length === 0) ? (
                  <p className="text-slate-400 italic py-3 text-center border border-dashed border-gov-border rounded">
                    No specific questions extracted from feedback records.
                  </p>
                ) : (
                  <div className="grid sm:grid-cols-2 gap-2.5">
                    {data.top_questions.map((item: any, idx: number) => (
                      <div 
                        key={idx} 
                        className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between gap-2 shadow-xs"
                      >
                        <span className="font-medium text-slate-800 dark:text-slate-200 leading-snug">
                          {item.question}
                        </span>
                        <span className="bg-gov-blue/10 text-gov-blue dark:text-gov-accent font-bold px-2 py-0.5 rounded text-[9px] shrink-0">
                          {item.count} {item.count === 1 ? 'mention' : 'mentions'} ({item.frequency_pct}%)
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* SECTION 7: STUDENT EXPERIENCES & SUGGESTIONS */}
              <div className="space-y-3">
                <h4 className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Lightbulb size={14} className="text-amber-500" />
                  7. Consolidated Candidate Experiences & Preparation Advice
                </h4>

                {/* Senior Advice & Actionable Tips */}
                {data.senior_advice && data.senior_advice.length > 0 && (
                  <div className="border border-gov-border dark:border-slate-800 rounded-lg p-3 bg-white dark:bg-slate-900 space-y-2">
                    <span className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                      Preparation Suggestions for Upcoming Batches
                    </span>
                    <div className="space-y-2">
                      {data.senior_advice.map((item: any, idx: number) => (
                        <div 
                          key={idx} 
                          className="p-2.5 rounded border border-amber-100 dark:border-amber-950/40 bg-amber-50/20 dark:bg-amber-950/10 flex items-start gap-2"
                        >
                          <span className="text-amber-500 font-bold text-sm leading-none shrink-0">&bull;</span>
                          <div className="flex-1">
                            <p className="font-medium text-slate-700 dark:text-slate-300">{item.advice}</p>
                            {item.mentions > 1 && (
                              <span className="text-[9px] text-slate-400 font-semibold uppercase">
                                Recommended by {item.mentions} candidates
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reported Blockers & Critical Prep Areas */}
                {data.common_bottlenecks && data.common_bottlenecks.length > 0 && (
                  <div className="border border-gov-border dark:border-slate-800 rounded-lg p-3 bg-white dark:bg-slate-900 space-y-2">
                    <span className="block text-[10px] font-bold text-red-600 dark:text-red-400 uppercase tracking-wider">
                      Reported Interview Hurdles & Technical Weak Points
                    </span>
                    <div className="space-y-1.5">
                      {data.common_bottlenecks.map((bot: any, idx: number) => (
                        <div 
                          key={idx} 
                          className="p-2 rounded border border-red-100 dark:border-red-950/40 bg-red-50/30 dark:bg-red-950/10 flex items-center justify-between"
                        >
                          <span className="font-semibold text-slate-800 dark:text-slate-200 text-[11px]">{bot.bottleneck}</span>
                          <span className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 font-bold px-2 py-0.5 rounded text-[9px]">
                            {bot.count} {bot.count === 1 ? 'candidate' : 'candidates'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Privacy Footer */}
              <div className="p-3 rounded-lg border border-gov-border dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 flex items-center gap-2 text-slate-500 text-[10px]">
                <ShieldAlert size={14} className="text-gov-blue shrink-0" />
                <span>
                  Institutional Privacy Guarantee: Individual candidate identities and roll numbers are anonymized in aggregated feedback reports.
                </span>
              </div>

              {/* Close Button */}
              <div className="flex justify-end pt-2">
                <button
                  onClick={onClose}
                  className="px-5 py-2 rounded font-bold uppercase text-[11px] bg-gov-navy hover:bg-slate-800 text-white transition shadow-sm"
                >
                  Close Report
                </button>
              </div>

            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default DriveFeedbackReportModal;
