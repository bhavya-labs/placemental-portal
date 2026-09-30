import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Search as SearchIcon, Users, Briefcase, Globe, ArrowRight, X, FileText, Calendar, AlertCircle } from 'lucide-react';
import { TableSkeleton } from '../components/LoadingSkeleton';

export const Search: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<{
    students: any[];
    drives: any[];
    companies: any[];
    applications: any[];
    activities: any[];
  }>({
    students: [],
    drives: [],
    companies: [],
    applications: [],
    activities: []
  });

  const inputRef = useRef<HTMLInputElement>(null);

  const handleSearch = async (searchQuery: string) => {
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      setResults({ students: [], drives: [], companies: [], applications: [], activities: [] });
      setError(null);
      return;
    }

    // Minimum search length check: Must be at least 2 characters, or a numeric digit (Roll Number ID)
    if (trimmed.length < 2 && !/^\d+$/.test(trimmed)) {
      setResults({ students: [], drives: [], companies: [], applications: [], activities: [] });
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/api/search', {
        params: { q: trimmed }
      });
      const data = response.data || {};
      setResults({
        students: Array.isArray(data.students) ? data.students : [],
        drives: Array.isArray(data.drives) ? data.drives : [],
        companies: Array.isArray(data.companies) ? data.companies : [],
        applications: Array.isArray(data.applications) ? data.applications : [],
        activities: Array.isArray(data.activities) ? data.activities : []
      });
    } catch (err: any) {
      console.error('Search failed', err);
      setError(err.response?.data?.detail || 'Something went wrong while processing your request. Please try again.');
      setResults({ students: [], drives: [], companies: [], applications: [], activities: [] });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      handleSearch(query);
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  const handleClear = () => {
    setQuery('');
    setResults({ students: [], drives: [], companies: [], applications: [], activities: [] });
    setError(null);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Check if we have any search results at all
  const hasResults = 
    results.students.length > 0 || 
    results.drives.length > 0 || 
    results.companies.length > 0 || 
    results.applications.length > 0 || 
    results.activities.length > 0;

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350">
      
      {/* Search Input Bar Card */}
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-6 rounded-lg shadow-card space-y-4">
        <div className="text-center max-w-xl mx-auto space-y-2">
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center justify-center gap-2">
            <SearchIcon className="text-gov-blue" size={22} />
            Institutional Directory Search
          </h2>
          <p className="text-[10px] text-slate-450 leading-relaxed">
            Search dynamically across authorized student profiles, recruitment drives, activities, and registered firms.
          </p>
        </div>

        <div className="max-w-xl mx-auto flex items-center gap-2 border border-gov-border rounded p-2.5 bg-slate-50 dark:bg-slate-955 shadow-inner relative">
          <SearchIcon size={18} className="text-slate-400 shrink-0 ml-1" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type roll number, name, role, activity, or firm..."
            className="w-full text-xs font-medium bg-transparent focus:outline-none text-slate-855 dark:text-slate-100 pr-8"
          />
          {query && (
            <button 
              onClick={handleClear}
              className="absolute right-3 p-1 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-full text-slate-400 hover:text-slate-650"
              title="Clear Search"
              aria-label="Clear Search Input"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {query.trim().length > 0 && query.trim().length < 2 && !/^\d+$/.test(query.trim()) && (
          <p className="text-center text-[10px] text-amber-600 font-semibold">
            Please enter at least 2 characters to trigger search.
          </p>
        )}
      </div>

      {/* Error Alert Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-955/20 border border-red-200 dark:border-red-900 rounded p-4 flex items-center gap-2 text-red-750 dark:text-red-300">
          <AlertCircle size={16} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? <TableSkeleton /> : (
        <div className="space-y-6">
          {!query.trim() && !hasResults && (
            <div className="text-center py-10 bg-slate-50 dark:bg-slate-900/50 border border-gov-border dark:border-slate-850 rounded-lg">
              <p className="text-slate-450 italic font-semibold">Enter search parameters above to view records.</p>
            </div>
          )}

          {query.trim() && !hasResults && !error && (
            <div className="text-center py-10 bg-slate-50 dark:bg-slate-900/50 border border-gov-border dark:border-slate-850 rounded-lg">
              <p className="text-slate-450 italic font-semibold">No records found matching the specified parameters.</p>
            </div>
          )}

          {hasResults && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              
              {/* Category 1: Students */}
              <div className="gov-card space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-gov-border dark:border-slate-800">
                  <span className="font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Users size={16} className="text-gov-blue" /> Scoped Candidates
                  </span>
                  <span className="bg-slate-100 dark:bg-slate-800 text-slate-500 font-bold px-2 py-0.5 rounded text-[9px]">
                    {results.students.length} found
                  </span>
                </div>

                {results.students.length === 0 ? (
                  <p className="text-center py-6 text-slate-400 italic">No candidates found.</p>
                ) : (
                  <div className="space-y-3">
                    {results.students.map((student: any) => {
                      const canNavigate = user && ['admin', 'faculty', 'hod'].includes(user.role);
                      return (
                        <div 
                          key={student.id} 
                          tabIndex={canNavigate ? 0 : -1}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && canNavigate) {
                              navigate(`/student-360/${student.id}`);
                            }
                          }}
                          onClick={() => canNavigate && navigate(`/student-360/${student.id}`)}
                          className={`p-3 rounded border border-gov-border dark:border-slate-855 bg-slate-50 dark:bg-slate-950 space-y-1.5 focus:ring-1 focus:ring-gov-blue focus:outline-none ${
                            canNavigate ? 'cursor-pointer hover:border-gov-blue/50' : ''
                          }`}
                        >
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-slate-800 dark:text-slate-200">{student.name}</span>
                            <span className="text-[9px] text-slate-400 font-mono">#{student.id}</span>
                          </div>
                          <p className="text-[10px] text-slate-550">{student.dept_code} Department • {student.cgpa} CGPA</p>
                          
                          {canNavigate && (
                            <div className="flex items-center justify-end text-[9px] text-gov-blue font-bold uppercase gap-0.5">
                              <span>360 Profile</span> <ArrowRight size={10} />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Category 2: Placement Drives */}
              <div className="gov-card space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-gov-border dark:border-slate-800">
                  <span className="font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Briefcase size={16} className="text-emerald-500" /> Active Drives
                  </span>
                  <span className="bg-slate-100 dark:bg-slate-800 text-slate-500 font-bold px-2 py-0.5 rounded text-[9px]">
                    {results.drives.length} found
                  </span>
                </div>

                {results.drives.length === 0 ? (
                  <p className="text-center py-6 text-slate-400 italic">No recruitment drives found.</p>
                ) : (
                  <div className="space-y-3">
                    {results.drives.map((drive: any) => (
                      <div 
                        key={drive.id}
                        className="p-3 rounded border border-gov-border dark:border-slate-855 bg-slate-50 dark:bg-slate-955 space-y-1.5"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <span className="font-bold text-slate-855 dark:text-slate-100 block">{drive.role}</span>
                            <span className="text-[9px] text-slate-400 uppercase font-semibold">{drive.company_name}</span>
                          </div>
                          <span className="bg-emerald-50 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-400 font-bold text-[8px] px-1.5 rounded uppercase">
                            {drive.package_lpa} LPA
                          </span>
                        </div>
                        <p className="text-[9px] text-slate-550 capitalize">Status: <span className="font-bold">{drive.status.replace(/_/g, ' ').toLowerCase()}</span></p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Category 3: Applications */}
              <div className="gov-card space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-gov-border dark:border-slate-800">
                  <span className="font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <FileText size={16} className="text-indigo-500" /> Scoped Applications
                  </span>
                  <span className="bg-slate-100 dark:bg-slate-800 text-slate-500 font-bold px-2 py-0.5 rounded text-[9px]">
                    {results.applications.length} found
                  </span>
                </div>

                {results.applications.length === 0 ? (
                  <p className="text-center py-6 text-slate-400 italic">No applications found.</p>
                ) : (
                  <div className="space-y-3">
                    {results.applications.map((app: any) => (
                      <div 
                        key={app.id}
                        className="p-3 rounded border border-gov-border dark:border-slate-855 bg-slate-50 dark:bg-slate-950 space-y-1.5"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <span className="font-bold text-slate-800 dark:text-slate-200 block">{app.student_name}</span>
                            <span className="text-[9px] text-slate-400 uppercase font-semibold">{app.company_name} • {app.role}</span>
                          </div>
                          <span className={`px-2 py-0.5 rounded text-[8px] font-bold ${
                            app.status === 'Selected' ? 'bg-emerald-50 text-emerald-700' :
                            app.status === 'Rejected' ? 'bg-red-50 text-red-700' :
                            'bg-blue-50 text-blue-700'
                          }`}>
                            {app.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Category 4: Companies */}
              <div className="gov-card space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-gov-border dark:border-slate-800">
                  <span className="font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Globe size={16} className="text-amber-500" /> Registered Firms
                  </span>
                  <span className="bg-slate-100 dark:bg-slate-800 text-slate-500 font-bold px-2 py-0.5 rounded text-[9px]">
                    {results.companies.length} found
                  </span>
                </div>

                {results.companies.length === 0 ? (
                  <p className="text-center py-6 text-slate-400 italic">No registered firms found.</p>
                ) : (
                  <div className="space-y-3">
                    {results.companies.map((company: any) => (
                      <div 
                        key={company.id}
                        className="p-3 rounded border border-gov-border dark:border-slate-855 bg-slate-50 dark:bg-slate-950 space-y-1.5"
                      >
                        <span className="font-bold text-slate-800 dark:text-slate-200 block">{company.name}</span>
                        <p className="text-[10px] text-slate-500">{company.industry} Industry • {company.website}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Category 5: Activities */}
              <div className="gov-card space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-gov-border dark:border-slate-800">
                  <span className="font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Calendar size={16} className="text-pink-500" /> Scoped Activities
                  </span>
                  <span className="bg-slate-100 dark:bg-slate-800 text-slate-500 font-bold px-2 py-0.5 rounded text-[9px]">
                    {results.activities.length} found
                  </span>
                </div>

                {results.activities.length === 0 ? (
                  <p className="text-center py-6 text-slate-400 italic">No activities found.</p>
                ) : (
                  <div className="space-y-3">
                    {results.activities.map((act: any) => (
                      <div 
                        key={act.id}
                        className="p-3 rounded border border-gov-border dark:border-slate-855 bg-slate-50 dark:bg-slate-955 space-y-1.5"
                      >
                        <span className="font-bold text-slate-855 dark:text-slate-100 block">{act.name}</span>
                        <div className="flex justify-between items-center text-[9px] text-slate-400 font-semibold">
                          <span className="capitalize">{act.activity_type.toLowerCase()}</span>
                          <span>{act.date}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>
          )}
        </div>
      )}

    </div>
  );
};

export default Search;
