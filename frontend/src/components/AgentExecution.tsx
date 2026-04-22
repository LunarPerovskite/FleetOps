import React, { useState, useEffect } from 'react';
import { useToast } from '../hooks/useToast';
import { api } from '../lib/api';
import { Loading } from '../components/Loading';
import { Play, Pause, Square, CheckCircle, XCircle, Bot, Clock, AlertTriangle, Loader } from 'lucide-react';

interface AgentExecutionProps {
  taskId: string;
  taskTitle: string;
  onExecutionComplete?: () => void;
}

interface AgentType {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  status: string;
}

export default function AgentExecution({ taskId, taskTitle, onExecutionComplete }: AgentExecutionProps) {
  const [agents, setAgents] = useState<AgentType[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [executionStatus, setExecutionStatus] = useState<string>('idle');
  const [executionId, setExecutionId] = useState<string>('');
  const [progress, setProgress] = useState(0);
  const [autoApprove, setAutoApprove] = useState(false);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await api.get('/agent-execute/agents');
      const agentList = Object.entries(response.data.agents || {}).map(([id, data]: [string, any]) => ({
        id,
        ...data
      }));
      setAgents(agentList);
      if (agentList.length > 0) {
        setSelectedAgent(agentList[0].id);
      }
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const startExecution = async () => {
    if (!selectedAgent) {
      toast({ title: 'Error', description: 'Please select an agent', variant: 'destructive' });
      return;
    }

    setLoading(true);
    setExecutionStatus('starting');
    setLogs([]);

    try {
      const response = await api.post(`/agent-execute/${taskId}`, null, {
        params: {
          agent_type: selectedAgent,
          auto_approve_low_risk: autoApprove
        }
      });

      setExecutionId(response.data.execution_id);
      setExecutionStatus('running');
      toast({ title: 'Agent Started', description: `${response.data.agent_type} is working on this task` });

      // Start polling
      startPolling(response.data.execution_id);

    } catch (error: any) {
      setExecutionStatus('error');
      toast({ 
        title: 'Execution Failed', 
        description: error.response?.data?.detail || error.message,
        variant: 'destructive' 
      });
    } finally {
      setLoading(false);
    }
  };

  const startPolling = (execId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/agent-execute/status/${taskId}`);
        const status = response.data;

        setExecutionStatus(status.status);
        setProgress(status.progress || 0);

        if (status.status === 'completed') {
          clearInterval(interval);
          toast({ title: 'Task Complete', description: 'Agent finished successfully. Please review the results.' });
          if (onExecutionComplete) onExecutionComplete();
        } else if (status.status === 'failed') {
          clearInterval(interval);
          toast({ title: 'Task Failed', description: status.error || 'Execution failed', variant: 'destructive' });
        } else if (status.status === 'awaiting_approval') {
          clearInterval(interval);
          toast({ 
            title: 'Approval Needed', 
            description: 'Agent needs your approval to continue',
            variant: 'default'
          });
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 3000);

    // Cleanup after 1 hour
    setTimeout(() => clearInterval(interval), 3600000);
  };

  const cancelExecution = async () => {
    try {
      await api.post(`/agent-execute/cancel/${taskId}`, { reason: 'User cancelled' });
      setExecutionStatus('cancelled');
      toast({ title: 'Cancelled', description: 'Execution cancelled' });
    } catch (error: any) {
      toast({ 
        title: 'Cancel Failed', 
        description: error.response?.data?.detail || error.message,
        variant: 'destructive' 
      });
    }
  };

  const getStatusIcon = () => {
    switch (executionStatus) {
      case 'running':
        return <Loader className="h-5 w-5 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'awaiting_approval':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'cancelled':
        return <Square className="h-5 w-5 text-gray-500" />;
      default:
        return <Bot className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (executionStatus) {
      case 'idle': return 'Ready to execute';
      case 'starting': return 'Starting...';
      case 'running': return `Executing (${progress}%)`;
      case 'completed': return 'Completed - Review results';
      case 'failed': return 'Failed - Check logs';
      case 'awaiting_approval': return 'Awaiting your approval';
      case 'cancelled': return 'Cancelled';
      default: return 'Unknown';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold">AI Agent Execution</h3>
        </div>
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="text-sm font-medium">{getStatusText()}</span>
        </div>
      </div>

      {/* Progress Bar */}
      {executionStatus === 'running' && (
        <div className="mb-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{progress}% complete</p>
        </div>
      )}

      {/* Agent Selection */}
      {executionStatus === 'idle' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Agent
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {agents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent.id)}
                  className={`p-3 border rounded-lg text-left transition-colors ${
                    selectedAgent === agent.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{agent.name}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      agent.status === 'available' 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {agent.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{agent.description}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {agent.capabilities.slice(0, 3).map((cap: string) => (
                      <span key={cap} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                        {cap.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Auto-approve Option */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="autoApprove"
              checked={autoApprove}
              onChange={(e) => setAutoApprove(e.target.checked)}
              className="rounded border-gray-300"
            />
            <label htmlFor="autoApprove" className="text-sm text-gray-700">
              Auto-approve low-risk steps (read-only operations)
            </label>
          </div>

          {/* Execute Button */}
          <button
            onClick={startExecution}
            disabled={loading || !selectedAgent}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader className="h-5 w-5 animate-spin" />
            ) : (
              <Play className="h-5 w-5" />
            )}
            {loading ? 'Starting...' : 'Execute with Agent'}
          </button>
        </div>
      )}

      {/* Running State */}
      {(executionStatus === 'running' || executionStatus === 'awaiting_approval') && (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">
                {executionStatus === 'awaiting_approval' 
                  ? 'Agent is waiting for your approval' 
                  : 'Agent is working...'}
              </span>
            </div>
            <p className="text-sm text-blue-700">
              {executionStatus === 'awaiting_approval'
                ? 'Review the agent\'s work and approve to continue, or reject to stop.'
                : 'The agent is executing steps. You will be notified when approval is needed.'}
            </p>
          </div>

          <button
            onClick={cancelExecution}
            className="w-full flex items-center justify-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
          >
            <Square className="h-5 w-5" />
            Cancel Execution
          </button>
        </div>
      )}

      {/* Completed State */}
      {executionStatus === 'completed' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span className="font-medium text-green-900">Execution Complete</span>
          </div>
          <p className="text-sm text-green-700 mb-3">
            The agent has finished. Please review the results and mark the task as complete.
          </p>
          <button
            onClick={() => {
              setExecutionStatus('idle');
              setExecutionId('');
              setProgress(0);
            }}
            className="text-sm text-green-700 hover:text-green-900 underline"
          >
            Execute Again
          </button>
        </div>
      )}

      {/* Failed State */}
      {executionStatus === 'failed' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <XCircle className="h-5 w-5 text-red-600" />
            <span className="font-medium text-red-900">Execution Failed</span>
          </div>
          <p className="text-sm text-red-700 mb-3">
            The agent encountered an error. Check the task logs for details.
          </p>
          <button
            onClick={() => {
              setExecutionStatus('idle');
              setExecutionId('');
            }}
            className="text-sm text-red-700 hover:text-red-900 underline"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
