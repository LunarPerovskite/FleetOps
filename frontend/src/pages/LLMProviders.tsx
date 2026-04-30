import { useState, useEffect } from 'react';
import { modelsAPI } from '../lib/api';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import {
  Plug,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  KeyRound,
  Eye,
  EyeOff,
  Bot,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Server
} from 'lucide-react';

interface ProviderStatus {
  provider: string;
  has_api_key: boolean;
  env_var: string;
  models_registered: number;
  adapter_available: boolean;
}

interface DiscoveredModel {
  id: string;
  name: string;
  capabilities: string[];
}

interface ProviderCard {
  id: string;
  name: string;
  description: string;
  icon: string;
  docsUrl: string;
}

const PROVIDER_CARDS: ProviderCard[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT-4o, GPT-4o Mini, o1, embeddings, DALL-E',
    icon: '⚡',
    docsUrl: 'https://platform.openai.com/api-keys'
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    description: 'Claude 3.7 Sonnet, Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku',
    icon: '🌿',
    docsUrl: 'https://console.anthropic.com/settings/keys'
  },
  {
    id: 'gemini',
    name: 'Google Gemini',
    description: 'Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini Pro Vision',
    icon: '🔮',
    docsUrl: 'https://aistudio.google.com/app/apikey'
  },
  {
    id: 'ollama',
    name: 'Ollama',
    description: 'Local models: Llama, Mistral, Gemma, CodeGen',
    icon: '🦙',
    docsUrl: 'https://ollama.com'
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    description: 'DeepSeek Chat, Coder, Reasoner',
    icon: '🐋',
    docsUrl: 'https://platform.deepseek.com'
  },
  {
    id: 'mistral',
    name: 'Mistral AI',
    description: 'Mistral Large, Mistral Medium, Mistral Small',
    icon: '🌪️',
    docsUrl: 'https://console.mistral.ai'
  },
  {
    id: 'cohere',
    name: 'Cohere',
    description: 'Command R, Command R+, Embed, Rerank',
    icon: '📊',
    docsUrl: 'https://dashboard.cohere.com'
  },
  {
    id: 'zai',
    name: 'Z.ai (Qwen)',
    description: 'Qwen3 72B, Qwen3 235B, Qwen VL Max',
    icon: '🤖',
    docsUrl: 'https://z.ai'
  },
  {
    id: 'minimax',
    name: 'MiniMax',
    description: 'MiniMax abab6.5s, abab6',
    icon: '📱',
    docsUrl: 'https://platform.minimax.chat'
  },
  {
    id: 'elevenlabs',
    name: 'ElevenLabs',
    description: 'Text-to-Speech voices',
    icon: '🎙️',
    docsUrl: 'https://elevenlabs.io'
  },
];

