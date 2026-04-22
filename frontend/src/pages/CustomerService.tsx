import { useState } from 'react'
import { useQueueStats } from '../hooks/useDashboard'
import { Phone, MessageSquare, Mail, Globe, MessageCircle, Users, AlertTriangle, Clock } from 'lucide-react'

export default function CustomerService() {
  const { data: stats, isLoading } = useQueueStats()
  const [activeTab, setActiveTab] = useState<'overview' | 'queues' | 'breaches'>('overview')

  const channels = [
    { name: 'WhatsApp', icon: MessageCircle, color: 'bg-green-500' },
    { name: 'Telegram', icon: MessageSquare, color: 'bg-blue-500' },
    { name: 'Web Chat', icon: Globe, color: 'bg-indigo-500' },
    { name: 'Voice', icon: Phone, color: 'bg-purple-500' },
    { name: 'Email', icon: Mail, color: 'bg-orange-500' },
    { name: 'Discord', icon: MessageSquare, color: 'bg-indigo-600' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Customer Service</h1>
        <div className="flex space-x-2">
          {(['overview', 'queues', 'breaches'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Channel Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {channels.map((channel) => (
          <div key={channel.name} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <channel.icon className={`w-6 h-6 text-white p-1 rounded ${channel.color}`} />
              <span className="text-2xl font-bold text-gray-900">
                {stats?.by_channel?.[channel.name.toLowerCase()] || 0}
              </span>
            </div>
            <p className="text-sm text-gray-600">{channel.name}</p>
          </div>
        ))}
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Queue Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Active Conversations</p>
                  <p className="text-3xl font-bold text-gray-900">{stats?.active || 0}</p>
                </div>
                <Users className="w-8 h-8 text-indigo-600" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Pending</p>
                  <p className="text-3xl font-bold text-yellow-600">{stats?.pending || 0}</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-600" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">SLA Breaches</p>
                  <p className="text-3xl font-bold text-red-600">{stats?.sla_breaches || 0}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Today</p>
                  <p className="text-3xl font-bold text-green-600">
                    {stats?.total_conversations || 0}
                  </p>
                </div>
                <MessageSquare className="w-8 h-8 text-green-600" />
              </div>
            </div>
          </div>

          {/* Priority Breakdown */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">By Priority</h2>
            <div className="space-y-3">
              {stats?.by_priority && Object.entries(stats.by_priority).map(([priority, count]) => (
                <div key={priority} className="flex items-center">
                  <span className="w-20 text-sm text-gray-600 capitalize">{priority}</span>
                  <div className="flex-1 mx-3">
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          priority === 'critical' ? 'bg-red-500' :
                          priority === 'high' ? 'bg-orange-500' :
                          priority === 'medium' ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(100, (count / (stats.total_conversations || 1)) * 100)}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {activeTab === 'queues' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Agent Queues</h2>
          <div className="space-y-4">
            {stats?.agent_utilization && Object.entries(stats.agent_utilization).map(([agentId, count]) => (
              <div key={agentId} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                    <Users className="w-4 h-4 text-indigo-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Agent {agentId.slice(0, 8)}...</p>
                    <p className="text-sm text-gray-500">{count} conversations</p>
                  </div>
                </div>
                <span className={`px-3 py-1 text-sm rounded-full ${
                  count > 10 ? 'bg-red-100 text-red-800' :
                  count > 5 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-green-100 text-green-800'
                }`}>
                  {count > 10 ? 'Overloaded' : count > 5 ? 'Busy' : 'Available'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'breaches' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">SLA Breaches</h2>
          {stats?.breach_details?.length === 0 ? (
            <div className="text-center py-8">
              <AlertTriangle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <p className="text-gray-600">No active SLA breaches!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {stats?.breach_details?.map((breach: any) => (
                <div key={breach.conversation_id} className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-red-900">
                      {breach.breach_type === 'first_response' ? 'First Response' : 'Resolution'} Breach
                    </span>
                    <span className="text-sm text-red-700">
                      {Math.round(breach.elapsed_minutes)} min elapsed
                    </span>
                  </div>
                  <p className="text-sm text-red-800">
                    Customer: {breach.customer_id} | Channel: {breach.channel} | Priority: {breach.priority}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
