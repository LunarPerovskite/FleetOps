import { useState, useEffect } from 'react';
import { hierarchyAPI } from '../lib/api';
import { Loading, SkeletonCard } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { toast } from '../hooks/useToast';
import { Users, Bot, ChevronUp, ChevronDown, Plus, Save } from 'lucide-react';

interface HierarchyLevel {
  id: string;
  name: string;
  order: number;
  color: string;
  permissions: string[];
}

interface HierarchyScale {
  id: string;
  name: string;
  type: 'human' | 'agent';
  levels: HierarchyLevel[];
}

export default function Hierarchy() {
  const [activeTab, setActiveTab] = useState<'human' | 'agent'>('human');
  const [scales, setScales] = useState<HierarchyScale[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<HierarchyScale | null>(null);

  useEffect(() => {
    fetchHierarchy();
  }, []);

  const fetchHierarchy = async () => {
    try {
      setLoading(true);
      const response = await hierarchyAPI.get();
      setScales(response?.scales || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load hierarchy');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (scale: HierarchyScale) => {
    try {
      await hierarchyAPI.update({ scales: [scale] });
      toast.success('Hierarchy updated');
      setEditing(null);
      fetchHierarchy();
    } catch (err: any) {
      toast.error('Failed to update');
    }
  };

  const moveLevel = (scaleId: string, levelId: string, direction: 'up' | 'down') => {
    setScales(prev => prev.map(scale => {
      if (scale.id !== scaleId) return scale;
      
      const levels = [...scale.levels];
      const index = levels.findIndex(l => l.id === levelId);
      if (index === -1) return scale;
      
      const newIndex = direction === 'up' ? index - 1 : index + 1;
      if (newIndex < 0 || newIndex >= levels.length) return scale;
      
      [levels[index], levels[newIndex]] = [levels[newIndex], levels[index]];
      
      // Update order numbers
      levels.forEach((l, i) => { l.order = i + 1; });
      
      return { ...scale, levels };
    }));
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchHierarchy} />;
  }

  const filteredScales = scales.filter(s => s.type === activeTab);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Hierarchy</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('human')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'human'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Users className="w-4 h-4" />
            Human
          </button>
          <button
            onClick={() => setActiveTab('agent')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'agent'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Bot className="w-4 h-4" />
            Agent
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {filteredScales.map((scale) => (
          <div key={scale.id} className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">{scale.name}</h2>
              <button
                onClick={() => setEditing(editing?.id === scale.id ? null : scale)}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                {editing?.id === scale.id ? 'Done' : 'Edit'}
              </button>
            </div>

            <div className="space-y-3">
              {scale.levels.map((level, index) => (
                <div
                  key={level.id}
                  className="flex items-center gap-4 p-3 rounded-lg border border-gray-100"
                  style={{ borderLeftWidth: '4px', borderLeftColor: level.color }}
                >
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm"
                    style={{ backgroundColor: level.color }}
                  >
                    {level.order}
                  </div>
                  
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{level.name}</p>
                    <p className="text-sm text-gray-500">{level.permissions.join(', ')}</p>
                  </div>

                  {editing?.id === scale.id && (
                    <div className="flex gap-1">
                      <button
                        onClick={() => moveLevel(scale.id, level.id, 'up')}
                        disabled={index === 0}
                        className="p-1 hover:bg-gray-100 rounded disabled:opacity-30"
                      >
                        <ChevronUp className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => moveLevel(scale.id, level.id, 'down')}
                        disabled={index === scale.levels.length - 1}
                        className="p-1 hover:bg-gray-100 rounded disabled:opacity-30"
                      >
                        <ChevronDown className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {editing?.id === scale.id && (
              <div className="mt-4 flex justify-end">
                <button
                  onClick={() => handleUpdate(scale)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Save className="w-4 h-4" />
                  Save Changes
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Tip:</strong> Use the hierarchy to define approval ladders. 
          Higher levels can approve more critical tasks.
        </p>
      </div>
    </div>
  );
}
