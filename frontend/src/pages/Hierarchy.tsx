import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Users, Bot, Settings, ChevronUp, ChevronDown } from 'lucide-react'

export default function Hierarchy() {
  const [activeTab, setActiveTab] = useState<'scales' | 'levels' | 'assignments' | 'ladders'>('scales')
  const [showCreateScale, setShowCreateScale] = useState(false)

  // Mock data - would come from API
  const scales = [
    {
      id: 'scale_1',
      name: 'Corporate',
      type: 'human',
      levels: [
        { id: 'l1', name: 'Executive', order: 10, color: '#EF4444', icon: 'crown', permissions: ['all'] },
        { id: 'l2', name: 'Director', order: 9, color: '#F97316', icon: 'user-tie', permissions: ['approve_critical', 'manage_teams'] },
        { id: 'l3', name: 'Manager', order: 8, color: '#F59E0B', icon: 'users', permissions: ['approve_high', 'manage_agents'] },
        { id: 'l4', name: 'Senior', order: 7, color: '#10B981', icon: 'user-check', permissions: ['approve_medium'] },
        { id: 'l5', name: 'Operator', order: 6, color: '#3B82F6', icon: 'user', permissions: ['approve_low'] },
        { id: 'l6', name: 'Viewer', order: 5, color: '#6B7280', icon: 'eye', permissions: ['view'] }
      ]
    },
    {
      id: 'scale_2',
      name: 'Flat Team',
      type: 'human',
      levels: [
        { id: 'l7', name: 'Lead', order: 3, color: '#8B5CF6', icon: 'star', permissions: ['approve_all', 'manage_team'] },
        { id: 'l8', name: 'Member', order: 2, color: '#06B6D4', icon: 'user', permissions: ['approve_low', 'view'] }
      ]
    }
  ]

  const ladders = [
    { id: 'lad1', name: 'Standard', risk: 'low', min_level: 6, auto_approve: true },
    { id: 'lad2', name: 'Careful', risk: 'medium', min_level: 7, auto_approve: false },
    { id: 'lad3', name: 'Strict', risk: 'high', min_level: 8, auto_approve: false, second_pair: true },
    { id: 'lad4', name: 'Executive', risk: 'critical', min_level: 10, auto_approve: false, second_pair: true }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Hierarchy Management</h1>
        <button
          onClick={() => setShowCreateScale(true)}
          className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Scale
        </button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2">
        {(['scales', 'levels', 'assignments', 'ladders'] as const).map((tab) => (
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

      {/* Scales View */}
      {activeTab === 'scales' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {scales.map((scale) => (
            <div key={scale.id} className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-6 border-b border-gray-100">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{scale.name}</h3>
                    <p className="text-sm text-gray-500">{scale.type} hierarchy • {scale.levels.length} levels</p>
                  </div>
                  <span className="px-3 py-1 text-xs rounded-full bg-green-100 text-green-800">
                    Active
                  </span>
                </div>
              </div>
              
              <div className="p-6">
                <div className="space-y-3">
                  {scale.levels.sort((a, b) => b.order - a.order).map((level, idx) => (
                    <div key={level.id} className="flex items-center">
                      <div className="flex flex-col items-center mr-3">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: level.color }}
                        />
                        {idx < scale.levels.length - 1 && (
                          <div className="w-0.5 h-6 bg-gray-200" />
                        )}
                      </div>
                      <div className="flex-1 p-3 rounded-lg border border-gray-100 hover:border-gray-300 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span 
                              className="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold"
                              style={{ backgroundColor: level.color }}
                            >
                              {level.order}
                            </span>
                            <span className="font-medium text-gray-900">{level.name}</span>
                          </div>
                          <span className="text-xs text-gray-500">{level.permissions.length} permissions</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Approval Ladders */}
      {activeTab === 'ladders' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Approval Ladders</h2>
            <p className="text-sm text-gray-500">Configure who can approve what based on risk level</p>
          </div>
          
          <div className="divide-y divide-gray-100">
            {ladders.map((ladder) => (
              <div key={ladder.id} className="p-6 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div className="flex items-center space-x-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    ladder.risk === 'critical' ? 'bg-red-100 text-red-600' :
                    ladder.risk === 'high' ? 'bg-orange-100 text-orange-600' :
                    ladder.risk === 'medium' ? 'bg-yellow-100 text-yellow-600' :
                    'bg-green-100 text-green-600'
                  }`}>
                    <span className="text-sm font-bold">{ladder.risk[0].toUpperCase()}</span>
                  </div>
                  
                  <div>
                    <h3 className="font-medium text-gray-900">{ladder.name}</h3>
                    <p className="text-sm text-gray-500">
                      Min level: {ladder.min_level} • 
                      {ladder.auto_approve ? 'Auto-approve' : 'Manual approval'}
                      {ladder.second_pair && ' • Second pair required'}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button className="p-2 text-gray-400 hover:text-gray-600">
                    <Settings className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Assignments */}
      {activeTab === 'assignments' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">User Assignments</h3>
          <p className="text-gray-500">Assign users to hierarchy levels</p>
          <button className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
            Assign User
          </button>
        </div>
      )}

      {/* Create Scale Modal */}
      {showCreateScale && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Hierarchy Scale</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input type="text" className="mt-1 w-full rounded-lg border-gray-300" placeholder="e.g., Engineering Team" />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Type</label>
                <select className="mt-1 w-full rounded-lg border-gray-300">
                  <option value="human">Human Hierarchy</option>
                  <option value="agent">Agent Hierarchy</option>
                  <option value="mixed">Mixed</option>
                </select>
              </div>
            </div>
            
            <div className="mt-6 flex justify-end space-x-3">
              <button 
                onClick={() => setShowCreateScale(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button 
                onClick={() => setShowCreateScale(false)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Create Scale
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
