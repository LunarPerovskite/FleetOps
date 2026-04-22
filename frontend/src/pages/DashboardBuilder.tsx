import { useState } from 'react';
import { Plus, Trash2, Move, Settings } from 'lucide-react';
import { toast } from '../hooks/useToast';

interface Widget {
  id: string;
  type: 'stats' | 'tasks' | 'agents' | 'approvals' | 'chart' | 'activity';
  title: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

const WIDGET_TYPES = [
  { type: 'stats', title: 'Statistics', w: 4, h: 2 },
  { type: 'tasks', title: 'Recent Tasks', w: 3, h: 3 },
  { type: 'agents', title: 'Active Agents', w: 3, h: 3 },
  { type: 'approvals', title: 'Pending Approvals', w: 2, h: 2 },
  { type: 'chart', title: 'Performance Chart', w: 4, h: 3 },
  { type: 'activity', title: 'Activity Feed', w: 3, h: 4 },
];

export default function DashboardBuilder() {
  const [widgets, setWidgets] = useState<Widget[]>([
    { id: '1', type: 'stats', title: 'Statistics', x: 0, y: 0, w: 4, h: 2 },
    { id: '2', type: 'tasks', title: 'Recent Tasks', x: 4, y: 0, w: 3, h: 3 },
    { id: '3', type: 'agents', title: 'Active Agents', x: 0, y: 2, w: 3, h: 3 },
  ]);
  const [isEditing, setIsEditing] = useState(false);

  const addWidget = (widgetType: typeof WIDGET_TYPES[0]) => {
    const newWidget: Widget = {
      id: `widget_${Date.now()}`,
      type: widgetType.type as Widget['type'],
      title: widgetType.title,
      x: 0,
      y: Math.max(...widgets.map(w => w.y + w.h), 0),
      w: widgetType.w,
      h: widgetType.h,
    };
    setWidgets([...widgets, newWidget]);
    toast.success(`Added ${widgetType.title} widget`);
  };

  const removeWidget = (id: string) => {
    setWidgets(widgets.filter(w => w.id !== id));
    toast.success('Widget removed');
  };

  const renderWidgetContent = (widget: Widget) => {
    switch (widget.type) {
      case 'stats':
        return (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-2xl font-bold text-blue-700">12</p>
              <p className="text-sm text-blue-600">Active Tasks</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <p className="text-2xl font-bold text-green-700">5</p>
              <p className="text-sm text-green-600">Completed</p>
            </div>
          </div>
        );
      case 'tasks':
        return (
          <div className="space-y-2">
            <div className="p-2 bg-gray-50 rounded text-sm">Review Q3 Report</div>
            <div className="p-2 bg-gray-50 rounded text-sm">Update Documentation</div>
            <div className="p-2 bg-gray-50 rounded text-sm">Deploy to Production</div>
          </div>
        );
      case 'agents':
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2 p-2 bg-green-50 rounded">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span className="text-sm">Claude Code</span>
            </div>
            <div className="flex items-center gap-2 p-2 bg-green-50 rounded">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span className="text-sm">GitHub Copilot</span>
            </div>
          </div>
        );
      case 'approvals':
        return (
          <div className="text-center">
            <p className="text-3xl font-bold text-orange-600">3</p>
            <p className="text-sm text-orange-500">Need attention</p>
          </div>
        );
      case 'chart':
        return (
          <div className="h-full flex items-end justify-around gap-2 px-4">
            {[40, 65, 45, 80, 55, 70, 60].map((h, i) => (
              <div key={i} className="flex-1 bg-blue-400 rounded-t" style={{ height: `${h}%` }} />
            ))}
          </div>
        );
      case 'activity':
        return (
          <div className="space-y-2 text-sm">
            <p>Task created by User</p>
            <p>Agent completed review</p>
            <p>Approval granted</p>
            <p>New agent registered</p>
          </div>
        );
      default:
        return <p className="text-gray-400">Widget content</p>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Builder</h1>
        <button
          onClick={() => setIsEditing(!isEditing)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            isEditing
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'border border-gray-200 text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Settings className="w-4 h-4" />
          {isEditing ? 'Done Editing' : 'Edit Dashboard'}
        </button>
      </div>

      {isEditing && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <h3 className="font-medium text-gray-900">Add Widgets</h3>
          <div className="flex flex-wrap gap-2">
            {WIDGET_TYPES.map((type) => (
              <button
                key={type.type}
                onClick={() => addWidget(type)}
                className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm hover:border-blue-300 transition-colors"
              >
                <Plus className="w-4 h-4 text-blue-600" />
                {type.title}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Grid Layout - Simple CSS Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 auto-rows-min">
        {widgets.map((widget) => (
          <div
            key={widget.id}
            className={`bg-white rounded-xl border border-gray-200 p-4 relative group ${
              isEditing ? 'ring-2 ring-blue-100' : ''
            }`}
            style={{
              gridColumn: `span ${Math.min(widget.w, 6)}`,
              minHeight: `${widget.h * 80}px`,
            }}
          >
            {isEditing && (
              <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="p-1 bg-gray-100 rounded hover:bg-gray-200">
                  <Move className="w-4 h-4 text-gray-600" />
                </button>
                <button
                  onClick={() => removeWidget(widget.id)}
                  className="p-1 bg-red-50 rounded hover:bg-red-100"
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </button>
              </div>
            )}
            
            <h3 className="font-medium text-gray-900 mb-3">{widget.title}</h3>
            <div className="h-full">
              {renderWidgetContent(widget)}
            </div>
          </div>
        ))}
      </div>

      {widgets.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-xl">
          <p className="text-gray-500 mb-2">Your dashboard is empty</p>
          <button
            onClick={() => setIsEditing(true)}
            className="text-blue-600 hover:text-blue-700"
          >
            Start adding widgets
          </button>
        </div>
      )}

      {isEditing && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
          <p className="font-medium">Note:</p>
          <p>For drag-and-drop functionality, install react-grid-layout:</p>
          <code className="block mt-2 p-2 bg-gray-800 text-white rounded">npm install react-grid-layout</code>
        </div>
      )}
    </div>
  );
}
