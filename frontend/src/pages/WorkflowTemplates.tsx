import { useState } from 'react';
import { 
  GitBranch, 
  CheckCircle, 
  ArrowRight,
  Play,
  Copy,
  Check,
  Code2,
  FlaskConical,
  Palette,
  Briefcase,
  HeadphonesIcon,
  Server
} from 'lucide-react';
import { toast } from '../hooks/useToast';

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  icon: any;
  category: string;
  stages: { name: string; agent_action: string; human_role: string; approval_required: boolean }[];
  config: object;
}

const templates: WorkflowTemplate[] = [
  {
    id: 'code-review',
    name: 'Code Review Pipeline',
    description: 'AI generates code → Senior dev reviews → Tests run → Deploy',
    icon: Code2,
    category: 'Software Engineering',
    stages: [
      { name: 'Generate', agent_action: 'AI writes feature code', human_role: 'Provide requirements', approval_required: false },
      { name: 'Review', agent_action: 'Copilot suggests improvements', human_role: 'Senior dev reviews', approval_required: true },
      { name: 'Test', agent_action: 'CI runs automated tests', human_role: 'QA approves results', approval_required: true },
      { name: 'Deploy', agent_action: 'CD prepares release', human_role: 'Lead approves deploy', approval_required: true }
    ],
    config: {
      name: 'Code Review Pipeline',
      risk_levels: ['low', 'medium', 'high'],
      auto_approve_low_risk: true,
      require_2_approvers_for_high: true,
      notify_slack: true
    }
  },
  {
    id: 'experiment',
    name: 'ML Experiment Workflow',
    description: 'Design experiment → Run training → Evaluate → Publish model',
    icon: FlaskConical,
    category: 'Data Science',
    stages: [
      { name: 'Design', agent_action: 'AI proposes methodology', human_role: 'Data scientist approves', approval_required: true },
      { name: 'Execute', agent_action: 'Runs training pipeline', human_role: 'Monitor progress', approval_required: false },
      { name: 'Evaluate', agent_action: 'Generates evaluation report', human_role: 'Review metrics', approval_required: true },
      { name: 'Deploy', agent_action: 'Prepares model for production', human_role: 'ML engineer approves', approval_required: true }
    ],
    config: {
      name: 'ML Experiment Workflow',
      track_metrics: true,
      compare_with_baseline: true,
      require_reproducibility: true
    }
  },
  {
    id: 'content',
    name: 'Content Approval Chain',
    description: 'AI drafts → Editor reviews → Brand check → Publish',
    icon: Palette,
    category: 'Creative',
    stages: [
      { name: 'Draft', agent_action: 'AI generates content', human_role: 'Provide brief', approval_required: false },
      { name: 'Edit', agent_action: 'Iterates on feedback', human_role: 'Editor reviews', approval_required: true },
      { name: 'Brand', agent_action: 'Checks compliance', human_role: 'Brand manager approves', approval_required: true },
      { name: 'Publish', agent_action: 'Prepares final assets', human_role: 'CMO approves', approval_required: true }
    ],
    config: {
      name: 'Content Approval Chain',
      brand_guidelines_url: 'https://...',
      tone_check: true,
      plagiarism_check: true
    }
  },
  {
    id: 'infrastructure',
    name: 'Infrastructure Change',
    description: 'Terraform plan → Policy check → SRE approval → Apply',
    icon: Server,
    category: 'DevOps',
    stages: [
      { name: 'Plan', agent_action: 'Terraform generates plan', human_role: 'SRE reviews changes', approval_required: true },
      { name: 'Validate', agent_action: 'Runs policy checks', human_role: 'Security approves', approval_required: true },
      { name: 'Apply', agent_action: 'Executes changes', human_role: 'Monitors deployment', approval_required: true },
      { name: 'Verify', agent_action: 'Health checks', human_role: 'Confirms stability', approval_required: false }
    ],
    config: {
      name: 'Infrastructure Change',
      require_dry_run: true,
      backup_before_apply: true,
      rollback_window_minutes: 30
    }
  },
  {
    id: 'customer-ticket',
    name: 'Customer Ticket Resolution',
    description: 'Classify → AI responds → Escalate if needed → Resolve',
    icon: HeadphonesIcon,
    category: 'Customer Service',
    stages: [
      { name: 'Classify', agent_action: 'AI categorizes ticket', human_role: 'Sets routing rules', approval_required: false },
      { name: 'Respond', agent_action: 'Drafts response', human_role: 'Reviews if needed', approval_required: false },
      { name: 'Escalate', agent_action: 'Detects need for human', human_role: 'Takes over complex', approval_required: true },
      { name: 'Resolve', agent_action: 'Documents resolution', human_role: 'Confirms satisfaction', approval_required: false }
    ],
    config: {
      name: 'Customer Ticket Resolution',
      auto_resolve_confidence_threshold: 0.9,
      escalation_keywords: ['urgent', 'refund', 'complaint'],
      sla_hours: 24
    }
  },
  {
    id: 'workflow-generic',
    name: 'Generic Approval Workflow',
    description: 'Simple 3-stage approval for any process',
    icon: Briefcase,
    category: 'Operations',
    stages: [
      { name: 'Submit', agent_action: 'Process request', human_role: 'Submit request', approval_required: false },
      { name: 'Review', agent_action: 'Checks completeness', human_role: 'Manager reviews', approval_required: true },
      { name: 'Approve', agent_action: 'Validates compliance', human_role: 'Director approves', approval_required: true }
    ],
    config: {
      name: 'Generic Approval Workflow',
      allow_delegate: true,
      reminder_frequency_hours: 24,
      escalation_after_days: 3
    }
  }
];

