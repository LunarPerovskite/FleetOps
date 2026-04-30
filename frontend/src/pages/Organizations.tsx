import { useState, useEffect } from 'react';
import { orgsAPI } from '../lib/api';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import { useForm } from '../hooks/useForm';
import { toast } from '../hooks/useToast';
import { 
  Building2, 
  Plus, 
  Users, 
  DollarSign,
  Shield,
  Trash2,
  Edit2,
  Check,
  X
} from 'lucide-react';

interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  plan: string;
  member_count: number;
  monthly_budget: number;
  current_usage: number;
  created_at: string;
  is_active: boolean;
}

export default function Organizations() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const fetchOrgs = async () => {
    try {
      setLoading(true);
      const response = await orgsAPI.list();
      setOrgs(response?.organizations || response || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load organizations');
      toast.error('Failed to load organizations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgs();
  }, []);

  const handleCreate = async (values: any) => {
    try {
      await orgsAPI.create(values);
      toast.success('Organization created');
      setShowCreate(false);
      fetchOrgs();
    } catch (err: any) {
      toast.error(err.message || 'Failed to create organization');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure? This cannot be undone.')) return;
    try {
      await orgsAPI.delete?.(id) || fetch(`/api/v1/orgs/${id}`, { method: 'DELETE' });
      toast.success('Organization deleted');
      fetchOrgs();
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete');
    }
  };

  const { values, errors, handleChange, handleSubmit } = useForm(
    { name: '', slug: '', description: '', monthly_budget: 1000 },
    {
      name: { required: true, minLength: 1, maxLength: 100 },
      slug: { required: true, minLength: 1, maxLength: 50 },
    },
    handleCreate
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between">
          <SkeletonCard />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map(i => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={fetchOrgs} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Organizations</h1>
          <p className="text-gray-500 mt-1">Manage multi-tenant organizations</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Organization
        </button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Create Organization</h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                name="name"
                value={values.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Acme Corp"
              />
              {errors.name && <span className="text-red-500 text-sm">{errors.name}</span>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Slug</label>
              <input
                type="text"
                name="slug"
                value={values.slug}
                onChange={(e) => handleChange('slug', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="acme-corp"
              />
              {errors.slug && <span className="text-red-500 text-sm">{errors.slug}</span>}
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                name="description"
                value={values.description}
                onChange={(e) => handleChange('description', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                rows={2}
                placeholder="Organization description..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Budget ($)</label>
              <input
                type="number"
                name="monthly_budget"
                value={values.monthly_budget}
                onChange={(e) => handleChange('monthly_budget', e.target.value)}
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

      {/* Organizations Grid */}
      {orgs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {orgs.map((org) => (
            <div key={org.id} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{org.name}</h3>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span>@{org.slug}</span>
                      <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">{org.plan}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => setEditingId(editingId === org.id ? null : org.id)}
                    className="p-2 text-gray-400 hover:text-gray-600"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => handleDelete(org.id)}
                    className="p-2 text-red-400 hover:text-red-600"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {org.description && (
                <p className="text-sm text-gray-600 mt-3">{org.description}</p>
              )}

              <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-100">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-600">{org.member_count || 0} members</span>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-600">
                    ${(org.monthly_budget || 0).toLocaleString()}/mo
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-gray-400" />
                  <span className={`text-sm ${org.is_active ? 'text-green-600' : 'text-gray-400'}`}>
                    {org.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>

              {/* Budget Bar */}
              <div className="mt-4">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Budget Usage</span>
                  <span className="font-medium text-gray-900">
                    {((org.current_usage / org.monthly_budget) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all ${
                      (org.current_usage / org.monthly_budget) > 0.9 ? 'bg-red-500' : 'bg-indigo-500'
                    }`}
                    style={{ width: `${Math.min((org.current_usage / org.monthly_budget) * 100, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>${org.current_usage?.toFixed(2) || '0.00'}</span>
                  <span>${org.monthly_budget?.toLocaleString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState 
          message="No organizations yet" 
          action={{ label: 'Create Organization', onClick: () => setShowCreate(true) }}
        />
      )}
    </div>
  );
}
