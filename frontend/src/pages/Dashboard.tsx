import { useDashboardStats, useTasks, useAgents, usePendingApprovals } from '../hooks/useDashboard'
import StatCard from '../components/StatCard'
import TaskList from '../components/TaskList'
import { Bot, CheckSquare, Clock, Shield, Activity } from 'lucide-react'

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats()
  const { data: tasks } = useTasks()
  const { data: agents } = useAgents()
  const { data: approvals } = usePendingApprovals()

  return (
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
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Tasks</h2>
          <a href="/tasks" className="text-sm text-indigo-600 hover:text-indigo-800">
            View all
          </a>
        </div>
        <TaskList tasks={tasks?.slice(0, 5) || []} />
      </div>

      {/* Active Agents */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Active Agents</h2>
          <a href="/agents" className="text-sm text-indigo-600 hover:text-indigo-800">
            View all
          </a>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents?.slice(0, 6).map((agent: any) => (
            <div key={agent.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                    <Bot className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{agent.name}</h3>
                    <p className="text-sm text-gray-500">{agent.provider}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  agent.status === 'active' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {agent.status}
                </span>
              </div>
              <div className="mt-3 flex items-center justify-between text-sm">
                <span className="text-gray-500">Level: {agent.level}</span>
                <span className="text-gray-500">
                  ${agent.cost_to_date?.toFixed(2) || '0.00'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
