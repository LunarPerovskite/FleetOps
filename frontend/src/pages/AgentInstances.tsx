import React, { useState, useEffect } from 'react';
import { useToast } from '../hooks/useToast';
import { api } from '../lib/api';
import { Loading } from '../components/Loading';
import {
  Bot,
  Power,
  PowerOff,
  Shield,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  Globe,
  Server,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Plus,
  Trash2,
  Edit,
  Settings,
  ChevronDown,
  ChevronUp,
  Activity,
  Lock,
  Unlock
} from 'lucide-react';

interface AgentInstance {
  id: string;
  agent_type: string;
  name: string;
  description: string;
  status: string;
  is_active: boolean;
  is_remote: boolean;
  host_url: string;
  permission_level: string;
  auto_approve_low_risk: boolean;
  auto_approve_read_only: boolean;
  auto_approve_predefined: boolean;
  max_risk_level: string;
  approved_actions: string[];
  blocked_actions: string[];
  max_execution_time: number;
  max_steps_per_session: number;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
}

interface PermissionLevel {
  id: string;
  name: string;
  description: string;
  auto_approve: boolean | string;
  risk: string;
}

export default function AgentInstances() {
  const [instances, setInstances] = useState<AgentInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedInstance, setSelectedInstance] = useState<AgentInstance | null>(null);
  const [permissionLevels, setPermissionLevels] = useState<PermissionLevel[]>([]);
  const [agentTypes, setAgentTypes] = useState<any[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    loadInstances();
    loadPermissionLevels();
    loadAgentTypes();
  }, []);

  const loadInstances = async () => {
    try {
      const response = await api.get('/agent-instances/');
      setInstances(response.data.instances || []);
    } catch (error) {
      console.error('Error loading instances:', error);
      toast({ title: 'Error', description: 'Failed to load agent instances', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const loadPermissionLevels = async () => {
    try {
      const response = await api.get('/agent-instances/permissions/levels');
      setPermissionLevels(response.data.permission_levels || []);
    } catch (error) {
      console.error('Error loading permission levels:', error);
    }
  };

  const loadAgentTypes = async () => {
    try {
      const response = await api.get('/agent-instances/types/available');
      setAgentTypes(response.data.agent_types || []);
    } catch (error) {
      console.error('Error loading agent types:', error);
    }
  };

  const activateInstance = async (id: string) => {
    try {
      await api.post(`/agent-instances/${id}/activate`);
      toast({ title: 'Activated', description: 'Agent instance activated' });
      loadInstances();
    } catch (error: any) {
      toast({ title: 'Error', description: error.response?.data?.detail || 'Failed to activate', variant: 'destructive' });
    }
  };

  const deactivateInstance = async (id: string) => {
    try {
      await api.post(`/agent-instances/${id}/deactivate`);
      toast({ title: 'Deactivated', description: 'Agent instance deactivated' });
      loadInstances();
    } catch (error: any) {
      toast({ title: 'Error', description: error.response?.data?.detail || 'Failed to deactivate', variant: 'destructive' });
    }
  };

  const deleteInstance = async (id: string) => {
    if (!confirm('Are you sure you want to delete this agent instance?')) return;
    
    try {
      await api.delete(`/agent-instances/${id}`);
      toast({ title: 'Deleted', description: 'Agent instance deleted' });
      loadInstances();
    } catch (error: any) {
      toast({ title: 'Error', description: error.response?.data?.detail || 'Failed to delete', variant: 'destructive' });
    }
  };

  const updatePermissions = async (id: string, permissionLevel: string, settings: any) => {
    try {
      await api.post(`/agent-instances/${id}/permissions`, null, {
        params: {
          permission_level: permissionLevel,
          auto_approve_low_risk: settings.auto_approve_low_risk,
          auto_approve_read_only: settings.auto_approve_read_only,
          auto_approve_predefined: settings.auto_approve_predefined
        }
      });
      toast({ title: 'Updated', description: 'Permissions updated' });
      loadInstances();
    } catch (error: any) {
      toast({ title: 'Error', description: error.response?.data?.detail || 'Failed to update', variant: 'destructive' });
    }
  };

  const getPermissionIcon = (level: string) => {
    switch (level) {
      case 'read_only':
        return <ShieldCheck className="h-4 w-4 text-green-500" />;
      case 'low_risk':
        return <Shield className="h-4 w-4 text-blue-500" />;
      case 'approved_actions':
        return <ShieldCheck className="h-4 w-4 text-yellow-500" />;
      case 'full_access':
        return <ShieldAlert className="h-4 w-4 text-orange-500" />;
      case 'supervised':
        return <ShieldX className="h-4 w-4 text-red-500" />;
      case 'autonomous':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Shield className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusIcon = (instance: AgentInstance) => {
    if (!instance.is_active) {
      return <PowerOff className="h-4 w-4 text-gray-400" />;
    }
    if (instance.is_remote) {
      return <Globe className="h-4 w-4 text-blue-500" />;
    }
    return <Server className="h-4 w-4 text-green-500" />;
  };

  const getSuccessRate = (instance: AgentInstance) => {
    if (instance.total_executions === 0) return 0;
    return Math.round((instance.successful_executions / instance.total_executions) * 100);
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="h-6 w-6 text-blue-600" />
          <h1 className="text-2xl font-bold">Agent Instances</h1>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Add Agent Instance
        </button>
      </div>

      {/* Instance List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {instances.map((instance) => (
          <div
            key={instance.id}
            className={`bg-white rounded-lg border p-4 ${
              !instance.is_active ? 'opacity-60' : ''
            }`}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-2">
                {getStatusIcon(instance)}
                <div>
                  <h3 className="font-semibold">{instance.name}</h3>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <span className="capitalize">{instance.agent_type}</span>
                    {instance.is_remote && <span>• Remote</span>}
                    <span>• {instance.permission_level.replace('_', ' ')}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-1">
                {instance.is_active ? (
                  <button
                    onClick={() => deactivateInstance(instance.id)}
                    className="p-1 text-green-600 hover:text-red-600 transition-colors"
                    title="Deactivate"
                  >
                    <Power className="h-5 w-5" />
                  </button>
                ) : (
                  <button
                    onClick={() => activateInstance(instance.id)}
                    className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                    title="Activate"
                  >
                    <PowerOff className="h-5 w-5" />
                  </button>
                )}
                <button
                  onClick={() => setSelectedInstance(selectedInstance?.id === instance.id ? null : instance)}
                  className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                  title="Edit"
                >
                  <Edit className="h-5 w-5" />
                </button>
                <button
                  onClick={() => deleteInstance(instance.id)}
                  className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                  title="Delete"
                >
                  <Trash2 className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="bg-gray-50 rounded p-2 text-center">
                <div className="text-lg font-bold">{instance.total_executions}</div>
                <div className="text-xs text-gray-500">Total Runs</div>
              </div>
              <div className="bg-green-50 rounded p-2 text-center">
                <div className="text-lg font-bold text-green-600">{getSuccessRate(instance)}%</div>
                <div className="text-xs text-gray-500">Success Rate</div>
              </div>
              <div className="bg-blue-50 rounded p-2 text-center">
                <div className="text-lg font-bold text-blue-600">{instance.max_execution_time}s</div>
                <div className="text-xs text-gray-500">Timeout</div>
              </div>
            </div>

            {/* Permission Summary */}
            <div className="flex items-center gap-2 text-sm">
              {getPermissionIcon(instance.permission_level)}
              <span className="capitalize">{instance.permission_level.replace('_', ' ')}</span>
              
              {instance.auto_approve_read_only && (
                <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded text-xs">
                  Auto Read
                </span>
              )}
              
              {instance.auto_approve_low_risk && (
                <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">
                  Auto Low Risk
                </span>
              )}
              
              {instance.auto_approve_predefined && (
                <span className="bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded text-xs">
                  Auto Predefined
                </span>
              )}
              
              {!instance.auto_approve_read_only && !instance.auto_approve_low_risk && !instance.auto_approve_predefined && (
                <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs">
                  Manual Approval
                </span>
              )}
            </div>

            {/* Expanded Settings */}
            {selectedInstance?.id === instance.id && (
              <div className="mt-4 pt-4 border-t space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Permission Level</h4>
                  <div className="space-y-2">
                    {permissionLevels.map((level) => (
                      <button
                        key={level.id}
                        onClick={() => updatePermissions(instance.id, level.id, {
                          auto_approve_low_risk: instance.auto_approve_low_risk,
                          auto_approve_read_only: instance.auto_approve_read_only,
                          auto_approve_predefined: instance.auto_approve_predefined
                        })}
                        className={`w-full flex items-center gap-2 p-2 rounded text-left ${
                          instance.permission_level === level.id
                            ? 'bg-blue-50 border border-blue-200'
                            : 'bg-gray-50 border border-gray-200 hover:bg-gray-100'
                        }`}
                      >
                        {getPermissionIcon(level.id)}
                        <div className="flex-1">
                          <div className="font-medium">{level.name}</div>
                          <div className="text-xs text-gray-500">{level.description}</div>
                        </div>
                        {instance.permission_level === level.id && (
                          <CheckCircle className="h-4 w-4 text-blue-600" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">Auto-Approve Settings</h4>
                  <div className="space-y-2">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={instance.auto_approve_read_only}
                        onChange={(e) => updatePermissions(instance.id, instance.permission_level, {
                          ...instance,
                          auto_approve_read_only: e.target.checked
                        })}
                        className="rounded"
                      />
                      <span className="text-sm">Auto-approve read-only actions</span>
                    </label>
                    
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={instance.auto_approve_low_risk}
                        onChange={(e) => updatePermissions(instance.id, instance.permission_level, {
                          ...instance,
                          auto_approve_low_risk: e.target.checked
                        })}
                        className="rounded"
                      />
                      <span className="text-sm">Auto-approve low-risk actions</span>
                    </label>
                    
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={instance.auto_approve_predefined}
                        onChange={(e) => updatePermissions(instance.id, instance.permission_level, {
                          ...instance,
                          auto_approve_predefined: e.target.checked
                        })}
                        className="rounded"
                      />
                      <span className="text-sm">Auto-approve predefined actions</span>
                    </label>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">Action Lists</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-gray-600 mb-1">Approved Actions</div>
                      <div className="flex flex-wrap gap-1">
                        {instance.approved_actions.length > 0 ? (
                          instance.approved_actions.map((action) => (
                            <span key={action} className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs">
                              {action}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-gray-400">No approved actions</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600 mb-1">Blocked Actions</div>
                      <div className="flex flex-wrap gap-1">
                        {instance.blocked_actions.length > 0 ? (
                          instance.blocked_actions.map((action) => (
                            <span key={action} className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs">
                              {action}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-gray-400">No blocked actions</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
        
        {instances.length === 0 && (
          <div className="col-span-2 text-center py-12 bg-gray-50 rounded-lg">
            <Bot className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No agent instances configured</p>
            <p className="text-sm text-gray-400 mt-1">Add an agent to get started</p>
          </div>
        )}
      </div>

      {/* Create Instance Modal */}
      {showCreate && (
        <CreateInstanceModal
          agentTypes={agentTypes}
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            loadInstances();
          }}
        />
      )}
    </div>
  );
}

function CreateInstanceModal({ agentTypes, onClose, onCreated }: {
  agentTypes: any[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    agent_type: '',
    name: '',
    description: '',
    is_remote: false,
    host_url: '',
    permission_level: 'approved_actions',
    auto_approve_low_risk: false,
    auto_approve_read_only: true,
    max_execution_time: 3600
  });
  const { toast } = useToast();

  const handleCreate = async () => {
    try {
      await api.post('/agent-instances/', null, { params: formData });
      toast({ title: 'Created', description: 'Agent instance created successfully' });
      onCreated();
    } catch (error: any) {
      toast({ title: 'Error', description: error.response?.data?.detail || 'Failed to create', variant: 'destructive' });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Add Agent Instance</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><XCircle className="h-5 w-5" /></button>
        </div>

        {step === 1 && (
          <div className="space-y-4">
            <h3 className="font-medium">Select Agent Type</h3>
            <div className="grid grid-cols-1 gap-2">
              {agentTypes.map((type) => (
                <button
                  key={type.id}
                  onClick={() => {
                    setFormData({ ...formData, agent_type: type.id });
                    setStep(2);
                  }}
                  className={`p-3 border rounded-lg text-left ${
                    formData.agent_type === type.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium">{type.name}</div>
                  <div className="text-sm text-gray-500">{type.description}</div>
                  <div className="flex gap-1 mt-1">
                    {type.supports_local && <span className="text-xs bg-gray-100 px-1 rounded">Local</span>}
                    {type.supports_remote && <span className="text-xs bg-blue-100 text-blue-700 px-1 rounded">Remote</span>}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="My OpenClaw Agent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
                rows={2}
                placeholder="Optional description..."
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="isRemote"
                checked={formData.is_remote}
                onChange={(e) => setFormData({ ...formData, is_remote: e.target.checked })}
                className="rounded"
              />
              <label htmlFor="isRemote" className="text-sm">
                Remote Agent (running on different machine)
              </label>
            </div>

            {formData.is_remote && (
              <div>
                <label className="block text-sm font-medium mb-1">Host URL</label>
                <input
                  type="url"
                  value={formData.host_url}
                  onChange={(e) => setFormData({ ...formData, host_url: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="http://192.168.1.100:8080"
                />
              </div>
            )}

            <div className="flex gap-2">
              <button onClick={() => setStep(1)} className="flex-1 border rounded-lg py-2">Back</button>
              <button
                onClick={() => setStep(3)}
                disabled={!formData.name}
                className="flex-1 bg-blue-600 text-white rounded-lg py-2 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Permission Level</label>
              <select
                value={formData.permission_level}
                onChange={(e) => setFormData({ ...formData, permission_level: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
              >
                <option value="read_only">Read Only</option>
                <option value="low_risk">Low Risk</option>
                <option value="approved_actions">Approved Actions</option>
                <option value="full_access">Full Access (with Approval)</option>
                <option value="supervised">Fully Supervised</option>
                <option value="autonomous">⚠️ Autonomous</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.auto_approve_read_only}
                  onChange={(e) => setFormData({ ...formData, auto_approve_read_only: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm">Auto-approve read-only actions</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.auto_approve_low_risk}
                  onChange={(e) => setFormData({ ...formData, auto_approve_low_risk: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm">Auto-approve low-risk actions</span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Max Execution Time (seconds)</label>
              <input
                type="number"
                value={formData.max_execution_time}
                onChange={(e) => setFormData({ ...formData, max_execution_time: parseInt(e.target.value) })}
                className="w-full border rounded-lg px-3 py-2"
              />
            </div>

            <div className="flex gap-2">
              <button onClick={() => setStep(2)} className="flex-1 border rounded-lg py-2">Back</button>
              <button
                onClick={handleCreate}
                className="flex-1 bg-blue-600 text-white rounded-lg py-2 hover:bg-blue-700"
              >
                Create Agent Instance
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
