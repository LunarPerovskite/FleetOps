import { useState, useEffect } from 'react';
import api from '../lib/api';
import { Loading } from '../components/Loading';
import { toast } from '../hooks/useToast';
import { 
  CheckCircle, 
  Circle, 
  ChevronRight, 
  ChevronLeft,
  Sparkles,
  Building,
  Plug,
  Bot,
  FileText,
  Users,
  Settings
} from 'lucide-react';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  required: boolean;
  order: number;
}

const stepIcons: Record<string, any> = {
  welcome: Sparkles,
  org_setup: Building,
  providers: Plug,
  first_agent: Bot,
  first_task: FileText,
  team_invite: Users,
  customize: Settings,
};

export default function Onboarding() {
  const [steps, setSteps] = useState<OnboardingStep[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [orgName, setOrgName] = useState('');
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    fetchProgress();
  }, []);

  const fetchProgress = async () => {
    try {
      const response = await api.get('/onboarding/progress');
      const sortedSteps = response.steps.sort((a: OnboardingStep, b: OnboardingStep) => a.order - b.order);
      setSteps(sortedSteps);
      
      // Find first uncompleted step
      const firstUncompleted = sortedSteps.findIndex((s: OnboardingStep) => !s.completed);
      setCurrentStep(firstUncompleted === -1 ? sortedSteps.length - 1 : firstUncompleted);
      
      setCompleted(response.is_complete);
      setLoading(false);
    } catch (error) {
      toast.error('Failed to load onboarding progress');
      setLoading(false);
    }
  };

  const completeStep = async (stepId: string) => {
    try {
      await api.post(`/onboarding/steps/${stepId}/complete`);
      
      setSteps(prev => prev.map(s => 
        s.id === stepId ? { ...s, completed: true } : s
      ));
      
      toast.success('Step completed!');
      
      // Move to next step
      const nextStep = currentStep + 1;
      if (nextStep < steps.length) {
        setCurrentStep(nextStep);
      } else {
        setCompleted(true);
      }
    } catch (error) {
      toast.error('Failed to complete step');
    }
  };

  const skipStep = async (stepId: string) => {
    try {
      await api.post(`/onboarding/steps/${stepId}/skip`);
      setSteps(prev => prev.map(s => 
        s.id === stepId ? { ...s, completed: true } : s
      ));
      
      const nextStep = currentStep + 1;
      if (nextStep < steps.length) {
        setCurrentStep(nextStep);
      }
    } catch (error) {
      toast.error('Failed to skip step');
    }
  };

  if (loading) {
    return <Loading fullPage text="Loading onboarding..." />;
  }

  if (completed) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
          <h1 className="text-2xl font-bold text-gray-900">Setup Complete!</h1>
          <p className="text-gray-500">You're all set to start using FleetOps.</p>
          <button
            onClick={() => window.location.href = '/dashboard'}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const activeStep = steps[currentStep];
  const progress = (steps.filter(s => s.completed).length / steps.length) * 100;
  const Icon = activeStep ? stepIcons[activeStep.id] || Sparkles : Sparkles;

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-3xl mx-auto px-4">
        {/* Progress Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Welcome to FleetOps</h1>
          <p className="text-gray-500 mb-4">Complete these steps to get started</p>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-sm text-gray-500 mt-2">
            {steps.filter(s => s.completed).length} of {steps.length} steps completed
          </p>
        </div>

        {/* Steps Sidebar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Step List */}
          <div className="space-y-2">
            {steps.map((step, index) => {
              const StepIcon = stepIcons[step.id] || Circle;
              return (
                <button
                  key={step.id}
                  onClick={() => setCurrentStep(index)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors ${
                    index === currentStep 
                      ? 'bg-blue-50 border-blue-200 border' 
                      : step.completed 
                        ? 'bg-green-50' 
                        : 'bg-white border border-gray-200'
                  }`}
                >
                  {step.completed ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <StepIcon className={`w-5 h-5 ${index === currentStep ? 'text-blue-600' : 'text-gray-400'}`} />
                  )}
                  <span className={`text-sm ${
                    step.completed ? 'text-green-700' : index === currentStep ? 'text-blue-900' : 'text-gray-700'
                  }`}>
                    {step.title}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Active Step Content */}
          <div className="md:col-span-2">
            {activeStep && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <Icon className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">{activeStep.title}</h2>
                    <p className="text-gray-500">{activeStep.description}</p>
                  </div>
                </div>

                {/* Step-specific content */}
                <div className="space-y-4">
                  {activeStep.id === 'welcome' && (
                    <div className="space-y-4">
                      <p className="text-gray-700">
                        FleetOps helps you govern human-AI collaboration with:
                      </p>
                      <ul className="list-disc list-inside space-y-2 text-gray-600">
                        <li>Human-in-the-loop at any workflow stage</li>
                        <li>Immutable evidence and audit trails</li>
                        <li>Multi-channel customer service</li>
                        <li>Flexible provider integration</li>
                      </ul>
                    </div>
                  )}

                  {activeStep.id === 'org_setup' && (
                    <div className="space-y-4">
                      <label className="block text-sm font-medium text-gray-700">
                        Organization Name
                      </label>
                      <input
                        type="text"
                        value={orgName}
                        onChange={(e) => setOrgName(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="My Organization"
                      />
                    </div>
                  )}

                  {activeStep.id === 'providers' && (
                    <div className="space-y-4">
                      <p className="text-gray-700">
                        Choose your stack in the Provider Configuration page:
                      </p>
                      <button
                        onClick={() => window.location.href = '/providers'}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Configure Providers
                      </button>
                    </div>
                  )}

                  {activeStep.id === 'first_agent' && (
                    <div className="space-y-4">
                      <p className="text-gray-700">
                        Create your first AI agent to start automating tasks.
                      </p>
                      <button
                        onClick={() => window.location.href = '/agents'}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Create Agent
                      </button>
                    </div>
                  )}

                  {activeStep.id === 'first_task' && (
                    <div className="space-y-4">
                      <p className="text-gray-700">
                        Create a task to see the approval workflow in action.
                      </p>
                      <button
                        onClick={() => window.location.href = '/tasks'}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Create Task
                      </button>
                    </div>
                  )}
                </div>

                {/* Navigation */}
                <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
                  <button
                    onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                    disabled={currentStep === 0}
                    className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Previous
                  </button>

                  <div className="flex gap-3">
                    {!activeStep.required && (
                      <button
                        onClick={() => skipStep(activeStep.id)}
                        className="px-4 py-2 text-gray-500 hover:text-gray-700"
                      >
                        Skip
                      </button>
                    )}
                    <button
                      onClick={() => completeStep(activeStep.id)}
                      className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      {currentStep === steps.length - 1 ? 'Finish' : 'Next'}
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
