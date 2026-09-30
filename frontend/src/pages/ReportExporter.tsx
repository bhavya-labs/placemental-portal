import React, { useState } from 'react';
import { analyticsService } from '../services/api';
import { TableSkeleton } from '../components/LoadingSkeleton';
import { 
  FileSpreadsheet, Printer, Download, Eye, FileText, 
  GraduationCap, BookOpen, Layers, Award, ShieldAlert 
} from 'lucide-react';

export const ReportExporter: React.FC = () => {
  const [exportType, setExportType] = useState<string>('student');
  const [exportDept, setExportDept] = useState<number | undefined>(undefined);
  const [filterBatch, setFilterBatch] = useState<string>('2026');
  const [exportData, setExportData] = useState<any[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [reportTitle, setReportTitle] = useState('');

  const handlePreviewReport = async () => {
    setPreviewLoading(true);
    try {
      const data = await analyticsService.getReportData(exportType, exportDept, filterBatch);
      setExportData(data);
      
      const titles: Record<string, string> = {
        student: 'Student Performance & Placement Preparation Profile',
        company: 'Registered Recruiters & Annual CTC Offer Matrix',
        placement: 'Campus Recruitment Applications Outcomes Summary',
        department: 'Branch-wise Placement Statistics & Package Ratios',
        ai: 'Placement Preparation & Skill Improvement Areas Report'
      };
      setReportTitle(titles[exportType] || 'Institutional Career Report');
    } catch (err) {
      alert('Failed to preview requested report records.');
    } finally {
      setExportLoading(false);
    }
  };

  // State mapper wrapper to avoid lint errors
  const setExportLoading = (val: boolean) => {
    setPreviewLoading(val);
  };

  const handlePrint = () => {
    window.print();
  };

  // Convert JSON to CSV file downloads
  const handleExportCSV = () => {
    if (exportData.length === 0) return;
    const headers = Object.keys(exportData[0]).join(',');
    const rows = exportData.map(row => 
      Object.values(row).map(val => {
        const str = String(val ?? '');
        return str.includes(',') ? `"${str.replace(/"/g, '""')}"` : str;
      }).join(',')
    );
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers, ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `placement_report_${exportType}_batch_${filterBatch}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Convert JSON to tab-separated XLS formats
  const handleExportExcel = () => {
    if (exportData.length === 0) return;
    const headers = Object.keys(exportData[0]).join('\t');
    const rows = exportData.map(row => 
      Object.values(row).map(val => String(val ?? '')).join('\t')
    );
    const xlsContent = [headers, ...rows].join('\n');
    const blob = new Blob([xlsContent], { type: 'application/vnd.ms-excel;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `placement_report_${exportType}_batch_${filterBatch}.xls`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350 print-expand">
      
      {/* Header card block */}
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card no-print">
        <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
          <FileSpreadsheet className="text-gov-blue" size={24} />
          Institutional Evaluation Report Exporter
        </h2>
        <p className="text-[10px] text-slate-500 mt-1">
          Compile official metrics, company drive statistics, candidate outcomes, and placement preparation listings into PDF, Excel, or CSV files.
        </p>
      </div>

      {/* Configuration filters */}
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-4 rounded-lg shadow-card space-y-4 no-print">
        <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <Layers size={14} className="text-gov-blue" />
          Configure Report Data Snapshot
        </h3>
        
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label htmlFor="export-category-select" className="block font-bold text-slate-500 uppercase mb-1">Report Category</label>
            <select
              id="export-category-select"
              value={exportType}
              onChange={(e) => {
                setExportType(e.target.value);
                setExportData([]);
              }}
              className="border border-gov-border rounded p-2 bg-white text-slate-850 dark:bg-slate-950 dark:border-slate-850 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-gov-blue"
            >
              <option value="student">Student Performance & Preparation</option>
              <option value="company">Registered Recruiters & CTC Matrix</option>
              <option value="placement">Placement Applications Outcomes</option>
              <option value="department">Branch-wise Statistics</option>
              <option value="ai">Placement Preparation Assessment Nominees</option>
            </select>
          </div>

          <div>
            <label htmlFor="export-branch-select" className="block font-bold text-slate-500 uppercase mb-1">Branch / Department</label>
            <select
              id="export-branch-select"
              value={exportDept || ''}
              onChange={(e) => setExportDept(e.target.value ? Number(e.target.value) : undefined)}
              className="border border-gov-border rounded p-2 bg-white text-slate-850 dark:bg-slate-955 dark:border-slate-850 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-gov-blue"
            >
              <option value="">All Branches</option>
              <option value="1">Computer Science (CSE)</option>
              <option value="2">Information Tech (IT)</option>
              <option value="3">Electronics (ECE)</option>
              <option value="4">Electrical (EEE)</option>
              <option value="5">Mechanical (MECH)</option>
              <option value="6">Civil (CIVIL)</option>
            </select>
          </div>

          <div>
            <label htmlFor="export-batch-select" className="block font-bold text-slate-500 uppercase mb-1">Batch Year</label>
            <select
              id="export-batch-select"
              value={filterBatch}
              onChange={(e) => {
                setFilterBatch(e.target.value);
                setExportData([]);
              }}
              className="border border-gov-border rounded p-2 bg-white text-slate-855 dark:bg-slate-955 dark:border-slate-850 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-gov-blue"
            >
              <option value="2026">2026 (Active)</option>
              <option value="2025">2025 (Graduated)</option>
            </select>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handlePreviewReport}
              className="gov-btn-primary py-2 px-4 rounded font-bold uppercase tracking-wider bg-gov-navy border-0 text-white hover:bg-gov-accent flex items-center gap-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
            >
              <Eye size={14} /> Preview Sheet
            </button>
            
            {exportData.length > 0 && (
              <>
                <button
                  onClick={handlePrint}
                  className="gov-btn-secondary border border-gov-border hover:bg-slate-55 dark:hover:bg-slate-800 py-2 px-4 rounded font-bold uppercase tracking-wider flex items-center gap-1.5 focus:outline-none"
                >
                  <Printer size={14} className="text-gov-blue" /> Print PDF
                </button>
                <button
                  onClick={handleExportExcel}
                  className="gov-btn-secondary border border-gov-border hover:bg-slate-55 dark:hover:bg-slate-800 py-2 px-4 rounded font-bold uppercase tracking-wider flex items-center gap-1.5 focus:outline-none"
                >
                  <Download size={14} className="text-emerald-600" /> Export Excel
                </button>
                <button
                  onClick={handleExportCSV}
                  className="gov-btn-secondary border border-gov-border hover:bg-slate-55 dark:hover:bg-slate-800 py-2 px-4 rounded font-bold uppercase tracking-wider flex items-center gap-1.5 focus:outline-none"
                >
                  <Download size={14} className="text-blue-600" /> Export CSV
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Report preview layout */}
      {previewLoading ? (
        <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-8 rounded-lg">
          <TableSkeleton />
        </div>
      ) : exportData.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 rounded-lg p-12 text-center text-slate-400 uppercase font-bold tracking-wide no-print">
          Configure filters and click "Preview Sheet" to verify datasets before file generation.
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-850 rounded-lg p-8 shadow-card space-y-6 print-expand">
          
          {/* Header block for printed page */}
          <div className="flex justify-between items-center border-b-2 border-slate-900 dark:border-slate-700 pb-4">
            <div className="flex items-center gap-3">
              <div className="bg-slate-950 dark:bg-slate-800 text-white p-2.5 rounded-full flex items-center justify-center">
                <GraduationCap size={32} />
              </div>
              <div className="space-y-0.5">
                <h2 className="text-base font-extrabold text-slate-900 dark:text-slate-100 uppercase tracking-wide leading-tight">
                  Placement Portal
                </h2>
                <p className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider">
                  Official Institutional Career Evaluation & Statistics Report
                </p>
              </div>
            </div>
            
            <div className="text-right text-[10px] text-slate-500 font-bold space-y-0.5">
              <p>BATCH YEAR: {filterBatch}</p>
              <p>COMPILED ON: {new Date().toLocaleDateString()}</p>
              <p className="text-slate-400">REPORT ID: REP-{exportType.toUpperCase()}-08</p>
            </div>
          </div>

          {/* Title description */}
          <div className="space-y-1">
            <h3 className="text-sm font-extrabold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <FileText className="text-gov-blue shrink-0" size={16} />
              {reportTitle}
            </h3>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              The database table below represents the compiled audit records. Authenticated and compiled by College Placement Cell.
            </p>
          </div>

          {/* Responsive Data Table */}
          <div className="overflow-x-auto border border-slate-300 dark:border-slate-850 rounded">
            <table className="min-w-full divide-y divide-slate-350 dark:divide-slate-800 text-left text-xs">
              <thead>
                <tr className="bg-slate-100 dark:bg-slate-800">
                  {Object.keys(exportData[0]).map((key, i) => (
                    <th key={i} className="px-4 py-3 font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 border-b border-slate-350 dark:border-slate-750">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {exportData.map((row, rIdx) => (
                  <tr key={rIdx} className={rIdx % 2 === 1 ? 'bg-slate-50/50 dark:bg-slate-900/40' : ''}>
                    {Object.values(row).map((val: any, cIdx) => (
                      <td key={cIdx} className="px-4 py-3 text-slate-650 dark:text-slate-400 font-medium">
                        {typeof val === 'boolean' ? (val ? 'Yes' : 'No') : (val ?? '-')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Signature slots for print output */}
          <div className="pt-20 flex justify-between items-center text-[10px] font-bold text-slate-500">
            <div className="text-center space-y-1">
              <div className="h-0.5 w-40 bg-slate-350 mx-auto"></div>
              <p className="uppercase">Compiled by Coordinator</p>
            </div>
            <div className="text-center space-y-1">
              <div className="h-0.5 w-40 bg-slate-350 mx-auto"></div>
              <p className="uppercase">Chief Placement Director Sign</p>
            </div>
          </div>

        </div>
      )}

    </div>
  );
};

export default ReportExporter;
