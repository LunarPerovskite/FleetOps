import { useState, useEffect } from 'react';
import { teamsAPI, usersAPI } from '../lib/api';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import { useForm } from '../hooks/useForm';
import { toast } from '../hooks/useToast';
import { 
  Users, 
  Plus, 
  UserPlus,
  Shield,
  Trash2,
  Mail,
  Crown
} from 'lucide-react';

interface Team {
  id: string;
  name: string;
  description?: string;
  members: TeamMember[];
  budget: number;
  current_usage: number;
  created_at: string;
  created_by: string;
}

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'member' | 'viewer';
  joined_at: string;
}

export default function Teams() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);

  const fetchTeams = async () => {
    try {
      setLoading(true);
      const [teamsRes, usersRes] = await Promise.all([
        teamsAPI.list(),
        usersAPI.list(),
      ]);
      setTeams(teamsRes?.teams || teamsRes || []);
      setUsers(usersRes?.users || usersRes || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load teams');
      toast.error('Failed to load teams');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeams();
  }, []);

  const handleCreate = async (values: any) => {
    try {
      await teamsAPI.create(values);
      toast.success('Team created');
      setShowCreate(false);
      fetchTeams();
    } catch (err: any) {
      toast.error(err.message || 'Failed to create team');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure?')) return;
    try {
      await teamsAPI.delete?.(id);
      toast.success('Team deleted');
      await fetchTeams();
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete');
    }
  };

  const { values, errors, handleChange, handleSubmit } = useForm({
    initialValues: { name: '', description: '', budget: 500 },
    validationSchema: {
      name: { required: true, minLength: 1, maxLength: 100 },
    },
    onSubmit: handleCreate,
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map(i => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchTeams} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Teams</h1>
          <p className="text-gray-500 mt-1">Manage teams and their budgets</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Team
        </button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Create Team</h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                name="name"
                value={values.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Engineering Team"
              />
              {errors.name && <span className="text-red-500 text-sm">{errors.name}</span>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Budget ($)</label>
              <input
                type="number"
                name="budget"
                value={values.budget}
                onChange={(e) => handleChange('budget', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="flex items-end gap-2">
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Create
              </button>
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Teams Grid */}
      {teams.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {teams.map((team) => (
            <div 
              key={team.id} 
              className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedTeam(selectedTeam?.id === team.id ? null : team)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
                    <Users className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{team.name}</h3>
                    <div className="text-sm text-gray-500">
                      {team.members?.length || 0} members
                    </div>
                  </div>
                </div>
                <button 
                  onClick={(e) => { e.stopPropagation(); handleDelete(team.id); }}
                  className="p-2 text-red-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Budget */}
              <div className="mt-4">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Budget Usage</span>
                  <span className="font-medium">
                    ${team.current_usage?.toFixed(2) || '0.00'} / ${team.budget?.toLocaleString()}
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all ${
                      ((team.current_usage || 0) / (team.budget || 1)) > 0.9 ? 'bg-red-500' : 'bg-indigo-500'
                    }`}
                    style={{ width: `${Math.min(((team.current_usage || 0) / (team.budget || 1)) * 100, 100)}%` }}
                  />
                </div>
              </div>

              {/* Members Preview */}
              {team.members && team.members.length > 0 && (
                <div className="mt-4 flex items-center gap-2">
                  <div className="flex -space-x-2">
                    {team.members.slice(0, 4).map((member, i) => (
                      <div 
                        key={member.id}
                        className="w-8 h-8 rounded-full bg-gray-200 border-2 border-white flex items-center justify-center text-xs font-medium"
                        title={member.name}
                      >
                        {member.name.charAt(0).toUpperCase()}
                      </div>
                    ))}
                    {team.members.length > 4 && (
                      <div className="w-8 h-8 rounded-full bg-gray-100 border-2 border-white flex items-center justify-center text-xs text-gray-600">
                        +{team.members.length - 4}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Expanded Member List */}
              {selectedTeam?.id === team.id && team.members && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Members</h4>
                  <div className="space-y-2">
                    {team.members.map((member) => (
                      <div key={member.id} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-sm font-medium text-indigo-600">
                            {member.name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="text-sm font-medium">{member.name}</div>
                            <div className="text-xs text-gray-500">{member.email}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {member.role === 'admin' && <Crown className="w-4 h-4 text-amber-500" />}
                          <span className={`text-xs px-2 py-1 rounded ${
                            member.role === 'admin' ? 'bg-amber-100 text-amber-700' :
                            member.role === 'member' ? 'bg-indigo-100 text-indigo-700' :
                            'bg-gray-100 text-gray-600'
                          }`}>
                            {member.role}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState 
          message="No teams yet" 
          action={{ label: 'Create Team', onClick: () => setShowCreate(true) }}
        />
      )}
    </div>
  );
}
