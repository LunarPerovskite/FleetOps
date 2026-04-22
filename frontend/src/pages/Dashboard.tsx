import { useState, useEffect } from 'react';
import { useDashboardStats, useActivity, useAgents, usePendingApprovals } from '../hooks/useDashboard'
import { useWebSocketContext } from '../hooks/useWebSocketContext'
import { Loading, SkeletonCard, SkeletonTable } from '../components/Loading'
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay'
import StatCard from '../components/StatCard'
import { toast } from '../hooks/useToast'
import { Bot, CheckSquare, Clock, Shield, Activity } from 'lucide-react'

export default function Dashboard() {
  const { ws, isConnected } = useWebSocketContext()
  const { data: stats, isLoading: statsLoading, error: statsError, refresh: refreshStats } = useDashboardStats()
  const { data: activities, isLoading: activityLoading, error: activityError, refresh: refreshActivity } = useActivity()
  const { data: agents, isLoading: agentsLoading, error: agentsError, refresh: refreshAgents } = useAgents()
  const { data: approvals, isLoading: approvalsLoading, error: approvalsError, refresh: refreshApprovals } = usePendingApprovals()

  // WebSocket: Listen for real-time updates
  useEffect(() => {
    if (!ws) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'task_created':
          case 'task_updated':
          case 'task_completed':
            refreshStats();
            refreshActivity();
            toast.info(`Task ${data.type.replace('task_', '')}: ${data.task_title || 'Unknown'}`);
            break;
          
          case 'agent_created':
          case 'agent_updated':
            refreshAgents();
            refreshStats();
            toast.info(`Agent ${data.type.replace('agent_', '')}: ${data.agent_name || 'Unknown'}`);
            break;
          
          case 'approval_required':
            refreshApprovals();
            refreshStats();
            toast.warning(`Approval needed: ${data.task_title || 'Unknown task'}`);
            break;
          
          case 'approval_decided':
            refreshApprovals();
            refreshStats();
            toast.info(`Approval ${data.decision}: ${data.task_title || 'Unknown'}`);
            break;
          
          case 'event':
            refreshActivity();
            break;
          
          case 'error':
            toast.error(`Error: ${data.message || 'Unknown error'}`);
            break;
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.addEventListener('message', handleMessage);
    
    return () => {
      ws.removeEventListener('message', handleMessage);
    };
  }, [ws]);

  // Connection status indicator
  const ConnectionStatus = () => (
    <div className={`fixed bottom-4 right-4 flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium ${
      isConnected 
        ? 'bg-green-50 text-green-700 border border-green-200' 
        : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
    }`}>
      <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-yellow-500'}`} />
      {isConnected ? 'Live' : 'Reconnecting...'}
    </div>
  );

  if (statsLoading && !stats) {
    return (
      <>
        <div className="space-y-6">
          <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
          <SkeletonTable rows={3} />
        </div>
        <ConnectionStatus />
      </>
    )
  }

  if (statsError) {
    return (
      <>
        <ErrorDisplay
          title="Failed to load dashboard"
          message={statsError}
          onRetry={() => window.location.reload()}
          fullPage
        />
        <ConnectionStatus />
      </>
    )
  }

  return (
    <>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Fleet Overview</h1>
          <span className="text-sm text-gray-500">
            {new Date().toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </span>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Active Agents"
            value={stats?.active_agents || 0}
            icon={Bot}
            trend="+2 today"
            trendUp={true}
          />
          <StatCard
            title="Tasks In Progress"
            value={stats?.tasks_in_progress || 0}
            icon={Activity}
            trend="3 completed today"
            trendUp={true}
          />
          <StatCard
            title="Pending Approvals"
            value={stats?.pending_approvals || 0}
            icon={Shield}
            trend="2 urgent"
            trendUp={false}
          />
          <StatCard
            title="Cost Today"
            value={`$${(stats?.cost_today || 0).toFixed(2)}`}
            icon={Clock}
            trend="Under budget"
            trendUp={true}
          />
        </div>

        {/* Pending Approvals Alert */}
        {approvals && approvals.length > 0 && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Shield className="w-5 h-5 text-orange-600" />
                <div>
                  <h3 className="font-medium text-orange-900">
                    {approvals.length} Approval{approvals.length !== 1 ? 's' : ''} Pending
                  </h3>
                  <p className="text-sm text-orange-700">
                    Action required from your team
                  </p>
                </div>
              </div>
              <button className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors">
                Review
              </button>
            </div>
          </div>
        )}

        {/* Recent Tasks */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          
          {activityLoading ? (
            <SkeletonTable rows={5} />
          ) : activityError ? (
            <ErrorDisplay message={activityError} onRetry={refreshActivity} />
          ) : activities && activities.length > 0 ? (
            <div className="space-y-3">
              {activities.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0"
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      activity.type === 'task_completed' ? 'bg-green-500' :
                      activity.type === 'approval_required' ? 'bg-orange-500' :
                      'bg-blue-500'
                    }`} />
                    <div>
                      <p className="text-sm text-gray-900">{activity.description}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(activity.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                  {activity.user && (
                    <span className="text-xs text-gray-500">{activity.user}</span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No recent activity"
              message="Activity will appear here when agents start working."
            />
          )}
        </div>

        {/* Active Agents */}
        {agentsLoading ? (
          <Loading text="Loading agents..." />
        ) : agentsError ? (
          <ErrorDisplay message={agentsError} onRetry={refreshAgents} />
        ) : agents && agents.length > 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Agents</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agents.slice(0, 6).map((agent) => (
                <div
                  key={agent.id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <Bot className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{agent.name}</p>
                      <p className="text-sm text-gray-500">{agent.provider}</p>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      agent.status === 'active'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {agent.status}
                    </span>
                    <span className="text-xs text-gray-500">
                      {agent.tasks_count || 0} tasks
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <EmptyState
            title="No agents yet"
            message="Create your first agent to get started."
            action={{ label: 'Create Agent', onClick: () => {} }}
          />
        )}
      </div>
      <ConnectionStatus />
    </>
  )
}
