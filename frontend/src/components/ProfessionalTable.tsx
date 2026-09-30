import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ArrowUpDown, ArrowUp, ArrowDown, Search, Download } from 'lucide-react';

interface Column {
  header: string;
  accessor: string;
  render?: (row: any) => React.ReactNode;
  sortable?: boolean;
}

export interface ServerPaginationProps {
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (newPage: number) => void;
  onPageSizeChange?: (newPageSize: number) => void;
  pageSizeOptions?: number[];
}

interface ProfessionalTableProps {
  columns: Column[];
  data: any[];
  searchPlaceholder?: string;
  exportFileName?: string;
  serverPagination?: ServerPaginationProps;
  onSearchChange?: (query: string) => void;
  searchValue?: string;
  hideSearch?: boolean;
}

export const ProfessionalTable: React.FC<ProfessionalTableProps> = ({
  columns,
  data,
  searchPlaceholder = 'Search records...',
  exportFileName = 'table_export',
  serverPagination,
  onSearchChange,
  searchValue,
  hideSearch = false
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const isServer = Boolean(serverPagination);
  const currentSearch = searchValue !== undefined ? searchValue : searchQuery;

  // Filter logic
  const filteredData = useMemo(() => {
    if (isServer) return data;
    if (!currentSearch) return data;
    
    return data.filter((row) => {
      return Object.keys(row).some((key) => {
        const val = row[key];
        if (val === null || val === undefined) return false;
        return String(val).toLowerCase().includes(currentSearch.toLowerCase());
      });
    });
  }, [data, currentSearch, isServer]);

  // Sorting logic
  const sortedData = useMemo(() => {
    if (!sortColumn) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];

      if (aVal === undefined || aVal === null) return 1;
      if (bVal === undefined || bVal === null) return -1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      const strA = String(aVal).toLowerCase();
      const strB = String(bVal).toLowerCase();

      if (strA < strB) return sortDirection === 'asc' ? -1 : 1;
      if (strA > strB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredData, sortColumn, sortDirection]);

  // Pagination parameters
  const activePage = isServer ? serverPagination!.page : currentPage;
  const activePageSize = isServer ? serverPagination!.pageSize : pageSize;
  const totalRecords = isServer ? serverPagination!.total : sortedData.length;
  const totalPages = isServer
    ? Math.max(Math.ceil(serverPagination!.total / serverPagination!.pageSize), 1)
    : Math.max(Math.ceil(sortedData.length / pageSize), 1);

  // Pagination bounds
  const paginatedData = useMemo(() => {
    if (isServer) return sortedData;
    const startIndex = (currentPage - 1) * pageSize;
    return sortedData.slice(startIndex, startIndex + pageSize);
  }, [sortedData, currentPage, pageSize, isServer]);

  const handlePageChange = (newPage: number) => {
    const clamped = Math.max(1, Math.min(newPage, totalPages));
    if (isServer) {
      serverPagination!.onPageChange(clamped);
    } else {
      setCurrentPage(clamped);
    }
  };

  const handlePageSizeChange = (newSize: number) => {
    if (isServer) {
      serverPagination!.onPageSizeChange?.(newSize);
      serverPagination!.onPageChange(1);
    } else {
      setPageSize(newSize);
      setCurrentPage(1);
    }
  };

  const pageNumbers = useMemo(() => {
    const pages: (number | string)[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (activePage > 3) pages.push('...');
      const start = Math.max(2, activePage - 1);
      const end = Math.min(totalPages - 1, activePage + 1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (activePage < totalPages - 2) pages.push('...');
      pages.push(totalPages);
    }
    return pages;
  }, [totalPages, activePage]);

  const handleSort = (columnName: string) => {
    if (sortColumn === columnName) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else {
        setSortColumn(null); // Clear sort
      }
    } else {
      setSortColumn(columnName);
      setSortDirection('asc');
    }
    if (!isServer) {
      setCurrentPage(1);
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (searchValue === undefined) {
      setSearchQuery(val);
    }
    if (onSearchChange) {
      onSearchChange(val);
    }
    if (!isServer) {
      setCurrentPage(1);
    }
  };

  // Convert table data to CSV and trigger file download
  const handleExportCSV = () => {
    if (data.length === 0) return;

    // Headers
    const headers = columns.map(c => `"${c.header.replace(/"/g, '""')}"`).join(',');
    
    // Rows
    const rows = sortedData.map(row => {
      return columns.map(col => {
        // Resolve raw accessor value or fallback to string representation
        const cellVal = row[col.accessor];
        const valStr = cellVal !== undefined && cellVal !== null ? String(cellVal) : '';
        return `"${valStr.replace(/"/g, '""')}"`;
      }).join(',');
    });

    const csvContent = [headers, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `${exportFileName}_${new Date().toISOString().slice(0,10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const searchId = useMemo(() => `table-search-${Math.random().toString(36).substr(2, 9)}`, []);
  const pageSizeId = useMemo(() => `table-size-${Math.random().toString(36).substr(2, 9)}`, []);

  return (
    <div className="space-y-4">
      {/* Top action grid */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between no-print">
        {/* Search Input bar */}
        {!hideSearch && (
          <div className="relative w-full sm:w-80">
            <label htmlFor={searchId} className="sr-only">
              {searchPlaceholder}
            </label>
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-400" aria-hidden="true">
              <Search size={16} />
            </span>
            <input
              id={searchId}
              type="text"
              placeholder={searchPlaceholder}
              value={currentSearch}
              onChange={handleSearchChange}
              className="w-full pl-9 pr-4 py-2 border border-gov-border rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100 text-sm"
            />
          </div>
        )}

        {/* Exporter and count menu */}
        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          <button
            onClick={handleExportCSV}
            aria-label={`Export ${exportFileName.replace(/_/g, ' ')} as CSV file`}
            className="gov-btn-secondary py-2 border border-gov-border rounded flex items-center gap-2 hover:bg-slate-50 dark:hover:bg-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
            title="Download CSV"
          >
            <Download size={14} className="text-gov-blue" aria-hidden="true" />
            <span className="text-xs font-semibold">Export CSV</span>
          </button>
          
          <div className="flex items-center gap-1.5">
            <label htmlFor={pageSizeId} className="text-[10px] font-bold text-slate-500 uppercase">
              Page Size:
            </label>
            <select
              id={pageSizeId}
              value={activePageSize}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              className="border border-gov-border rounded py-2 px-3 text-xs bg-white text-slate-700 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
            >
              {(serverPagination?.pageSizeOptions || [10, 20, 25, 50, 100, 200]).map((size) => (
                <option key={size} value={size}>
                  {size} rows
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main Table view */}
      <div className="overflow-x-auto border border-gov-border dark:border-slate-800 rounded-lg bg-white dark:bg-slate-900">
        <table className="min-w-full divide-y divide-gov-border dark:divide-slate-800 text-left">
          <caption className="sr-only">List of {exportFileName.replace(/_/g, ' ')}</caption>
          <thead>
            <tr>
              {columns.map((col) => {
                const isSorted = sortColumn === col.accessor;
                const ariaSortValue = isSorted
                  ? (sortDirection === 'asc' ? 'ascending' : 'descending')
                  : undefined;
                return (
                  <th
                    key={col.accessor}
                    scope="col"
                    aria-sort={ariaSortValue}
                    onClick={() => col.sortable !== false && handleSort(col.accessor)}
                    className={`gov-table-th select-none ${col.sortable !== false ? 'cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700 focus-visible:bg-slate-100 dark:focus-visible:bg-slate-700 focus:outline-none' : ''}`}
                    tabIndex={col.sortable !== false ? 0 : undefined}
                    onKeyDown={(e) => {
                      if (col.sortable !== false && (e.key === ' ' || e.key === 'Enter')) {
                        e.preventDefault();
                        handleSort(col.accessor);
                      }
                    }}
                  >
                    <div className="flex items-center gap-1">
                      <span>{col.header}</span>
                      {col.sortable !== false && (
                        <span className="text-slate-400 no-print" aria-hidden="true">
                          {sortColumn === col.accessor ? (
                            sortDirection === 'asc' ? <ArrowUp size={12} /> : <ArrowDown size={12} />
                          ) : (
                            <ArrowUpDown size={12} />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-gov-border dark:divide-slate-850">
            {paginatedData.length > 0 ? (
              paginatedData.map((row, rIdx) => (
                <tr 
                  key={rIdx} 
                  className={`hover:bg-slate-50/50 dark:hover:bg-slate-850/50 transition-colors ${
                    rIdx % 2 === 1 ? 'bg-slate-50/20 dark:bg-slate-900/30' : ''
                  }`}
                >
                  {columns.map((col, cIdx) => (
                    <td 
                      key={col.accessor} 
                      scope={cIdx === 0 ? 'row' : undefined}
                      className={`gov-table-td ${cIdx === 0 ? 'font-bold' : ''}`}
                    >
                      {col.render ? col.render(row) : (row[col.accessor] ?? '-')}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="px-6 py-12 text-center text-sm text-slate-500">
                  No records match your search criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination control panel */}
      {totalRecords > 0 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-gov-border dark:border-slate-800 pt-4 no-print">
          <div className="text-xs text-slate-500">
            Showing <span className="font-semibold text-slate-700 dark:text-slate-300">{totalRecords > 0 ? (activePage - 1) * activePageSize + 1 : 0}</span> to{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              {Math.min(activePage * activePageSize, totalRecords)}
            </span>{' '}
            of <span className="font-semibold text-slate-700 dark:text-slate-300">{totalRecords}</span> records
          </div>

          {totalPages > 1 && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => handlePageChange(1)}
                disabled={activePage === 1}
                aria-label="First page"
                className="p-1.5 border border-gov-border dark:border-slate-800 rounded hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 disabled:opacity-30 disabled:hover:bg-transparent dark:text-slate-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                title="First page"
              >
                <ChevronsLeft size={16} aria-hidden="true" />
              </button>
              <button
                onClick={() => handlePageChange(activePage - 1)}
                disabled={activePage === 1}
                aria-label="Previous page"
                className="p-1.5 border border-gov-border dark:border-slate-800 rounded hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 disabled:opacity-30 disabled:hover:bg-transparent dark:text-slate-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                title="Previous page"
              >
                <ChevronLeft size={16} aria-hidden="true" />
              </button>

              <div className="flex items-center gap-1 mx-1">
                {pageNumbers.map((p, idx) => (
                  p === '...' ? (
                    <span key={`ellipsis-${idx}`} className="px-1 text-slate-400 text-xs">...</span>
                  ) : (
                    <button
                      key={`page-${p}`}
                      onClick={() => handlePageChange(Number(p))}
                      aria-label={`Page ${p}`}
                      aria-current={activePage === p ? 'page' : undefined}
                      className={`min-w-[28px] h-7 px-1.5 text-xs rounded font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue ${
                        activePage === p
                          ? 'bg-gov-navy text-white dark:bg-sky-600'
                          : 'border border-gov-border dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-350'
                      }`}
                    >
                      {p}
                    </button>
                  )
                ))}
              </div>

              <button
                onClick={() => handlePageChange(activePage + 1)}
                disabled={activePage === totalPages}
                aria-label="Next page"
                className="p-1.5 border border-gov-border dark:border-slate-800 rounded hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 disabled:opacity-30 disabled:hover:bg-transparent dark:text-slate-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                title="Next page"
              >
                <ChevronRight size={16} aria-hidden="true" />
              </button>
              <button
                onClick={() => handlePageChange(totalPages)}
                disabled={activePage === totalPages}
                aria-label="Last page"
                className="p-1.5 border border-gov-border dark:border-slate-800 rounded hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 disabled:opacity-30 disabled:hover:bg-transparent dark:text-slate-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue"
                title="Last page"
              >
                <ChevronsRight size={16} aria-hidden="true" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default ProfessionalTable;
