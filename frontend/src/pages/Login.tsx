import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useForm } from '../hooks/useForm';
import { Loading } from '../components/Loading';
import { toast } from '../hooks/useToast';
import { LogIn, UserPlus, Zap, Shield, Users } from 'lucide-react';

const loginSchema = {
  email: { required: true, email: true },
  password: { required: true, minLength: 8 },
};

const registerSchema = {
  email: { required: true, email: true },
  password: { required: true, minLength: 8 },
  name: { required: true, minLength: 2 },
  org_name: { required: false },
};

export default function Login() {
  const [isRegistering, setIsRegistering] = useState(false);
  const { login, register, isLoading: authLoading } = useAuth();

  const loginForm = useForm(
    { email: '', password: '' },
    loginSchema,
    async (values) => {
      await login(values.email, values.password);
      toast.success('Welcome back!');
      window.location.href = '/';
    }
  );

  const registerForm = useForm(
    { email: '', password: '', name: '', org_name: '' },
    registerSchema,
    async (values) => {
      await register(values);
      toast.success('Account created!');
      window.location.href = '/onboarding';
    }
  );

  if (authLoading) {
    return <Loading fullPage text="Authenticating..." />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">FleetOps</h1>
          <p className="text-gray-500 mt-1">The Operating System for Governed Human-Agent Work</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="flex mb-6">
            <button
              onClick={() => setIsRegistering(false)}
              className={`flex-1 pb-2 text-center font-medium transition-colors ${
                !isRegistering ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setIsRegistering(true)}
              className={`flex-1 pb-2 text-center font-medium transition-colors ${
                isRegistering ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              Create Account
            </button>
          </div>

          {isRegistering ? (
            <form onSubmit={registerForm.handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                <input {...registerForm.getFieldProps('name')} type="text" className="w-full px-4 py-2 border border-gray-200 rounded-lg" placeholder="John Doe" />
                {registerForm.errors.name && registerForm.touched.name && <p className="text-sm text-red-500 mt-1">{registerForm.errors.name}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input {...registerForm.getFieldProps('email')} type="email" className="w-full px-4 py-2 border border-gray-200 rounded-lg" placeholder="you@company.com" />
                {registerForm.errors.email && registerForm.touched.email && <p className="text-sm text-red-500 mt-1">{registerForm.errors.email}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
                <input {...registerForm.getFieldProps('password')} type="password" className="w-full px-4 py-2 border border-gray-200 rounded-lg" placeholder="Min 8 characters" />
                {registerForm.errors.password && registerForm.touched.password && <p className="text-sm text-red-500 mt-1">{registerForm.errors.password}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Organization (optional)</label>
                <input {...registerForm.getFieldProps('org_name')} type="text" className="w-full px-4 py-2 border border-gray-200 rounded-lg" placeholder="My Company" />
              </div>
              <button type="submit" disabled={registerForm.isSubmitting} className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                <UserPlus className="w-4 h-4" />
                {registerForm.isSubmitting ? 'Creating...' : 'Create Account'}
              </button>
            </form>
          ) : (
            <form onSubmit={loginForm.handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input {...loginForm.getFieldProps('email')} type="email" className="w-full px-4 py-2 border border-gray-200 rounded-lg" placeholder="you@company.com" />
                {loginForm.errors.email && loginForm.touched.email && <p className="text-sm text-red-500 mt-1">{loginForm.errors.email}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input {...loginForm.getFieldProps('password')} type="password" className="w-full px-4 py-2 border border-gray-200 rounded-lg" placeholder="Your password" />
                {loginForm.errors.password && loginForm.touched.password && <p className="text-sm text-red-500 mt-1">{loginForm.errors.password}</p>}
              </div>
              <button type="submit" disabled={loginForm.isSubmitting} className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                <LogIn className="w-4 h-4" />
                {loginForm.isSubmitting ? 'Signing in...' : 'Sign In'}
              </button>
            </form>
          )}
        </div>

        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div className="p-3"><Shield className="w-6 h-6 text-blue-600 mx-auto mb-2" /><p className="text-xs text-gray-600">Enterprise Security</p></div>
          <div className="p-3"><Users className="w-6 h-6 text-blue-600 mx-auto mb-2" /><p className="text-xs text-gray-600">Human-in-the-Loop</p></div>
          <div className="p-3"><Zap className="w-6 h-6 text-blue-600 mx-auto mb-2" /><p className="text-xs text-gray-600">Real-time Updates</p></div>
        </div>
      </div>
    </div>
  );
}
