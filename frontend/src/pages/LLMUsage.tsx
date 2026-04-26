import { useState, useEffect } from 'react';
import { agentsAPI } from '../lib/api';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import { 
  Bot, 
  DollarSign, 
  Activity,
  Layers,
  Clock
} from 'lucide-react';

interface LLMUsageRecord {
  id: string;
  agent_name: string;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  cost: number;
  timestamp: string;
  task_id?: string;
}

export default function LLMUsage() {
  const [usage, setUsage] = useState<LLMUsageRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('timestamp');

  const fetchUsage = async () => {
    try {
      setLoading(true);
      const response = await agentsAPI.list();
      // Transform agent data to usage records
      const records: LLMUsageRecord[] = [];
      (response?.agents || []).forEach((agent: any) => {
        if (agent.usage_history) {
          agent.usage_history.forEach((u: any) => {
            records.push({
              id: `${agent.id}-${u.timestamp}`,
              agent_name: agent.name,
              provider: agent.provider,
              model: agent.model || 'unknown',
              input_tokens: u.input_tokens || 0,
              output_tokens: u.output_tokens || 0,
              cost: u.cost || 0,
              timestamp: u.timestamp,
              task_id: u.task_id,
            });
          });
        }
      });
      
      // Sort
      records.sort((a, b) => {
        if (sortBy === 'timestamp') return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        if (sortBy === 'cost') return b.cost - a.cost;
        if (sortBy === 'tokens') return (b.input_tokens + b.output_tokens) - (a.input_tokens + a.output_tokens);
        return 0;
      });
      
      setUsage(records);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load usage data');
      toast.error('Failed to load LLM usage data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsage();
  }, [sortBy]);

  const filteredUsage = filter === 'all' 
    ? usage 
    : usage.filter(u => u.provider === filter);

  const providers = [...new Set(usage.map(u => u.provider))];
  
  const totalCost = filteredUsage.reduce((sum, u) => sum + u.cost, 0);
  const totalTokens = filteredUsage.reduce((sum, u) => sum + u.input_tokens + u.output_tokens, 0);
  const totalCalls = filteredUsage.length;

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <SkeletonCard />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={fetchUsage} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">LLM Usage</h1>
          <p className="text-gray-500 mt-1">Detailed token usage and cost per model</p>
        </div>
        <div className="flex items-center gap-3">
          <select 
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Providers</option>
            {providers.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <select 
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="timestamp">Recent First</option>
            <option value="cost">Highest Cost</option>
            <option value="tokens">Most Tokens</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-50 text-green-600 flex items-center justify-center">
              <DollarSign className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">${totalCost.toFixed(2)}</div>
              <div className="text-sm text-gray-500">Total Cost</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{totalTokens.toLocaleString()}</div>
              <div className="text-sm text-gray-500">Total Tokens</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{totalCalls}</div>
              <div className="text-sm text-gray-500">Total Calls</div>
            </div>
          </div>
        </div>
      </div>

      {/* Usage Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {filteredUsage.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Agent</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Provider/Model</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Input Tokens</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Output Tokens</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Cost</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Time</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsage.map((record) => (
                  <tr key={record.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-indigo-600" />
                        </div>
                        <span className="font-medium text-gray-900">{record.agent_name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{record.provider}</div>
                        <div className="text-xs text-gray-500">{record.model}</div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-gray-600">
                      {record.input_tokens.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-gray-600">
                      {record.output_tokens.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-gray-900 font-medium">
                      ${record.cost.toFixed(4)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        <Clock className="w-3 h-3" />
                        {new Date(record.timestamp).toLocaleString()}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState message="No LLM usage data available" />
        )}
      </div>
    </div>
  );
}
