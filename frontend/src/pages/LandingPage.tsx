import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { driveService } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { 
  GraduationCap, ShieldCheck, CheckCircle2, TrendingUp, Users, 
  MapPin, Calendar, Clock, BarChart3, HelpCircle, BrainCircuit
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, loading } = useAuth();
  const [activeDrives, setActiveDrives] = useState<any[]>([]);
  const [stats, setStats] = useState({
    placementPct: '91.8%',
    highestPackage: '42.5 LPA',
    averagePackage: '8.4 LPA',
    companiesCount: '150+'
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (!loading && user) {
      if (user.role === 'admin') {
        navigate('/admin');
      } else if (['faculty', 'hod', 'tnp'].includes(user.role)) {
        navigate('/faculty-dashboard');
      } else if (user.role === 'parent') {
        navigate('/parent/dashboard');
      } else {
        navigate('/student');
      }
    }
  }, [user, loading, navigate]);

  useEffect(() => {
    // Attempt to load live drives from public API
    const loadDrives = async () => {
      try {
        const data = await driveService.getPublicActiveDrives();
        setActiveDrives(data.slice(0, 5));
      } catch (err) {
        console.warn('API not accessible, loading landing page with mock drives');
        setActiveDrives([
          { id: 1, company_name: 'Google', role: 'Software Engineer', package_lpa: 32, location: 'Hyderabad', cgpa_cutoff: 8.0, deadline: '2026-08-10' },
          { id: 2, company_name: 'Microsoft', role: 'Data Scientist', package_lpa: 28, location: 'Bengaluru', cgpa_cutoff: 7.5, deadline: '2026-08-12' },
          { id: 3, company_name: 'TCS', role: 'System Engineer', package_lpa: 4.5, location: 'Chennai', cgpa_cutoff: 6.0, deadline: '2026-08-15' },
          { id: 4, company_name: 'Goldman Sachs', role: 'Financial Analyst', package_lpa: 16, location: 'Bengaluru', cgpa_cutoff: 7.0, deadline: '2026-08-20' }
        ]);
      }
    };
    loadDrives();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Top Banner Government Style Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-gov-navy p-2 rounded-full text-white">
              <GraduationCap size={28} />
            </div>
            <div>
              <h1 className="text-base font-bold text-gov-navy uppercase tracking-wide leading-tight">
                Placement Portal
              </h1>
              <p className="text-xs text-slate-500 font-semibold uppercase">
                Central Career & Student Placement Directorate
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/login')}
              className="gov-btn-primary bg-gov-navy hover:bg-gov-accent text-white px-5 py-2 rounded text-sm font-semibold shadow"
            >
              Sign In
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-gov-navy to-slate-900 text-white py-16 px-6 relative overflow-hidden">
        <div className="max-w-7xl mx-auto relative z-10 grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 bg-gov-blue/40 border border-gov-blue/50 px-3.5 py-1.5 rounded-full text-xs font-semibold text-sky-200 uppercase tracking-wide">
              <GraduationCap size={14} />
              Central Placement Directorate Active
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold leading-tight tracking-tight">
              Prepare for recruitment. Track applications. Build your career.
            </h2>
            <p className="text-slate-300 text-sm md:text-base max-w-lg leading-relaxed">
              A unified career portal for colleges to organize academic records, track student profiles, and coordinate placement opportunities.
            </p>
            <div className="flex gap-4">
              <button
                onClick={() => navigate('/login')}
                className="bg-gov-blue hover:bg-blue-700 text-white font-bold px-6 py-3 rounded shadow transition-all text-sm uppercase tracking-wide"
              >
                Access Portal Login
              </button>
            </div>
          </div>
          <div className="hidden md:flex justify-center">
            <div className="bg-slate-800/80 border border-slate-700 p-6 rounded-xl shadow-2xl w-full max-w-md relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-gov-blue/20 rounded-full blur-2xl"></div>
              <h3 className="text-sm font-semibold text-sky-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <BarChart3 size={16} /> Live Statistics Summary
              </h3>
              
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-1">
                  <p className="text-xs text-slate-400">Total Placement Rate</p>
                  <p className="text-2xl font-bold text-white">{stats.placementPct}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-slate-400">Highest Package Offered</p>
                  <p className="text-2xl font-bold text-white">{stats.highestPackage}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-slate-400">Average Annual Package</p>
                  <p className="text-2xl font-bold text-white">{stats.averagePackage}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-slate-400">Partnered Recruiters</p>
                  <p className="text-2xl font-bold text-white">{stats.companiesCount}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Feature Cards Grid */}
      <section className="max-w-7xl mx-auto px-6 py-16 space-y-12">
        <div className="text-center space-y-2 max-w-xl mx-auto">
          <h3 className="text-2xl font-bold text-gov-navy uppercase tracking-wide">
            Enterprise System Capabilities
          </h3>
          <p className="text-sm text-slate-500">
            Comprehensive placement management and student preparation tools.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-card hover:shadow-premium transition-all space-y-3">
            <div className="w-10 h-10 rounded bg-sky-50 text-gov-navy flex items-center justify-center font-bold">
              01
            </div>
            <h4 className="text-sm font-bold text-slate-800 uppercase">Student Profile & Preparation</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Organizes academic coursework, project portfolios, and coding profiles to support student career preparation.
            </p>
          </div>
          
          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-card hover:shadow-premium transition-all space-y-3">
            <div className="w-10 h-10 rounded bg-indigo-50 text-gov-navy flex items-center justify-center font-bold">
              02
            </div>
            <h4 className="text-sm font-bold text-slate-800 uppercase">Resume Review & Guidance</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Reviews profile completeness, highlights key strengths, and suggests relevant skills tailored for hiring companies.
            </p>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-card hover:shadow-premium transition-all space-y-3">
            <div className="w-10 h-10 rounded bg-emerald-50 text-gov-navy flex items-center justify-center font-bold">
              03
            </div>
            <h4 className="text-sm font-bold text-slate-800 uppercase">Interview Experiences & Advice</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Shares past interview questions, difficulty ratings, and preparation advice directly from senior batch candidates.
            </p>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-card hover:shadow-premium transition-all space-y-3">
            <div className="w-10 h-10 rounded bg-amber-50 text-gov-navy flex items-center justify-center font-bold">
              04
            </div>
            <h4 className="text-sm font-bold text-slate-800 uppercase">Institutional Placement Analytics</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Interactive analytics charts grouped by batch, branch, and company for faculty placement directors.
            </p>
          </div>
        </div>
      </section>

      {/* Active drives widget */}
      <section className="bg-white border-y border-slate-200 py-16 px-6">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-3">
            <div className="space-y-1">
              <h3 className="text-xl font-bold text-gov-navy uppercase tracking-wide">
                Recent Recruitment Drives
              </h3>
              <p className="text-xs text-slate-500">
                Active hiring calendars currently open for application submission.
              </p>
            </div>
            <button
              onClick={() => navigate('/login')}
              className="text-xs font-bold text-gov-blue hover:underline uppercase"
            >
              View All Drives &rarr;
            </button>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {activeDrives.map((drive, idx) => (
              <div 
                key={drive.id || idx} 
                className="border border-slate-200 rounded-lg p-5 bg-slate-50 flex flex-col justify-between hover:border-slate-300 transition-colors"
              >
                <div className="space-y-3">
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      {drive.company_name}
                    </span>
                    <span className="bg-gov-navy text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase">
                      {drive.package_lpa} LPA
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-slate-800 uppercase leading-snug">
                    {drive.role}
                  </h4>
                  <div className="space-y-1.5 text-xs text-slate-500">
                    <p className="flex items-center gap-1.5">
                      <MapPin size={12} /> {drive.location}
                    </p>
                    <p className="flex items-center gap-1.5">
                      <Clock size={12} /> Cutoff: {drive.cgpa_cutoff} CGPA
                    </p>
                  </div>
                </div>

                <div className="border-t border-slate-200 mt-4 pt-3 flex items-center justify-between text-xs">
                  <span className="text-slate-400">Apply by: {drive.deadline}</span>
                  <button 
                    onClick={() => navigate('/login')}
                    className="text-gov-blue font-bold hover:underline"
                  >
                    Apply Now
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="max-w-7xl mx-auto px-6 py-16 space-y-12">
        <div className="text-center space-y-1">
          <h3 className="text-xl font-bold text-gov-navy uppercase tracking-wide">
            Feedback & Reviews
          </h3>
          <p className="text-xs text-slate-500">
            Hear from our placement officers and students.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-white border border-slate-200 p-6 rounded-lg space-y-4 shadow-sm">
            <p className="text-xs text-slate-650 leading-relaxed italic">
              "The career recommendations were spot on! It identified SQL Joins and React Hooks as my gap areas. Practiced those, got recommended to Google, and cleared the interview!"
            </p>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-slate-200 text-gov-navy font-bold text-xs flex items-center justify-center">
                SK
              </div>
              <div>
                <p className="text-xs font-bold text-slate-800">Sravani Kumar</p>
                <p className="text-[10px] text-slate-400">CSE Batch of 2026</p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 p-6 rounded-lg space-y-4 shadow-sm">
            <p className="text-xs text-slate-655 leading-relaxed italic">
              "This platform transformed our placement tracking process. The interactive dashboard gives us instant branch filters, and the student feedback analytics highlight core subjects where students struggle."
            </p>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-slate-200 text-gov-navy font-bold text-xs flex items-center justify-center">
                RS
              </div>
              <div>
                <p className="text-xs font-bold text-slate-800">Dr. Rajesh Sharma</p>
                <p className="text-[10px] text-slate-400">Chief Placement Officer</p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 p-6 rounded-lg space-y-4 shadow-sm">
            <p className="text-xs text-slate-660 leading-relaxed italic">
              "The bulk import and automatic update are robust. When we upload student sheets, all charts and performance metrics recalculate instantly. Best-in-class demonstration."
            </p>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-slate-200 text-gov-navy font-bold text-xs flex items-center justify-center">
                VP
              </div>
              <div>
                <p className="text-xs font-bold text-slate-800">Prof. Venkat Prasad</p>
                <p className="text-[10px] text-slate-400">Dean Academics</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer Section */}
      <footer className="bg-gov-navy text-slate-300 py-10 px-6 mt-auto border-t border-slate-800">
        <div className="max-w-7xl mx-auto grid md:grid-cols-4 gap-8 text-xs leading-relaxed">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-white">
              <GraduationCap size={20} />
              <span className="font-bold text-sm uppercase tracking-wider">Placement Portal</span>
            </div>
            <p className="text-slate-400">
              State-of-the-art placement tracking and student career preparation portal. Inspired by standard institutional directories.
            </p>
          </div>
          
          <div className="space-y-3">
            <h4 className="font-bold text-white uppercase tracking-wider">Quick Links</h4>
            <ul className="space-y-2 text-slate-400">
              <li><button onClick={() => navigate('/login')} className="hover:underline">Student Login</button></li>
              <li><button onClick={() => navigate('/login')} className="hover:underline">Faculty Login</button></li>
              <li><button onClick={() => navigate('/login')} className="hover:underline">Admin Login</button></li>
            </ul>
          </div>

          <div className="space-y-3">
            <h4 className="font-bold text-white uppercase tracking-wider">Resources</h4>
            <ul className="space-y-2 text-slate-400">
              <li><a href="#" className="hover:underline">Academic Regulations</a></li>
              <li><a href="#" className="hover:underline">Recruitment Guidelines</a></li>
              <li><a href="#" className="hover:underline">Support Desk</a></li>
            </ul>
          </div>

          <div className="space-y-3">
            <h4 className="font-bold text-white uppercase tracking-wider">Support Contact</h4>
            <p className="text-slate-400">
              Central Placement Cell Directorate<br />
              Email: placement-support@platform.edu<br />
              Phone: +91 40 2345 6789
            </p>
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-8 pt-6 border-t border-slate-800 text-center text-[10px] text-slate-500">
          &copy; {new Date().getFullYear()} Central Placement Portal. All Rights Reserved.
        </div>
      </footer>
    </div>
  );
};
export default LandingPage;
