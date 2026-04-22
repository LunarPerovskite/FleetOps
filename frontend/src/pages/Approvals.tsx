import { useState, useEffect } from 'react';
import { approvalsAPI } from '../lib/api';
import { Loading, SkeletonTable } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import { Shield, CheckCircle, XCircle, AlertTriangle, Clock } from 'lucide-react';

export default function Approvals() {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [processing, setProcessing] = useState<string | null>(null);

  const fetchApprovals = async () => {
    try {
      setLoading(true);
      const response = await approvalsAPI.list(
        statusFilter !== 'all' ? { status: statusFilter } : undefined
      );
      setApprovals(response?.approvals || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load approvals');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, [statusFilter]);

  const handleDecision = async (id: string, decision: string, comments?: string) => {
    try {
      setProcessing(id);
      await approvalsAPI.decide(id, { decision, comments });
      toast.success(`Approval ${decision}d`);
      fetchApprovals();
    } catch (err: any) {
      toast.error(err.message || `Failed to ${decision}`);
    } finally {
      setProcessing(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'rejected': return <XCircle className="w-5 h-5 text-red-500" />;
      case 'escalated': return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      default: return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-50 text-green-700';
      case 'rejected': return 'bg-red-50 text-red-700';
      case 'escalated': return 'bg-orange-50 text-orange-700';
      default: return 'bg-yellow-50 text-yellow-700';
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
        <SkeletonTable rows={5} />
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchApprovals} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Approvals</h1>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="escalated">Escalated</option>
        </select>
      </div>

      {/* Pending Counter */}
      {statusFilter === 'pending' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <div>
              <p className="font-medium text-yellow-900">
                {approvals.length} approval{approvals.length !== 1 ? 's' : ''} need attention
              </p>
              <p className="text-sm text-yellow-700">
                Review and take action on pending requests
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Approvals List */}
      {approvals && approvals.length > 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Task</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3 hidden md:table-cell">Stage</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Status</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3 hidden sm:table-cell">SLA</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {approvals.map((approval) => (
                  <tr key={approval.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(approval.status)}
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {approval.task_title || 'Untitled Task'}
                          </p>
                          <p className="text-xs text-gray-500">
                            ID: {approval.task_id?.slice(0, 8)}...
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 hidden md:table-cell">
                      <span className="text-sm text-gray-600 capitalize">
                        {approval.stage}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(approval.status)}`}>
                        {approval.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 hidden sm:table-cell">
                      {approval.sla_deadline ? (
                        <div className="flex items-center gap-1 text-sm text-gray-500">
                          <Clock className="w-4 h-4" />
                          {new Date(approval.sla_deadline).toLocaleDateString()}
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">No SLA</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {approval.status === 'pending' ? (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleDecision(approval.id, 'approve')}
                            disabled={processing === approval.id}
                            className="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
                          >
                            {processing === approval.id ? '...' : 'Approve'}
                          </button>
                          <button
                            onClick={() => handleDecision(approval.id, 'reject')}
                            disabled={processing === approval.id}
                            className="px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50 transition-colors"
                          >
                            {processing === approval.id ? '...' : 'Reject'}
                          </button>
                          <button
                            onClick={() => handleDecision(approval.id, 'escalate')}
                            disabled={processing === approval.id}
                            className="px-3 py-1.5 bg-orange-600 text-white text-sm rounded hover:bg-orange-700 disabled:opacity-50 transition-colors"
                          >
                            Escalate
                          </button>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">
                          {approval.decision}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <EmptyState
          title="No approvals"
          message={
            statusFilter === 'pending'
              ? "No pending approvals - you're all caught up!"
              : "No approvals in this status."
          }
        />
      )}
    </div>
  );
}
