import { useState } from 'react';
import { agentsAPI } from '../lib/api';
import { Loading, SkeletonTable } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import { useForm } from '../hooks/useForm';
import { toast } from '../hooks/useToast';
import { Plus, Bot, ChevronDown, ChevronUp } from 'lucide-react';

const validationSchema = {
  name: { required: true, minLength: 1, maxLength: 255 },
  provider: { required: true },
  model: { required: false },
  capabilities: { required: false },
};

export default function Agents() {
  const [showCreate, setShowCreate] = useState(false);
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      const response = await agentsAPI.list();
      setAgents(response?.agents || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  useState(() => {
    fetchAgents();
  });

  const form = useForm(
    { name: '', provider: 'claude', model: '', capabilities: '' },
    validationSchema,
    async (values) => {
      await agentsAPI.create({
        ...values,
        capabilities: values.capabilities.split(',').map((c: string) => c.trim()),
        level: 'junior',
      });
      toast.success('Agent created successfully');
      setShowCreate(false);
      fetchAgents();
    }
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
        <SkeletonTable rows={5} />
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchAgents} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Agents</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Agent
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-lg mx-4 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Create New Agent</h2>
            <form onSubmit={form.handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  {...form.getFieldProps('name')}
                  type="text"
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Agent name"
                />
                {form.errors.name && form.touched.name && (
                  <p className="text-sm text-red-500 mt-1">{form.errors.name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Provider *</label>
                <select
                  {...form.getFieldProps('provider')}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="claude">Claude</option>
                  <option value="openai">OpenAI</option>
                  <option value="github">GitHub Copilot</option>
                  <option value="custom">Custom</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                <input
                  {...form.getFieldProps('model')}
                  type="text"
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="claude-3-sonnet"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Capabilities (comma-separated)</label>
                <input
                  {...form.getFieldProps('capabilities')}
                  type="text"
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="coding, analysis, review"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-900"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={form.isSubmitting}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {form.isSubmitting ? 'Creating...' : 'Create Agent'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Agents List */}
      {agents && agents.length > 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Agent</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3 hidden sm:table-cell">Provider</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3 hidden md:table-cell">Level</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Status</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3 hidden lg:table-cell">Tasks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {agents.map((agent) => (
                  <>
                    <tr
                      key={agent.id}
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => setExpandedAgent(expandedAgent === agent.id ? null : agent.id)}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                            <Bot className="w-5 h-5 text-blue-600" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{agent.name}</p>
                            <p className="text-xs text-gray-500">{agent.model}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 hidden sm:table-cell">
                        <span className="text-sm text-gray-600 capitalize">{agent.provider}</span>
                      </td>
                      <td className="px-6 py-4 hidden md:table-cell">
                        <span className="text-sm text-gray-600 capitalize">{agent.level}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          agent.status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {agent.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 hidden lg:table-cell">
                        <div className="flex items-center gap-1">
                          <span className="text-sm text-gray-600">{agent.tasks_count || 0}</span>
                          {agent.sub_agents?.length > 0 && (
                            <span className="text-xs text-blue-600">+{agent.sub_agents.length} sub</span>
                          )}
                        </div>
                      </td>
                    </tr>
                    {expandedAgent === agent.id && (
                      <tr>
                        <td colSpan={5} className="px-6 py-4 bg-gray-50">
                          <div className="space-y-3">
                            <div>
                              <p className="text-sm font-medium text-gray-700">Capabilities</p>
                              <div className="flex flex-wrap gap-2 mt-1">
                                {(agent.capabilities || []).map((cap: string) => (
                                  <span key={cap} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                                    {cap}
                                  </span>
                                ))}
                              </div>
                            </div>
                            <div className="grid grid-cols-3 gap-4 text-sm">
                              <div>
                                <p className="text-gray-500">Cost to date</p>
                                <p className="font-medium">${(agent.cost_to_date || 0).toFixed(2)}</p>
                              </div>
                              <div>
                                <p className="text-gray-500">Max sub-agents</p>
                                <p className="font-medium">{agent.max_sub_agents || 'Unlimited'}</p>
                              </div>
                              <div>
                                <p className="text-gray-500">Created</p>
                                <p className="font-medium">{new Date(agent.created_at).toLocaleDateString()}</p>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <EmptyState
          title="No agents yet"
          message="Create your first AI agent to get started."
          action={{ label: 'Create Agent', onClick: () => setShowCreate(true) }}
        />
      )}
    </div>
  );
}
