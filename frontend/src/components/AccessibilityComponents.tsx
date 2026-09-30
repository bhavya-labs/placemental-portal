import React, { useRef, useEffect } from 'react';
import { X, ChevronUp, ChevronDown } from 'lucide-react';

// ==========================================
// 1. ACCESSIBLE BUTTON
// ==========================================
interface AccessibleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label?: string;
  icon?: React.ReactNode;
}

export const AccessibleButton: React.FC<AccessibleButtonProps> = ({
  children,
  label,
  icon,
  className = '',
  ...props
}) => {
  return (
    <button
      aria-label={label || (typeof children === 'string' ? children : undefined)}
      className={`focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-gov-blue focus:outline-none transition-all ${className}`}
      {...props}
    >
      {icon && <span aria-hidden="true" className="shrink-0">{icon}</span>}
      {children}
    </button>
  );
};

// ==========================================
// 2. ACCESSIBLE INPUT
// ==========================================
interface AccessibleInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  id: string;
  error?: string;
  helperText?: string;
  required?: boolean;
}

export const AccessibleInput: React.FC<AccessibleInputProps> = ({
  label,
  id,
  error,
  helperText,
  required,
  className = '',
  ...props
}) => {
  const describedBy = [
    error ? `${id}-error` : null,
    helperText ? `${id}-helper` : null
  ].filter(Boolean).join(' ');

  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block font-bold text-slate-650 dark:text-slate-400 uppercase text-[11px]">
        {label} {required && <span className="text-red-500" aria-hidden="true">*</span>}
      </label>
      <input
        id={id}
        required={required}
        aria-required={required ? 'true' : 'false'}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={describedBy || undefined}
        className={`w-full p-2 border rounded bg-white text-slate-800 dark:bg-slate-950 dark:border-slate-800 dark:text-slate-100 focus-visible:ring-2 focus-visible:ring-gov-blue focus:outline-none transition-all ${
          error ? 'border-red-500 focus-visible:ring-red-500' : 'border-gov-border'
        } ${className}`}
        {...props}
      />
      {error && (
        <p id={`${id}-error`} role="alert" className="text-[10px] font-bold text-red-650 dark:text-red-400 mt-0.5">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={`${id}-helper`} className="text-[9px] text-slate-500 dark:text-slate-400 leading-normal">
          {helperText}
        </p>
      )}
    </div>
  );
};

// ==========================================
// 3. ACCESSIBLE FORM FIELD CONTAINER
// ==========================================
interface AccessibleFormFieldProps {
  label: string;
  id: string;
  error?: string;
  required?: boolean;
  children: React.ReactElement<any>;
}

export const AccessibleFormField: React.FC<AccessibleFormFieldProps> = ({
  label,
  id,
  error,
  required,
  children
}) => {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block font-bold text-slate-655 dark:text-slate-400 uppercase text-[11px]">
        {label} {required && <span className="text-red-500" aria-hidden="true">*</span>}
      </label>
      {React.cloneElement(children, {
        id,
        required,
        'aria-required': required ? 'true' : 'false',
        'aria-invalid': error ? 'true' : 'false',
        'aria-describedby': error ? `${id}-error` : undefined,
        className: `${children.props.className || ''} focus-visible:ring-2 focus-visible:ring-gov-blue focus:outline-none transition-all`
      } as any)}
      {error && (
        <p id={`${id}-error`} role="alert" className="text-[10px] font-bold text-red-650 dark:text-red-400 mt-0.5">
          {error}
        </p>
      )}
    </div>
  );
};

// ==========================================
// 4. ACCESSIBLE TABS
// ==========================================
interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

interface AccessibleTabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: any) => void;
  ariaLabel?: string;
}

export const AccessibleTabs: React.FC<AccessibleTabsProps> = ({
  tabs,
  activeTab,
  onChange,
  ariaLabel = 'Dashboard sections'
}) => {
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let nextIndex = -1;
    if (e.key === 'ArrowRight') {
      nextIndex = (index + 1) % tabs.length;
    } else if (e.key === 'ArrowLeft') {
      nextIndex = (index - 1 + tabs.length) % tabs.length;
    } else if (e.key === 'Home') {
      nextIndex = 0;
    } else if (e.key === 'End') {
      nextIndex = tabs.length - 1;
    }

    if (nextIndex !== -1) {
      e.preventDefault();
      const targetId = tabs[nextIndex].id;
      onChange(targetId);
      setTimeout(() => {
        tabRefs.current[targetId]?.focus();
      }, 10);
    }
  };

  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className="flex border-b border-gov-border dark:border-slate-800 no-print overflow-x-auto whitespace-nowrap"
    >
      {tabs.map((tab, idx) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            ref={(el) => { tabRefs.current[tab.id] = el; }}
            role="tab"
            aria-selected={isActive}
            aria-controls={`panel-${tab.id}`}
            id={`tab-${tab.id}`}
            tabIndex={isActive ? 0 : -1}
            onKeyDown={(e) => handleKeyDown(e, idx)}
            onClick={() => onChange(tab.id)}
            className={`pb-3 px-4 text-xs font-bold uppercase tracking-wider border-b-2 transition-all flex items-center gap-1.5 focus:outline-none focus-visible:border-gov-blue ${
              isActive
                ? 'border-gov-blue text-gov-blue dark:text-sky-400 dark:border-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
            }`}
          >
            {tab.icon && <span aria-hidden="true" className="shrink-0">{tab.icon}</span>}
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
};

// ==========================================
// 5. ACCESSIBLE MODAL
// ==========================================
interface AccessibleModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  triggerRef?: React.RefObject<HTMLButtonElement | null>;
  maxWidth?: string;
}

export const AccessibleModal: React.FC<AccessibleModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  triggerRef,
  maxWidth
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  const triggerRefCurrent = useRef(triggerRef);
  triggerRefCurrent.current = triggerRef;
  const wasOpenRef = useRef(false);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';

      // Initial focus: only focus the first interactive element when transitioning from closed to open
      if (!wasOpenRef.current) {
        wasOpenRef.current = true;
        requestAnimationFrame(() => {
          const focusables = modalRef.current?.querySelectorAll<HTMLElement>(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
          );
          if (focusables && focusables.length > 0) {
            focusables[0].focus();
          }
        });
      }

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          onCloseRef.current();
          return;
        }

        if (e.key === 'Tab') {
          const focusables = modalRef.current?.querySelectorAll<HTMLElement>(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
          );
          if (!focusables || focusables.length === 0) {
            e.preventDefault();
            return;
          }

          const firstEl = focusables[0];
          const lastEl = focusables[focusables.length - 1];

          if (e.shiftKey) {
            if (document.activeElement === firstEl || !modalRef.current?.contains(document.activeElement)) {
              e.preventDefault();
              lastEl.focus();
            }
          } else {
            if (document.activeElement === lastEl || !modalRef.current?.contains(document.activeElement)) {
              e.preventDefault();
              firstEl.focus();
            }
          }
        }
      };

      window.addEventListener('keydown', handleKeyDown);

      return () => {
        window.removeEventListener('keydown', handleKeyDown);
      };
    } else {
      if (wasOpenRef.current) {
        wasOpenRef.current = false;
        document.body.style.overflow = '';
        if (triggerRefCurrent.current?.current) {
          triggerRefCurrent.current.current.focus();
        }
      }
    }
  }, [isOpen]);

  // Handle unmount cleanup
  useEffect(() => {
    return () => {
      document.body.style.overflow = '';
      if (wasOpenRef.current && triggerRefCurrent.current?.current) {
        triggerRefCurrent.current.current.focus();
      }
    };
  }, []);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div
        ref={modalRef}
        className={`bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 rounded-lg shadow-premium ${maxWidth || 'max-w-lg'} w-full flex flex-col max-h-[90vh] animate-fadeIn`}
      >
        <header className="p-4 border-b border-gov-border dark:border-slate-855 flex items-center justify-between">
          <h3 id="modal-title" className="text-sm font-bold text-slate-850 dark:text-slate-100 uppercase tracking-wide">
            {title}
          </h3>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="text-slate-400 hover:text-slate-600 dark:hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-gov-blue rounded p-1"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>
        <div className="flex-1 p-6 overflow-y-auto text-xs">
          {children}
        </div>
      </div>
    </div>
  );
};

// ==========================================
// 6. ACCESSIBLE TABLE
// ==========================================
interface TableColumn {
  header: string;
  accessor: string;
  sortable?: boolean;
}

interface AccessibleTableProps {
  caption: string;
  columns: TableColumn[];
  data: any[];
  sortColumn?: string;
  sortDirection?: 'asc' | 'desc';
  onSort?: (accessor: string) => void;
  emptyMessage?: string;
}

export const AccessibleTable: React.FC<AccessibleTableProps> = ({
  caption,
  columns,
  data,
  sortColumn,
  sortDirection,
  onSort,
  emptyMessage = 'No records found.'
}) => {
  return (
    <div className="overflow-x-auto border border-gov-border dark:border-slate-800 rounded-lg bg-white dark:bg-slate-900">
      <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-xs">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="bg-slate-50 dark:bg-slate-950 font-bold uppercase tracking-wider text-slate-505 dark:text-slate-400">
            {columns.map((col, idx) => {
              const isSorted = sortColumn === col.accessor;
              const ariaSortValue = isSorted
                ? (sortDirection === 'asc' ? 'ascending' : 'descending')
                : undefined;

              return (
                <th
                  key={idx}
                  scope="col"
                  aria-sort={ariaSortValue}
                  className="px-4 py-3.5 text-left"
                >
                  {col.sortable && onSort ? (
                    <button
                      onClick={() => onSort(col.accessor)}
                      className="flex items-center gap-1.5 hover:text-slate-700 dark:hover:text-white uppercase tracking-wider font-extrabold focus:outline-none focus-visible:ring-1 focus-visible:ring-gov-blue"
                    >
                      <span>{col.header}</span>
                      {isSorted ? (
                        sortDirection === 'asc' ? <ChevronUp size={12} aria-hidden="true" /> : <ChevronDown size={12} aria-hidden="true" />
                      ) : null}
                    </button>
                  ) : (
                    <span>{col.header}</span>
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-gov-border dark:divide-slate-800">
          {data.length > 0 ? (
            data.map((row, rIdx) => (
              <tr
                key={rIdx}
                className="hover:bg-slate-55 dark:hover:bg-slate-950/20 transition-colors"
              >
                {columns.map((col, cIdx) => (
                  <td
                    key={cIdx}
                    scope={cIdx === 0 ? 'row' : undefined}
                    className={`px-4 py-3 text-slate-700 dark:text-slate-350 font-medium ${cIdx === 0 ? 'font-bold' : ''}`}
                  >
                    {row[col.accessor] ?? '-'}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-slate-400 font-semibold">
                {emptyMessage}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

// ==========================================
// 7. ACCESSIBLE CHART
// ==========================================
interface AccessibleChartProps {
  title: string;
  description: string;
  data: any[];
  keys: { dataKey: string; label: string }[];
  labelKey: string;
  children: React.ReactNode;
}

export const AccessibleChart: React.FC<AccessibleChartProps> = ({
  title,
  description,
  data,
  keys,
  labelKey,
  children
}) => {
  return (
    <section aria-label={title} className="space-y-4">
      <div className="space-y-1">
        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
          {title}
        </h4>
        <p className="text-[10px] text-slate-500 dark:text-slate-400">
          {description}
        </p>
      </div>

      <div aria-hidden="true" className="h-64">
        {children}
      </div>

      <div className="sr-only">
        <h5>Dataset Table for {title}</h5>
        <table>
          <caption>{description}</caption>
          <thead>
            <tr>
              <th scope="col">{labelKey.toUpperCase()}</th>
              {keys.map((k) => (
                <th key={k.dataKey} scope="col">{k.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data && data.map((row, idx) => (
              <tr key={idx}>
                <th scope="row">{row[labelKey]}</th>
                {keys.map((k) => (
                  <td key={k.dataKey}>{row[k.dataKey]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

// ==========================================
// 8. ACCESSIBLE TOAST / LIVE ANNOUNCEMENTS
// ==========================================
interface AccessibleToastProps {
  message: string | null;
  type: 'success' | 'error' | 'info' | null;
}

export const AccessibleToast: React.FC<AccessibleToastProps> = ({ message, type }) => {
  if (!message) return null;

  const styles = {
    success: 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-400 border-emerald-300',
    error: 'bg-red-50 text-red-800 dark:bg-red-950/30 dark:text-red-400 border-red-300',
    info: 'bg-indigo-50 text-indigo-800 dark:bg-indigo-950/30 dark:text-indigo-400 border-indigo-300'
  };

  return (
    <div
      role="status"
      aria-live="polite"
      className={`p-3 border rounded text-xs font-bold uppercase tracking-wide flex items-center gap-2 ${styles[type || 'info']} transition-all animate-fadeIn no-print`}
    >
      <span>{message}</span>
    </div>
  );
};
