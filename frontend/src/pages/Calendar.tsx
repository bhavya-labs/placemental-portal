import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Calendar as CalendarIcon, Filter, Briefcase, Clock, AlertTriangle, FileText, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { CardSkeleton } from '../components/LoadingSkeleton';

export const Calendar: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [events, setEvents] = useState<any[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<any[]>([]);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedEvent, setSelectedEvent] = useState<any | null>(null);

  // Filters state
  const [filterType, setFilterType] = useState<string>('all');

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/calendar/events');
      setEvents(response.data);
      setFilteredEvents(response.data);
    } catch (err) {
      console.error('Failed to load placement calendar events', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  useEffect(() => {
    if (filterType === 'all') {
      setFilteredEvents(events);
    } else {
      setFilteredEvents(events.filter(e => e.type === filterType));
    }
  }, [filterType, events]);

  // Calendar calculations
  const year = selectedDate.getFullYear();
  const month = selectedDate.getMonth();

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayIndex = new Date(year, month, 1).getDay();

  const prevMonth = () => {
    setSelectedDate(new Date(year, month - 1, 1));
  };

  const nextMonth = () => {
    setSelectedDate(new Date(year, month + 1, 1));
  };

  // Check if a day has events
  const getEventsForDay = (day: number) => {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return filteredEvents.filter(e => e.start.startsWith(dateStr));
  };

  return (
    <div className="space-y-6 text-xs text-slate-700 dark:text-slate-350">
      
      {/* Header Panel */}
      <div className="bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide flex items-center gap-2">
            <CalendarIcon className="text-gov-blue" size={24} />
            Institutional Placement Calendar
          </h2>
          <p className="text-[10px] text-slate-500 mt-1">
            Recruitment drives, registration deadlines, scheduled interviews, and placement training events.
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-950 p-1.5 rounded border border-gov-border dark:border-slate-850">
          <Filter size={14} className="text-slate-400 ml-1" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-transparent border-0 focus:ring-0 text-[10px] uppercase font-bold text-slate-650 focus:outline-none"
          >
            <option value="all">Show All Events</option>
            <option value="drive">Placement Drives</option>
            <option value="deadline">Registration Deadlines</option>
            <option value="interview">Interviews Schedule</option>
            <option value="activity">Training & Workshops</option>
          </select>
        </div>
      </div>

      {loading ? <CardSkeleton /> : (
        <div className="grid md:grid-cols-3 gap-6">
          
          {/* Interactive Calendar grid */}
          <div className="md:col-span-2 bg-white dark:bg-slate-900 border border-gov-border dark:border-slate-800 p-5 rounded-lg shadow-card space-y-4">
            
            {/* Header navigator */}
            <div className="flex justify-between items-center pb-2 border-b border-gov-border dark:border-slate-850">
              <span className="font-bold text-sm text-slate-805 dark:text-slate-205 uppercase tracking-wide">
                {monthNames[month]} {year}
              </span>
              <div className="flex items-center gap-1.5">
                <button onClick={prevMonth} className="p-1 border border-gov-border rounded hover:bg-slate-50 dark:hover:bg-slate-850">
                  <ChevronLeft size={16} />
                </button>
                <button onClick={nextMonth} className="p-1 border border-gov-border rounded hover:bg-slate-50 dark:hover:bg-slate-850">
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>

            {/* Days grid */}
            <div className="grid grid-cols-7 gap-2 text-center text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              <span>Sun</span>
              <span>Mon</span>
              <span>Tue</span>
              <span>Wed</span>
              <span>Thu</span>
              <span>Fri</span>
              <span>Sat</span>
            </div>

            <div className="grid grid-cols-7 gap-2 h-96">
              {/* Empty placeholder cells for previous month padding */}
              {Array.from({ length: firstDayIndex }).map((_, i) => (
                <div key={`empty-${i}`} className="bg-slate-50/50 dark:bg-slate-950/20 rounded border border-transparent"></div>
              ))}

              {/* Day cells */}
              {Array.from({ length: daysInMonth }).map((_, i) => {
                const day = i + 1;
                const dayEvents = getEventsForDay(day);
                const isToday = new Date().toDateString() === new Date(year, month, day).toDateString();
                
                return (
                  <div 
                    key={`day-${day}`} 
                    className={`rounded p-1 bg-slate-50 dark:bg-slate-950 border relative flex flex-col justify-between overflow-hidden cursor-pointer hover:border-gov-blue/50 ${
                      isToday ? 'border-gov-blue ring-1 ring-gov-blue/20 bg-gov-blue/5' : 'border-gov-border dark:border-slate-850'
                    }`}
                  >
                    <span className={`font-bold text-[10px] ${isToday ? 'text-gov-blue font-black' : 'text-slate-500'}`}>
                      {day}
                    </span>

                    {/* Mini event tags */}
                    <div className="space-y-0.5 mt-1 overflow-hidden max-h-12">
                      {dayEvents.map((evt, idx) => (
                        <div 
                          key={idx}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedEvent(evt);
                          }}
                          className="text-[8px] font-semibold truncate rounded px-1 text-white select-none cursor-pointer"
                          style={{ backgroundColor: evt.color }}
                          title={evt.title}
                        >
                          {evt.title}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

          </div>

          {/* Sidebar - Upcoming Events details list */}
          <div className="space-y-6">
            
            {/* Event detail inspector box */}
            {selectedEvent ? (
              <div className="gov-card border-gov-blue/30 space-y-4">
                <div className="flex justify-between items-start border-b border-gov-border dark:border-slate-800 pb-2">
                  <div>
                    <span 
                      className="px-2 py-0.5 rounded text-[8px] text-white font-bold uppercase"
                      style={{ backgroundColor: selectedEvent.color }}
                    >
                      {selectedEvent.type}
                    </span>
                    <h4 className="font-bold text-slate-800 dark:text-slate-100 text-xs mt-1.5 uppercase leading-normal">
                      {selectedEvent.title}
                    </h4>
                  </div>
                  <button onClick={() => setSelectedEvent(null)} className="text-slate-400 hover:text-slate-600">
                    <X size={14} />
                  </button>
                </div>
                <div className="space-y-2 text-[10px] text-slate-600 dark:text-slate-450 leading-relaxed">
                  <p><strong>Scheduled:</strong> {new Date(selectedEvent.start).toLocaleString()}</p>
                  <p><strong>Description / Cutoff:</strong> {selectedEvent.details}</p>
                </div>
              </div>
            ) : (
              <div className="gov-card bg-slate-50 dark:bg-slate-900 border-dashed border-gov-border dark:border-slate-800 py-12 text-center text-slate-450 uppercase font-bold">
                Select calendar entry for detailed specs
              </div>
            )}

            {/* List view of active Month's events */}
            <div className="gov-card space-y-4">
              <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider border-b border-gov-border dark:border-slate-850 pb-2">
                This Month's Placement Timeline
              </h3>
              <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                {filteredEvents.filter(e => {
                  const evDate = new Date(e.start);
                  return evDate.getFullYear() === year && evDate.getMonth() === month;
                }).length === 0 ? (
                  <p className="text-[10px] text-slate-400 italic">No placement activities or events are currently scheduled.</p>
                ) : (
                  filteredEvents.filter(e => {
                    const evDate = new Date(e.start);
                    return evDate.getFullYear() === year && evDate.getMonth() === month;
                  }).map((e, idx) => (
                    <div 
                      key={idx} 
                      onClick={() => setSelectedEvent(e)}
                      className="border-l-2 p-2 bg-slate-50 dark:bg-slate-950 rounded cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-900 transition-colors"
                      style={{ borderLeftColor: e.color }}
                    >
                      <div className="flex justify-between items-center text-[9px] font-bold text-slate-400 uppercase">
                        <span>{e.type}</span>
                        <span>{new Date(e.start).toLocaleDateString()}</span>
                      </div>
                      <p className="font-semibold text-slate-800 dark:text-slate-200 text-[10px] truncate mt-0.5">{e.title}</p>
                    </div>
                  ))
                )}
              </div>
            </div>

          </div>

        </div>
      )}

    </div>
  );
};

export default Calendar;