export default function WorkflowTemplates() {
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);
  const [copied, setCopied] = useState(false);
  const [filter, setFilter] = useState('all');

  const categories = ['all', ...new Set(templates.map(t => t.category))];

  const filtered = filter === 'all' ? templates : templates.filter(t => t.category === filter);

  const copyConfig = (config: object) => {
    navigator.clipboard.writeText(JSON.stringify(config, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success('Template copied!');
  };

  const activateTemplate = (template: WorkflowTemplate) => {
    toast.success(`Activated: ${template.name}`);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold text-gray-900">Workflow Templates</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Pre-built approval workflows for every team type. Activate in one click and customize for your needs.
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
            {cat === 'all' ? 'All Templates' : cat}
          </button>
        ))}
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map(template => {
          const Icon = template.icon;
          return (
            <div
              key={template.id}
              className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => setSelectedTemplate(template)}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-blue-50 rounded-xl">
                  <Icon className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{template.name}</h3>
                  <span className="text-xs text-gray-500">{template.category}</span>
                </div>
              </div>

              <p className="text-gray-600 text-sm mb-4">{template.description}</p>

              <div className="flex items-center gap-2 text-sm text-gray-500">
                <GitBranch className="w-4 h-4" />
                {template.stages.length} stages
                <span className="mx-2">•</span>
                <CheckCircle className="w-4 h-4" />
                {template.stages.filter(s => s.approval_required).length} approvals
              </div>
            </div>
          );
        })}
      </div>

      {/* Template Detail Modal */}
      {selectedTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedTemplate(null)}
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
                    <selectedTemplate.icon className="w-8 h-8 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{selectedTemplate.name}</h2>
                    <p className="text-gray-500">{selectedTemplate.category}</p>
                  </div>
                </div>
                <button 
                  onClick={() => setSelectedTemplate(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <p className="text-gray-700">{selectedTemplate.description}</p>

              {/* Workflow Stages */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Workflow Stages</h3>
                <div className="space-y-3">
                  {selectedTemplate.stages.map((stage, i) => (
                    <div key={i} className="flex items-start gap-4">
                      <div className="flex flex-col items-center">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                          stage.approval_required 
                            ? 'bg-yellow-100 text-yellow-700' 
                            : 'bg-green-100 text-green-700'
                        }`}>
                          {i + 1}
                        </div>
                        {i < selectedTemplate.stages.length - 1 && (
                          <div className="w-0.5 h-8 bg-gray-200" />
                        )}
                      </div>
                      <div className="flex-1 pb-4">
                        <div className="font-medium text-gray-900">{stage.name}</div>
                        <div className="flex items-center gap-3 mt-1 text-sm">
                          <span className="text-blue-600">🤖 {stage.agent_action}</span>
                          <span className="text-gray-400">→</span>
                          <span className="text-gray-700">👤 {stage.human_role}</span>
                        </div>
                        {stage.approval_required && (
                          <span className="inline-block mt-1 px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                            Requires Approval
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Config */}
              <div className="bg-gray-900 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400 text-sm">Configuration</span>
                  <button
                    onClick={() => copyConfig(selectedTemplate.config)}
                    className="text-gray-400 hover:text-white text-sm flex items-center gap-1"
                  >
                    {copied ? <><Check className="w-4 h-4" /> Copied!</> : <><Copy className="w-4 h-4" /> Copy</>}
                  </button>
                </div>
                <pre className="text-green-400 text-sm overflow-x-auto">
                  {JSON.stringify(selectedTemplate.config, null, 2)}
                </pre>
              </div>

              <button 
                className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                onClick={() => activateTemplate(selectedTemplate)}
              >
                <Play className="w-5 h-5" />
                Activate Workflow
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
