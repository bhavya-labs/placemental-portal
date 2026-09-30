import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { studentService, aiService, driveService } from '../services/api';
import { CardSkeleton } from '../components/LoadingSkeleton';
import {
  User,
  Award,
  Link2,
  GitBranch,
  Terminal,
  Upload,
  FileText,
  CheckCircle2,
  X,
  Compass,
} from 'lucide-react';
import {
  AccessibleToast,
  AccessibleInput,
} from '../components/AccessibilityComponents';

export const StudentProfile: React.FC = () => {
  const { user, refreshProfile } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [studentDetails, setStudentDetails] = useState<any>(null);
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);

  // Profile forms
  const [skillsInput, setSkillsInput] = useState('');
  const [cgpaInput, setCgpaInput] = useState(0.0);
  const [attendanceInput, setAttendanceInput] = useState(0.0);
  const [backlogsInput, setBacklogsInput] = useState(0);
  const [githubInput, setGithubInput] = useState('');
  const [linkedinInput, setLinkedinInput] = useState('');
  const [leetcodeInput, setLeetcodeInput] = useState(0);
  const [codechefInput, setCodechefInput] = useState(0);
  const [hackerrankInput, setHackerrankInput] = useState(0);

  // Resume scanning states & target drive selection
  const [drives, setDrives] = useState<any[]>([]);
  const [selectedDriveId, setSelectedDriveId] = useState<string>('');
  const [uploadingResume, setUploadingResume] = useState(false);
  const [resumeAnalysisResult, setResumeAnalysisResult] = useState<any>(null);
  const [resumeUploadSuccess, setResumeUploadSuccess] = useState('');

  const showToast = (
    message: string,
    type: 'success' | 'error' | 'info'
  ) => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const loadProfile = async () => {
    if (!user) return;

    setLoading(true);

    try {
      const details = await studentService.getStudentById(user.id);
      setStudentDetails(details);

      let skillsList: string[] = [];

      if (Array.isArray(details.skills)) {
        skillsList = details.skills;
      } else if (typeof details.skills === 'string') {
        try {
          const parsed = JSON.parse(details.skills);

          if (Array.isArray(parsed)) {
            skillsList = parsed;
          }
        } catch {
          skillsList = details.skills
            .split(',')
            .map((s: string) => s.trim())
            .filter(Boolean);
        }
      }

      setSkillsInput(skillsList.join(', '));
      setCgpaInput(details.cgpa);
      setAttendanceInput(details.attendance);
      setBacklogsInput(details.backlogs);
      setGithubInput(details.github_url || '');
      setLinkedinInput(details.linkedin_url || '');
      setLeetcodeInput(details.leetcode_score || 0);
      setCodechefInput(details.codechef_score || 0);
      setHackerrankInput(details.hackerrank_score || 0);

      if (details.resume_ats_score) {
        let parsedAnalysis = {};

        try {
          parsedAnalysis = JSON.parse(details.resume_analysis_json);
        } catch {
          parsedAnalysis = {};
        }

        setResumeAnalysisResult({
          score: details.resume_ats_score,
          ...parsedAnalysis,
        });
      }

      try {
        const activeDrives = await driveService.getDrives('Active');
        setDrives(activeDrives || []);
      } catch (e) {
        console.error('Failed to load active drives', e);
      }
    } catch (err) {
      console.error('Failed to load profile details', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, [user]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) return;

    try {
      const skillsArray = skillsInput
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      await studentService.updateStudent(user.id, {
        phone: studentDetails.phone || '9876543210',
        cgpa: cgpaInput,
        attendance: attendanceInput,
        backlogs: backlogsInput,
        skills: JSON.stringify(skillsArray),
        github_url: githubInput,
        linkedin_url: linkedinInput,
        leetcode_score: leetcodeInput,
        codechef_score: codechefInput,
        hackerrank_score: hackerrankInput,
      });

      showToast('Profile updated successfully!', 'success');

      if (refreshProfile) {
        refreshProfile();
      }

      loadProfile();
    } catch (err: any) {
      showToast(
        err.response?.data?.detail || 'Failed to update profile.',
        'error'
      );
    }
  };

  const handleResumeUpload = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (!e.target.files || e.target.files.length === 0) return;

    const file = e.target.files[0];

    setUploadingResume(true);
    setResumeUploadSuccess('');
    setResumeAnalysisResult(null);

    const formData = new FormData();
    formData.append('file', file);

    if (selectedDriveId) {
      formData.append('drive_id', selectedDriveId);
    }

    try {
      const res = await aiService.uploadResume(formData);

      const analysisData = res.analysis || {};
      const targetName =
        res.comparison_target || 'General Industry Software Baseline';

      setResumeUploadSuccess(
        `Resume successfully evaluated against: ${targetName}`
      );

      setResumeAnalysisResult({
        score: res.ats_score ?? analysisData.ats_score ?? 0,
        formatting_score: analysisData.formatting_score ?? 0,
        skills_matched:
          analysisData.skills_matched ||
          analysisData.matching_skills ||
          [],
        missing_skills: analysisData.missing_skills || [],
        suggestions:
          analysisData.suggestions ||
          analysisData.improvement_tips ||
          [],
        comparison_target: targetName,
      });

      showToast('Resume evaluation complete!', 'success');

      loadProfile();
    } catch (err: any) {
      showToast(
        err.response?.data?.detail ||
        'Resume upload and evaluation failed.',
        'error'
      );
    } finally {
      setUploadingResume(false);
    }
  };

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350">
      <AccessibleToast
        message={toast?.message || null}
        type={toast?.type || null}
      />

      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card">
        <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
          <User className="text-gov-blue" size={24} />
          Student Profile & Career Assessments
        </h2>

        <p className="text-[10px] text-slate-500 mt-1">
          Update your academic parameters, career preferences,
          competitive coding profiles, and upload your resume.
        </p>
      </div>

      {loading || !studentDetails ? (
        <CardSkeleton />
      ) : (
        <div className="grid md:grid-cols-3 gap-6">
          {/* Edit profile forms */}
          <div className="md:col-span-2 gov-card space-y-4">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider border-b border-gov-border dark:border-slate-850 pb-2">
              Academic Parameters & Profile Information
            </h3>

            {studentDetails.verification_status === 'VERIFIED' ? (
              <div className="bg-sky-50 dark:bg-sky-955/20 border border-sky-200 dark:border-sky-900 rounded p-3 text-xs text-slate-700 dark:text-slate-350 flex flex-col gap-1.5">
                <p className="font-semibold text-sky-850 dark:text-sky-400">
                  Your profile has been submitted and verified.
                  Institutional information is now locked.
                </p>

                <button
                  type="button"
                  onClick={() => navigate('/correction-requests')}
                  className="w-fit text-gov-blue dark:text-sky-400 hover:underline font-bold uppercase text-[10px]"
                >
                  Need to correct your information? Request Correction
                </button>
              </div>
            ) : (
              <div className="bg-amber-50 dark:bg-amber-955/20 border border-amber-200 dark:border-amber-900 rounded p-3 text-xs text-amber-850 dark:text-amber-400 font-semibold">
                Profile Completion Required: Please enter and submit your
                institutional details.
              </div>
            )}

            <form onSubmit={handleProfileSubmit} className="space-y-4">
              {/* Personal & Institutional Details */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 border-b border-gov-border dark:border-slate-800 pb-4">
                <div>
                  <label className="block font-bold text-slate-450 uppercase">
                    Full Name
                  </label>

                  <div className="mt-1 p-2 bg-slate-50 dark:bg-slate-955 border border-gov-border dark:border-slate-800 rounded dark:text-slate-300 font-semibold">
                    {studentDetails.name}
                  </div>
                </div>

                <div>
                  <label className="block font-bold text-slate-450 uppercase">
                    Roll Number
                  </label>

                  <div className="mt-1 p-2 bg-slate-50 dark:bg-slate-955 border border-gov-border dark:border-slate-800 rounded dark:text-slate-300 font-mono font-semibold">
                    {studentDetails.id}
                  </div>
                </div>

                <div>
                  <label className="block font-bold text-slate-450 uppercase">
                    Email Address
                  </label>

                  <div className="mt-1 p-2 bg-slate-50 dark:bg-slate-955 border border-gov-border dark:border-slate-800 rounded dark:text-slate-300 font-semibold truncate">
                    {studentDetails.email}
                  </div>
                </div>

                <div>
                  <label className="block font-bold text-slate-450 uppercase">
                    Branch / Department
                  </label>

                  <div className="mt-1 p-2 bg-slate-50 dark:bg-slate-955 border border-gov-border dark:border-slate-800 rounded dark:text-slate-300 font-semibold animate-pulse-subtle">
                    {studentDetails.dept_name ||
                      studentDetails.dept_code}
                  </div>
                </div>

                <div>
                  <label className="block font-bold text-slate-450 uppercase">
                    Section
                  </label>

                  <div className="mt-1 p-2 bg-slate-50 dark:bg-slate-955 border border-gov-border dark:border-slate-800 rounded dark:text-slate-300 font-semibold">
                    {studentDetails.section || 'A'}
                  </div>
                </div>

                <div>
                  <label className="block font-bold text-slate-450 uppercase">
                    Batch / Graduation Year
                  </label>

                  <div className="mt-1 p-2 bg-slate-50 dark:bg-slate-955 border border-gov-border dark:border-slate-800 rounded dark:text-slate-300 font-semibold">
                    {studentDetails.batch}
                  </div>
                </div>
              </div>

              {/* Academics */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label
                    htmlFor="profile-cgpa"
                    className="block font-bold text-slate-500 uppercase"
                  >
                    Cumulative CGPA
                  </label>

                  <input
                    id="profile-cgpa"
                    type="number"
                    step="0.01"
                    min="0"
                    max="10"
                    required
                    value={cgpaInput}
                    onChange={(e) =>
                      setCgpaInput(Number(e.target.value))
                    }
                    disabled={
                      studentDetails.verification_status === 'VERIFIED'
                    }
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:border-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-gov-blue disabled:bg-slate-50 dark:disabled:bg-slate-905"
                  />
                </div>

                <div>
                  <label
                    htmlFor="profile-attendance"
                    className="block font-bold text-slate-500 uppercase"
                  >
                    Attendance %
                  </label>

                  <input
                    id="profile-attendance"
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    required
                    value={attendanceInput}
                    onChange={(e) =>
                      setAttendanceInput(Number(e.target.value))
                    }
                    disabled={
                      studentDetails.verification_status === 'VERIFIED'
                    }
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:border-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-gov-blue disabled:bg-slate-50 dark:disabled:bg-slate-905"
                  />
                </div>

                <div>
                  <label
                    htmlFor="profile-backlogs"
                    className="block font-bold text-slate-500 uppercase"
                  >
                    Active Backlogs
                  </label>

                  <input
                    id="profile-backlogs"
                    type="number"
                    min="0"
                    required
                    value={backlogsInput}
                    onChange={(e) =>
                      setBacklogsInput(Number(e.target.value))
                    }
                    disabled={
                      studentDetails.verification_status === 'VERIFIED'
                    }
                    className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-955 dark:border-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-gov-blue disabled:bg-slate-50 dark:disabled:bg-slate-905"
                  />
                </div>
              </div>

              {/* Competitive Programming */}
              <div className="border-t border-gov-border dark:border-slate-800 pt-3">
                <h4 className="font-bold text-slate-700 dark:text-slate-350 uppercase mb-2">
                  Coding Platform Metrics
                </h4>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label
                      htmlFor="profile-leetcode"
                      className="block font-bold text-slate-500 uppercase"
                    >
                      LeetCode Solved
                    </label>

                    <input
                      id="profile-leetcode"
                      type="number"
                      value={leetcodeInput}
                      onChange={(e) =>
                        setLeetcodeInput(Number(e.target.value))
                      }
                      className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:border-slate-800 dark:text-slate-100 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="profile-codechef"
                      className="block font-bold text-slate-500 uppercase"
                    >
                      CodeChef Rating
                    </label>

                    <input
                      id="profile-codechef"
                      type="number"
                      value={codechefInput}
                      onChange={(e) =>
                        setCodechefInput(Number(e.target.value))
                      }
                      className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:border-slate-800 dark:text-slate-100 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="profile-hackerrank"
                      className="block font-bold text-slate-500 uppercase"
                    >
                      HackerRank Rating
                    </label>

                    <input
                      id="profile-hackerrank"
                      type="number"
                      value={hackerrankInput}
                      onChange={(e) =>
                        setHackerrankInput(Number(e.target.value))
                      }
                      className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:border-slate-800 dark:text-slate-100 focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Social URLs */}
              <div className="border-t border-gov-border dark:border-slate-800 pt-3">
                <h4 className="font-bold text-slate-700 dark:text-slate-350 uppercase mb-2">
                  Portfolio Web Links
                </h4>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label
                      htmlFor="profile-github"
                      className="block font-bold text-slate-500 uppercase flex items-center gap-1"
                    >
                      <GitBranch size={12} />
                      GitHub Profile URL
                    </label>

                    <input
                      id="profile-github"
                      type="url"
                      value={githubInput}
                      onChange={(e) =>
                        setGithubInput(e.target.value)
                      }
                      className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:border-slate-800 dark:text-slate-100 focus:outline-none"
                      placeholder="https://github.com/username"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="profile-linkedin"
                      className="block font-bold text-slate-500 uppercase flex items-center gap-1"
                    >
                      <Link2 size={12} />
                      LinkedIn Profile URL
                    </label>

                    <input
                      id="profile-linkedin"
                      type="url"
                      value={linkedinInput}
                      onChange={(e) =>
                        setLinkedinInput(e.target.value)
                      }
                      className="mt-1 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:border-slate-800 dark:text-slate-100 focus:outline-none"
                      placeholder="https://linkedin.com/in/username"
                    />
                  </div>
                </div>
              </div>

              {/* Skills */}
              <div className="border-t border-gov-border dark:border-slate-800 pt-3">
                <label
                  htmlFor="profile-skills"
                  className="block font-bold text-slate-550 uppercase"
                >
                  Registered Tech Skills (Comma Separated)
                </label>

                <textarea
                  id="profile-skills"
                  value={skillsInput}
                  onChange={(e) => setSkillsInput(e.target.value)}
                  className="mt-1.5 w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:border-slate-800 dark:text-slate-100 h-20 focus:outline-none focus:ring-1 focus:ring-gov-blue"
                  placeholder="React, Java, SQL, Python"
                />
              </div>

              <button
                type="submit"
                className="gov-btn-primary w-full py-2.5 font-bold uppercase tracking-wider bg-gov-navy border-0 text-white"
              >
                {studentDetails.verification_status === 'VERIFIED'
                  ? 'Save Changes'
                  : 'Submit Profile'}
              </button>
            </form>
          </div>

          {/* Resume Upload and completeness scorecard */}
          <div className="gov-card h-fit space-y-5">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider border-b border-gov-border dark:border-slate-850 pb-2 flex items-center gap-2">
              <FileText size={16} className="text-gov-blue" />
              Resume Review & Completeness
            </h3>

            <p className="text-slate-500 leading-relaxed">
              Upload your resume (PDF, Word, or text format) to check
              formatting completeness and receive recommendations tailored
              to your target opportunity.
            </p>

            {/* Target Opportunity Selector */}
            <div className="space-y-1.5">
              <label
                htmlFor="target-drive-select"
                className="block font-bold text-slate-600 dark:text-slate-400 uppercase text-[11px]"
              >
                Target Opportunity for Skill Comparison (Optional)
              </label>

              <select
                id="target-drive-select"
                value={selectedDriveId}
                onChange={(e) =>
                  setSelectedDriveId(e.target.value)
                }
                className="w-full p-2 border border-gov-border rounded dark:bg-slate-950 dark:border-slate-800 dark:text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-gov-blue"
              >
                <option value="">
                  General Industry Software Baseline
                </option>

                {drives.map((d: any) => (
                  <option key={d.id} value={d.id}>
                    {d.company?.name
                      ? `${d.company.name} - ${d.role}`
                      : d.role}
                  </option>
                ))}
              </select>

              <span className="text-[10px] text-slate-400 block">
                Select an active recruitment drive to compare your skills
                against specific job requirements, or keep the default
                baseline.
              </span>
            </div>

            {/* Upload Zone */}
            <div className="border border-dashed border-gov-border dark:border-slate-800 p-6 rounded-lg text-center bg-slate-50 dark:bg-slate-950 space-y-3 relative hover:bg-slate-100 dark:hover:bg-slate-900/60 transition-colors">
              <input
                id="resume-file-upload"
                type="file"
                accept=".pdf,.txt,.docx"
                onChange={handleResumeUpload}
                disabled={uploadingResume}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />

              <div className="flex flex-col items-center gap-2">
                <Upload size={24} className="text-slate-400" />

                <span className="font-bold text-slate-700 dark:text-slate-350">
                  {uploadingResume
                    ? 'Evaluating Resume...'
                    : 'Drag & Drop or Click to Upload'}
                </span>

                <span className="text-[10px] text-slate-450">
                  Formats accepted: PDF, DOCX, TXT up to 5 MB
                </span>
              </div>
            </div>

            {resumeUploadSuccess && (
              <div className="bg-emerald-50 text-emerald-800 border border-emerald-250 p-2.5 rounded font-bold uppercase text-[10px]">
                {resumeUploadSuccess}
              </div>
            )}

            {/* Score gauge and comparison breakdown */}
            {resumeAnalysisResult && (
              <div className="space-y-4 pt-3 border-t border-gov-border dark:border-slate-850">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-500 uppercase">
                    Resume Completeness:
                  </span>

                  <span className="font-extrabold text-sm text-gov-blue dark:text-sky-400">
                    {resumeAnalysisResult.score}%
                  </span>
                </div>

                <div className="w-full bg-slate-200 h-2 rounded overflow-hidden">
                  <div
                    className="bg-gov-blue h-full"
                    style={{
                      width: `${resumeAnalysisResult.score}%`,
                    }}
                  />
                </div>

                {resumeAnalysisResult.comparison_target && (
                  <div className="text-[11px] p-2 bg-slate-50 dark:bg-slate-950 rounded border border-slate-200 dark:border-slate-800 flex items-center justify-between">
                    <span className="font-medium text-slate-500">
                      Evaluated Against:
                    </span>

                    <span className="font-bold text-gov-blue dark:text-sky-400">
                      {resumeAnalysisResult.comparison_target}
                    </span>
                  </div>
                )}

                {resumeAnalysisResult.skills_matched &&
                  resumeAnalysisResult.skills_matched.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="font-bold text-slate-500 uppercase text-[10px]">
                        Matching Competencies
                      </span>

                      <div className="flex flex-wrap gap-1.5">
                        {resumeAnalysisResult.skills_matched.map(
                          (sk: string, i: number) => (
                            <span
                              key={i}
                              className="px-2 py-0.5 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/80 rounded text-[10px] font-medium"
                            >
                              {sk}
                            </span>
                          )
                        )}
                      </div>
                    </div>
                  )}

                {resumeAnalysisResult.missing_skills &&
                  resumeAnalysisResult.missing_skills.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="font-bold text-slate-500 uppercase text-[10px]">
                        Recommended Additional Skills
                      </span>

                      <div className="flex flex-wrap gap-1.5">
                        {resumeAnalysisResult.missing_skills.map(
                          (sk: string, i: number) => (
                            <span
                              key={i}
                              className="px-2 py-0.5 bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800/80 rounded text-[10px] font-medium"
                            >
                              {sk}
                            </span>
                          )
                        )}
                      </div>
                    </div>
                  )}

                {resumeAnalysisResult.suggestions &&
                  resumeAnalysisResult.suggestions.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="font-bold text-slate-500 uppercase">
                        Suggestions to Strengthen Your Resume
                      </span>

                      <ul className="pl-4 list-disc space-y-1 text-slate-600 dark:text-slate-400">
                        {resumeAnalysisResult.suggestions.map(
                          (sug: string, i: number) => (
                            <li key={i}>{sug}</li>
                          )
                        )}
                      </ul>
                    </div>
                  )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentProfile;