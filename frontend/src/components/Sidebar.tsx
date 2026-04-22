import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  CheckSquare, 
  Bot, 
  Shield, 
  FileText, 
  Settings,
  MessageCircle,
  Users,
  ShieldCheck,
  LayoutTemplate,
  Plug,
  Zap,
  Link2,
  CreditCard,
  ShieldAlert,
  KeyRound,
  Lightbulb,
  Puzzle
} from 'lucide-react'

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/use-cases', icon: Lightbulb, label: 'Use Cases' },
  { path: '/integrations', icon: Puzzle, label: 'Integrations' },
  { path: '/tasks', icon: CheckSquare, label: 'Tasks' },
  { path: '/agents', icon: Bot, label: 'Agents' },
  { path: '/approvals', icon: Shield, label: 'Approvals' },
  { path: '/events', icon: FileText, label: 'Events' },
  { path: '/customer-service', icon: MessageCircle, label: 'Customer Service' },
  { path: '/hierarchy', icon: Users, label: 'Hierarchy' },
  { path: '/audit', icon: ShieldCheck, label: 'Audit Log' },
  { path: '/dashboard-builder', icon: LayoutTemplate, label: 'Dashboard Builder' },
  { path: '/webhooks', icon: Link2, label: 'Webhooks' },
  { path: '/providers', icon: Plug, label: 'Providers' },
  { path: '/billing', icon: CreditCard, label: 'Billing' },
  { path: '/api-keys', icon: KeyRound, label: 'API Keys' },
  { path: '/settings', icon: Settings, label: 'Settings' },
  { path: '/admin', icon: ShieldAlert, label: 'Admin' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-indigo-600">FleetOps</h1>
        <p className="text-sm text-gray-500 mt-1">Governed Human-Agent Work</p>
      </div>
      <nav className="flex-1 px-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-indigo-50 text-indigo-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
