import { useState } from 'react';
import { useTaskList, useCreateTask } from '../hooks/useTasks';
import { Loading, SkeletonTable } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import { useForm } from '../hooks/useForm';
import { toast } from '../hooks/useToast';
import { Plus, Search, Filter, ChevronDown } from 'lucide-react';

const validationSchema = {
  title: { required: true, minLength: 3, maxLength: 200 },
  description: { required: false, maxLength: 2000 },
  agent_id: { required: true },
  risk_level: { required: true },
};

export default function Tasks() {
  const [showCreate, setShowCreate] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  
  const { data: tasks, isLoading, error, refresh } = useTaskList(
    statusFilter !== 'all' ? { status: statusFilter } : undefined
  );
  
  const { create, isLoading: creating } = useCreateTask();

  const form = useForm(
    { title: '', description: '', agent_id: '', risk_level: 'low' },
    validationSchema,
    async (values) => {
      await create(values);
      toast.success('Task created successfully');
      setShowCreate(false);
      refresh();
    }
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
        <SkeletonTable rows={5} />
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={refresh} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Task
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search tasks..."
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Status</option>
          <option value="created">Created</option>
          <option value="planning">Planning</option>
          <option value="executing">Executing</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      {/* Create Task Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Create New Task</h2>
              
              <form onSubmit={form.handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                  <input
                    {...form.getFieldProps('title')}
                    type="text"
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Task title"
                  />
                  {form.errors.title && form.touched.title && (
                    <p className="text-sm text-red-500 mt-1">{form.errors.title}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    {...form.getFieldProps('description')}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Task description"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Agent *</label>
                  <select
                    {...form.getFieldProps('agent_id')}
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select an agent</option>
                    <option value="agent_1">Claude Code Agent</option>
                    <option value="agent_2">GitHub Copilot Agent</option>
                    <option value="agent_3">OpenAI Codex Agent</option>
                  </select>
                  {form.errors.agent_id && form.touched.agent_id && (
                    <p className="text-sm text-red-500 mt-1">{form.errors.agent_id}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Risk Level *</label>
                  <select
                    {...form.getFieldProps('risk_level')}
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">Low - Auto-approve</option>
                    <option value="medium">Medium - Operator review</option>
                    <option value="high">High - Director approval</option>
                    <option value="critical">Critical - Executive approval</option>
                  </select>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreate(false)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-900"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={form.isSubmitting || creating}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {form.isSubmitting || creating ? 'Creating...' : 'Create Task'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Tasks List */}
      {tasks && tasks.length > 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Task</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Status</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Risk</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Agent</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {tasks.map((task) => (
                <tr key={task.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <p className="text-sm font-medium text-gray-900">{task.title}</p>
                    <p className="text-xs text-gray-500 truncate max-w-xs">{task.description}</p>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      task.status === 'completed' ? 'bg-green-100 text-green-800' :
                      task.status === 'executing' ? 'bg-blue-100 text-blue-800' :
                      task.status === 'planning' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {task.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs ${
                      task.risk_level === 'low' ? 'bg-green-50 text-green-700' :
                      task.risk_level === 'medium' ? 'bg-yellow-50 text-yellow-700' :
                      task.risk_level === 'high' ? 'bg-orange-50 text-orange-700' :
                      'bg-red-50 text-red-700'
                    }`}>
                      {task.risk_level}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{task.agent_id}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(task.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          title="No tasks yet"
          message="Create your first task to get started."
          action={{ label: 'Create Task', onClick: () => setShowCreate(true) }}
        />
      )}
    </div>
  );
}
