import { useState } from 'react'
import { Check, ChevronRight, Server, Shield, Database, Globe, Bell, Lock } from 'lucide-react'

interface ProviderOption {
  id: string
  name: string
  description: string
  price: string
  features: string[]
  setupTime: string
  recommended?: boolean
}

const PROVIDERS = {
  auth: [
    { id: 'clerk', name: 'Clerk', description: 'Modern auth with React SDK', price: 'Free up to 10k MAU', features: ['OAuth', 'MFA', 'Session mgmt'], setupTime: '5 min', recommended: true },
    { id: 'auth0', name: 'Auth0', description: 'Enterprise standard', price: 'Free up to 7.5k MAU', features: ['SAML', 'SSO', 'Enterprise'], setupTime: '30 min' },
    { id: 'okta', name: 'Okta', description: 'Workforce identity', price: '$2/user/month', features: ['Best SSO', 'Compliance', 'MFA'], setupTime: '2 hours' },
    { id: 'self_hosted', name: 'Self-Hosted', description: 'FleetOps built-in auth', price: '$0', features: ['Full control', 'No vendor lock-in'], setupTime: '1 hour' }
  ],
  database: [
    { id: 'supabase', name: 'Supabase', description: 'PostgreSQL + Realtime', price: 'Free 500MB', features: ['PostgreSQL', 'Realtime', 'Auth included'], setupTime: '10 min', recommended: true },
    { id: 'neon', name: 'Neon', description: 'Serverless PostgreSQL', price: 'Free 3GB', features: ['Serverless', 'Branching', 'Auto-scale'], setupTime: '10 min' },
    { id: 'postgres', name: 'Self-Hosted', description: 'Your own PostgreSQL', price: '$0', features: ['Full control', 'No limits'], setupTime: '1 hour' }
  ],
  hosting: [
    { id: 'vercel', name: 'Vercel', description: 'Frontend + Edge', price: 'Free hobby', features: ['Edge network', 'Auto-deploy', 'Analytics'], setupTime: '5 min', recommended: true },
    { id: 'railway', name: 'Railway', description: 'Backend hosting', price: '$5/month', features: ['Simple', 'Auto-scale', 'Databases'], setupTime: '15 min' },
    { id: 'aws', name: 'AWS', description: 'Enterprise cloud', price: 'Pay per use', features: ['Global', 'Compliance', 'Scale'], setupTime: '2 hours' }
  ],
  secrets: [
    { id: 'env', name: '.env Files', description: 'Environment variables', price: '$0', features: ['Simple', 'No setup'], setupTime: '1 min', recommended: true },
    { id: 'doppler', name: 'Doppler', description: 'Modern secrets platform', price: 'Free tier', features: ['Sync', 'Versioning', 'Teams'], setupTime: '5 min' },
    { id: 'vault', name: 'HashiCorp Vault', description: 'Enterprise secrets', price: 'Open source', features: ['Dynamic secrets', 'Encryption'], setupTime: '2 hours' }
  ]
}

