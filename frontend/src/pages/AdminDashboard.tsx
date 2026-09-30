import React, { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { studentService, analyticsService } from '../services/api';
import { CardSkeleton } from '../components/LoadingSkeleton';
import { 
  Users, Award, Star, Briefcase, LayoutDashboard, 
  MapPin, Activity, ShieldCheck, Upload, CheckCircle2, ShieldAlert, RefreshCw 
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { AccessibleChart, AccessibleModal, AccessibleToast } from '../components/AccessibilityComponents';

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState<any | null>(null);

  // Bulk uploader modal state
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkInput, setBulkInput] = useState('');
  const [bulkSuccess, setBulkSuccess] = useState<string | null>(null);
  const [bulkError, setBulkError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const handleBulkSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBulkSuccess(null);
    setBulkError(null);
    setUploading(true);

    try {
      const payload = JSON.parse(bulkInput);
      if (!Array.isArray(payload)) {
        throw new Error('Data payload must be a JSON array of student profiles.');
      }
      
      const response = await studentService.bulkUpload(payload);
      setBulkSuccess(response.message || 'Successfully bulk imported student records and retrained models!');
      setBulkInput('');
      showToast('Students bulk upload complete!', 'success');
      loadAdminOverview();
    } catch (err: any) {
      setBulkError(err.message || err.response?.data?.detail || 'Failed to parse JSON. Verify template formatting.');
      showToast('Bulk upload parsing failed.', 'error');
    } finally {
      setUploading(false);
    }
  };

  const loadAdminOverview = async () => {
    setLoading(true);
    try {
      const stats = await analyticsService.getDashboardStats();
      setKpis(stats);
    } catch (err) {
      console.error('Failed to load admin overview metrics', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminOverview();
  }, []);

  const COLORS = ['#0F2942', '#328CC1', '#D9B310', '#B45309', '#0D9488'];

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350">
      <AccessibleToast message={toast?.message || null} type={toast?.type || null} />

      {/* Header banner */}
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
            <LayoutDashboard className="text-gov-blue" size={24} />
            Admin Operations & System Center
          </h2>
          <p className="text-[10px] text-slate-500 mt-1">
            Monitor system metrics, coordinate placement logs, modify credentials, and evaluate institutional outcomes.
          </p>
        </div>

        <button
          onClick={() => setShowBulkModal(true)}
          className="gov-btn-primary py-2 px-3 bg-gov-navy text-white rounded flex items-center gap-1.5 hover:bg-slate-800 text-xs font-semibold shrink-0"
          title="Import batch student records"
        >
          <Upload size={14} />
          Bulk Import Records
        </button>
      </div>

      {/* Bulk Importer Modal */}
      <AccessibleModal
        isOpen={showBulkModal}
        onClose={() => {
          setShowBulkModal(false);
          setBulkSuccess(null);
          setBulkError(null);
        }}
        title="Batch Student Records Importer"
        maxWidth="max-w-2xl"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-500 leading-normal">
            Insert a JSON array containing candidate records to register them in the relational tables and refresh profile metrics.
          </p>

          <form onSubmit={handleBulkSubmit} className="space-y-4">
            <div>
              <label htmlFor="modal-bulk-json-input" className="block font-bold text-slate-600 dark:text-slate-300 uppercase text-[10px] mb-1">
                Student JSON Array Format
              </label>
              <textarea
                id="modal-bulk-json-input"
                required
                value={bulkInput}
                onChange={(e) => setBulkInput(e.target.value)}
                className="w-full h-48 p-3 border border-gov-border rounded dark:bg-slate-950 font-mono text-[10px] focus:outline-none focus:ring-1 focus:ring-gov-blue"
                placeholder={`[
  {
    "name": "Suresh Kumar",
    "email": "suresh@university.edu",
    "dept_id": 1,
    "cgpa": 8.4,
    "attendance": 88.0,
    "backlogs": 0,
    "gender": "Male",
    "batch": "2026",
    "skills": ["Java", "SQL", "React"]
  }
]`}
              />
            </div>

            {bulkSuccess && (
              <div className="bg-emerald-50 text-emerald-800 border border-emerald-250 p-3 rounded font-bold uppercase flex items-center gap-2">
                <CheckCircle2 size={16} />
                {bulkSuccess}
              </div>
            )}

            {bulkError && (
              <div className="bg-red-50 text-red-800 border border-red-250 p-3 rounded font-bold uppercase flex items-center gap-2">
                <ShieldAlert size={16} />
                {bulkError}
              </div>
            )}

            <div className="flex gap-2 justify-end pt-2">
              <button
                type="button"
                onClick={() => setShowBulkModal(false)}
                className="px-4 py-2 border border-gov-border rounded hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-semibold"
              >
                Close
              </button>
              <button
                type="submit"
                disabled={uploading || !bulkInput}
                className="gov-btn-primary px-4 py-2 bg-gov-navy text-white rounded font-bold text-xs flex items-center gap-1.5 hover:bg-slate-800"
              >
                <RefreshCw size={12} className={uploading ? 'animate-spin' : ''} />
                {uploading ? 'Processing Records...' : 'Import Records'}
              </button>
            </div>
          </form>
        </div>
      </AccessibleModal>

      {loading || !kpis ? <CardSkeleton /> : (
        <>
          {/* KPI metrics row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="gov-card flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Evaluated Students</p>
                <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">{kpis.total_students} candidates</p>
                <p className="text-[10px] text-slate-500 mt-1">Status: Registered Accounts</p>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                <Users size={20} />
              </div>
            </div>

            <div className="gov-card flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Placed Candidates</p>
                <div className="flex items-baseline gap-1 mt-1">
                  <p className="text-2xl font-bold text-gov-navy dark:text-slate-200">{kpis.placed_students}</p>
                  <span className="text-[10px] text-slate-500">offers</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-1">Success Ratio: {kpis.placement_percentage}%</p>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                <Award size={20} />
              </div>
            </div>

            <div className="gov-card flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Highest Offer CTC</p>
                <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">{kpis.highest_package} LPA</p>
                <p className="text-[10px] text-slate-500 mt-1">Industry Standard packages</p>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                <Star size={20} />
              </div>
            </div>

            <div className="gov-card flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Average Offer CTC</p>
                <p className="text-2xl font-bold text-gov-navy dark:text-slate-200 mt-1">{kpis.average_package} LPA</p>
                <p className="text-[10px] text-slate-500 mt-1">Median CTC: {kpis.median_package} LPA</p>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded text-gov-navy dark:text-slate-300">
                <Briefcase size={20} />
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            
            {/* Recharts Branch distribution */}
            <div className="gov-card space-y-4">
              <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider border-b border-gov-border dark:border-slate-850 pb-2">
                Branch-wise Placement Statistics Summary
              </h3>
              
              <div className="h-56">
                <AccessibleChart
                  title="Branch Placement Distribution Bar Chart"
                  description="Aggregate comparison of placed student percentages across academic divisions."
                  data={kpis.branch_hiring || []}
                  keys={[{ dataKey: 'placed', label: 'Placed Count' }]}
                  labelKey="dept_code"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={kpis.branch_hiring || []}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="dept_code" tick={{ fontSize: 9 }} />
                      <YAxis tick={{ fontSize: 9 }} />
                      <Tooltip />
                      <Bar dataKey="placed" fill="#328CC1" radius={[4, 4, 0, 0]}>
                        {(kpis.branch_hiring || []).map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </AccessibleChart>
              </div>
            </div>

            {/* Recruiters analysis */}
            <div className="gov-card space-y-4">
              <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider border-b border-gov-border dark:border-slate-850 pb-2">
                Top Recruiters by Selected Student Candidates
              </h3>
              
              <div className="space-y-3">
                {kpis.company_hiring && kpis.company_hiring.map((comp: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-center border-b border-gov-border dark:border-slate-850 pb-2.5 last:border-0 last:pb-0">
                    <div className="space-y-0.5">
                      <span className="font-bold text-slate-800 dark:text-slate-200 uppercase">{comp.company_name}</span>
                    </div>
                    <span className="bg-gov-blue/10 text-gov-blue dark:bg-sky-950/20 dark:text-sky-400 px-2 py-0.5 rounded text-[10px] font-bold">
                      {comp.hires} hires
                    </span>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </>
      )}

    </div>
  );
};

export default AdminDashboard;
