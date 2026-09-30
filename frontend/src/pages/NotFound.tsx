import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertOctagon, ArrowLeft, GraduationCap } from 'lucide-react';

export const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gov-light dark:bg-gov-dark flex flex-col justify-center items-center px-6 text-center space-y-6">
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-8 rounded-lg shadow-card max-w-md w-full space-y-6">
        <div className="flex justify-center text-red-500">
          <AlertOctagon size={48} className="animate-bounce" />
        </div>
        
        <div className="space-y-2">
          <h2 className="text-xl font-bold text-gov-navy dark:text-slate-100 uppercase tracking-wide">
            404 - Resource Not Found
          </h2>
          <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">
            Institutional Career & Placement Portal
          </p>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
            The page or student profile you are attempting to access does not exist or has been archived. Please check the address or contact administrator.
          </p>
        </div>

        <button
          onClick={() => navigate('/')}
          className="gov-btn-primary w-full py-2.5 font-bold uppercase tracking-wider text-xs flex items-center justify-center gap-1.5"
        >
          <ArrowLeft size={14} /> Back to Gateway
        </button>
      </div>

      <div className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center gap-2">
        <GraduationCap size={16} /> Placement Portal
      </div>
    </div>
  );
};
export default NotFound;