export default function ProviderConfig() {
  const [selectedProviders, setSelectedProviders] = useState<Record<string, string>>({
    auth: 'clerk',
    database: 'supabase',
    hosting: 'vercel',
    secrets: 'env'
  })
  const [activeCategory, setActiveCategory] = useState<string>('auth')
  const [showAdvanced, setShowAdvanced] = useState(false)

  const categories = [
    { id: 'auth', name: 'Authentication', icon: Shield },
    { id: 'database', name: 'Database', icon: Database },
    { id: 'hosting', name: 'Hosting', icon: Server },
    { id: 'secrets', name: 'Secrets', icon: Lock }
  ]

  const handleSelect = (category: string, providerId: string) => {
    setSelectedProviders(prev => ({ ...prev, [category]: providerId }))
  }

  const handleQuickStart = () => {
    setSelectedProviders({
      auth: 'clerk',
      database: 'supabase',
      hosting: 'vercel',
      secrets: 'env'
    })
  }

  const handleEnterprise = () => {
    setSelectedProviders({
      auth: 'okta',
      database: 'postgres',
      hosting: 'aws',
      secrets: 'vault'
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Provider Configuration</h1>
          <p className="text-gray-500">Choose your infrastructure stack</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleQuickStart}
            className="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm font-medium"
          >
            Quick Start (Free)
          </button>
          <button
            onClick={handleEnterprise}
            className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm font-medium"
          >
            Enterprise
          </button>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeCategory === cat.id
                ? 'bg-white text-indigo-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <cat.icon className="w-4 h-4 mr-2" />
            {cat.name}
            {selectedProviders[cat.id] && (
              <Check className="w-3 h-3 ml-2 text-green-500" />
            )}
          </button>
        ))}
      </div>

      {/* Provider Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {PROVIDERS[activeCategory as keyof typeof PROVIDERS]?.map((provider: ProviderOption) => (
          <div
            key={provider.id}
            onClick={() => handleSelect(activeCategory, provider.id)}
            className={`relative p-6 rounded-lg border-2 cursor-pointer transition-all ${
              selectedProviders[activeCategory] === provider.id
                ? 'border-indigo-600 bg-indigo-50'
                : 'border-gray-200 hover:border-gray-300 bg-white'
            }`}
          >
            {provider.recommended && (
              <span className="absolute top-3 right-3 px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full font-medium">
                Recommended
              </span>
            )}
            
            <h3 className="text-lg font-semibold text-gray-900">{provider.name}</h3>
            <p className="text-sm text-gray-500 mt-1">{provider.description}</p>
            <p className="text-sm font-medium text-indigo-600 mt-2">{provider.price}</p>
            
            <div className="mt-4 space-y-2">
              {provider.features.map(feature => (
                <div key={feature} className="flex items-center text-sm text-gray-600">
                  <Check className="w-3 h-3 mr-2 text-green-500" />
                  {feature}
                </div>
              ))}
            </div>
            
            <p className="text-xs text-gray-400 mt-4">Setup: {provider.setupTime}</p>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="bg-gray-900 rounded-lg p-6 text-white">
        <h3 className="text-lg font-semibold mb-4">Your Stack</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {categories.map(cat => {
            const provider = PROVIDERS[cat.id as keyof typeof PROVIDERS]?.find(
              (p: ProviderOption) => p.id === selectedProviders[cat.id]
            )
            return (
              <div key={cat.id} className="bg-gray-800 rounded-lg p-4">
                <cat.icon className="w-5 h-5 text-indigo-400 mb-2" />
                <p className="text-xs text-gray-400">{cat.name}</p>
                <p className="font-medium">{provider?.name || 'Not selected'}</p>
                <p className="text-xs text-gray-500 mt-1">{provider?.price}</p>
              </div>
            )
          })}
        </div>
        
        <div className="mt-6 flex justify-end">
          <button className="flex items-center px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors">
            Save Configuration
            <ChevronRight className="w-4 h-4 ml-2" />
          </button>
        </div>
      </div>

      {/* Advanced */}
      <div className="border border-gray-200 rounded-lg">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full px-6 py-4 flex items-center justify-between text-left"
        >
          <span className="font-medium text-gray-900">Advanced Configuration</span>
          <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${showAdvanced ? 'rotate-90' : ''}`} />
        </button>
        
        {showAdvanced && (
          <div className="px-6 pb-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Custom API Endpoint</label>
              <input type="text" className="mt-1 w-full rounded-lg border-gray-300" placeholder="https://api.yourcompany.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Webhook URL</label>
              <input type="text" className="mt-1 w-full rounded-lg border-gray-300" placeholder="https://hooks.yourcompany.com/fleetops" />
            </div>
            <div className="flex items-center space-x-2">
              <input type="checkbox" className="rounded text-indigo-600" />
              <span className="text-sm text-gray-700">Enable audit logging to external SIEM</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
