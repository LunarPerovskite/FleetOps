import { useState, useEffect } from 'react';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import { Key, Plus, Trash2, Copy, Eye, EyeOff, Calendar } from 'lucide-react';

interface APIKey {
  id: string;
  name: string;
  key: string;
  prefix: string;
  created_at: string;
  last_used?: string;
  scopes: string[];
}

const SCOPES = [
  { value: 'read:tasks', label: 'Read Tasks' },
  { value: 'write:tasks', label: 'Write Tasks' },
  { value: 'read:agents', label: 'Read Agents' },
  { value: 'write:agents', label: 'Write Agents' },
  { value: 'read:approvals', label: 'Read Approvals' },
  { value: 'write:approvals', label: 'Write Approvals' },
  { value: 'read:events', label: 'Read Events' },
  { value: 'admin', label: 'Admin Access' },
];

export default function APIKeys() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [newKey, setNewKey] = useState({
    name: '',
    scopes: ['read:tasks', 'read:agents']
  });

  useEffect(() => {
    fetchKeys();
  }, []);

  const fetchKeys = async () => {
    try {
      setLoading(true);
      // In production, fetch from API
      setKeys([
        {
          id: 'key_1',
          name: 'Production',
          key: 'fk_prod_51HYs0sJh8uPqWwXyZ123456789',
          prefix: 'fk_prod_51HY',
          created_at: '2026-04-01T10:00:00Z',
          last_used: '2026-04-22T08:30:00Z',
          scopes: ['read:tasks', 'write:tasks', 'read:agents']
        }
      ]);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    const key = {
      id: `key_${Date.now()}`,
      name: newKey.name,
      key: `fk_prod_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`,
      prefix: 'fk_prod_',
      created_at: new Date().toISOString(),
      scopes: newKey.scopes
    };
    setKeys(prev => [key, ...prev]);
    setShowForm(false);
    setNewKey({ name: '', scopes: ['read:tasks'] });
    toast.success('API key created. Copy it now - you won\'t see it again!');
  };

  const handleDelete = (id: string) => {
    if (!confirm('Delete this API key? This action cannot be undone.')) return;
    setKeys(prev => prev.filter(k => k.id !== id));
    toast.success('API key deleted');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const toggleScope = (scope: string) => {
    setNewKey(prev => ({
      ...prev,
      scopes: prev.scopes.includes(scope)
        ? prev.scopes.filter(s => s !== scope)
        : [...prev.scopes, scope]
    }));
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
        <SkeletonCard />
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchKeys} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Keys</h1>
          <p className="text-gray-500 mt-1">Manage API keys for programmatic access</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Key
        </button>
      </div>

      {/* Create Form */}
      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h3 className="font-semibold text-gray-900">Create API Key</h3>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={newKey.name}
              onChange={e => setNewKey(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Production, CI/CD, Zapier"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Scopes (Permissions)</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {SCOPES.map(scope => (
                <button
                  key={scope.value}
                  onClick={() => toggleScope(scope.value)}
                  className={`px-3 py-2 rounded-lg text-sm transition-colors text-left ${
                    newKey.scopes.includes(scope.value)
                      ? 'bg-blue-100 text-blue-700 border border-blue-300'
                      : 'bg-gray-50 text-gray-600 border border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  {scope.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={!newKey.name}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              Create API Key
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Keys List */}
      {keys.length === 0 ? (
        <EmptyState
          icon={Key}
          title="No API keys"
          description="Create API keys to authenticate your applications and integrations"
          action={{
            label: 'Create API Key',
            onClick: () => setShowForm(true)
          }}
        />
      ) : (
        <div className="space-y-4">
          {keys.map(key => (
            <div key={key.id} className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-start justify-between">
                <div className="space-y-3 flex-1">
                  <div className="flex items-center gap-2">
                    <Key className="w-5 h-5 text-blue-600" />
                    <span className="font-semibold text-gray-900">{key.name}</span>
                    <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                      {key.prefix}***
                    </span>
                  </div>

                  <div className="flex items-center gap-2 bg-gray-50 rounded-lg p-3">
                    <code className="text-sm text-gray-700 font-mono flex-1 truncate">
                      {showKey[key.id] ? key.key : `${key.key.substring(0, 20)}...`}
                    </code>
                    <button
                      onClick={() => setShowKey(prev => ({ ...prev, [key.id]: !prev[key.id] }))}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      {showKey[key.id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                    <button
                      onClick={() => copyToClipboard(key.key)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      Created {new Date(key.created_at).toLocaleDateString()}
                    </span>
                    {key.last_used && (
                      <span>
                        Last used {new Date(key.last_used).toLocaleDateString()}
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {key.scopes.map(scope => (
                      <span key={scope} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full">
                        {scope}
                      </span>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => handleDelete(key.id)}
                  className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Usage Example */}
      <div className="bg-gray-900 rounded-xl p-6">
        <h3 className="font-semibold text-gray-100 mb-3">API Usage Example</h3>
        <pre className="text-sm text-green-400 overflow-x-auto">
{`curl https://api.fleetops.io/api/v1/tasks \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"

# Response:
{
  "tasks": [
    {"id": "task_123", "title": "Review Q3 Report", "status": "completed"}
  ],
  "total": 1
}`}
        </pre>
      </div>
    </div>
  );
}
