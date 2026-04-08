import { useEffect, useState } from 'react';
import { Bell, Check, AlertCircle, Filter, Clock, Activity } from 'lucide-react';
import apiClient from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import type { Database } from '../types/database';

type Alert = Database['public']['Tables']['alerts']['Row'];

interface AlertWithStudent extends Alert {
  student: {
    full_name: string;
    student_id: string;
  };
}

export default function AlertsPage() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<AlertWithStudent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unacknowledged' | 'critical' | 'high'>('unacknowledged');
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(() => {
      loadAlerts();
    }, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [filter]);

  async function loadAlerts() {
    try {
      const params: any = { limit: 200 };
      if (filter === 'unacknowledged') params.acknowledged = false;
      if (filter === 'critical') params.severity = 'critical';
      if (filter === 'high') params.severity = 'high';

      const data = await apiClient.getAlerts(params);
      setAlerts((data as AlertWithStudent[]) || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error loading alerts:', error);
    } finally {
      setLoading(false);
    }
  }

  async function acknowledgeAlert(alertId: string) {
    try {
      await apiClient.acknowledgeAlert(alertId, user?.id || 'system');
      loadAlerts();
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-red-300 bg-red-50';
      case 'high':
        return 'border-amber-300 bg-amber-50';
      case 'medium':
        return 'border-blue-300 bg-blue-50';
      default:
        return 'border-slate-300 bg-slate-50';
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-700 border-red-300';
      case 'high':
        return 'bg-amber-100 text-amber-700 border-amber-300';
      case 'medium':
        return 'bg-blue-100 text-blue-700 border-blue-300';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-300';
    }
  };

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return '1 day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const criticalCount = alerts.filter((a) => a.severity === 'critical' && !a.acknowledged).length;
  const highCount = alerts.filter((a) => a.severity === 'high' && !a.acknowledged).length;
  const unacknowledgedCount = alerts.filter((a) => !a.acknowledged).length;

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-slate-200 rounded w-48"></div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Early Warning Alerts</h1>
          <p className="text-slate-600 mt-1">
            Real-time notifications for at-risk students requiring immediate attention
          </p>
          <div className="flex items-center space-x-2 mt-2 text-xs text-slate-500">
            <Activity className="h-3 w-3" />
            <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      {/* Alert Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-700">Critical Alerts</p>
              <p className="text-2xl font-bold text-red-900">{criticalCount}</p>
            </div>
            <AlertCircle className="h-8 w-8 text-red-600" />
          </div>
        </div>
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-amber-700">High Priority</p>
              <p className="text-2xl font-bold text-amber-900">{highCount}</p>
            </div>
            <AlertCircle className="h-8 w-8 text-amber-600" />
          </div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-700">Unacknowledged</p>
              <p className="text-2xl font-bold text-blue-900">{unacknowledgedCount}</p>
            </div>
            <Bell className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-700">Total Alerts</p>
              <p className="text-2xl font-bold text-slate-900">{alerts.length}</p>
            </div>
            <Bell className="h-8 w-8 text-slate-600" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center space-x-2 mb-3">
          <Filter className="h-4 w-4 text-slate-500" />
          <span className="text-sm font-medium text-slate-700">Filter Alerts</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setFilter('unacknowledged')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'unacknowledged'
                ? 'bg-slate-900 text-white'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            Unacknowledged
          </button>
          <button
            onClick={() => setFilter('critical')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'critical'
                ? 'bg-red-600 text-white'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            Critical
          </button>
          <button
            onClick={() => setFilter('high')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'high'
                ? 'bg-amber-600 text-white'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            High Priority
          </button>
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'all'
                ? 'bg-slate-900 text-white'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            All Alerts
          </button>
        </div>
      </div>

      {/* Alerts List */}
      {alerts.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <Bell className="h-16 w-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No Alerts</h3>
          <p className="text-slate-500">
            {filter === 'unacknowledged'
              ? 'All alerts have been acknowledged. Great work!'
              : 'No alerts match the current filter.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`border-2 rounded-xl p-6 transition-all hover:shadow-lg ${
                getSeverityColor(alert.severity)
              } ${!alert.acknowledged ? 'ring-2 ring-offset-2 ring-slate-400' : ''}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="flex-shrink-0">
                    <div className={`h-12 w-12 rounded-lg flex items-center justify-center ${
                      alert.severity === 'critical' ? 'bg-red-200' :
                      alert.severity === 'high' ? 'bg-amber-200' : 'bg-blue-200'
                    }`}>
                      <AlertCircle className={`h-6 w-6 ${
                        alert.severity === 'critical' ? 'text-red-700' :
                        alert.severity === 'high' ? 'text-amber-700' : 'text-blue-700'
                      }`} />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className={`px-3 py-1 text-xs font-bold uppercase rounded border ${getSeverityBadge(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      <span className="text-sm font-semibold text-slate-700 capitalize">
                        {alert.alert_type.replace(/_/g, ' ')}
                      </span>
                      {!alert.acknowledged && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-red-500 text-white rounded">
                          NEW
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg font-bold text-slate-900 mb-1">
                      {alert.student.full_name} ({alert.student.student_id})
                    </h3>
                    <p className="text-slate-700 mb-3">{alert.message}</p>
                    <div className="flex items-center space-x-4 text-sm text-slate-500">
                      <div className="flex items-center space-x-1">
                        <Clock className="h-4 w-4" />
                        <span>Detected {getTimeAgo(alert.created_at)}</span>
                      </div>
                      <span>•</span>
                      <span>{new Date(alert.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
                {!alert.acknowledged && (
                  <button
                    onClick={() => acknowledgeAlert(alert.id)}
                    className="flex items-center space-x-2 px-4 py-2 bg-white text-slate-900 font-medium rounded-lg hover:bg-slate-50 transition-colors border-2 border-slate-300 shadow-sm"
                  >
                    <Check className="h-4 w-4" />
                    <span>Acknowledge</span>
                  </button>
                )}
              </div>
              {alert.acknowledged && (
                <div className="mt-4 pt-4 border-t border-slate-200">
                  <div className="flex items-center space-x-2 text-sm text-slate-600">
                    <Check className="h-4 w-4 text-green-600" />
                    <span>Acknowledged on {new Date(alert.acknowledged_at!).toLocaleString()}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
