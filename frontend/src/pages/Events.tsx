import { useState, useEffect } from 'react';
import { eventsAPI } from '../lib/api';
import { Loading, SkeletonTable } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import SearchBar from '../components/SearchBar';
import { toast } from '../hooks/useToast';
import { Activity, Filter, Download, Shield, Clock } from 'lucide-react';

export default function Events() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Record<string, string>>({});

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await eventsAPI.list({ limit: 100, ...filters });
      setEvents(response?.events || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [filters]);

  const handleSearch = (query: string, activeFilters: Record<string, string>) => {
    setFilters({ search: query, ...activeFilters });
  };

  const exportEvents = () => {
    const dataStr = JSON.stringify(events, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `fleetops_events_${new Date().toISOString().split('T')[0]}.json`;
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    toast.success('Events exported');
  };

  const filterOptions = [
    {
      key: 'event_type',
      label: 'Event Type',
      options: [
        { value: 'task_created', label: 'Task Created' },
        { value: 'task_completed', label: 'Task Completed' },
        { value: 'approval_required', label: 'Approval Required' },
        { value: 'agent_created', label: 'Agent Created' },
        { value: 'user_login', label: 'User Login' },
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
        <div className="flex items-center gap-3">
          <Activity className="w-6 h-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">Events</h1>
        </div>
        <button
          onClick={exportEvents}
          className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm hover:bg-gray-50 transition-colors"
        >
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>

      <SearchBar 
        onSearch={handleSearch} 
        placeholder="Search events..."
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
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3 hidden md:table-cell">Data</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Time</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3 hidden lg:table-cell">Signature</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {events.map((event) => (
                  <tr key={event.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900 capitalize">
                          {event.event_type?.replace(/_/g, ' ')}
                        </p>
                        <p className="text-xs text-gray-500">
                          ID: {event.id?.slice(0, 8)}...
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4 hidden sm:table-cell">
                      <p className="text-sm text-gray-600">
                        {event.user_id ? `User: ${event.user_id.slice(0, 8)}` : 
                         event.agent_id ? `Agent: ${event.agent_id.slice(0, 8)}` : 'System'}
                      </p>
                    </td>
                    <td className="px-6 py-4 hidden md:table-cell">
                      <p className="text-sm text-gray-600 font-mono text-xs truncate max-w-xs">
                        {JSON.stringify(event.data || {}).slice(0, 60)}...
                      </p>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        <Clock className="w-4 h-4" />
                        {new Date(event.timestamp).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 hidden lg:table-cell">
                      {event.signature ? (
                        <div className="flex items-center gap-2">
                          <Shield className="w-4 h-4 text-green-500" />
                          <span className="text-xs text-green-600">Signed</span>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <EmptyState
          title="No events"
          message="Events will appear here as your team works."
        />
      )}
    </div>
  );
}
