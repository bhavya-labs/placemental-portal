import React, { useState, useEffect } from 'react';
import { aiService, driveService } from '../services/api';
import { CardSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import { 
  Brain, Smile, Meh, Frown, BookOpen, Users, HelpCircle, 
  MessageSquare, Star, Search, Filter, ArrowUpRight 
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { AccessibleChart } from '../components/AccessibilityComponents';
import { ProfessionalTable } from '../components/ProfessionalTable';
import { DriveFeedbackReportModal } from '../components/DriveFeedbackReportModal';

export const AISentimentMiner: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [sentimentData, setSentimentData] = useState<any | null>(null);
  const [feedbackRows, setFeedbackRows] = useState<any[]>([]);
  const [difficultyFilter, setDifficultyFilter] = useState<string>('');
  const [sentimentFilter, setSentimentFilter] = useState<string>('');
  const [drivesList, setDrivesList] = useState<any[]>([]);
  const [selectedDriveId, setSelectedDriveId] = useState<string>('');
  const [reportModalDriveId, setReportModalDriveId] = useState<number | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sentRes, drives, rows] = await Promise.all([
        aiService.getFeedbackSentiment().catch(() => null),
        driveService.getDrives().catch(() => []),
        aiService.getFeedbacks().catch(() => [])
      ]);
      setSentimentData(sentRes);
      setDrivesList(drives);
      setFeedbackRows(Array.isArray(rows) ? rows : []);
    } catch (err) {
      console.error('Failed to load feedback analytics metrics', err);
      setFeedbackRows([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const selectedDrive = drivesList.find(d => String(d.id) === selectedDriveId);

  // Filter feedback rows based on select tags & drive focus
  const filteredFeedbacks = feedbackRows.filter(row => {
    const matchesDrive = !selectedDrive || 
      (row.company_name?.toLowerCase() === selectedDrive.company_name?.toLowerCase() &&
       row.role?.toLowerCase() === selectedDrive.role?.toLowerCase());
    const matchesDiff = difficultyFilter === '' || row.difficulty_rating.toString() === difficultyFilter;
    let matchesSent = true;
    if (sentimentFilter === 'positive') matchesSent = row.sentiment_score > 0.15;
    else if (sentimentFilter === 'negative') matchesSent = row.sentiment_score < -0.15;
    else if (sentimentFilter === 'neutral') matchesSent = row.sentiment_score >= -0.15 && row.sentiment_score <= 0.15;
    return matchesDrive && matchesDiff && matchesSent;
  });

  // Recharts colors
  const COLORS = ['#0F2942', '#328CC1', '#D9B310', '#B45309', '#0D9488', '#4F46E5'];

  // Table columns for student feedbacks
  const feedbackColumns = [
    { header: 'Student', accessor: 'student_name' },
    { header: 'Company', accessor: 'company_name' },
    { header: 'Role', accessor: 'role', render: (row: any) => <span className="font-semibold uppercase text-[10px]">{row.role}</span> },
    { header: 'Difficulty', accessor: 'difficulty_rating', render: (row: any) => (
      <div className="flex gap-0.5 text-amber-500">
        {Array.from({ length: 5 }).map((_, i) => (
          <Star key={i} size={10} fill={i < row.difficulty_rating ? 'currentColor' : 'none'} />
        ))}
      </div>
    )},
    { header: 'Feedback Tone', accessor: 'sentiment_score', render: (row: any) => (
      <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
        row.sentiment_score > 0.15 
          ? 'bg-emerald-50 text-emerald-800 border border-emerald-250' 
          : row.sentiment_score < -0.15 
            ? 'bg-red-50 text-red-800 border border-red-250' 
            : 'bg-amber-50 text-amber-800 border border-amber-250'
      }`}>
        {row.sentiment_score > 0.15 ? 'Positive' : row.sentiment_score < -0.15 ? 'Negative' : 'Neutral'}
      </span>
    )},
    { header: 'Extracted Topic', accessor: 'topic_analysis' },
    { header: 'Date', accessor: 'created_at' }
  ];

  // Derive technical FAQs dynamically from real feedback records
  const dynamicFAQs = React.useMemo(() => {
    const counts: Record<string, { count: number; tag: string }> = {};
    feedbackRows.forEach((fb: any) => {
      if (fb.questions_asked) {
        const parts = String(fb.questions_asked)
          .split(/[,;\n]+/)
          .map((s: string) => s.trim())
          .filter((s: string) => s.length >= 5);
        parts.forEach((p: string) => {
          if (!counts[p]) {
            counts[p] = { count: 0, tag: fb.topic_analysis || 'Technical' };
          }
          counts[p].count += 1;
        });
      }
    });
    return Object.entries(counts)
      .map(([q, val]) => ({ q, frequency: val.count, tag: val.tag }))
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 5);
  }, [feedbackRows]);

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350">
      
      {/* Header section */}
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
            <Brain className="text-gov-blue" size={24} />
            Student Interview Feedback Analysis
          </h2>
          <p className="text-[10px] text-slate-500 mt-1">
            Real-time analysis of student interview reviews, topic distributions, and technical blockers.
          </p>
        </div>

        {/* Filter by Placement Drive */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 w-full md:w-auto">
          <label htmlFor="drive-focus-filter" className="text-[10px] font-bold text-slate-500 uppercase shrink-0">
            Scope / Drive:
          </label>
          <select
            id="drive-focus-filter"
            value={selectedDriveId}
            onChange={(e) => setSelectedDriveId(e.target.value)}
            className="border border-gov-border rounded p-1.5 bg-white text-slate-700 dark:bg-slate-950 dark:text-slate-200 text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue w-full sm:w-64"
          >
            <option value="">All Placement Drives (Global Overview)</option>
            {drivesList.map((d: any) => (
              <option key={d.id} value={d.id}>
                {d.company_name} — {d.role} (#{d.id})
              </option>
            ))}
          </select>
          {selectedDriveId && (
            <button
              onClick={() => setReportModalDriveId(Number(selectedDriveId))}
              className="gov-btn-primary py-1.5 px-3 rounded uppercase font-bold text-[10px] flex items-center gap-1.5 bg-gov-navy hover:bg-slate-800 text-white shrink-0 shadow-sm"
              title="View Aggregated Drive Intelligence"
            >
              <Brain size={13} /> View Feedback Summary
            </button>
          )}
        </div>
      </div>

      {/* Selected Drive Focus Banner */}
      {selectedDrive && (
        <div className="bg-gov-blue/5 border border-gov-blue/20 rounded-lg p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-gov-blue/10 text-gov-blue dark:text-gov-accent">
              <Brain size={20} />
            </div>
            <div>
              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Filtered Recruitment Drive Focus</span>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase">
                {selectedDrive.company_name} — {selectedDrive.role}
              </h3>
              <p className="text-[10px] text-slate-500">
                Salary: {selectedDrive.package_lpa} LPA &bull; Status: {selectedDrive.status} &bull; Batch: {selectedDrive.batch}
              </p>
            </div>
          </div>
          <button
            onClick={() => setReportModalDriveId(selectedDrive.id)}
            className="gov-btn-primary py-1.5 px-3.5 rounded font-bold uppercase text-[10px] flex items-center gap-1.5 bg-gov-navy hover:bg-slate-800 text-white shadow-sm"
          >
            <Brain size={13} /> Open Interview Feedback Report
          </button>
        </div>
      )}

      {loading || !sentimentData ? <CardSkeleton /> : (
        <>
          {/* Sentiment polarities dashboard row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <div className="gov-card flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Average Interview Difficulty</p>
                <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">
                  {sentimentData.average_difficulty} / 5.0
                </p>
                <p className="text-[10px] text-slate-500 mt-1">Scale: 1 (Easy) to 5 (Hard)</p>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                <BookOpen size={20} />
              </div>
            </div>

            <div className="gov-card flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Feedbacks Analyzed</p>
                <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">
                  {sentimentData.total_feedbacks} logs
                </p>
                <p className="text-[10px] text-slate-500 mt-1">Processed from Student Feedbacks</p>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                <Users size={20} />
              </div>
            </div>

            <div className="gov-card flex flex-col justify-between">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Feedback Distribution Ratio</p>
              <div className="space-y-1.5 text-[10px]">
                <div className="flex justify-between font-bold text-slate-600 dark:text-slate-350">
                  <span className="flex items-center gap-1"><Smile size={12} className="text-emerald-500" /> Positive: {sentimentData.sentiment_summary.positive_pct}%</span>
                  <span className="flex items-center gap-1"><Meh size={12} className="text-amber-500" /> Neutral: {sentimentData.sentiment_summary.neutral_pct}%</span>
                  <span className="flex items-center gap-1"><Frown size={12} className="text-red-500" /> Negative: {sentimentData.sentiment_summary.negative_pct}%</span>
                </div>
                
                <div className="w-full bg-slate-200 h-2 rounded overflow-hidden flex">
                  <div className="bg-emerald-500" style={{ width: `${sentimentData.sentiment_summary.positive_pct}%` }}></div>
                  <div className="bg-amber-400" style={{ width: `${sentimentData.sentiment_summary.neutral_pct}%` }}></div>
                  <div className="bg-red-500" style={{ width: `${sentimentData.sentiment_summary.negative_pct}%` }}></div>
                </div>
              </div>
            </div>

          </div>

          {/* Word cloud and Rejection bottlenecks */}
          <div className="grid md:grid-cols-2 gap-6">
            
            {/* Dynamic CSS Word Cloud */}
            <div className="gov-card space-y-4">
              <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider border-b border-gov-border dark:border-slate-850 pb-2">
                Student Interview Keyword Tag Cloud
              </h3>
              <p className="text-[10px] text-slate-500 leading-normal">
                Frequency count of core concepts mentioned in technical rounds. Font sizes correspond to occurrences count.
              </p>
              <div className="border border-gov-border dark:border-slate-850 rounded p-6 bg-slate-50 dark:bg-slate-950 flex flex-wrap gap-x-4 gap-y-3 justify-center items-center h-48 overflow-y-auto">
                {sentimentData.word_cloud && sentimentData.word_cloud.map((w: any, idx: number) => {
                  const sizes = ['text-[10px]', 'text-[11px]', 'text-xs', 'text-sm', 'text-base', 'text-lg', 'text-xl'];
                  const fontClass = sizes[Math.min(Math.floor(w.value / 2), sizes.length - 1)];
                  const colors = ['text-slate-500', 'text-slate-700', 'text-gov-blue', 'text-gov-navy', 'text-sky-500'];
                  const colorClass = colors[idx % colors.length];
                  return (
                    <span 
                      key={idx} 
                      className={`${fontClass} ${colorClass} font-bold capitalize select-none cursor-help hover:underline`} 
                      title={`Mentioned ${w.value} times`}
                    >
                      {w.text}
                    </span>
                  );
                })}
              </div>
            </div>

            {/* Top 5 bottlenecks */}
            <div className="gov-card space-y-4">
              <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider border-b border-gov-border dark:border-slate-850 pb-2">
                Top 5 Interview Blockers & Skill Improvement Areas
              </h3>
              <p className="text-[10px] text-slate-500 leading-normal">
                Technical areas where student evaluations indicated interview blockers.
              </p>
              
              <div className="space-y-3">
                {sentimentData.common_bottlenecks && sentimentData.common_bottlenecks.map((bot: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-center border-b border-gov-border dark:border-slate-850 pb-2.5 last:border-0 last:pb-0">
                    <div className="space-y-0.5">
                      <span className="font-bold text-slate-800 dark:text-slate-200">{bot.bottleneck}</span>
                    </div>
                    <span className="bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400 px-2 py-0.5 rounded text-[9px] font-bold shrink-0">
                      {bot.count} cases
                    </span>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Recharts Topic analysis & Frequently Asked Questions */}
          <div className="grid md:grid-cols-3 gap-6">
            
            {/* Recharts Topic Analysis Chart */}
            <div className="gov-card md:col-span-2 space-y-4">
              <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider border-b border-gov-border dark:border-slate-850 pb-2">
                Interview Topic Volume & Distribution
              </h3>
              <p className="text-[10px] text-slate-500">
                Extracted category count distributions of feedback evaluations.
              </p>
              
              <div className="h-56">
                <AccessibleChart
                  title="Interview Topic Analysis Distribution Chart"
                  description="Extracted category count distributions of feedback evaluations."
                  data={sentimentData.topic_distribution || []}
                  keys={[{ dataKey: 'count', label: 'Mentions Count' }]}
                  labelKey="topic"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={sentimentData.topic_distribution || []}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="topic" tick={{ fontSize: 9 }} />
                      <YAxis tick={{ fontSize: 9 }} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#328CC1" radius={[4, 4, 0, 0]}>
                        {(sentimentData.topic_distribution || []).map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </AccessibleChart>
              </div>
            </div>

            {/* FAQs List */}
            <div className="gov-card space-y-4">
              <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider border-b border-gov-border dark:border-slate-850 pb-2">
                Common Technical FAQ Pools
              </h3>
              <p className="text-[10px] text-slate-500 leading-normal">
                Most repeated questions queried by company panels.
              </p>
              
              <div className="space-y-3">
                {dynamicFAQs.length === 0 ? (
                  <p className="text-slate-400 italic text-[10px]">No technical questions extracted from feedback records yet.</p>
                ) : (
                  dynamicFAQs.map((faq, index) => (
                    <div key={index} className="space-y-1 pb-2 border-b border-gov-border dark:border-slate-800 last:border-0 last:pb-0">
                      <span className="px-1.5 py-0.5 rounded text-[8px] bg-gov-blue text-white font-bold uppercase">
                        {faq.tag}
                      </span>
                      <p className="font-medium text-slate-700 dark:text-slate-300 italic">
                        "{faq.q}"
                      </p>
                      <span className="block text-[8px] text-slate-400 font-semibold uppercase">
                        Reported {faq.frequency} time{faq.frequency > 1 ? 's' : ''} in interviews
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

          </div>

          {/* SEMANTIC THEMES EXPLORER (Req 9) */}
          <div className="gov-card space-y-6 bg-slate-50/50 dark:bg-slate-900/50 border-gov-blue/20">
            <div className="border-b border-gov-border dark:border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <Brain size={18} className="text-gov-blue" />
                Interview Feedback Observations
              </h3>
              <p className="text-[10px] text-slate-500 mt-1">
                Aggregated, anonymized thematic reviews categorized to protect student privacy.
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Positive Observations */}
              <div className="space-y-4">
                <h4 className="font-bold text-emerald-700 dark:text-emerald-400 text-xs uppercase flex items-center gap-1.5 border-b border-gov-border dark:border-slate-850 pb-2">
                  <Smile size={14} />
                  Positive Observations & Praise
                </h4>
                {(!sentimentData.themes || sentimentData.themes.filter((t: any) => t.average_rating >= 3.5).length === 0) ? (
                  <p className="text-[10px] text-slate-400 italic">No positive observations recorded yet.</p>
                ) : (
                  <div className="space-y-3">
                    {sentimentData.themes.filter((t: any) => t.average_rating >= 3.5).map((t: any, idx: number) => (
                      <div key={idx} className="bg-white dark:bg-slate-950 p-3 rounded border border-gov-border dark:border-slate-850 space-y-1.5 shadow-sm">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-slate-800 dark:text-slate-200 text-[11px]">{t.theme}</span>
                          <span className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 px-1.5 py-0.5 rounded text-[8px] font-bold">
                            {t.student_count} Students
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-600 dark:text-slate-400">{t.consolidated_explanation}</p>
                        {t.suggestions && t.suggestions.length > 0 && (
                          <div className="text-[9px] text-slate-500 dark:text-slate-400 pt-1 border-t border-slate-100 dark:border-slate-900">
                            <strong>Key Suggestion:</strong> {t.suggestions[0]}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Issues / Areas for Improvement */}
              <div className="space-y-4">
                <h4 className="font-bold text-red-700 dark:text-red-400 text-xs uppercase flex items-center gap-1.5 border-b border-gov-border dark:border-slate-850 pb-2">
                  <Frown size={14} />
                  Issues, Bottlenecks & Improvements
                </h4>
                {(!sentimentData.themes || sentimentData.themes.filter((t: any) => t.average_rating < 3.5).length === 0) ? (
                  <p className="text-[10px] text-slate-400 italic">No areas for improvement recorded yet.</p>
                ) : (
                  <div className="space-y-3">
                    {sentimentData.themes.filter((t: any) => t.average_rating < 3.5).map((t: any, idx: number) => (
                      <div key={idx} className="bg-white dark:bg-slate-950 p-3 rounded border border-gov-border dark:border-slate-850 space-y-1.5 shadow-sm">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-slate-800 dark:text-slate-200 text-[11px]">{t.theme}</span>
                          <span className="bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400 px-1.5 py-0.5 rounded text-[8px] font-bold">
                            {t.student_count} Students
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-600 dark:text-slate-400">{t.consolidated_explanation}</p>
                        {t.suggestions && t.suggestions.length > 0 && (
                          <div className="text-[9px] text-amber-700 dark:text-amber-400 pt-1 border-t border-slate-100 dark:border-slate-900">
                            <strong>Proposed Improvement:</strong> {t.suggestions[0]}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Supporting Anonymized Quotes Explorer */}
            <div className="space-y-3 pt-3 border-t border-gov-border dark:border-slate-800">
              <h4 className="font-bold text-slate-800 dark:text-slate-200 text-xs uppercase flex items-center gap-1.5">
                <MessageSquare size={14} />
                Supporting Feedback Explorer (Anonymized Quotes)
              </h4>
              <p className="text-[9px] text-slate-450">
                Authorized staff review portal of student testimonials. Names and Roll Numbers are fully masked for privacy.
              </p>
              <div className="grid md:grid-cols-3 gap-4">
                {sentimentData.themes && sentimentData.themes.slice(0, 3).map((t: any, idx: number) => (
                  <div key={idx} className="bg-slate-100 dark:bg-slate-955 p-3 rounded border border-slate-250 dark:border-slate-850 space-y-2">
                    <span className="font-bold text-slate-700 dark:text-slate-300 text-[10px] uppercase block tracking-wider">{t.theme}</span>
                    <div className="space-y-1.5">
                      {t.supporting_points && t.supporting_points.map((quote: string, qIdx: number) => (
                        <div key={qIdx} className="bg-white dark:bg-slate-900 p-2 rounded border border-slate-200 dark:border-slate-800 text-[9px] italic text-slate-600 dark:text-slate-400 relative">
                          "{quote.length > 120 ? `${quote.substring(0, 120)}...` : quote}"
                          <span className="block mt-1 text-[8px] text-slate-400 text-right font-semibold uppercase not-italic">
                            — Anonymous Reviewer {qIdx + 1}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Feedback list grid with filters */}
          <div className="gov-card space-y-4">
            
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gov-border dark:border-slate-850 pb-2">
              <div>
                <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                  Student Feedback Transcripts
                </h3>
                <p className="text-[9px] text-slate-450">
                  Individual feedback comments analyzed and indexed by assessment services.
                </p>
              </div>

              {/* Filters */}
              <div className="flex gap-3 text-[10px]">
                <div>
                  <select
                    value={difficultyFilter}
                    onChange={(e) => setDifficultyFilter(e.target.value)}
                    className="border border-gov-border rounded p-1 bg-white text-slate-700 dark:bg-slate-950 focus:outline-none focus:ring-1 focus:ring-gov-blue"
                  >
                    <option value="">Difficulty: All</option>
                    <option value="1">1 Star</option>
                    <option value="2">2 Stars</option>
                    <option value="3">3 Stars</option>
                    <option value="4">4 Stars</option>
                    <option value="5">5 Stars</option>
                  </select>
                </div>
                <div>
                  <select
                    value={sentimentFilter}
                    onChange={(e) => setSentimentFilter(e.target.value)}
                    className="border border-gov-border rounded p-1 bg-white text-slate-700 dark:bg-slate-955 focus:outline-none focus:ring-1 focus:ring-gov-blue"
                  >
                    <option value="">Feedback: All</option>
                    <option value="positive">Positive Only</option>
                    <option value="neutral">Neutral Only</option>
                    <option value="negative">Negative Only</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Table */}
            {filteredFeedbacks.length === 0 ? (
              <div className="text-center py-12 text-slate-450 uppercase font-bold">
                No interview feedback logs match these specific filters.
              </div>
            ) : (
              <div className="space-y-4">
                <ProfessionalTable
                  columns={feedbackColumns}
                  data={filteredFeedbacks}
                  searchPlaceholder="Search reviews by company, topic, or keywords..."
                  exportFileName="student_feedback_logs"
                />
              </div>
            )}

          </div>

        </>
      )}

      {/* Aggregated Drive Feedback Report Modal */}
      <DriveFeedbackReportModal
        isOpen={reportModalDriveId !== null}
        onClose={() => setReportModalDriveId(null)}
        driveId={reportModalDriveId}
        driveTitle={
          drivesList.find(d => d.id === reportModalDriveId)
            ? `${drivesList.find(d => d.id === reportModalDriveId).company_name} — ${drivesList.find(d => d.id === reportModalDriveId).role}`
            : undefined
        }
      />

    </div>
  );
};

export default AISentimentMiner;
