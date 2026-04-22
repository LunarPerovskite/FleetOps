import { useState } from 'react';
import { 
  Store, 
  Search, 
  Star, 
  Download,
  ExternalLink,
  Code2,
  MessageCircle,
  BarChart3,
  Shield,
  Zap,
  CheckCircle
} from 'lucide-react';
import { toast } from '../hooks/useToast';

interface MarketplaceItem {
  id: string;
  name: string;
  description: string;
  icon: any;
  category: string;
  author: string;
  rating: number;
  downloads: number;
  price: string;
  tags: string[];
  installed: boolean;
}

const marketplaceItems: MarketplaceItem[] = [
  {
    id: 'github-advanced',
    name: 'GitHub Advanced Integration',
    description: 'Deep GitHub integration with PR automation, issue triage, and release management',
    icon: Code2,
    category: 'Development',
    author: 'FleetOps Team',
    rating: 4.8,
    downloads: 1250,
    price: 'Free',
    tags: ['GitHub', 'CI/CD', 'Automation'],
    installed: false
  },
  {
    id: 'slack-pro',
    name: 'Slack Pro Notifications',
    description: 'Advanced Slack integration with threaded approvals, custom workflows, and analytics',
    icon: MessageCircle,
    category: 'Communication',
    author: 'FleetOps Team',
    rating: 4.9,
    downloads: 890,
    price: 'Free',
    tags: ['Slack', 'Notifications', 'Workflows'],
    installed: true
  },
  {
    id: 'salesforce-connector',
    name: 'Salesforce Connector',
    description: 'Sync customer data, create leads from support tickets, track opportunities',
    icon: BarChart3,
    category: 'CRM',
    author: 'Community',
    rating: 4.5,
    downloads: 567,
    price: '$29',
    tags: ['Salesforce', 'CRM', 'Sales'],
    installed: false
  },
  {
    id: 'security-scanner',
    name: 'Security Scan Agent',
    description: 'Automated security scanning for code, infrastructure, and dependencies',
    icon: Shield,
    category: 'Security',
    author: 'FleetOps Team',
    rating: 4.7,
    downloads: 2100,
    price: 'Free',
    tags: ['Security', 'Scanning', 'Compliance'],
    installed: false
  },
  {
    id: 'performance-monitor',
    name: 'Performance Monitor',
    description: 'Real-time performance monitoring with alerts, dashboards, and anomaly detection',
    icon: Zap,
    category: 'Monitoring',
    author: 'Community',
    rating: 4.6,
    downloads: 743,
    price: '$49',
    tags: ['Monitoring', 'Performance', 'Alerts'],
    installed: false
  },
  {
    id: 'compliance-suite',
    name: 'Compliance Suite',
    description: 'SOC 2, HIPAA, and GDPR compliance tools with automated reporting',
    icon: CheckCircle,
    category: 'Compliance',
    author: 'FleetOps Team',
    rating: 4.9,
    downloads: 432,
    price: '$99',
    tags: ['Compliance', 'SOC2', 'GDPR'],
    installed: false
  }
];

const categories = ['All', 'Development', 'Communication', 'CRM', 'Security', 'Monitoring', 'Compliance'];

export default function Marketplace() {
  const [items, setItems] = useState(marketplaceItems);
  const [filter, setFilter] = useState('All');
  const [search, setSearch] = useState('');

  const filtered = items.filter(item => {
    const matchesCategory = filter === 'All' || item.category === filter;
    const matchesSearch = search === '' || 
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.description.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const installItem = (id: string) => {
    setItems(prev => prev.map(item => 
      item.id === id ? { ...item, installed: true } : item
    ));
    toast.success('Item installed successfully');
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-3">
          <Store className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Agent Marketplace</h1>
        </div>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Extend FleetOps with premium connectors, templates, and agents. 
          Free items are open source. Premium items fund continued development.
        </p>
      </div>

      {/* Search & Filter */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search marketplace..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                filter === cat
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Items Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map(item => {
          const Icon = item.icon;
          return (
            <div key={item.id} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-blue-50 rounded-xl">
                  <Icon className="w-6 h-6 text-blue-600" />
                </div>
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                  <span className="text-sm font-medium">{item.rating}</span>
                </div>
              </div>

              <h3 className="font-semibold text-gray-900 mb-1">{item.name}</h3>
              <p className="text-sm text-gray-500 mb-2">{item.category} • {item.author}</p>
              <p className="text-gray-600 text-sm mb-4">{item.description}</p>

              <div className="flex flex-wrap gap-2 mb-4">
                {item.tags.map(tag => (
                  <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                    {tag}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <Download className="w-4 h-4" />
                    {item.downloads.toLocaleString()}
                  </span>
                  <span className={`font-medium ${
                    item.price === 'Free' ? 'text-green-600' : 'text-blue-600'
                  }`}>
                    {item.price}
                  </span>
                </div>
                
                {item.installed ? (
                  <span className="flex items-center gap-1 text-green-600 text-sm font-medium">
                    <CheckCircle className="w-4 h-4" />
                    Installed
                  </span>
                ) : (
                  <button
                    onClick={() => installItem(item.id)}
                    className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    Install
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Submit Item CTA */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="font-semibold text-blue-900">Build for the Marketplace</h3>
            <p className="text-sm text-blue-700 mt-1">
              Create connectors, agents, or templates. Earn 70% of every sale.
            </p>
          </div>
          <a
            href="https://github.com/LunarPerovskite/FleetOps/blob/main/docs/ARCHITECTURE.md"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            Developer Docs
          </a>
        </div>
      </div>
    </div>
  );
}
