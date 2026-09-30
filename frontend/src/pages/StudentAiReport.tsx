import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { careerPathService, driveService } from '../services/api';
import { CardSkeleton } from '../components/LoadingSkeleton';
import { 
  Brain, Compass, Terminal, Award, BookOpen, 
  RefreshCw, Clock, AlertTriangle 
} from 'lucide-react';
import { AccessibleToast } from '../components/AccessibilityComponents';

export interface RoadmapItem {
  week: string;
  focus: string;
  activities: string[];
}

export interface ResumeQuality {
  score: number;
  suggestions: string[];
}

export interface AiReport {
  student_id?: number;
  name?: string;
  readiness_score: number;
  placement_probability: number;
  skills_gap: string[];
  recommended_skills: string[];
  recommended_projects: string[];
  recommended_certifications: string[];
  matching_companies: string[];
  explanation: string;
  at_risk: boolean;
  risk_reason?: string;
  improvement_tips?: string[];
  resume_quality: ResumeQuality;
  cohort_readiness_cutoff?: number;
  cohort_percentile?: number;
  preparation_tier?: string;
}

export interface Drive {
  id: number;
  company_name: string;
  role: string;
  package_lpa: number;
  location: string;
  cgpa_cutoff: number;
  allowed_depts: string;
  allowed_backlogs: number;
  deadline: string;
  status: string;
  responsibilities?: string;
  hiring_process?: string;
}

