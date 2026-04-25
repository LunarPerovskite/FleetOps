import { useState } from 'react';
import { useToast } from '../hooks/useToast';
import { 
  Plug, 
  ExternalLink, 
  CheckCircle, 
  Code2, 
  Terminal,
  Bot,
  Cpu,
  Sparkles,
  Zap,
  ArrowRight,
  Copy,
  Check
} from 'lucide-react';

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: any;
  category: string;
  status: 'available' | 'beta' | 'coming_soon';
  setupTime: string;
  features: string[];
  setupSteps: string[];
  configExample: string;
}

const integrations: Integration[] = [
  {
    id: 'claude-code',
    name: 'Claude Code',
    description: 'Anthropic\'s coding assistant with agentic capabilities',
    icon: Sparkles,
    category: 'Coding Agent',
    status: 'available',
    setupTime: '5 min',
    features: [
      'Natural language code editing',
      'Git commit and PR creation',
      'Test running and debugging',
      'Multi-file refactoring',
      'FleetOps approval gates'
    ],
    setupSteps: [
      'Install Claude Code: npm install -g @anthropic-ai/claude-code',
      'Configure API key in FleetOps Providers',
      'Set approval workflow for code changes',
      'Start using: claude "your task"'
    ],
    configExample: `{
  "agent": {
    "name": "Claude Code",
    "provider": "anthropic",
    "model": "claude-3-5-sonnet",
    "approval_required": true,
    "auto_approve_risk": "low"
  }
}`
  },
  {
    id: 'github-copilot',
    name: 'GitHub Copilot',
    description: 'AI pair programmer with IDE integration',
    icon: Code2,
    category: 'IDE Integration',
    status: 'available',
    setupTime: '3 min',
    features: [
      'IDE inline suggestions',
      'Copilot Chat for Q&A',
      'Code explanation and docs',
      'Test generation',
      'FleetOps review workflow'
    ],
    setupSteps: [
      'Install Copilot extension in VS Code/JetBrains',
      'Connect GitHub account',
      'Enable in FleetOps Agent settings',
      'All Copilot actions logged in Audit Log'
    ],
    configExample: `{
  "agent": {
    "name": "GitHub Copilot",
    "provider": "github",
    "type": "ide_integration",
    "track_all_suggestions": true
  }
}`
  },
  {
    id: 'cursor',
    name: 'Cursor',
    description: 'AI-native code editor with context awareness',
    icon: Terminal,
    category: 'AI Editor',
    status: 'available',
    setupTime: '5 min',
    features: [
      'AI-powered code editing',
      'Context-aware suggestions',
      'Terminal integration',
      'Composer for multi-file edits',
      'FleetOps approval for large changes'
    ],
    setupSteps: [
      'Download Cursor from cursor.com',
      'Enable FleetOps plugin in settings',
      'Configure approval thresholds',
      'Track all AI edits in FleetOps'
    ],
    configExample: `{
  "agent": {
    "name": "Cursor",
    "provider": "cursor",
    "type": "ai_editor",
    "approval_threshold_lines": 50
  }
}`
  },
  {
    id: 'codex',
    name: 'OpenAI Codex',
    description: 'OpenAI\'s coding agent for complex tasks',
    icon: Bot,
    category: 'Coding Agent',
    status: 'beta',
    setupTime: '10 min',
    features: [
      'Complex multi-step tasks',
      'Environment setup automation',
      'File system operations',
      'Integration with testing frameworks',
      'FleetOps human-in-the-loop'
    ],
    setupSteps: [
      'Get OpenAI API key with Codex access',
      'Configure in FleetOps Providers',
      'Set up sandbox environment',
      'Define approval workflows per environment'
    ],
    configExample: `{
  "agent": {
    "name": "Codex",
    "provider": "openai",
    "model": "codex-latest",
    "sandbox": true,
    "approval_required": true
  }
}`
  },
  {
    id: 'devin',
    name: 'Devin',
    description: 'Autonomous AI software engineer from Cognition',
    icon: Cpu,
    category: 'Autonomous Agent',
    status: 'beta',
    setupTime: '15 min',
    features: [
      'End-to-end software development',
      'Autonomous planning and execution',
      'Browser and terminal access',
      'Self-correction capabilities',
      'FleetOps oversight and approval'
    ],
    setupSteps: [
      'Request Devin access from Cognition',
      'Configure Devin integration in FleetOps',
      'Set up project workspace',
      'Define milestones requiring approval'
    ],
    configExample: `{
  "agent": {
    "name": "Devin",
    "provider": "cognition",
    "type": "autonomous",
    "milestone_approval": true,
    "daily_report": true
  }
}`
  },
  {
    id: 'v0',
    name: 'v0.dev',
    description: 'AI web development assistant from Vercel',
    icon: Zap,
    category: 'Web Development',
    status: 'available',
    setupTime: '5 min',
    features: [
      'Generate React components',
      'Style with Tailwind CSS',
      'Export to Next.js projects',
      'Iterate on designs',
      'FleetOps design approval'
    ],
    setupSteps: [
      'Use v0.dev to generate components',
      'Connect v0 to your FleetOps project',
      'Set design review workflow',
      'Deploy approved components'
    ],
    configExample: `{
  "agent": {
    "name": "v0",
    "provider": "vercel",
    "type": "design",
    "framework": "nextjs",
    "approval_required": true
  }
}`
  }
];

