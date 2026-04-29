import { useState, useEffect } from 'react';
import { agentsAPI, teamsAPI, sharedAgentsAPI } from '../lib/api';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import { 
  Share2, 
  Users, 
  Bot, 
  DollarSign,
  Trash2,
  Plus,
  Shield,
  Check
} from 'lucide-react';

interface SharedAgent {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_provider: string;
  team_id: string;
  team_name: string;
  budget_allocation: number;
  usage_limit: number | null;
  current_usage: number;
  permissions: string[];
  is_active: boolean;
}

export default function SharedAgents() {
  const [sharedAgents, setSharedAgents] = useState<SharedAgent[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showShare, setShowShare] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('');
  const [budgetAllocation, setBudgetAllocation] = useState(0);
  const [usageLimit, setUsageLimit] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sharedRes, teamsRes, agentsRes] = await Promise.all([
        sharedAgentsAPI.getOrgShared(),
        teamsAPI.list(),
        agentsAPI.list(),
      ]);

      // Flatten shared agents from org response
      const flattened: SharedAgent[] = [];
      (sharedRes?.shared_agents || []).forEach((agent: any) => {
        if (agent.shared_teams) {
          agent.shared_teams.forEach((team: any) => {
            flattened.push({
              id: `${agent.id}-${team.team_id}`,
              agent_id: agent.id,
              agent_name: agent.name,
              agent_provider: agent.provider,
              team_id: team.team_id,
              team_name: team.team_name,
              budget_allocation: team.budget_allocation,
              usage_limit: team.usage_limit,
              current_usage: team.current_usage,
              permissions: team.permissions,
              is_active: true,
            });
          });
        }
      });

      setSharedAgents(flattened);
      setTeams(teamsRes?.teams || teamsRes || []);
      setAgents(agentsRes?.agents || agentsRes || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load shared agents');
      toast.error('Failed to load shared agents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleShare = async () => {
    if (!selectedTeam || !selectedAgent) {
      toast.error('Please select both team and agent');
      return;
    }

    try {
      await sharedAgentsAPI.shareToTeam(selectedTeam, {
        agent_id: selectedAgent,
        budget_allocation: budgetAllocation,
        usage_limit: usageLimit ? parseFloat(usageLimit) : null,
        permissions: ['read', 'execute'],
      });

      toast.success('Agent shared successfully');
      setShowShare(false);
      setSelectedTeam('');
      setSelectedAgent('');
      setBudgetAllocation(0);
      setUsageLimit('');
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Failed to share agent');
    }
  };

  const handleRemove = async (teamId: string, assignmentId: string) => {
    if (!confirm('Remove this shared agent?')) return;

    try {
      await sharedAgentsAPI.remove(teamId, assignmentId);
      toast.success('Shared agent removed');
      fetchData();
    } catch (err: any) {
      toast.error(err.message || 'Failed to remove');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Shared Agents</h1>
          <p className="text-gray-500 mt-1">
            Share agents across teams with budget allocation
          </p>
        </div>
        <button
          onClick={() => setShowShare(!showShare)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Share2 className="w-4 h-4" />
          Share Agent
        </button>
      </div>

      {/* Share Form */}
      {showShare && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Share Agent with Team</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Agent
              </label>
              <select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select agent...</option>
                {agents.map((agent: any) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name} ({agent.provider})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Team
              </label>
              <select
                value={selectedTeam}
                onChange={(e) => setSelectedTeam(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select team...</option>
                {teams.map((team: any) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Budget Allocation (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={budgetAllocation}
                onChange={(e) => setBudgetAllocation(parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Usage Limit ($)
              </label>
              <input
                type="number"
                value={usageLimit}
                onChange={(e) => setUsageLimit(e.target.value)}
                placeholder="Unlimited"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-end gap-2">
              <button
                onClick={handleShare}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Share
              </button>
              <button
                onClick={() => setShowShare(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Shared Agents Grid */}
      {sharedAgents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sharedAgents.map((shared) => (
            <div
              key={shared.id}
              className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {shared.agent_name}
                    </h3>
                    <div className="text-sm text-gray-500">
                      {shared.agent_provider}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleRemove(shared.team_id, shared.id)}
                  className="p-2 text-red-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Team */}
              <div className="mt-4 flex items-center gap-2">
                <Users className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-600">
                  Shared with: <span className="font-medium">{shared.team_name}</span>
                </span>
              </div>

              {/* Budget */}
              <div className="mt-3">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Budget Usage</span>
                  <span className="font-medium">
                    ${shared.current_usage.toFixed(2)} / {shared.usage_limit ? `$${shared.usage_limit}` : 'Unlimited'}
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      shared.usage_limit && (shared.current_usage / shared.usage_limit) > 0.9
                        ? 'bg-red-500'
                        : 'bg-purple-500'
                    }`}
                    style={{
                      width: `${Math.min(
                        shared.usage_limit
                          ? (shared.current_usage / shared.usage_limit) * 100
                          : 0,
                        100
                      )}%`,
                    }}
                  />
                </div>
              </div>

              {/* Permissions */}
              <div className="mt-3 flex items-center gap-2">
                <Shield className="w-4 h-4 text-gray-400" />
                <div className="flex gap-1">
                  {shared.permissions.map((perm) => (
                    <span
                      key={perm}
                      className="text-xs px-2 py-0.5 bg-gray-100 rounded text-gray-600"
                    >
                      {perm}
                    </span>
                  ))}
                </div>
              </div>

              {/* Budget Allocation */}
              {shared.budget_allocation > 0 && (
                <div className="mt-2 text-sm text-gray-500">
                  Budget allocation: {shared.budget_allocation}%
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          message="No shared agents yet"
          action={{
            label: 'Share an Agent',
            onClick: () => setShowShare(true),
          }}
        />
      )}
    </div>
  );
}