export const StudentAiReport: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [aiReport, setAiReport] = useState<AiReport | null>(null);
  const [drives, setDrives] = useState<Drive[]>([]);
  const [selectedDriveForRoadmap, setSelectedDriveForRoadmap] = useState<number | null>(null);
  const [roadmapData, setRoadmapData] = useState<RoadmapItem[]>([]);
  const [loadingRoadmap, setLoadingRoadmap] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const loadData = async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const report = await careerPathService.getStudentReport(user.id);
      setAiReport(report);

      const activeDrives = await driveService.getDrives('Active');
      setDrives(activeDrives);
      if (activeDrives.length > 0) {
        setSelectedDriveForRoadmap(activeDrives[0].id);
      }
    } catch (err: unknown) {
      console.error('Failed to load career reports', err);
      setError('Connection to Placement Analytics server failed. Displaying fallback profile metrics.');
      setAiReport({
        readiness_score: 72,
        placement_probability: 0.65,
        skills_gap: ['Docker', 'AWS', 'System Design'],
        recommended_skills: ['Container Orchestration', 'Cloud Architecture'],
        recommended_certifications: ['AWS Certified Cloud Practitioner', 'Docker Certified Associate'],
        recommended_projects: [
          'REST API Gateway Middleware',
          'Distributed Cache Sync Node'
        ],
        matching_companies: ['TCS', 'Infosys', 'Wipro'],
        explanation: 'You have a solid foundation with clear opportunities to stand out. Focusing on hands-on project work and core cloud tools will give you a competitive edge.',
        at_risk: false,
        resume_quality: {
          score: 80,
          suggestions: ['Include more metrics-driven achievements', 'Specify database indices used']
        }
      });
      setDrives([
        { id: 1, company_name: 'TCS', role: 'System Engineer', allowed_depts: 'CSE', cgpa_cutoff: 6.0, allowed_backlogs: 2, deadline: '2026-08-31', package_lpa: 3.6, location: 'Hyderabad', status: 'Active' }
      ]);
      setSelectedDriveForRoadmap(1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const handleGenerateRoadmap = async () => {
    if (!user || !selectedDriveForRoadmap) return;
    setLoadingRoadmap(true);
    setRoadmapData([]);
    try {
      const roadmap = await careerPathService.getPrepRoadmap(selectedDriveForRoadmap);
      setRoadmapData(roadmap || []);
      showToast('Personalized 4-Week preparation plan generated successfully!', 'success');
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to construct study plan.';
      showToast(errorMsg, 'error');
      setRoadmapData([
        {
          week: 'Week 1',
          focus: 'Core Principles & Analytical Foundations',
          activities: [
            'Practice quantitative reasoning and analytical problem solving sheets',
            'Review foundational concepts and programming principles in your primary language'
          ]
        },
        {
          week: 'Week 2',
          focus: 'Role-Specific Technical Skills',
          activities: [
            'Complete practical exercises and tutorials on key required competencies',
            'Build a small practical project to apply these concepts'
          ]
        },
        {
          week: 'Week 3',
          focus: 'Technical Practice & Mock Discussions',
          activities: [
            'Solve practice coding and technical domain questions',
            'Complete a mock technical discussion with placement cell mentors'
          ]
        },
        {
          week: 'Week 4',
          focus: 'Interview Preparation & Review',
          activities: [
            'Review common interview formats and company discussion points',
            'Refine your resume formatting and prepare situational responses'
          ]
        }
      ]);

    } finally {
      setLoadingRoadmap(false);
    }
  };

  useEffect(() => {
    if (selectedDriveForRoadmap && user) {
      handleGenerateRoadmap();
    }
  }, [selectedDriveForRoadmap]);

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-355">
      <AccessibleToast message={toast?.message || null} type={toast?.type || null} />

      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card">
        <h2 className="text-xl font-bold text-slate-805 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
          <Brain className="text-gov-blue" size={24} />
          Skill Development & Career Guidance Plan
        </h2>
        <p className="text-[10px] text-slate-500 mt-1">
          Review in-demand skills for your target roles, recommended projects, and your personalized 4-week preparation roadmap.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-955/20 border border-red-250 dark:border-red-900 rounded p-4 flex items-center justify-between gap-4 animate-fadeIn no-print">
          <div className="flex items-center gap-2 text-red-800 dark:text-red-400 font-bold uppercase tracking-wide">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
          <button 
            onClick={loadData}
            className="gov-btn-secondary px-3 py-1 font-bold border border-red-300 text-red-800 rounded bg-white hover:bg-red-50 uppercase text-[9px] focus:outline-none"
          >
            Retry Connection
          </button>
        </div>
      )}

      {loading || !aiReport ? <CardSkeleton /> : (
        <div className="grid md:grid-cols-3 gap-6">
          
          {/* Main Suggestions */}
          <div className="md:col-span-2 space-y-6">
            
            {/* Risk Warnings */}
            {aiReport.at_risk && (
              <div className="bg-amber-50 dark:bg-amber-955/20 border border-amber-300 dark:border-amber-900 rounded-lg p-5 flex items-start gap-4 animate-fadeIn">
                <AlertTriangle size={24} className="text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-bold text-amber-850 dark:text-amber-400 uppercase tracking-wider">Key Areas to Strengthen for Upcoming Drives</h4>
                  <p className="text-xs text-amber-800 dark:text-amber-300 mt-1">
                    Strengthening a few focused areas will significantly improve your chances: <span className="font-semibold">{aiReport.risk_reason || 'building practical projects and adding core technical skills'}</span>. Take a look at the recommended projects and certifications below to build your placement preparation.
                  </p>
                </div>
              </div>
            )}

            {/* General Explanation */}
            <div className="gov-card space-y-4">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Compass size={18} className="text-gov-blue" />
                Your Strengths & Opportunities
              </h3>
              <p className="text-xs text-slate-650 dark:text-slate-455 leading-relaxed bg-slate-50 dark:bg-slate-950 p-4 rounded border border-gov-border dark:border-slate-850">
                {aiReport.explanation}
              </p>
            </div>

            {/* Projects & Certs */}
            <div className="grid sm:grid-cols-2 gap-6">
              
              <div className="gov-card space-y-3">
                <h4 className="text-xs font-bold text-slate-855 dark:text-slate-200 uppercase tracking-wider flex items-center gap-1.5 border-b border-gov-border dark:border-slate-850 pb-2">
                  <Terminal size={14} className="text-gov-blue" /> Skill Improvement Areas
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {aiReport.skills_gap && aiReport.skills_gap.map((s: string, idx: number) => (
                    <span key={idx} className="bg-red-50 text-red-800 dark:bg-red-950/20 dark:text-red-400 text-xs px-2 py-0.5 rounded border border-red-250/20">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              <div className="gov-card space-y-3">
                <h4 className="text-xs font-bold text-slate-855 dark:text-slate-200 uppercase tracking-wider flex items-center gap-1.5 border-b border-gov-border dark:border-slate-850 pb-2">
                  <Award size={14} className="text-gov-blue" /> Recommended Certifications
                </h4>
                <ul className="text-xs space-y-1.5 text-slate-650 dark:text-slate-400 list-disc pl-4">
                  {aiReport.recommended_certifications && aiReport.recommended_certifications.map((c: string, idx: number) => (
                    <li key={idx}>{c}</li>
                  ))}
                </ul>
              </div>

            </div>

            {/* Suggested portfolio projects */}
            <div className="gov-card space-y-4">
              <h4 className="text-xs font-bold text-slate-805 dark:text-slate-200 uppercase tracking-wider border-b border-gov-border dark:border-slate-850 pb-2">
                Suggested Portfolio Projects
              </h4>
              <div className="space-y-3">
                {aiReport.recommended_projects && aiReport.recommended_projects.map((p: string, idx: number) => (
                  <div key={idx} className="border border-gov-border dark:border-slate-850 rounded p-3 text-xs flex gap-3 bg-slate-50/50 dark:bg-slate-950/20">
                    <div className="bg-slate-100 dark:bg-slate-955 border border-gov-border dark:border-slate-800 w-8 h-8 rounded-full flex items-center justify-center font-bold text-gov-blue shrink-0">
                      {idx + 1}
                    </div>
                    <div>
                      <p className="font-bold text-slate-700 dark:text-slate-350">{p}</p>
                      <p className="text-slate-450 mt-0.5 leading-relaxed">Focus on writing cleaner code and implementing robust SQL schema databases to satisfy candidate requirements.</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Week-by-Week Roadmaps Generator (Right column) */}
          <div className="space-y-4">
            <div className="gov-card space-y-4">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider border-b border-gov-border dark:border-slate-850 pb-2 flex items-center gap-1.5">
                <BookOpen size={16} className="text-gov-blue" />
                Company Preparation Guide
              </h3>
              
              <p className="text-slate-505 leading-normal">
                Select an upcoming recruitment drive to generate a step-by-step 4-week study plan tailored for the role.
              </p>

              <div>
                <label htmlFor="drive-roadmap-selector" className="block font-bold text-slate-550 uppercase mb-1">Target Placement Drive</label>
                <select
                  id="drive-roadmap-selector"
                  value={selectedDriveForRoadmap || ''}
                  onChange={(e) => setSelectedDriveForRoadmap(e.target.value ? Number(e.target.value) : null)}
                  className="w-full border border-gov-border rounded p-2 bg-white text-slate-850 dark:bg-slate-950 dark:border-slate-850 focus:outline-none focus:ring-1 focus:ring-gov-blue"
                >
                  <option value="">Select Drive</option>
                  {drives.map((d: Drive) => (
                    <option key={d.id} value={d.id}>{d.company_name} - {d.role}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleGenerateRoadmap}
                disabled={loadingRoadmap || !selectedDriveForRoadmap}
                className="gov-btn-primary w-full py-2 font-bold uppercase tracking-wider bg-gov-navy border-0 text-white flex items-center justify-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-gov-blue"
              >
                <RefreshCw size={12} className={loadingRoadmap ? 'animate-spin' : ''} />
                Generate 4-Week Study Plan
              </button>
            </div>

            {/* Generated roadmap items */}
            {roadmapData && roadmapData.length > 0 ? (
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-850 dark:text-slate-250 uppercase tracking-wider">
                  Your 4-Week Prep Timeline
                </h4>
                
                <div className="space-y-3">
                  {roadmapData.map((item: RoadmapItem, idx: number) => (
                    <div key={idx} className="gov-card border-l-4 border-l-gov-blue space-y-3.5 p-3.5 bg-white dark:bg-slate-900 shadow-sm animate-fadeIn">
                      <div className="flex justify-between items-center text-[10px] text-slate-450 uppercase font-bold">
                        <span>{item.week}</span>
                        <span className="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded flex items-center gap-1"><Clock size={10} /> {item.focus}</span>
                      </div>
                      
                      <ul className="text-[10px] text-slate-650 dark:text-slate-400 space-y-1 list-disc pl-4">
                        {item.activities && item.activities.length > 0 ? (
                          item.activities.map((act: string, aIdx: number) => (
                            <li key={aIdx}>{act}</li>
                          ))
                        ) : (
                          <li className="italic text-slate-450">No activities available.</li>
                        )}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              selectedDriveForRoadmap && !loadingRoadmap && (
                <div className="gov-card p-6 text-center text-slate-400 italic">
                  No weekly preparation milestones available for this drive profile.
                </div>
              )
            )}

          </div>

        </div>
      )}

    </div>
  );
};

export default StudentAiReport;