export default function LLMProviders() {
  const [statuses, setStatuses] = useState<ProviderStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [discovering, setDiscovering] = useState<Record<string, boolean>>({});
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [discoveredModels, setDiscoveredModels] = useState<Record<string, DiscoveredModel[]>>({});
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    fetchStatuses();
  }, []);

  const fetchStatuses = async () => {
    try {
      setLoading(true);
      const data: any = await modelsAPI.providerStatus();
      setStatuses(data || []);
      setLastUpdated(new Date());
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load provider status');
    } finally {
      setLoading(false);
    }
  };

  const handleDiscoverAll = async () => {
    try {
      setLoading(true);
      const result: any = await modelsAPI.discover();
      toast.success(`Discovered ${result.total_discovered} models across all providers`);
      await fetchStatuses();
    } catch (err: any) {
      toast.error(err.message || 'Discovery failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshKey = async (provider: string) => {
    const key = apiKeys[provider];
    if (!key) {
      toast.error('Please enter an API key');
      return;
    }

    try {
      setDiscovering(prev => ({ ...prev, [provider]: true }));
      const result: any = await modelsAPI.refreshProviderKey(provider, key);

      if (result.models_discovered > 0) {
        setDiscoveredModels(prev => ({
          ...prev,
          [provider]: result.models
        }));
        toast.success(
          `Discovered ${result.models_discovered} models from ${provider}`
        );
      } else {
        toast('No new models found. Key may be invalid or no models available.');
      }

      // Clear the key from state for security
      setApiKeys(prev => ({ ...prev, [provider]: '' }));
      await fetchStatuses();
    } catch (err: any) {
      toast.error(err.message || `Failed to refresh ${provider} key`);
    } finally {
      setDiscovering(prev => ({ ...prev, [provider]: false }));
    }
  };

  const toggleExpand = (provider: string) => {
    setExpanded(prev => ({ ...prev, [provider]: !prev[provider] }));
  };

  const getStatus = (providerId: string): ProviderStatus | undefined => {
    return statuses.find(s => s.provider === providerId);
  };

  const getProviderCard = (providerId: string): ProviderCard | undefined => {
    return PROVIDER_CARDS.find(p => p.id === providerId);
  };

  if (loading && statuses.length === 0) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
        <SkeletonCard />
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchStatuses} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">LLM Providers</h1>
          <p className="text-gray-500 mt-1">
            Connect your AI providers and auto-discover available models
          </p>
          {lastUpdated && (
            <p className="text-xs text-gray-400 mt-1">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchStatuses}
            className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={handleDiscoverAll}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            {loading ? 'Discovering...' : 'Auto-Discover All'}
          </button>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <Plug className="w-4 h-4" />
            <span className="text-sm font-medium">Providers</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {statuses.filter(s => s.has_api_key).length} / {statuses.length}
          </p>
          <p className="text-xs text-gray-500">Connected</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <Bot className="w-4 h-4" />
            <span className="text-sm font-medium">Models</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {statuses.reduce((sum, s) => sum + s.models_registered, 0)}
          </p>
          <p className="text-xs text-gray-500">Registered</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <Server className="w-4 h-4" />
            <span className="text-sm font-medium">Active</span>
          </div>
          <p className="text-2xl font-bold text-green-600">
            {statuses.filter(s => s.has_api_key && s.models_registered > 0).length}
          </p>
          <p className="text-xs text-gray-500">Ready to use</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-sm font-medium">Missing</span>
          </div>
          <p className="text-2xl font-bold text-amber-600">
            {statuses.filter(s => !s.has_api_key).length}
          </p>
          <p className="text-xs text-gray-500">Need configuration</p>
        </div>
      </div>

      {/* Provider Cards */}
      <div className="space-y-4">
        {PROVIDER_CARDS.map(card => {
          const status = getStatus(card.id);
          const isConnected = status?.has_api_key || false;
          const modelCount = status?.models_registered || 0;
          const isExpanded = expanded[card.id] || false;
          const models = discoveredModels[card.id] || [];

          return (
            <div
              key={card.id}
              className={`bg-white rounded-xl border transition-all ${
                isConnected
                  ? 'border-green-200 shadow-sm'
                  : 'border-gray-200'
              }`}
            >
              {/* Header */}
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="text-3xl">{card.icon}</div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {card.name}
                        </h3>
                        {isConnected ? (
                          <span className="flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                            <CheckCircle className="w-3 h-3" />
                            Connected
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full font-medium">
                            <AlertTriangle className="w-3 h-3" />
                            Not configured
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        {card.description}
                      </p>
                      {isConnected && modelCount > 0 && (
                        <p className="text-sm text-green-600 mt-1 font-medium">
                          {modelCount} models registered
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {isConnected && (
                      <button
                        onClick={() => toggleExpand(card.id)}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors"
                      >
                        {isExpanded ? (
                          <>
                            <ChevronUp className="w-4 h-4" />
                            Hide
                          </>
                        ) : (
                          <>
                            <ChevronDown className="w-4 h-4" />
                            Manage
                          </>
                        )}
                      </button>
                    )}
                    <a
                      href={card.docsUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:text-blue-700"
                    >
                      Get key →
                    </a>
                  </div>
                </div>
              </div>

              {/* Expanded: API Key Input + Models */}
              {isExpanded && (
                <div className="px-6 pb-6 border-t border-gray-100 pt-4">
                  {/* API Key Input */}
                  {!isConnected && (
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        API Key
                      </label>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <input
                            type={showKey[card.id] ? 'text' : 'password'}
                            value={apiKeys[card.id] || ''}
                            onChange={e =>
                              setApiKeys(prev => ({
                                ...prev,
                                [card.id]: e.target.value
                              }))
                            }
                            placeholder={`Paste your ${card.name} API key`}
                            className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          />
                          <button
                            onClick={() =>
                              setShowKey(prev => ({
                                ...prev,
                                [card.id]: !prev[card.id]
                              }))
                            }
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                          >
                            {showKey[card.id] ? (
                              <EyeOff className="w-4 h-4" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                        <button
                          onClick={() => handleRefreshKey(card.id)}
                          disabled={discovering[card.id] || !apiKeys[card.id]}
                          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                        >
                          <KeyRound className="w-4 h-4" />
                          {discovering[card.id]
                            ? 'Discovering...'
                            : 'Connect & Discover'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Discovered Models */}
                  {models.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">
                        Discovered Models
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {models.map(model => (
                          <div
                            key={model.id}
                            className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-100"
                          >
                            <Bot className="w-4 h-4 text-blue-500" />
                            <div className="min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {model.name}
                              </p>
                              <p className="text-xs text-gray-500 truncate">
                                {model.capabilities.slice(0, 2).join(', ')}
                                {model.capabilities.length > 2 && '...'}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Already Connected: Show registered models info */}
                  {isConnected && modelCount > 0 && !models.length && (
                    <div className="flex items-center gap-2 text-sm text-green-600">
                      <CheckCircle className="w-4 h-4" />
                      <span>
                        {modelCount} models already registered. Use "Auto-Discover All" to refresh.
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* How it works */}
      <div className="bg-blue-50 rounded-xl border border-blue-100 p-6">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">
          How Auto-Discovery Works
        </h3>
        <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
          <li>Paste your API key in the provider card above</li>
          <li>FleetOps validates the key and fetches available models</li>
          <li>Models are automatically registered in your model registry</li>
          <li>Use "Auto-Discover All" to refresh all providers at once</li>
        </ol>
        <p className="text-xs text-blue-600 mt-3">
          Your API keys are stored securely and never exposed in the UI after saving.
        </p>
      </div>
    </div>
  );
}
