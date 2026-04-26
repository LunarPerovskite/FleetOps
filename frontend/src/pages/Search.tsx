import { useState, useEffect, useCallback } from 'react';
import { searchAPI } from '../lib/api';
import { Loading } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import {
  Search as SearchIcon,
  Bot,
  CheckSquare,
  Shield,
  FileText,
  Users,
  X,
  Filter
} from 'lucide-react';

interface SearchResult {
  id: string;
  type: 'agent' | 'task' | 'audit_event' | 'user' | 'team';
  title: string;
  description: string;
  url: string;
  metadata: Record<string, any>;
  score: number;
}

const typeIcons = {
  agent: Bot,
  task: CheckSquare,
  audit_event: Shield,
  user: Users,
  team: Users,
};

const typeColors = {
  agent: 'bg-purple-100 text-purple-600',
  task: 'bg-blue-100 text-blue-600',
  audit_event: 'bg-green-100 text-green-600',
  user: 'bg-orange-100 text-orange-600',
  team: 'bg-indigo-100 text-indigo-600',
};

export default function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  const performSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await searchAPI.search({
        query: searchQuery,
        filters: selectedTypes.length > 0 ? { types: selectedTypes } : undefined,
      });

      setResults(response?.results || response || []);
      setHasSearched(true);
    } catch (err: any) {
      setError(err.message || 'Search failed');
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  }, [selectedTypes]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.trim()) {
        performSearch(query);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, performSearch]);

  const toggleType = (type: string) => {
    setSelectedTypes(prev =>
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const clearFilters = () => {
    setSelectedTypes([]);
    setQuery('');
    setResults([]);
    setHasSearched(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Search</h1>
        <p className="text-gray-500 mt-1">Search across all entities</p>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search agents, tasks, audit logs, users..."
          className="w-full pl-12 pr-12 py-3 border border-gray-200 rounded-xl text-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
        {query && (
          <button
            onClick={() => { setQuery(''); setResults([]); setHasSearched(false); }}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Type Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="w-4 h-4 text-gray-400" />
        {Object.entries(typeIcons).map(([type, Icon]) => (
          <button
            key={type}
            onClick={() => toggleType(type)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              selectedTypes.includes(type)
                ? typeColors[type as keyof typeof typeColors]
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            {type.replace('_', ' ')}
          </button>
        ))}
        {(selectedTypes.length > 0 || query) && (
          <button
            onClick={clearFilters}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Results */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/4 mb-2" />
              <div className="h-3 bg-gray-200 rounded w-3/4" />
            </div>
          ))}
        </div>
      ) : error ? (
        <ErrorDisplay error={error} onRetry={() => performSearch(query)} />
      ) : results.length > 0 ? (
        <div className="space-y-3">
          <div className="text-sm text-gray-500">
            {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
          </div>
          {results.map((result) => {
            const Icon = typeIcons[result.type] || FileText;
            const colorClass = typeColors[result.type] || 'bg-gray-100 text-gray-600';

            return (
              <div
                key={result.id}
                className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => window.location.href = result.url}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorClass}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900">{result.title}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded ${colorClass}`}>
                        {result.type.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-gray-400">
                        {(result.score * 100).toFixed(0)}% match
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{result.description}</p>
                    {result.metadata && Object.keys(result.metadata).length > 0 && (
                      <div className="flex items-center gap-3 mt-2">
                        {Object.entries(result.metadata).slice(0, 3).map(([key, value]) => (
                          <span key={key} className="text-xs text-gray-400">
                            {key}: {String(value)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : hasSearched ? (
        <div className="text-center py-12">
          <SearchIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No results found</h3>
          <p className="text-gray-500 mt-1">Try adjusting your search or filters</p>
        </div>
      ) : null}
    </div>
  );
}
