import { useState } from 'react';
import { 
  Code2, 
  BarChart3, 
  Palette, 
  Briefcase, 
  HeadphonesIcon, 
  FlaskConical,
  Server,
  CheckCircle,
  ArrowRight,
  Bot,
  Users,
  Shield
} from 'lucide-react';

interface UseCase {
  id: string;
  icon: any;
  title: string;
  subtitle: string;
  description: string;
  color: string;
  bgColor: string;
  features: string[];
  workflow: { step: string; agent: string; human: string }[];
}

const useCases: UseCase[] = [
  {
    id: 'software',
    icon: Code2,
    title: 'Software Engineering',
    subtitle: 'Govern AI-generated code',
    description: 'Connect Claude Code, GitHub Copilot, Cursor, or any coding agent. Every code generation goes through your approval workflow.',
    color: 'blue',
    bgColor: 'bg-blue-50',
    features: [
      'AI code generation with human review',
      'Automated testing gates',
      'Infrastructure change approvals',
      'Security scan integration',
      'Deployment approval workflows'
    ],
    workflow: [
      { step: '1. Generate', agent: 'Claude Code writes feature', human: 'Specify requirements' },
      { step: '2. Review', agent: 'Copilot suggests improvements', human: 'Senior dev reviews code' },
      { step: '3. Test', agent: 'CI runs automated tests', human: 'QA approves test results' },
      { step: '4. Deploy', agent: 'CD pipeline prepares release', human: 'Lead approves production deploy' }
    ]
  },
  {
    id: 'data',
    icon: BarChart3,
    title: 'Data Science',
    subtitle: 'Manage AI experiments safely',
    description: 'Run model training, data pipelines, and experiments with full oversight. Every experiment is tracked and approved.',
    color: 'purple',
    bgColor: 'bg-purple-50',
    features: [
      'Experiment tracking and approval',
      'Model evaluation workflows',
      'Data quality gates',
      'Pipeline orchestration',
      'Result publication review'
    ],
    workflow: [
      { step: '1. Design', agent: 'AI suggests experiment design', human: 'Data scientist approves' },
      { step: '2. Execute', agent: 'Runs training pipeline', human: 'Monitor progress' },
      { step: '3. Evaluate', agent: 'Generates evaluation report', human: 'Review metrics' },
      { step: '4. Deploy', agent: 'Prepares model for production', human: 'ML engineer approves' }
    ]
  },
  {
    id: 'creative',
    icon: Palette,
    title: 'Creative Teams',
    subtitle: 'AI-assisted content creation',
    description: 'Generate content, designs, and campaigns with brand compliance checks and creative director approval.',
    color: 'pink',
    bgColor: 'bg-pink-50',
    features: [
      'Content generation workflows',
      'Brand compliance checking',
      'Multi-stage creative review',
      'Asset management',
      'Campaign approval chains'
    ],
    workflow: [
      { step: '1. Brief', agent: 'AI interprets creative brief', human: 'Creative director inputs vision' },
      { step: '2. Create', agent: 'Generates draft content', human: 'Designer reviews concepts' },
      { step: '3. Refine', agent: 'Iterates based on feedback', human: 'Brand manager checks compliance' },
      { step: '4. Publish', agent: 'Prepares final assets', human: 'CMO approves campaign' }
    ]
  },
  {
    id: 'operations',
    icon: Briefcase,
    title: 'Operations',
    subtitle: 'Automated workflows with oversight',
    description: 'Streamline operations while maintaining control. Every automated decision can be reviewed and overridden.',
    color: 'orange',
    bgColor: 'bg-orange-50',
    features: [
      'Workflow automation with gates',
      'Document processing pipelines',
      'Approval hierarchies',
      'Exception handling',
      'Audit trail for compliance'
    ],
    workflow: [
      { step: '1. Intake', agent: 'Classifies incoming request', human: 'Sets priority and category' },
      { step: '2. Process', agent: 'Executes workflow steps', human: 'Monitors progress' },
      { step: '3. Verify', agent: 'Checks quality and compliance', human: 'Reviews edge cases' },
      { step: '4. Complete', agent: 'Generates completion report', human: 'Final approval' }
    ]
  },
  {
    id: 'customer',
    icon: HeadphonesIcon,
    title: 'Customer Service',
    subtitle: 'Multi-channel AI support',
    description: 'Handle customer inquiries across WhatsApp, Telegram, Email, Web Chat, Voice, and Discord with seamless handoff to humans.',
    color: 'green',
    bgColor: 'bg-green-50',
    features: [
      'Multi-channel support (6 channels)',
      'Intelligent routing',
      'Human handoff triggers',
      'Context preservation across channels',
      'SLA tracking and escalation'
    ],
    workflow: [
      { step: '1. Receive', agent: 'AI classifies inquiry', human: 'Sets routing rules' },
      { step: '2. Respond', agent: 'Drafts initial response', human: 'Reviews if needed' },
      { step: '3. Escalate', agent: 'Detects need for human', human: 'Takes over complex case' },
      { step: '4. Resolve', agent: 'Documents resolution', human: 'Confirms satisfaction' }
    ]
  },
  {
    id: 'research',
    icon: FlaskConical,
    title: 'Research',
    subtitle: 'Accelerate research safely',
    description: 'Manage literature reviews, experiment design, and data analysis with full traceability and reproducibility.',
    color: 'teal',
    bgColor: 'bg-teal-50',
    features: [
      'Literature review automation',
      'Experiment protocol design',
      'Data analysis workflows',
      'Collaboration management',
      'Publication preparation'
    ],
    workflow: [
      { step: '1. Explore', agent: 'Searches and summarizes papers', human: 'Defines research question' },
      { step: '2. Design', agent: 'Proposes methodology', human: 'PI approves protocol' },
      { step: '3. Analyze', agent: 'Processes experimental data', human: 'Validates results' },
      { step: '4. Publish', agent: 'Drafts manuscript sections', human: 'Lead author approves' }
    ]
  },
  {
    id: 'devops',
    icon: Server,
    title: 'DevOps / SRE',
    subtitle: 'Govern infrastructure changes',
    description: 'Every Terraform plan, Ansible playbook, or infrastructure change goes through approval before execution.',
    color: 'indigo',
    bgColor: 'bg-indigo-50',
    features: [
      'Infrastructure change approvals',
      'Deployment gates',
      'Incident response workflows',
      'Rollback procedures',
      'Compliance auditing'
    ],
    workflow: [
      { step: '1. Plan', agent: 'Terraform generates plan', human: 'SRE reviews changes' },
      { step: '2. Validate', agent: 'Runs policy checks', human: 'Security team approves' },
      { step: '3. Apply', agent: 'Executes approved changes', human: 'Monitors deployment' },
      { step: '4. Verify', agent: 'Runs health checks', human: 'Confirms stability' }
    ]
  }
];

