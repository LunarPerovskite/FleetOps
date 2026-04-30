import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  CheckSquare, 
  Bot, 
  Shield, 
  Settings,
  Menu,
  X,
  BarChart3,
  Search,
  Lightbulb,
  Puzzle,
  GitBranch,
  FileText,
  MessageCircle,
  Users,
  ShieldCheck,
  LayoutTemplate,
  Store,
  ServerCog,
  Link2,
  Plug,
  CreditCard,
  ShieldAlert,
  KeyRound,
  Building2,
  Users2,
  Share2
} from 'lucide-react';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/analytics', icon: BarChart3, label: 'Analytics' },
  { path: '/search', icon: Search, label: 'Search' },
  { path: '/use-cases', icon: Lightbulb, label: 'Use Cases' },
  { path: '/integrations', icon: Puzzle, label: 'Integrations' },
  { path: '/workflow-templates', icon: GitBranch, label: 'Workflows' },
  { path: '/tasks', icon: CheckSquare, label: 'Tasks' },
  { path: '/agents', icon: Bot, label: 'Agents' },
  { path: '/approvals', icon: Shield, label: 'Approvals' },
  { path: '/events', icon: FileText, label: 'Events' },
  { path: '/customer-service', icon: MessageCircle, label: 'Customer Service' },
  { path: '/hierarchy', icon: Users, label: 'Hierarchy' },
  { path: '/audit', icon: ShieldCheck, label: 'Audit Log' },
  { path: '/dashboard-builder', icon: LayoutTemplate, label: 'Dashboard Builder' },
  { path: '/marketplace', icon: Store, label: 'Marketplace' },
  { path: '/agent-instances', icon: ServerCog, label: 'Agent Instances' },
  { path: '/webhooks', icon: Link2, label: 'Webhooks' },
  { path: '/providers', icon: Plug, label: 'Providers' },
  { path: '/billing', icon: CreditCard, label: 'Billing' },
  { path: '/api-keys', icon: KeyRound, label: 'API Keys' },
  { path: '/llm-usage', icon: BarChart3, label: 'LLM Usage' },
  { path: '/organizations', icon: Building2, label: 'Organizations' },
  { path: '/teams', icon: Users2, label: 'Teams' },
  { path: '/shared-agents', icon: Share2, label: 'Shared Agents' },
  { path: '/settings', icon: Settings, label: 'Settings' },
  { path: '/admin', icon: ShieldAlert, label: 'Admin' },
];

export default function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  return (
    <>
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 bg-white border-b border-gray-200 z-40">
        <div className="flex items-center justify-between px-4 h-14">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">F</span>
            </div>
            <span className="font-semibold text-gray-900">FleetOps</span>
          </div>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-2 text-gray-600 hover:text-gray-900"
          >
            {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {isOpen && (
        <>
          <div 
            className="lg:hidden fixed inset-0 bg-black/50 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="lg:hidden fixed top-14 left-0 bottom-0 w-64 bg-white border-r border-gray-200 z-50 overflow-y-auto">
            <nav className="p-4 space-y-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                const Icon = item.icon;
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </>
      )}
    </>
  );
}
