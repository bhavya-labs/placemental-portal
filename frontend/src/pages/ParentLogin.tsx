import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { parentService } from '../services/api';
import { GraduationCap, Mail, Phone, Lock, AlertCircle, Info, ArrowLeft } from 'lucide-react';

export const ParentLogin: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const [rollNumber, setRollNumber] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [otp, setOtp] = useState('');
  
  const [step, setStep] = useState<'request' | 'verify'>('request');
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [otpDebug, setOtpDebug] = useState<string | null>(null);

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rollNumber || !mobileNumber) {
      setError('Please fill in child roll number and parent mobile number.');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setInfo(null);

    try {
      const res = await parentService.requestOtp(parseInt(rollNumber), mobileNumber);
      setStep('verify');
      setInfo('OTP code sent successfully to registered mobile number.');
      if (res.otp_debug) {
        setOtpDebug(res.otp_debug);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to request OTP. Make sure the roll number and mobile match registered files.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp) {
      setError('Please enter the OTP verification code.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const res = await parentService.verifyOtp(parseInt(rollNumber), mobileNumber, otp);
      
      // Store token in localStorage
      localStorage.setItem('token', res.access_token);
      
      // Store parent user object
      const parentUser = {
        name: res.name,
        role: 'parent',
        email: res.email
      };
      localStorage.setItem('user', JSON.stringify(parentUser));
      
      // Force reload page to initialize session from storage
      window.location.href = '/parent/dashboard';
    } catch (err: any) {
      setIsSubmitting(false);
      setError(err.response?.data?.detail || 'Incorrect OTP code. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gov-light dark:bg-gov-dark flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-4">
        <div className="mx-auto h-12 w-12 rounded-full bg-gov-navy text-white flex items-center justify-center shadow-premium">
          <GraduationCap size={28} />
        </div>
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-gov-navy dark:text-slate-100 uppercase tracking-wide">
            Parent Access Portal
          </h2>
          <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
            Placement Portal Parent Coordinator Access
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-slate-900 py-8 px-4 border border-gov-border dark:border-slate-800 rounded-lg shadow-card sm:px-10">
          
          <button
            onClick={() => navigate('/login')}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-gov-blue font-semibold mb-6 focus:outline-none"
          >
            <ArrowLeft size={14} />
            <span>Back to Staff / Student Login</span>
          </button>

          {error && (
            <div role="alert" className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded p-3 text-xs text-red-700 dark:text-red-400 flex items-start gap-2 mb-4 animate-fadeIn">
              <AlertCircle size={14} className="shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {info && (
            <div role="status" className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-250 dark:border-emerald-900 rounded p-3 text-xs text-emerald-700 dark:text-emerald-400 flex items-start gap-2 mb-4">
              <Info size={14} className="shrink-0 mt-0.5 text-emerald-500" />
              <span>{info}</span>
            </div>
          )}

          {otpDebug && (
            <div className="bg-sky-50 dark:bg-sky-950/25 border border-sky-200 rounded p-3 text-xs text-slate-650 dark:text-slate-355 mb-4">
              <p className="font-semibold text-slate-700 dark:text-slate-300">One-Time Password (Development Mode):</p>
              <p className="font-mono text-sm mt-1 font-bold tracking-wider">{otpDebug}</p>
            </div>
          )}

          {step === 'request' ? (
            <form className="space-y-5" onSubmit={handleRequestOtp}>
              <div>
                <label htmlFor="child-roll-input" className="block text-xs font-bold uppercase tracking-wider text-slate-650 dark:text-slate-400">
                  Child Roll Number / Student ID
                </label>
                <div className="mt-1 relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <GraduationCap size={16} />
                  </span>
                  <input
                    id="child-roll-input"
                    type="number"
                    value={rollNumber}
                    onChange={(e) => setRollNumber(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-2.5 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue text-sm"
                    placeholder="Enter Student Roll Number"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="parent-phone-input" className="block text-xs font-bold uppercase tracking-wider text-slate-650 dark:text-slate-400">
                  Registered Parent Mobile Number
                </label>
                <div className="mt-1 relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Phone size={16} />
                  </span>
                  <input
                    id="parent-phone-input"
                    type="tel"
                    value={mobileNumber}
                    onChange={(e) => setMobileNumber(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-2.5 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue text-sm"
                    placeholder="Enter Registered Mobile"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-gov-navy hover:bg-gov-accent text-white py-2.5 rounded font-bold uppercase tracking-wider text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gov-blue shadow disabled:opacity-50"
              >
                {isSubmitting ? 'Verifying Student Details...' : 'Request OTP Code'}
              </button>
            </form>
          ) : (
            <form className="space-y-5" onSubmit={handleVerifyOtp}>
              <div>
                <label htmlFor="otp-verify-input" className="block text-xs font-bold uppercase tracking-wider text-slate-650 dark:text-slate-400">
                  Enter 6-Digit OTP Verification Code
                </label>
                <div className="mt-1 relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Lock size={16} />
                  </span>
                  <input
                    id="otp-verify-input"
                    type="text"
                    maxLength={6}
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-2.5 border border-gov-border dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue text-sm font-bold tracking-widest text-center"
                    placeholder="••••••"
                  />
                </div>
              </div>

              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Didn't receive code?</span>
                <button
                  type="button"
                  onClick={() => setStep('request')}
                  className="text-gov-blue hover:underline font-semibold focus:outline-none"
                >
                  Change Details
                </button>
              </div>

              <button
                type="submit"
                className="w-full bg-gov-blue hover:bg-gov-accent text-white py-2.5 rounded font-bold uppercase tracking-wider text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gov-blue shadow"
              >
                Verify & Login
              </button>
            </form>
          )}

        </div>
      </div>
    </div>
  );
};

export default ParentLogin;
