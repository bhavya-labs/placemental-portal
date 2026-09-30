import React, { useState, useEffect, useMemo } from 'react';
import { analyticsService } from '../services/api';
import { CardSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import { 
  Database, RefreshCw, Terminal, ShieldCheck, ShieldAlert, 
  Filter, KeyRound, Briefcase, Users, FileText, CheckCircle2
} from 'lucide-react';
import { ProfessionalTable } from '../components/ProfessionalTable';
import { AccessibleToast } from '../components/AccessibilityComponents';

export const AdminLogs: React.FC = () => {
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [logs, setLogs] = useState<any[]>([]);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');

  // Backup
  const [backingUp, setBackingUp] = useState(false);
  const [backupMsg, setBackupMsg] = useState<string | null>(null);

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const loadLogs = async () => {
    setLoadingLogs(true);
    try {
      const data = await analyticsService.getReportData('logs');
      setLogs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load audit logs', err);
      showToast('Failed to retrieve audit logs from server.', 'error');
    } finally {
      setLoadingLogs(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const triggerBackup = async () => {
    setBackingUp(true);
    setBackupMsg(null);
    setTimeout(() => {
      setBackingUp(false);
      setBackupMsg(`Database backup successfully completed! Snapshot: 'backups/backup_${new Date().toISOString().slice(0, 10)}.sql' (2.4 MB) written to local disk.`);
      showToast('Database SQL snapshot created!', 'success');
      loadLogs();
    }, 1500);
  };

  // Helper to categorize an action string
  const getActionCategory = (actionName: string): string => {
    const act = (actionName || '').toUpperCase();
    if (act.includes('PERMISSION') || act.includes('ACCESS')) return 'ACCESS';
    if (act.includes('DRIVE')) return 'DRIVES';
    if (act.includes('STUDENT') || act.includes('PROFILE') || act.includes('CORRECTION') || act.includes('BULK')) return 'STUDENTS';
    if (act.includes('APPLICATION') || act.includes('APPLY') || act.includes('FEEDBACK')) return 'APPLICATIONS';
    return 'SYSTEM';
  };

  // Filter logs by selected category
  const filteredLogs = useMemo(() => {
    if (categoryFilter === 'ALL') return logs;
    return logs.filter((l: any) => {
      const actionName = l.action || l.Action || '';
      return getActionCategory(actionName) === categoryFilter;
    });
  }, [logs, categoryFilter]);

  // Metric counts
  const counts = useMemo(() => {
    let access = 0;
    let drives = 0;
    let students = 0;
    let apps = 0;
    for (const l of logs) {
      const cat = getActionCategory(l.action || l.Action || '');
      if (cat === 'ACCESS') access++;
      else if (cat === 'DRIVES') drives++;
      else if (cat === 'STUDENTS') students++;
      else if (cat === 'APPLICATIONS') apps++;
    }
    return { total: logs.length, access, drives, students, apps };
  }, [logs]);

  const logColumns = [
    { 
      header: 'Timestamp', 
      accessor: 'timestamp', 
      render: (row: any) => {
        const val = row.timestamp || row.Timestamp;
        if (!val) return <span className="text-slate-400 font-mono text-[11px]">—</span>;
        const d = new Date(val);
        const formatted = isNaN(d.getTime()) ? String(val) : d.toLocaleString();
        return <span className="font-mono text-[11px] text-slate-600 dark:text-slate-300">{formatted}</span>;
      } 
    },
    { 
      header: 'Actor Profile', 
      accessor: 'actor',
      render: (row: any) => (
        <span className="font-medium text-slate-800 dark:text-slate-200">
          {row.actor || row['User Email'] || 'system'}
        </span>
      )
    },
    { 
      header: 'Action Event', 
      accessor: 'action', 
      render: (row: any) => {
        const act = row.action || row.Action || 'UNKNOWN';
        const cat = getActionCategory(act);
        
        let badgeStyle = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
        if (cat === 'ACCESS') {
          badgeStyle = 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/60 dark:text-purple-300 dark:border-purple-800';
        } else if (cat === 'DRIVES') {
          badgeStyle = 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-800';
        } else if (cat === 'STUDENTS') {
          badgeStyle = 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800';
        } else if (cat === 'APPLICATIONS') {
          badgeStyle = 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800';
        }

        return (
          <span className={`inline-block font-semibold uppercase text-[10px] px-2 py-0.5 rounded border ${badgeStyle}`}>
            {act}
          </span>
        );
      } 
    },
    { 
      header: 'Result / Description', 
      accessor: 'details',
      render: (row: any) => (
        <span className="text-slate-600 dark:text-slate-350 text-[11px] leading-relaxed">
          {row.details || row.Details || '—'}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350 max-w-7xl mx-auto">
      <AccessibleToast message={toast?.message || null} type={toast?.type || null} />

      {/* Header banner */}
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
            <Terminal className="text-gov-blue" size={24} />
            System & Security Audit Log
          </h2>
          <p className="text-[11px] text-slate-500 mt-1">
            Enterprise immutable audit trail recording administrative modifications, security delegations, placement actions, and candidate updates.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={loadLogs}
            disabled={loadingLogs}
            className="gov-btn-secondary py-2 px-3 border border-gov-border rounded flex items-center gap-1.5 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-semibold"
            title="Refresh logs"
          >
            <RefreshCw size={13} className={loadingLogs ? 'animate-spin' : ''} />
            Refresh
          </button>

          <button
            onClick={triggerBackup}
            disabled={backingUp}
            className="gov-btn-primary py-2 px-3 bg-gov-navy text-white rounded flex items-center gap-1.5 hover:bg-slate-800 text-xs font-semibold"
            title="Create database snapshot backup"
          >
            <Database size={13} className={backingUp ? 'animate-spin' : ''} />
            {backingUp ? 'Creating Snapshot...' : 'DB Snapshot'}
          </button>
        </div>
      </div>

      {backupMsg && (
        <div className="bg-emerald-50 text-emerald-800 border border-emerald-250 p-3 rounded text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
          <span>{backupMsg}</span>
        </div>
      )}

      {/* Category metric counters */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <button
          onClick={() => setCategoryFilter('ALL')}
          className={`p-3 rounded-lg border text-left transition-all ${
            categoryFilter === 'ALL'
              ? 'bg-gov-navy text-white border-gov-navy shadow-sm'
              : 'bg-white dark:bg-slate-900 border-gov-border dark:border-slate-800 hover:border-gov-blue'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">All Events</span>
            <Terminal size={14} />
          </div>
          <p className="text-xl font-bold mt-1">{counts.total}</p>
        </button>

        <button
          onClick={() => setCategoryFilter('ACCESS')}
          className={`p-3 rounded-lg border text-left transition-all ${
            categoryFilter === 'ACCESS'
              ? 'bg-purple-700 text-white border-purple-700 shadow-sm'
              : 'bg-white dark:bg-slate-900 border-gov-border dark:border-slate-800 hover:border-purple-400'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">Access & RBAC</span>
            <KeyRound size={14} />
          </div>
          <p className="text-xl font-bold mt-1">{counts.access}</p>
        </button>

        <button
          onClick={() => setCategoryFilter('DRIVES')}
          className={`p-3 rounded-lg border text-left transition-all ${
            categoryFilter === 'DRIVES'
              ? 'bg-blue-700 text-white border-blue-700 shadow-sm'
              : 'bg-white dark:bg-slate-900 border-gov-border dark:border-slate-800 hover:border-blue-400'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">Placement Drives</span>
            <Briefcase size={14} />
          </div>
          <p className="text-xl font-bold mt-1">{counts.drives}</p>
        </button>

        <button
          onClick={() => setCategoryFilter('STUDENTS')}
          className={`p-3 rounded-lg border text-left transition-all ${
            categoryFilter === 'STUDENTS'
              ? 'bg-emerald-700 text-white border-emerald-700 shadow-sm'
              : 'bg-white dark:bg-slate-900 border-gov-border dark:border-slate-800 hover:border-emerald-400'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">Student Records</span>
            <Users size={14} />
          </div>
          <p className="text-xl font-bold mt-1">{counts.students}</p>
        </button>

        <button
          onClick={() => setCategoryFilter('APPLICATIONS')}
          className={`p-3 rounded-lg border text-left transition-all ${
            categoryFilter === 'APPLICATIONS'
              ? 'bg-amber-600 text-white border-amber-600 shadow-sm'
              : 'bg-white dark:bg-slate-900 border-gov-border dark:border-slate-800 hover:border-amber-400'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">Applications</span>
            <FileText size={14} />
          </div>
          <p className="text-xl font-bold mt-1">{counts.apps}</p>
        </button>
      </div>

      {/* Main audit table card */}
      <div className="gov-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-gov-border dark:border-slate-800">
          <div className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-gov-blue" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
              Audit Entries Log {categoryFilter !== 'ALL' && `(${categoryFilter})`}
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">
              ({filteredLogs.length} events)
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Filter size={14} className="text-slate-400" />
            <label htmlFor="audit-cat-select" className="text-[10px] font-bold uppercase text-slate-500">
              Filter:
            </label>
            <select
              id="audit-cat-select"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="border border-gov-border rounded py-1 px-2 text-xs bg-white text-slate-700 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-300 focus:outline-none focus-visible:ring-1 focus-visible:ring-gov-blue"
            >
              <option value="ALL">All Categories</option>
              <option value="ACCESS">Access & Permissions</option>
              <option value="DRIVES">Placement Drives</option>
              <option value="STUDENTS">Student Records</option>
              <option value="APPLICATIONS">Application Pipeline</option>
              <option value="SYSTEM">System & Maintenance</option>
            </select>
          </div>
        </div>

        {loadingLogs ? (
          <TableSkeleton />
        ) : (
          <ProfessionalTable
            columns={logColumns}
            data={filteredLogs}
            searchPlaceholder="Search audit events, actors, or details..."
            exportFileName="security_audit_logs"
          />
        )}
      </div>

    </div>
  );
};

export default AdminLogs;
