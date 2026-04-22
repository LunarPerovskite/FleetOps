import { useState, useEffect } from 'react';
import { billingAPI } from '../lib/api';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import { CreditCard, TrendingUp, Users, Bot, CheckSquare, DollarSign, Info } from 'lucide-react';

export default function Billing() {
  const [usage, setUsage] = useState({
    tasks_this_month: 0,
    agents_active: 0,
    team_members: 0,
    api_calls: 0,
    storage_gb: 0,
    estimated_cost: 0
  });
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBillingData();
  }, []);

  const fetchBillingData = async () => {
    try {
      setLoading(true);
      const [usageRes, historyRes] = await Promise.all([
        billingAPI.usage(),
        billingAPI.history()
      ]);
      setUsage(usageRes || {});
      setHistory(historyRes?.invoices || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load billing data');
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

  const StatCard = ({ icon: Icon, label, value, subtext, color = "blue" }: any) => (
    <div className={`bg-${color}-50 rounded-xl p-6 border border-${color}-200`}>
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-2 bg-${color}-100 rounded-lg`}>
          <Icon className={`w-5 h-5 text-${color}-600`} />
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
        <h1 className="text-2xl font-bold text-gray-900">Billing & Usage</h1>
        <p className="text-gray-500 mt-1">Track your FleetOps usage and costs</p>
      </div>

      {/* Self-Hosted Notice */}
      <div className="bg-green-50 border border-green-200 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-green-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-green-900">Self-Hosted = FREE</h3>
            <p className="text-sm text-green-700 mt-1">
              You are running FleetOps on your own infrastructure. <strong>All features are unlimited and free.</strong>
              The cost estimates below show what you would pay if using FleetOps Cloud.
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
          subtext="Unlimited on self-hosted"
        />
        <StatCard
          icon={Bot}
          label="Active Agents"
          value={usage.agents_active?.toString() || '0'}
          subtext="Unlimited on self-hosted"
        />
        <StatCard
          icon={Users}
          label="Team Members"
          value={usage.team_members?.toString() || '0'}
          subtext="Unlimited on self-hosted"
        />
      </div>

      {/* Cost Comparison */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost Comparison</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Plan</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Your Usage</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Cloud Cost</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Self-Hosted</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <tr>
                <td className="py-4 px-4">
                  <div className="font-medium text-gray-900">Starter</div>
                  <div className="text-sm text-gray-500">Up to 5 team members</div>
                </td>
                <td className="py-4 px-4 text-gray-700">{usage.team_members} members</td>
                <td className="py-4 px-4 text-gray-700">$29/month</td>
                <td className="py-4 px-4">
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-sm rounded-full font-medium">$0 (Free)</span>
                </td>
              </tr>
              <tr>
                <td className="py-4 px-4">
                  <div className="font-medium text-gray-900">Pro</div>
                  <div className="text-sm text-gray-500">Up to 25 team members</div>
                </td>
                <td className="py-4 px-4 text-gray-700">{usage.team_members} members</td>
                <td className="py-4 px-4 text-gray-700">$59/month</td>
                <td className="py-4 px-4">
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-sm rounded-full font-medium">$0 (Free)</span>
                </td>
              </tr>
              <tr>
                <td className="py-4 px-4">
                  <div className="font-medium text-gray-900">Business</div>
                  <div className="text-sm text-gray-500">Unlimited everything</div>
                </td>
                <td className="py-4 px-4 text-gray-700">{usage.team_members} members</td>
                <td className="py-4 px-4 text-gray-700">$99/month</td>
                <td className="py-4 px-4">
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-sm rounded-full font-medium">$0 (Free)</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Cloud Benefits */}
      <div className="bg-blue-50 rounded-xl p-6">
        <h3 className="font-semibold text-blue-900 mb-3">Why Upgrade to Cloud?</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4">
            <div className="font-medium text-gray-900 mb-1">Zero Maintenance</div>
            <p className="text-sm text-gray-500">We handle servers, updates, and backups</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <div className="font-medium text-gray-900 mb-1">99.9% Uptime</div>
            <p className="text-sm text-gray-500">SLA-backed reliability guarantee</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <div className="font-medium text-gray-900 mb-1">Priority Support</div>
            <p className="text-sm text-gray-500">Get help when you need it</p>
          </div>
        </div>
      </div>
    </div>
  );
}
