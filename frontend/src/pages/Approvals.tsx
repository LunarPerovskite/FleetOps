import { usePendingApprovals } from '../hooks/useDashboard'
import { CheckCircle, XCircle, MessageSquare, ArrowUpCircle } from 'lucide-react'

export default function Approvals() {
  const { data: approvals, isLoading } = usePendingApprovals()

  const handleApprove = (taskId: string) => {
    // API call to approve
    console.log('Approving:', taskId)
  }

  const handleReject = (taskId: string) => {
    console.log('Rejecting:', taskId)
  }

  const handleEscalate = (taskId: string) => {
    console.log('Escalating:', taskId)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Pending Approvals</h1>
      
      {isLoading ? (
        <div className="text-center py-8">Loading...</div>
      ) : !approvals?.length ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">All caught up!</h3>
          <p className="text-gray-500">No pending approvals at the moment.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map((approval: any) => (
            <div key={approval.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      approval.risk_level === 'critical' ? 'bg-red-100 text-red-800' :
                      approval.risk_level === 'high' ? 'bg-orange-100 text-orange-800' :
                      approval.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {approval.risk_level}
                    </span>
                    <span className="text-sm text-gray-500">{approval.stage}</span>
                  </div>
                  
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {approval.task_title}
                  </h3>
                  
                  <p className="text-gray-600 mb-4">{approval.description}</p>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>Agent: {approval.agent_name}</span>
                    <span>Requested: {new Date(approval.created_at).toLocaleString()}</span>
                    <span className="text-orange-600 font-medium">
                      SLA: {approval.sla_remaining} min
                    </span>
                  </div>
                </div>
                
                <div className="flex flex-col space-y-2 ml-4">
                  <button
                    onClick={() => handleApprove(approval.task_id)}
                    className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Approve
                  </button>
                  
                  <button
                    onClick={() => handleReject(approval.task_id)}
                    className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Reject
                  </button>
                  
                  <button
                    onClick={() => handleEscalate(approval.task_id)}
                    className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <ArrowUpCircle className="w-4 h-4 mr-2" />
                    Escalate
                  </button>
                  
                  <button
                    className="flex items-center px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Request Changes
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
