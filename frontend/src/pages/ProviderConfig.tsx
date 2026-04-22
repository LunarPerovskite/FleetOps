import { useState, useEffect } from 'react';
import { providerConfigAPI } from '../lib/api';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import { CheckCircle, AlertTriangle, Save, RefreshCw } from 'lucide-react';

interface ProviderOption {
  id: string;
  name: string;
  description: string;
  category: string;
  freeTier: boolean;
  setupTime: string;
}

const AUTH_PROVIDERS: ProviderOption[] = [
  { id: 'clerk', name: 'Clerk', description: 'Modern auth with 10k MAU free tier', category: 'auth', freeTier: true, setupTime: '5 min' },
  { id: 'auth0', name: 'Auth0', description: 'Enterprise identity platform', category: 'auth', freeTier: true, setupTime: '15 min' },
  { id: 'okta', name: 'Okta', description: 'Enterprise SSO and identity', category: 'auth', freeTier: false, setupTime: '30 min' },
  { id: 'self_hosted', name: 'Self-Hosted', description: 'Your own auth system', category: 'auth', freeTier: true, setupTime: '2 hr' },
];

const DB_PROVIDERS: ProviderOption[] = [
  { id: 'supabase', name: 'Supabase', description: 'Open source Firebase alternative', category: 'database', freeTier: true, setupTime: '5 min' },
  { id: 'neon', name: 'Neon', description: 'Serverless PostgreSQL', category: 'database', freeTier: true, setupTime: '5 min' },
  { id: 'aws_rds', name: 'AWS RDS', description: 'Managed relational databases', category: 'database', freeTier: false, setupTime: '20 min' },
  { id: 'postgres', name: 'PostgreSQL', description: 'Self-hosted PostgreSQL', category: 'database', freeTier: true, setupTime: '30 min' },
];

const HOSTING_PROVIDERS: ProviderOption[] = [
  { id: 'vercel', name: 'Vercel', description: 'Frontend cloud platform', category: 'hosting', freeTier: true, setupTime: '5 min' },
  { id: 'railway', name: 'Railway', description: 'Infrastructure platform', category: 'hosting', freeTier: true, setupTime: '10 min' },
  { id: 'aws', name: 'AWS', description: 'Cloud computing services', category: 'hosting', freeTier: false, setupTime: '1 hr' },
];

const SECRETS_PROVIDERS: ProviderOption[] = [
  { id: 'env', name: 'Environment Variables', description: 'Simple .env files', category: 'secrets', freeTier: true, setupTime: '1 min' },
  { id: 'doppler', name: 'Doppler', description: 'Secret management platform', category: 'secrets', freeTier: true, setupTime: '10 min' },
  { id: 'vault', name: 'HashiCorp Vault', description: 'Enterprise secrets management', category: 'secrets', freeTier: true, setupTime: '1 hr' },
];

const MONITORING_PROVIDERS: ProviderOption[] = [
  { id: 'sentry', name: 'Sentry', description: 'Error tracking and performance', category: 'monitoring', freeTier: true, setupTime: '5 min' },
  { id: 'datadog', name: 'Datadog', description: 'Cloud monitoring and security', category: 'monitoring', freeTier: false, setupTime: '20 min' },
  { id: 'cloudwatch', name: 'CloudWatch', description: 'AWS monitoring', category: 'monitoring', freeTier: true, setupTime: '15 min' },
];

