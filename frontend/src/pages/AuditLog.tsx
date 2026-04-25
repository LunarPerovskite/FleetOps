import { useState, useEffect } from 'react';
import { eventsAPI } from '../lib/api';
import { Loading, SkeletonTable } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import SearchBar from '../components/SearchBar';
import { Shield, Clock, User, Bot, FileText } from 'lucide-react';

const eventIcons: Record<string, React.ComponentType<any>> = {
  task_created: FileText,
  task_completed: FileText,
  task_approved: Shield,
  agent_created: Bot,
  event_occurred: Clock,
  user_action: User,
};

const eventColors: Record<string, string> = {
  task_created: 'bg-blue-50 text-blue-700',
  task_completed: 'bg-green-50 text-green-700',
  task_approved: 'bg-purple-50 text-purple-700',
  agent_created: 'bg-indigo-50 text-indigo-700',
  event_occurred: 'bg-gray-50 text-gray-700',
  user_action: 'bg-orange-50 text-orange-700',
};

export default function AuditLog() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchEvents();
  }, [filters]);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await eventsAPI.list({ limit: 100, ...filters });
      setEvents(response?.events || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit log');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (query: string, activeFilters: Record<string, string>) => {
    setFilters({ search: query, ...activeFilters });
  };

  const filterOptions = [
    {
      key: 'event_type',
      label: 'Event Type',
      options: [
        { value: 'task_created', label: 'Task Created' },
        { value: 'task_completed', label: 'Task Completed' },
        { value: 'task_approved', label: 'Task Approved' },
        { value: 'agent_created', label: 'Agent Created' },
        { value: 'user_action', label: 'User Action' },
      ]
    }
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
        <SkeletonTable rows={5} />
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchEvents} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Shield className="w-4 h-4" />
          Immutable Evidence Trail
        </div>
      </div>

      <SearchBar 
        onSearch={handleSearch} 
        placeholder="Search audit log..."
        filterOptions={filterOptions}
      />

      {events && events.length > 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Event</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3 hidden sm:table-cell">Actor</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3 hidden md:table-cell">Details</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Time</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3 hidden lg:table-cell">Signature</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {events.map((event) => {
                  const Icon = eventIcons[event.event_type] || Clock;
                  const colorClass = eventColors[event.event_type] || 'bg-gray-50 text-gray-700';
                  
                  return (
                    <tr key={event.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${colorClass}`}>
                            <Icon className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {event.event_type?.replace(/_/g, ' ')}
                            </p>
                            <p className="text-xs text-gray-500">ID: {event.id?.slice(0, 8)}...</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 hidden sm:table-cell">
                        <div className="flex items-center gap-2">
                          {event.user_id ? (
                            <>
                              <User className="w-4 h-4 text-gray-400" />
                              <span className="text-sm text-gray-600">User</span>
                            </>
                          ) : event.agent_id ? (
                            <>
                              <Bot className="w-4 h-4 text-gray-400" />
                              <span className="text-sm text-gray-600">Agent</span>
                            </>
                          ) : (
                            <span className="text-sm text-gray-400">System</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 hidden md:table-cell">
                        <p className="text-sm text-gray-600 truncate max-w-xs">
                          {JSON.stringify(event.data || {}).slice(0, 50)}...
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-gray-500">
                          {new Date(event.timestamp).toLocaleDateString()}
                        </p>
                        <p className="text-xs text-gray-400">
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </p>
                      </td>
                      <td className="px-6 py-4 hidden lg:table-cell">
                        {event.signature ? (
                          <div className="flex items-center gap-2">
                            <Shield className="w-4 h-4 text-green-500" />
                            <span className="text-xs text-green-600">Verified</span>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">Pending</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <EmptyState
          title="No audit events"
          message="Events will be logged here as your team works."
        />
      )}
    </div>
  );
}