export default function UseCases() {
  const [activeCase, setActiveCase] = useState<UseCase>(useCases[0]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold text-gray-900">FleetOps for Every Team</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Not just customer service — FleetOps governs AI agents across your entire organization.
          From software engineering to research, every team gets human oversight.
        </p>
      </div>

      {/* Use Case Selector */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {useCases.map(uc => {
          const Icon = uc.icon;
          const isActive = activeCase.id === uc.id;
          return (
            <button
              key={uc.id}
              onClick={() => setActiveCase(uc)}
              className={`p-4 rounded-xl border-2 transition-all text-center ${
                isActive
                  ? `border-${uc.color}-500 ${uc.bgColor} shadow-md`
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <Icon className={`w-6 h-6 mx-auto mb-2 ${isActive ? `text-${uc.color}-600` : 'text-gray-400'}`} />
              <div className={`text-xs font-medium ${isActive ? `text-${uc.color}-700` : 'text-gray-600'}`}>
                {uc.title}
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Use Case Detail */}
      <div className={`${activeCase.bgColor} rounded-2xl p-8 border-2 border-${activeCase.color}-200`}>
        <div className="flex items-start gap-4 mb-6">
          <div className={`p-3 bg-${activeCase.color}-100 rounded-xl`}>
            <activeCase.icon className={`w-8 h-8 text-${activeCase.color}-600`} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{activeCase.title}</h2>
            <p className="text-gray-600">{activeCase.subtitle}</p>
          </div>
        </div>

        <p className="text-gray-700 mb-6">{activeCase.description}</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Features */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              Key Features
            </h3>
            <ul className="space-y-2">
              {activeCase.features.map((feature, i) => (
                <li key={i} className="flex items-start gap-2">
                  <ArrowRight className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                  <span className="text-gray-700">{feature}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Workflow */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Bot className="w-5 h-5 text-blue-500" />
              Human-Agent Workflow
            </h3>
            <div className="space-y-3">
              {activeCase.workflow.map((step, i) => (
                <div key={i} className="bg-white rounded-lg p-4 shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-semibold text-gray-900">{step.step}</span>
                  </div>
                  <div className="flex items-start gap-4 text-sm">
                    <div className="flex items-center gap-1 text-blue-600">
                      <Bot className="w-4 h-4" />
                      <span>{step.agent}</span>
                    </div>
                    <div className="text-gray-400">←</div>
                    <div className="flex items-center gap-1 text-gray-700">
                      <Users className="w-4 h-4" />
                      <span>{step.human}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Universal Benefits */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Shield className="w-5 h-5 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-900">Governance</h3>
          </div>
          <p className="text-gray-600 text-sm">
            Every AI action is tracked, signed, and auditable. Maintain compliance without slowing down.
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Bot className="w-5 h-5 text-green-600" />
            </div>
            <h3 className="font-semibold text-gray-900">Flexibility</h3>
          </div>
          <p className="text-gray-600 text-sm">
            Use any AI agent — Claude, GPT, Copilot, Cursor, Devin, or your own custom agent.
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Users className="w-5 h-5 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-900">Collaboration</h3>
          </div>
          <p className="text-gray-600 text-sm">
            Teams work together with clear roles. Executives oversee, operators execute, reviewers check.
          </p>
        </div>
      </div>
    </div>
  );
}
