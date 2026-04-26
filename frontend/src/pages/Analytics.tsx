import { useState, useEffect } from 'react';
import { analyticsAPI, dashboardAPI } from '../lib/api';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import { 
  TrendingUp, 
  DollarSign, 
  Bot, 
  Activity,
  Download,
  Calendar,
  BarChart3,
  PieChart
} from 'lucide-react';

// Simple bar chart component
function BarChart({ data, maxValue, color = 'bg-indigo-500' }: { 
  data: { label: string; value: number }[]; 
  maxValue: number;
  color?: string;
}) {
  return (
    <div className="space-y-3">
      {data.map((item, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="w-24 text-sm text-gray-600 truncate">{item.label}</div>
          <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden">
            <div 
              className={`${color} h-full rounded-full transition-all duration-500 flex items-center justify-end pr-2`}
              style={{ width: `${Math.min((item.value / maxValue) * 100, 100)}%` }}
            >
              <span className="text-xs text-white font-medium">
                {item.value >= 1000 ? `${(item.value / 1000).toFixed(1)}k` : item.value}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Line chart component (simplified)
function LineChart({ data, color = '#6366f1' }: { 
  data: { x: string; y: number }[];
  color?: string;
}) {
  if (!data.length) return null;
  
  const maxY = Math.max(...data.map(d => d.y)) || 1;
  const minY = Math.min(...data.map(d => d.y));
  const range = maxY - minY || 1;
  
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1 || 1)) * 100;
    const y = 100 - ((d.y - minY) / range) * 80 - 10;
    return `${x},${y}`;
  }).join(' ');
  
  return (
    <div className="w-full h-64 relative">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
        <defs>
          <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.2" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon 
          points={`0,100 ${points} 100,100`} 
          fill="url(#lineGradient)" 
        />
        <polyline 
          points={points} 
          fill="none" 
          stroke={color} 
          strokeWidth="0.5" 
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {data.map((d, i) => {
          const x = (i / (data.length - 1 || 1)) * 100;
          const y = 100 - ((d.y - minY) / range) * 80 - 10;
          return (
            <circle key={i} cx={x} cy={y} r="1" fill={color} />
          );
        })}
      </svg>
      <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-gray-400 px-2">
        {data.filter((_, i) => i % Math.ceil(data.length / 6) === 0 || i === data.length - 1).map((d, i) => (
          <span key={i}>{d.x}</span>
        ))}
      </div>
    </div>
  );
}

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('7d');
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const [overview, costs, agents] = await Promise.all([
        analyticsAPI.overview(),
        analyticsAPI.costs(),
        analyticsAPI.agents(),
      ]);
      
      setAnalytics({
        overview: overview || {},
        costs: costs || {},
        agents: agents || {},
      });
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics');
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const handleExport = (format: 'csv' | 'json') => {
    const data = {
      generatedAt: new Date().toISOString(),
      timeRange,
      analytics,
    };
    
    const blob = new Blob(
      [format === 'csv' ? convertToCSV(data) : JSON.stringify(data, null, 2)],
      { type: format === 'csv' ? 'text/csv' : 'application/json' }
    );
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fleetops-analytics-${timeRange}-${Date.now()}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast.success(`Analytics exported as ${format.toUpperCase()}`);
  };

  const convertToCSV = (data: any) => {
    // Simplified CSV export
    const rows = [
      ['Metric', 'Value'],
      ['Total Cost', data.analytics?.overview?.total_cost || 0],
      ['Total Tokens', data.analytics?.overview?.total_tokens || 0],
      ['Active Agents', data.analytics?.overview?.active_agents || 0],
      ['Tasks Completed', data.analytics?.overview?.tasks_completed || 0],
    ];
    return rows.map(r => r.join(',')).join('\n');
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <SkeletonCard />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={fetchAnalytics} />;
  }

  const overview = analytics?.overview || {};
  const costTrend = overview.cost_trend || [];
  const providerUsage = overview.provider_usage || [];
  const topAgents = analytics?.agents?.top_costs || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500 mt-1">Insights into your AI operations</p>
        </div>
        <div className="flex items-center gap-3">
          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            <Download className="w-4 h-4" />
            JSON
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          icon={DollarSign}
          label="Total Cost"
          value={`$${(overview.total_cost || 0).toFixed(2)}`}
          trend={overview.cost_change}
          color="bg-green-50 text-green-600"
        />
        <StatCard 
          icon={Activity}
          label="Total Tokens"
          value={(overview.total_tokens || 0).toLocaleString()}
          trend={overview.token_change}
          color="bg-blue-50 text-blue-600"
        />
        <StatCard 
          icon={Bot}
          label="Active Agents"
          value={overview.active_agents || 0}
          trend={overview.agent_change}
          color="bg-purple-50 text-purple-600"
        />
        <StatCard 
          icon={CheckSquare}
          label="Tasks Completed"
          value={overview.tasks_completed || 0}
          trend={overview.task_change}
          color="bg-orange-50 text-orange-600"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Trend */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-gray-900">Cost Trend</h2>
          </div>
          {costTrend.length > 0 ? (
            <LineChart data={costTrend} />
          ) : (
            <EmptyState message="No cost data available for this period" />
          )}
        </div>

        {/* Provider Usage */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <PieChart className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-gray-900">Usage by Provider</h2>
          </div>
          {providerUsage.length > 0 ? (
            <BarChart 
              data={providerUsage} 
              maxValue={Math.max(...providerUsage.map((p: any) => p.value)) || 1}
              color="bg-indigo-500"
            />
          ) : (
            <EmptyState message="No provider usage data available" />
          )}
        </div>
      </div>

      {/* Top Agents by Cost */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-indigo-600" />
          <h2 className="text-lg font-semibold text-gray-900">Top Agents by Cost</h2>
        </div>
        {topAgents.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Agent</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Cost</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Tokens</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Tasks</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Trend</th>
                </tr>
              </thead>
              <tbody>
                {topAgents.map((agent: any, i: number) => (
                  <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-indigo-600" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{agent.name}</div>
                          <div className="text-xs text-gray-500">{agent.provider}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-gray-900">
                      ${agent.cost?.toFixed(2) || '0.00'}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-600">
                      {(agent.tokens || 0).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-600">
                      {agent.tasks || 0}
                    </td>
                    <td className="py-3 px-4">
                      <div className="w-32 bg-gray-100 rounded-full h-2">
                        <div 
                          className="bg-indigo-500 h-2 rounded-full"
                          style={{ width: `${Math.min((agent.cost / (topAgents[0]?.cost || 1)) * 100, 100)}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState message="No agent cost data available" />
        )}
      </div>
    </div>
  );
}

// Import CheckSquare for the stat card
function CheckSquare(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <polyline points="9 11 12 14 22 4"></polyline>
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
    </svg>
  );
}

// Stat Card component
function StatCard({ icon: Icon, label, value, trend, color }: any) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="w-5 h-5" />
        </div>
        {trend !== undefined && (
          <span className={`text-xs font-medium ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>
      <div className="mt-4">
        <div className="text-2xl font-bold text-gray-900">{value}</div>
        <div className="text-sm text-gray-500 mt-1">{label}</div>
      </div>
    </div>
  );
}