export default function ProviderConfig() {
  const [config, setConfig] = useState({
    auth_provider: 'clerk',
    database: 'supabase',
    hosting: 'vercel',
    secrets: 'env',
    monitoring: 'sentry',
  });
  const [health, setHealth] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await providerConfigAPI.get();
      if (response?.config) {
        setConfig(response.config);
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const checkHealth = async () => {
    try {
      const response = await providerConfigAPI.health();
      setHealth(response?.statuses || {});
      toast.success('Health check complete');
    } catch (err: any) {
      toast.error('Health check failed');
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await providerConfigAPI.update(config);
      toast.success('Configuration saved');
      checkHealth();
    } catch (err: any) {
      toast.error(err.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const ProviderCard = ({ provider, selected, onClick }: { provider: ProviderOption; selected: boolean; onClick: () => void }) => (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
        selected
          ? 'border-blue-500 bg-blue-50 shadow-md'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">{provider.name}</h3>
          <p className="text-sm text-gray-500 mt-1">{provider.description}</p>
        </div>
        {provider.freeTier && (
          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
            Free Tier
          </span>
        )}
      </div>
      <div className="flex items-center gap-3 mt-3 text-xs text-gray-500">
        <span>Setup: {provider.setupTime}</span>
        {health[provider.id] === 'ok' ? (
          <span className="flex items-center gap-1 text-green-600">
            <CheckCircle className="w-3 h-3" /> Connected
          </span>
        ) : health[provider.id] === 'error' ? (
          <span className="flex items-center gap-1 text-red-600">
            <AlertTriangle className="w-3 h-3" /> Error
          </span>
        ) : null}
      </div>
      {selected && (
        <div className="mt-3 pt-3 border-t border-blue-200">
          <p className="text-xs text-blue-700">
            Selected as your {provider.category} provider
          </p>
        </div>
      )}
    </button>
  );

  const ProviderSection = ({ title, providers, configKey }: { title: string; providers: ProviderOption[]; configKey: keyof typeof config }) => (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {providers.map((provider) => (
          <ProviderCard
            key={provider.id}
            provider={provider}
            selected={config[configKey] === provider.id}
            onClick={() => setConfig(prev => ({ ...prev, [configKey]: provider.id }))}
          />
        ))}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchConfig} />;
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Provider Configuration</h1>
          <p className="text-gray-500 mt-1">Choose your infrastructure stack</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={checkHealth}
            className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Check Health
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Quick Start Presets */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h2 className="font-semibold text-blue-900 mb-3">Quick Start Presets</h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setConfig({ auth_provider: 'clerk', database: 'supabase', hosting: 'vercel', secrets: 'env', monitoring: 'sentry' })}
            className="px-4 py-2 bg-white border border-blue-300 rounded-lg text-sm font-medium text-blue-700 hover:bg-blue-50 transition-colors"
          >
            Easiest (Clerk + Vercel + Supabase)
          </button>
          <button
            onClick={() => setConfig({ auth_provider: 'auth0', database: 'neon', hosting: 'railway', secrets: 'doppler', monitoring: 'sentry' })}
            className="px-4 py-2 bg-white border border-blue-300 rounded-lg text-sm font-medium text-blue-700 hover:bg-blue-50 transition-colors"
          >
            Balanced (Auth0 + Railway + Neon)
          </button>
          <button
            onClick={() => setConfig({ auth_provider: 'okta', database: 'aws_rds', hosting: 'aws', secrets: 'vault', monitoring: 'datadog' })}
            className="px-4 py-2 bg-white border border-blue-300 rounded-lg text-sm font-medium text-blue-700 hover:bg-blue-50 transition-colors"
          >
            Enterprise (Okta + AWS)
          </button>
        </div>
      </div>

      <ProviderSection title="Authentication" providers={AUTH_PROVIDERS} configKey="auth_provider" />
      <ProviderSection title="Database" providers={DB_PROVIDERS} configKey="database" />
      <ProviderSection title="Hosting" providers={HOSTING_PROVIDERS} configKey="hosting" />
      <ProviderSection title="Secrets" providers={SECRETS_PROVIDERS} configKey="secrets" />
      <ProviderSection title="Monitoring" providers={MONITORING_PROVIDERS} configKey="monitoring" />

      {/* Summary */}
      <div className="bg-gray-50 rounded-xl p-6">
        <h3 className="font-semibold text-gray-900 mb-3">Your Stack</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(config).map(([key, value]) => (
            <div key={key} className="bg-white rounded-lg p-3 border border-gray-200">
              <p className="text-xs text-gray-500 capitalize">{key.replace('_', ' ')}</p>
              <p className="font-medium text-gray-900 capitalize">{value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
