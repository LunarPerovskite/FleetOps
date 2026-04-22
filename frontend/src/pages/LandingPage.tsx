import { Link } from 'react-router-dom';
import { 
  Shield, 
  Bot, 
  Users, 
  CheckCircle, 
  ArrowRight,
  Code2,
  Zap,
  Lock,
  GitBranch,
  Globe,
  Terminal,
  MessageCircle,
  BarChart3
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-2">
              <Shield className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">FleetOps</span>
            </div>
            <div className="flex items-center gap-4">
              <Link to="/login" className="text-gray-600 hover:text-gray-900">
                Sign In
              </Link>
              <Link 
                to="/login" 
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <h1 className="text-5xl font-bold text-gray-900 leading-tight">
            The Operating System for<br />
            <span className="text-blue-600">Governed Human-Agent Work</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Connect your AI agents to human oversight. Every action tracked, every decision approved, 
            every workflow governed — across all your teams.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link 
              to="/login"
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
            >
              Start Free
              <ArrowRight className="w-5 h-5" />
            </Link>
            <a 
              href="https://github.com/LunarPerovskite/FleetOps"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-6 py-3 border border-gray-300 rounded-xl font-medium hover:bg-gray-50 transition-colors"
            >
              <Terminal className="w-5 h-5" />
              View on GitHub
            </a>
          </div>
          <p className="text-sm text-gray-500">
            Self-hosted = 100% free. No limits. No restrictions. MIT License.
          </p>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-gray-900">7+</div>
              <div className="text-gray-600">Team Types</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-gray-900">6+</div>
              <div className="text-gray-600">AI Integrations</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-gray-900">19</div>
              <div className="text-gray-600">App Pages</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-gray-900">80+</div>
              <div className="text-gray-600">Git Commits</div>
            </div>
          </div>
        </div>
      </section>

      {/* For Every Team */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Built for Every Team That Uses AI
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: Code2, title: 'Software Engineering', desc: 'Govern code generation, review, and deployment' },
              { icon: BarChart3, title: 'Data Science', desc: 'Manage experiments, models, and pipelines' },
              { icon: Zap, title: 'Creative Teams', desc: 'Content creation with brand compliance' },
              { icon: Users, title: 'Operations', desc: 'Workflow automation with approval gates' },
              { icon: MessageCircle, title: 'Customer Service', desc: 'Multi-channel support with handoff' },
              { icon: GitBranch, title: 'DevOps/SRE', desc: 'Infrastructure changes with oversight' }
            ].map((team, i) => (
              <div key={i} className="p-6 border border-gray-200 rounded-xl hover:shadow-md transition-shadow">
                <team.icon className="w-8 h-8 text-blue-600 mb-3" />
                <h3 className="font-semibold text-gray-900 mb-1">{team.title}</h3>
                <p className="text-gray-600 text-sm">{team.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Everything You Need to Govern AI
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {[
              { icon: Shield, title: 'Human-in-the-Loop', desc: 'Insert approval at any stage. No AI action goes unreviewed.' },
              { icon: Lock, title: 'Immutable Audit Trail', desc: 'Cryptographically signed evidence. Every decision is permanent and verifiable.' },
              { icon: Bot, title: 'Agent Hierarchy', desc: 'Organize agents with levels, roles, and unlimited sub-agents.' },
              { icon: Globe, title: 'Provider Agnostic', desc: 'Use any stack: Clerk, Auth0, Okta, Supabase, AWS, etc.' },
              { icon: CheckCircle, title: 'Feature Flags', desc: 'Gradual rollouts and A/B testing for new AI features.' },
              { icon: Terminal, title: 'CLI + API', desc: 'Command-line management and full REST API access.' }
            ].map((feature, i) => (
              <div key={i} className="flex items-start gap-4">
                <div className="p-3 bg-white rounded-xl shadow-sm">
                  <feature.icon className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">{feature.title}</h3>
                  <p className="text-gray-600">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Open Source */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <h2 className="text-3xl font-bold text-gray-900">
            100% Open Source. Forever Free.
          </h2>
          <p className="text-lg text-gray-600">
            Self-hosted FleetOps is and always will be free. All features, unlimited users, 
            unlimited agents — no restrictions, no "freemium" traps.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <div className="px-6 py-4 bg-green-50 border border-green-200 rounded-xl">
              <div className="font-semibold text-green-900">Self-Hosted</div>
              <div className="text-2xl font-bold text-green-700">$0</div>
              <div className="text-sm text-green-600">All features, unlimited</div>
            </div>
            <div className="px-6 py-4 bg-blue-50 border border-blue-200 rounded-xl">
              <div className="font-semibold text-blue-900">Cloud</div>
              <div className="text-2xl font-bold text-blue-700">$29/mo</div>
              <div className="text-sm text-blue-600">Managed hosting</div>
            </div>
            <div className="px-6 py-4 bg-purple-50 border border-purple-200 rounded-xl">
              <div className="font-semibold text-purple-900">Enterprise</div>
              <div className="text-2xl font-bold text-purple-700">Custom</div>
              <div className="text-sm text-purple-600">Dedicated support</div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-gray-200">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <Shield className="w-6 h-6 text-blue-600" />
              <span className="font-semibold text-gray-900">FleetOps</span>
            </div>
            <div className="flex gap-6 text-sm text-gray-600">
              <a href="https://github.com/LunarPerovskite/FleetOps" className="hover:text-gray-900">GitHub</a>
              <Link to="/login" className="hover:text-gray-900">Sign In</Link>
              <a href="mailto:juanestebanmosquera@yahoo.com" className="hover:text-gray-900">Contact</a>
            </div>
            <div className="text-sm text-gray-500">
              MIT License • Built with ❤️
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
