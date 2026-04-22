import { useState, useEffect } from 'react';
import { billingAPI } from '../lib/api';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { CheckSquare, Bot, Users, Clock, Database, Server } from 'lucide-react';

export default function Billing() {
  const [usage, setUsage] = useState({
    tasks_this_month: 0,
    tasks_total: 0,
    agents_active: 0,
    agents_total: 0,
    team_members: 1,
    api_calls: 0,
    storage_gb: 0.5
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBillingData();
  }, []);

  const fetchBillingData = async () => {
    try {
      setLoading(true);
      const response = await billingAPI.usage();
      setUsage(response || {});
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load usage data');
    } finally {
      setLoading(false);
    }
  };

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
    return <ErrorDisplay message={error} onRetry={fetchBillingData} />;
  }

  const StatCard = ({ icon: Icon, label, value, subtext }: any) => (
    <div className="bg-white rounded-xl p-6 border border-gray-200">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-blue-50 rounded-lg">
          <Icon className="w-5 h-5 text-blue-600" />
        </div>
        <span className="text-sm text-gray-600">{label}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      {subtext && <p className="text-xs text-gray-500 mt-1">{subtext}</p>}
    </div>
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Usage Overview</h1>
        <p className="text-gray-500 mt-1">Track your FleetOps usage</p>
      </div>

      {/* Self-Hosted Notice */}
      <div className="bg-green-50 border border-green-200 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <Server className="w-5 h-5 text-green-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-green-900">Self-Hosted — 100% Free</h3>
            <p className="text-sm text-green-700 mt-1">
              You are running FleetOps on your own infrastructure. <strong>All features are unlimited and free.</strong>
              No billing, no limits, no restrictions.
            </p>
          </div>
        </div>
      </div>

      {/* Usage Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          icon={CheckSquare}
          label="Tasks This Month"
          value={usage.tasks_this_month?.toLocaleString() || '0'}
          subtext={`${usage.tasks_total || 0} total`}
        />
        <StatCard
          icon={Bot}
          label="Active Agents"
          value={usage.agents_active?.toString() || '0'}
          subtext={`${usage.agents_total || 0} total configured`}
        />
        <StatCard
          icon={Users}
          label="Team Members"
          value={usage.team_members?.toString() || '1'}
          subtext="Unlimited on self-hosted"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          icon={Clock}
          label="API Calls"
          value={usage.api_calls?.toLocaleString() || '0'}
          subtext="This month"
        />
        <StatCard
          icon={Database}
          label="Storage Used"
          value={`${usage.storage_gb?.toFixed(1) || '0.5'} GB`}
          subtext="Database + files"
        />
      </div>

      {/* Server Info */}
      <div className="bg-gray-50 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Server Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex justify-between py-2 border-b border-gray-200">
            <span className="text-gray-600">Deployment Type</span>
            <span className="font-medium text-gray-900">Self-Hosted</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-200">
            <span className="text-gray-600">License</span>
            <span className="font-medium text-gray-900">MIT (Open Source)</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-200">
            <span className="text-gray-600">Version</span>
            <span className="font-medium text-gray-900">v0.1.0-beta</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-200">
            <span className="text-gray-600">Uptime</span>
            <span className="font-medium text-gray-900">Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
