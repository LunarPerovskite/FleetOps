import { useState, useEffect } from 'react';
import { webhooksAPI } from '../lib/api';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay, EmptyState } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import { Webhook, Plus, Trash2, RefreshCw, CheckCircle, XCircle, Bell } from 'lucide-react';

interface WebhookConfig {
  id: string;
  url: string;
  events: string[];
  active: boolean;
  secret?: string;
  last_status?: string;
  last_delivery?: string;
}

const EVENT_TYPES = [
  { value: 'task_created', label: 'Task Created' },
  { value: 'task_completed', label: 'Task Completed' },
  { value: 'task_approved', label: 'Task Approved' },
  { value: 'agent_created', label: 'Agent Created' },
  { value: 'approval_required', label: 'Approval Required' },
  { value: 'agent_error', label: 'Agent Error' },
  { value: '*', label: 'All Events' },
];

export default function Webhooks() {
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [newWebhook, setNewWebhook] = useState({
    url: '',
    events: ['task_created', 'task_completed'],
    secret: ''
  });

  useEffect(() => {
    fetchWebhooks();
  }, []);

  const fetchWebhooks = async () => {
    try {
      setLoading(true);
      const response = await webhooksAPI.list();
      setWebhooks(response?.webhooks || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load webhooks');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await webhooksAPI.create({
        url: newWebhook.url,
        events: newWebhook.events.join(','),
        secret: newWebhook.secret || undefined
      });
      toast.success('Webhook created');
      setShowForm(false);
      setNewWebhook({ url: '', events: ['task_created'], secret: '' });
      fetchWebhooks();
    } catch (err: any) {
      toast.error(err.message || 'Failed to create webhook');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this webhook?')) return;
    try {
      await webhooksAPI.delete(id);
      toast.success('Webhook deleted');
      fetchWebhooks();
    } catch (err: any) {
      toast.error('Failed to delete webhook');
    }
  };

  const handleTest = async (id: string) => {
    try {
      const result = await webhooksAPI.test(id);
      if (result.success) {
        toast.success('Webhook test successful');
      } else {
        toast.error('Webhook test failed');
      }
    } catch (err: any) {
      toast.error('Test failed');
    }
  };

  const toggleEvent = (event: string) => {
    setNewWebhook(prev => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter(e => e !== event)
        : [...prev.events, event]
    }));
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchWebhooks} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Webhooks</h1>
          <p className="text-gray-500 mt-1">Connect FleetOps to external tools</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Webhook
        </button>
      </div>

      {/* Create Form */}
      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h3 className="font-semibold text-gray-900">New Webhook</h3>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
            <input
              type="url"
              value={newWebhook.url}
              onChange={e => setNewWebhook(prev => ({ ...prev, url: e.target.value }))}
              placeholder="https://hooks.zapier.com/..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Events</label>
            <div className="flex flex-wrap gap-2">
              {EVENT_TYPES.map(event => (
                <button
                  key={event.value}
                  onClick={() => toggleEvent(event.value)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    newWebhook.events.includes(event.value)
                      ? 'bg-blue-100 text-blue-700 border border-blue-300'
                      : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
                  }`}
                >
                  {event.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Secret (optional, for HMAC signature)</label>
            <input
              type="text"
              value={newWebhook.secret}
              onChange={e => setNewWebhook(prev => ({ ...prev, secret: e.target.value }))}
              placeholder="whsec_..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={!newWebhook.url}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              Create Webhook
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

      {/* Webhooks List */}
      {webhooks.length === 0 ? (
        <EmptyState
          title="No webhooks configured"
          message="Add webhooks to send events to external tools like Zapier, Slack, or your own API"
          action={{
            label: 'Add Webhook',
            onClick: () => setShowForm(true)
          }}
        />
      ) : (
        <div className="space-y-4">
          {webhooks.map(webhook => (
            <div key={webhook.id} className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    {webhook.active ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-500" />
                    )}
                    <span className="font-medium text-gray-900 truncate max-w-md">{webhook.url}</span>
                  </div>
                  
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Bell className="w-4 h-4" />
                    {Array.isArray(webhook.events) ? webhook.events.join(', ') : webhook.events}
                  </div>
                  
                  {webhook.last_status && (
                    <div className="text-xs text-gray-400">
                      Last delivery: {webhook.last_status} {webhook.last_delivery && `at ${new Date(webhook.last_delivery).toLocaleString()}`}
                    </div>
                  )}
                </div>
                
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTest(webhook.id)}
                    className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                    title="Test webhook"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(webhook.id)}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                    title="Delete webhook"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Integration Guide */}
      <div className="bg-blue-50 rounded-xl p-6">
        <h3 className="font-semibold text-blue-900 mb-3">Popular Integrations</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="https://zapier.com/apps/webhook/integrations"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white rounded-lg p-4 border border-blue-200 hover:shadow-md transition-shadow"
          >
            <h4 className="font-medium text-blue-700">Zapier</h4>
            <p className="text-sm text-gray-500 mt-1">Connect 5000+ apps with no code</p>
          </a>
          
          <a
            href="https://make.com"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white rounded-lg p-4 border border-blue-200 hover:shadow-md transition-shadow"
          >
            <h4 className="font-medium text-blue-700">Make.com</h4>
            <p className="text-sm text-gray-500 mt-1">Visual automation builder</p>
          </a>
          
          <a
            href="https://n8n.io"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white rounded-lg p-4 border border-blue-200 hover:shadow-md transition-shadow"
          >
            <h4 className="font-medium text-blue-700">n8n</h4>
            <p className="text-sm text-gray-500 mt-1">Open source workflow automation</p>
          </a>
        </div>
      </div>
    </div>
  );
}
