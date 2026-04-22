import { useState } from 'react';
import { useTheme } from '../hooks/useTheme';
import { toast } from '../hooks/useToast';
import { 
  Moon, 
  Sun, 
  Globe, 
  Bell, 
  Shield, 
  Key,
  Save
} from 'lucide-react';

export default function Settings() {
  const { isDark, toggleTheme } = useTheme();
  const [language, setLanguage] = useState('en');
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    slack: false,
  });

  const handleSave = () => {
    localStorage.setItem('fleetops_language', language);
    localStorage.setItem('fleetops_notifications', JSON.stringify(notifications));
    toast.success('Settings saved');
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {/* Appearance */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          {isDark ? <Moon className="w-5 h-5 text-gray-600" /> : <Sun className="w-5 h-5 text-gray-600" />}
          <h2 className="text-lg font-semibold text-gray-900">Appearance</h2>
        </div>
        
        <div className="flex items-center justify-between py-3">
          <div>
            <p className="font-medium text-gray-900">Dark Mode</p>
            <p className="text-sm text-gray-500">Switch between light and dark themes</p>
          </div>
          <button
            onClick={toggleTheme}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              isDark ? 'bg-blue-600' : 'bg-gray-200'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                isDark ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Language */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Globe className="w-5 h-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">Language</h2>
        </div>
        
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="en">English</option>
          <option value="es">Español</option>
        </select>
        
        <p className="text-sm text-gray-500 mt-2">
          Note: Full Spanish translation coming soon. Currently UI elements only.
        </p>
      </div>

      {/* Notifications */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Bell className="w-5 h-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">Notifications</h2>
        </div>
        
        <div className="space-y-3">
          {Object.entries(notifications).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium text-gray-900 capitalize">{key} Notifications</p>
                <p className="text-sm text-gray-500">Receive notifications via {key}</p>
              </div>
              <button
                onClick={() => setNotifications(prev => ({ ...prev, [key]: !value }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  value ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    value ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Security */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="w-5 h-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">Security</h2>
        </div>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium text-gray-900">Two-Factor Authentication</p>
              <p className="text-sm text-gray-500">Add an extra layer of security</p>
            </div>
            <button className="px-4 py-2 border border-gray-200 rounded-lg text-sm hover:bg-gray-50 transition-colors">
              Enable
            </button>
          </div>
          
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium text-gray-900">API Keys</p>
              <p className="text-sm text-gray-500">Manage your API access</p>
            </div>
            <button className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm hover:bg-gray-50 transition-colors">
              <Key className="w-4 h-4" />
              Manage
            </button>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Save className="w-4 h-4" />
          Save Changes
        </button>
      </div>
    </div>
  );
}