export default function Integrations() {
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [copied, setCopied] = useState(false);
  const [filter, setFilter] = useState('all');

  const categories = ['all', ...new Set(integrations.map(i => i.category))];

  const filteredIntegrations = filter === 'all' 
    ? integrations 
    : integrations.filter(i => i.category === filter);

  const copyConfig = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold text-gray-900">Agent Integrations</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Connect any AI coding agent to FleetOps. Every suggestion, edit, and action goes through your approval workflow.
        </p>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 justify-center">
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
            {cat === 'all' ? 'All Integrations' : cat}
          </button>
        ))}
      </div>

      {/* Integration Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredIntegrations.map(integration => {
          const Icon = integration.icon;
          return (
            <div
              key={integration.id}
              className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => setSelectedIntegration(integration)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-blue-50 rounded-xl">
                  <Icon className="w-6 h-6 text-blue-600" />
                </div>
                <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                  integration.status === 'available' 
                    ? 'bg-green-100 text-green-700'
                    : integration.status === 'beta'
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {integration.status === 'available' ? 'Available' : integration.status === 'beta' ? 'Beta' : 'Coming Soon'}
                </span>
              </div>

              <h3 className="text-lg font-semibold text-gray-900 mb-1">{integration.name}</h3>
              <p className="text-sm text-gray-500 mb-3">{integration.category}</p>
              <p className="text-gray-600 text-sm mb-4">{integration.description}</p>

              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Setup: {integration.setupTime}</span>
                <span className="flex items-center gap-1 text-sm text-blue-600 font-medium">
                  Configure
                  <ArrowRight className="w-4 h-4" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Integration Detail Modal */}
      {selectedIntegration && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedIntegration(null)}
        >
          <div 
            className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            <div className="p-6 space-y-6">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-blue-50 rounded-xl">
                    <selectedIntegration.icon className="w-8 h-8 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{selectedIntegration.name}</h2>
                    <p className="text-gray-500">{selectedIntegration.category}</p>
                  </div>
                </div>
                <button 
                  onClick={() => setSelectedIntegration(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <p className="text-gray-700">{selectedIntegration.description}</p>

              {/* Features */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Features</h3>
                <ul className="space-y-2">
                  {selectedIntegration.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Setup Steps */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Setup Steps</h3>
                <div className="space-y-3">
                  {selectedIntegration.setupSteps.map((step, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                        {i + 1}
                      </span>
                      <span className="text-gray-700">{step}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Config Example */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">Configuration Example</h3>
                  <button
                    onClick={() => copyConfig(selectedIntegration.configExample)}
                    className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
                  >
                    {copied ? <><Check className="w-4 h-4" /> Copied!</> : <><Copy className="w-4 h-4" /> Copy</>}
                  </button>
                </div>
                <pre className="bg-gray-900 text-green-400 p-4 rounded-xl overflow-x-auto text-sm">
                  {selectedIntegration.configExample}
                </pre>
              </div>

              <button 
                className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
                onClick={() => {
                  toast.success('Integration configured!');
                  setSelectedIntegration(null);
                }}
              >
                Add Integration
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Custom Integration */}
      <div className="bg-gray-50 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Custom Agent?</h2>
        <p className="text-gray-600 mb-4">
          FleetOps supports any AI agent via our API. Build your own integration using our SDK.
        </p>
        <div className="flex flex-wrap gap-3">
          <a 
            href="/docs/API_REFERENCE.md" 
            target="_blank"
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            API Reference
          </a>
          <a 
            href="/docs/ARCHITECTURE.md" 
            target="_blank"
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            <Terminal className="w-4 h-4" />
            SDK Guide
          </a>
        </div>
      </div>
    </div>
  );
}
