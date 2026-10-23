import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { GraduationCap, Eye, EyeOff, Lock, Mail, AlertCircle } from 'lucide-react';

export const Login: React.FC = () => {
  const { login, user, loading } = useAuth();
  const navigate = useNavigate();
  
  // Tab-based login role selection
  const [activeTab, setActiveTab] = useState<'student' | 'faculty' | 'admin'>('student');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleTabChange = (role: 'student' | 'faculty' | 'admin') => {
    setActiveTab(role);
    setError(null);
  };

  // Redirect if already authenticated
  React.useEffect(() => {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all credentials.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const userProfile = await login({ email, password, remember_me: rememberMe });
      
      // Verification of role matching
      if (userProfile.role !== activeTab) {
        // Faculty can log into faculty panel. If user role is admin, HOD, or TNP allow logging in as faculty too.
        if (activeTab === 'faculty' && ['admin', 'hod', 'tnp', 'faculty'].includes(userProfile.role)) {
          // Allowed
        } else {
          setError(`Incorrect portal. Your account is registered under role: '${userProfile.role.toUpperCase()}'.`);
          setIsSubmitting(false);
          return;
        }
      }

      // Redirect
      if (userProfile.role === 'admin') {
        navigate('/admin');
      } else if (['faculty', 'hod', 'tnp'].includes(userProfile.role)) {
        navigate('/faculty');
      } else {
        navigate('/student');
      }
    } catch (err: any) {
      if (!err.response) {
        setError(
          'Unable to reach backend service. The cloud server may be waking up from standby (Render Free tier). ' +
          'Please wait up to 30–45 seconds and try again.'
        );
      } else {
        setError(
          err.response?.data?.detail || 
          'Authentication failed. Please verify email and password.'
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gov-light dark:bg-gov-dark flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {/* Platform Branding header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-4">
        <div className="mx-auto h-12 w-12 rounded-full bg-gov-navy text-white flex items-center justify-center shadow-premium">
          <GraduationCap size={28} />
        </div>
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-gov-navy dark:text-slate-100 uppercase tracking-wide">
            Placement Portal
          </h2>
          <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
            Central Career & Student Placement Directorate
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-slate-900 py-8 px-4 border border-gov-border dark:border-slate-800 rounded-lg shadow-card sm:px-10">
          
          {/* Tab selector */}
          <div role="tablist" aria-label="Portal Role Selection" className="flex border-b border-gov-border dark:border-slate-800 mb-6">
            <button
              role="tab"
              aria-selected={activeTab === 'student'}
              aria-controls="login-form-panel"
              id="role-tab-student"
              onClick={() => handleTabChange('student')}
              className={`flex-1 pb-3 text-xs font-bold uppercase tracking-wider border-b-2 text-center transition-all focus:outline-none focus-visible:border-gov-blue ${
                activeTab === 'student'
                  ? 'border-gov-blue text-gov-blue'
                  : 'border-transparent text-slate-400 hover:text-slate-600'
              }`}
            >
              Student
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'faculty'}
              aria-controls="login-form-panel"
              id="role-tab-faculty"
              onClick={() => handleTabChange('faculty')}
              className={`flex-1 pb-3 text-xs font-bold uppercase tracking-wider border-b-2 text-center transition-all focus:outline-none focus-visible:border-gov-blue ${
                activeTab === 'faculty'
                  ? 'border-gov-blue text-gov-blue'
                  : 'border-transparent text-slate-400 hover:text-slate-600'
              }`}
            >
              Faculty
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'admin'}
              aria-controls="login-form-panel"
              id="role-tab-admin"
              onClick={() => handleTabChange('admin')}
              className={`flex-1 pb-3 text-xs font-bold uppercase tracking-wider border-b-2 text-center transition-all focus:outline-none focus-visible:border-gov-blue ${
                activeTab === 'admin'
                  ? 'border-gov-blue text-gov-blue'
                  : 'border-transparent text-slate-400 hover:text-slate-600'
              }`}
            >
              Admin
            </button>
          </div>

          {/* Form */}
          <form id="login-form-panel" role="tabpanel" aria-labelledby={`role-tab-${activeTab}`} className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div role="alert" className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded p-3 text-xs text-red-700 dark:text-red-400 flex items-start gap-2 animate-fadeIn">
                <AlertCircle size={14} className="shrink-0 mt-0.5" aria-hidden="true" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label htmlFor="login-email-input" className="block text-xs font-bold uppercase tracking-wider text-slate-650 dark:text-slate-400">
                Official Email Address
              </label>
              <div className="mt-1 relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400" aria-hidden="true">
                  <Mail size={16} />
                </span>
                <input
                  id="login-email-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  aria-required="true"
                  className="w-full pl-10 pr-4 py-2.5 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue text-sm"
                  placeholder="name@institution.edu"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center">
                <label htmlFor="login-password-input" className="block text-xs font-bold uppercase tracking-wider text-slate-650 dark:text-slate-400">
                  Security Password
                </label>
                <button
                  type="button"
                  className="text-xs text-gov-blue hover:underline font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue rounded px-1"
                  onClick={() => alert('Password reset is managed by the College IT Desk. Please contact admin@platform.edu.')}
                >
                  Forgot Password?
                </button>
              </div>
              <div className="mt-1 relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400" aria-hidden="true">
                  <Lock size={16} />
                </span>
                <input
                  id="login-password-input"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  aria-required="true"
                  className="w-full pl-10 pr-10 py-2.5 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue text-sm"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue rounded-r"
                >
                  {showPassword ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs">
              <label htmlFor="login-remember-input" className="flex items-center gap-2 select-none text-slate-600 dark:text-slate-400 cursor-pointer">
                <input
                  id="login-remember-input"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-gov-border text-gov-blue focus:ring-gov-blue w-4 h-4 focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-gov-blue"
                />
                <span>Remember this device</span>
              </label>
              
              <span className="text-slate-400 font-semibold uppercase">Secure SSL Session</span>
            </div>

            <div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-gov-navy hover:bg-gov-accent text-white py-2.5 rounded font-bold uppercase tracking-wider text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gov-blue shadow disabled:opacity-50"
              >
                {isSubmitting ? 'Verifying Account...' : 'Sign In to Workspace'}
              </button>
            </div>
          </form>

          <div className="mt-6 text-center border-t border-gov-border dark:border-slate-800 pt-4">
            <button
              type="button"
              onClick={() => navigate('/parent/login')}
              className="text-xs text-gov-blue hover:underline font-bold uppercase tracking-wider focus:outline-none"
            >
              Access Parent Portal (OTP Verification)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Login;
