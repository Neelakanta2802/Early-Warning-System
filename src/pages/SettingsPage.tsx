import { Settings, Bell, Shield, Users, Database } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function SettingsPage() {
  const { profile } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-600 mt-1">Manage your account and system preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
              <Users className="h-5 w-5 mr-2 text-slate-600" />
              Profile Information
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Full Name</label>
                <input
                  type="text"
                  defaultValue={profile?.full_name}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
                <input
                  type="email"
                  defaultValue={profile?.email}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                  disabled
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Role</label>
                <input
                  type="text"
                  defaultValue={profile?.role}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent capitalize"
                  disabled
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Department</label>
                <input
                  type="text"
                  defaultValue={profile?.department || 'Not specified'}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                />
              </div>
              <button className="px-6 py-2 bg-slate-900 text-white font-medium rounded-lg hover:bg-slate-800 transition-colors">
                Save Changes
              </button>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
              <Bell className="h-5 w-5 mr-2 text-slate-600" />
              Notification Preferences
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">High Risk Alerts</p>
                  <p className="text-sm text-slate-600">
                    Receive notifications when students are marked as high risk
                  </p>
                </div>
                <label className="relative inline-block w-12 h-6">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-12 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-6 after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-900"></div>
                </label>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">Attendance Drops</p>
                  <p className="text-sm text-slate-600">
                    Alert when student attendance falls below threshold
                  </p>
                </div>
                <label className="relative inline-block w-12 h-6">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-12 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-6 after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-900"></div>
                </label>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">Performance Decline</p>
                  <p className="text-sm text-slate-600">
                    Notify about significant drops in academic performance
                  </p>
                </div>
                <label className="relative inline-block w-12 h-6">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-12 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-6 after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-900"></div>
                </label>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">Weekly Summary</p>
                  <p className="text-sm text-slate-600">Receive weekly summary of key metrics</p>
                </div>
                <label className="relative inline-block w-12 h-6">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-12 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-6 after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-900"></div>
                </label>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
              <Database className="h-5 w-5 mr-2 text-slate-600" />
              Risk Assessment Configuration
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  High Risk Threshold
                </label>
                <div className="flex items-center space-x-4">
                  <input
                    type="range"
                    min="60"
                    max="100"
                    defaultValue="75"
                    className="flex-1"
                  />
                  <span className="text-sm font-semibold text-slate-900 w-12">75</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Students with risk scores above this value are marked as high risk
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Medium Risk Threshold
                </label>
                <div className="flex items-center space-x-4">
                  <input
                    type="range"
                    min="30"
                    max="70"
                    defaultValue="50"
                    className="flex-1"
                  />
                  <span className="text-sm font-semibold text-slate-900 w-12">50</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Scores between medium and high thresholds are medium risk
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Attendance Alert Threshold
                </label>
                <div className="flex items-center space-x-4">
                  <input
                    type="range"
                    min="50"
                    max="90"
                    defaultValue="75"
                    className="flex-1"
                  />
                  <span className="text-sm font-semibold text-slate-900 w-12">75%</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Alert when attendance falls below this percentage
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="font-semibold text-slate-900 mb-4 flex items-center">
              <Shield className="h-5 w-5 mr-2 text-slate-600" />
              Security
            </h3>
            <div className="space-y-3">
              <button className="w-full px-4 py-2 bg-slate-100 text-slate-900 font-medium rounded-lg hover:bg-slate-200 transition-colors text-sm">
                Change Password
              </button>
              <button className="w-full px-4 py-2 bg-slate-100 text-slate-900 font-medium rounded-lg hover:bg-slate-200 transition-colors text-sm">
                Two-Factor Authentication
              </button>
              <button className="w-full px-4 py-2 bg-slate-100 text-slate-900 font-medium rounded-lg hover:bg-slate-200 transition-colors text-sm">
                Active Sessions
              </button>
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-6 text-white">
            <h3 className="font-semibold mb-3 flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              System Status
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-300">Last Data Sync</span>
                <span className="font-medium">2 hours ago</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-300">Database Status</span>
                <span className="font-medium text-green-400">Healthy</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-300">Risk Model Version</span>
                <span className="font-medium">v2.1.4</span>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 rounded-xl border border-blue-100 p-6">
            <h3 className="font-semibold text-slate-900 mb-2">Academic Calendar</h3>
            <p className="text-sm text-slate-600 mb-4">
              Configure semester dates and academic year settings
            </p>
            <button className="w-full px-4 py-2 bg-white text-slate-900 font-medium rounded-lg hover:bg-slate-50 transition-colors border border-slate-200 text-sm">
              Manage Calendar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
