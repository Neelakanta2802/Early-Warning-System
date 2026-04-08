import { ReactNode, useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Users,
  AlertTriangle,
  Heart,
  FileText,
  Upload,
  Bell,
  Settings,
  HelpCircle,
  LogOut,
  Menu,
  X,
  GraduationCap,
  BarChart3,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../lib/api';

interface LayoutProps {
  children: ReactNode;
  currentPage: string;
  onNavigate: (page: string) => void;
}

export default function Layout({ children, currentPage, onNavigate }: LayoutProps) {
  const { profile, signOut } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [unreadAlerts, setUnreadAlerts] = useState(0);
  const [showAlertsDropdown, setShowAlertsDropdown] = useState(false);

  useEffect(() => {
    if (profile) {
      loadUnreadAlerts();
      const interval = setInterval(loadUnreadAlerts, 60000); // Check every minute
      return () => clearInterval(interval);
    }
  }, [profile]);

  async function loadUnreadAlerts() {
    try {
      // Use backend API so unread alerts count stays consistent with the rest of the app data.
      const alerts = await apiClient.getAlerts({ acknowledged: false, limit: 1000 });
      setUnreadAlerts(Array.isArray(alerts) ? alerts.length : 0);
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  }

  const navigation = [
    { name: 'Dashboard', icon: LayoutDashboard, page: 'dashboard' },
    { name: 'Students', icon: Users, page: 'students' },
    { name: 'Risk Analysis', icon: AlertTriangle, page: 'risk-analysis' },
    { name: 'Planning & Analytics', icon: BarChart3, page: 'planning-analytics' },
    { name: 'Interventions', icon: Heart, page: 'interventions' },
    { name: 'Reports', icon: FileText, page: 'reports' },
    { name: 'Data Upload', icon: Upload, page: 'data-upload' },
    { name: 'Alerts', icon: Bell, page: 'alerts' },
    { name: 'Settings', icon: Settings, page: 'settings' },
    { name: 'Help', icon: HelpCircle, page: 'help' },
  ];

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="lg:hidden fixed top-0 left-0 right-0 bg-white border-b border-slate-200 z-40">
        <div className="flex items-center justify-between px-4 h-16">
          <div className="flex items-center space-x-3">
            <GraduationCap className="h-6 w-6 text-slate-700" />
            <span className="font-semibold text-slate-900">EWS</span>
          </div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 text-slate-600 hover:text-slate-900"
          >
            {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      <div
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-slate-200 transform transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center space-x-3 px-6 py-4 border-b border-slate-200">
            <div className="h-10 w-10 bg-slate-900 rounded-lg flex items-center justify-center">
              <GraduationCap className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-slate-900">Early Warning</h1>
              <p className="text-xs text-slate-500">Student Success Platform</p>
            </div>
          </div>

          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.page;
              return (
                <button
                  key={item.name}
                  onClick={() => {
                    onNavigate(item.page);
                    setSidebarOpen(false);
                  }}
                  className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </button>
              );
            })}
          </nav>

          <div className="border-t border-slate-200 p-4">
            <div className="flex items-center space-x-3 mb-3">
              <div className="h-10 w-10 bg-slate-200 rounded-full flex items-center justify-center">
                <span className="text-sm font-semibold text-slate-700">
                  {profile?.full_name?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 truncate">
                  {profile?.full_name || 'User'}
                </p>
                <p className="text-xs text-slate-500 capitalize truncate">
                  {profile?.role || 'Role'}
                </p>
              </div>
            </div>
            <button
              onClick={handleSignOut}
              className="w-full flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium text-slate-700 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors"
            >
              <LogOut className="h-4 w-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </div>

      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-slate-900 bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Top Header Bar */}
      <div className="lg:pl-64 pt-16 lg:pt-0">
        <div className="hidden lg:block bg-white border-b border-slate-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h2 className="text-lg font-semibold text-slate-900">
                {navigation.find((n) => n.page === currentPage)?.name || 'Dashboard'}
              </h2>
            </div>
            <div className="flex items-center space-x-4">
              {/* Notification Bell */}
              <div className="relative">
                <button
                  onClick={() => {
                    setShowAlertsDropdown(!showAlertsDropdown);
                    onNavigate('alerts');
                  }}
                  className="relative p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <Bell className="h-5 w-5" />
                  {unreadAlerts > 0 && (
                    <span className="absolute top-0 right-0 h-5 w-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center transform translate-x-1 -translate-y-1">
                      {unreadAlerts > 9 ? '9+' : unreadAlerts}
                    </span>
                  )}
                </button>
              </div>
              <div className="h-8 w-px bg-slate-200"></div>
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <p className="text-sm font-medium text-slate-900">
                    {profile?.full_name || 'User'}
                  </p>
                  <p className="text-xs text-slate-500 capitalize">{profile?.role || 'Role'}</p>
                </div>
                <div className="h-10 w-10 bg-slate-200 rounded-full flex items-center justify-center">
                  <span className="text-sm font-semibold text-slate-700">
                    {profile?.full_name?.charAt(0) || 'U'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        {/* Mobile: reduce padding slightly to maximize content area, keep desktop unchanged */}
        <main className="p-4 sm:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
