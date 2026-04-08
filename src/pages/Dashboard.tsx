import { useEffect, useState } from 'react';
import { Users, AlertTriangle, Bell, Calendar, Filter, Activity } from 'lucide-react';
import apiClient from '../lib/api';
import KPICard from '../components/KPICard';
import RiskDonutChart from '../components/RiskDonutChart';
import EarlyWarningCard from '../components/EarlyWarningCard';

interface DashboardStats {
  totalStudents: number;
  highRiskStudents: number;
  newRiskAlerts: number;
  attendanceBreaches: number;
  lowRisk: number;
  mediumRisk: number;
  highRisk: number;
  activeInterventions: number;
  unacknowledgedAlerts: number;
}

interface RecentFlaggedStudent {
  studentId: string;
  studentName: string;
  studentIdNumber: string;
  riskLevel: 'low' | 'medium' | 'high';
  riskScore: number;
  detectedAt: string;
  reason: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalStudents: 0,
    highRiskStudents: 0,
    newRiskAlerts: 0,
    attendanceBreaches: 0,
    lowRisk: 0,
    mediumRisk: 0,
    highRisk: 0,
    activeInterventions: 0,
    unacknowledgedAlerts: 0,
  });
  const [recentFlagged, setRecentFlagged] = useState<RecentFlaggedStudent[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  
  // Filter states
  const [filterDepartment, setFilterDepartment] = useState<string>('all');
  const [filterSemester, setFilterSemester] = useState<string>('all');
  const [filterCourse, setFilterCourse] = useState<string>('all');
  const [departments, setDepartments] = useState<string[]>([]);
  const [riskTrendData, setRiskTrendData] = useState<Array<{ date: string; risk_score: number; risk_level: 'low' | 'medium' | 'high' }>>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [highRiskTrend, setHighRiskTrend] = useState<'up' | 'down' | 'stable' | undefined>(undefined);
  const [highRiskTrendValue, setHighRiskTrendValue] = useState<string | undefined>(undefined);

  useEffect(() => {
    // CRITICAL FIX: Listen for data upload events with polling mechanism
    const handleDataUploaded = (event?: CustomEvent) => {
      console.log('📥 Data upload event received, refreshing dashboard...');
      const uploadResult = event?.detail || null;
      
      // Poll for data availability
      let attempts = 0;
      const maxAttempts = 8;
      const pollInterval = (attempt: number) => Math.min(1000 * (attempt + 1), 5000);
      
      const pollForData = async () => {
        attempts++;
        console.log(`🔄 Dashboard polling attempt ${attempts}/${maxAttempts}...`);
        
        try {
          await loadDashboardData();
          
          if (attempts >= maxAttempts || attempts >= 3) {
            // After 3 successful attempts or max reached, we're done
            console.log('✅ Dashboard data refreshed');
            return;
          }
          
          // Continue polling
          if (attempts < maxAttempts) {
            setTimeout(pollForData, pollInterval(attempts));
          }
        } catch (error) {
          console.error('Error during dashboard polling:', error);
          if (attempts < maxAttempts) {
            setTimeout(pollForData, pollInterval(attempts));
          }
        }
      };
      
      setTimeout(pollForData, 1000);
    };
    
    window.addEventListener('dataUploaded', handleDataUploaded);
    window.addEventListener('dataUploadedWithResult', handleDataUploaded);
    
    return () => {
      window.removeEventListener('dataUploaded', handleDataUploaded);
      window.removeEventListener('dataUploadedWithResult', handleDataUploaded);
    };
  }, []);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(() => {
      loadDashboardData();
    }, 300000); // Refresh every 5 minutes

    return () => clearInterval(interval);
  }, [filterDepartment, filterSemester]);

  async function loadDashboardData() {
    try {
      setLoadError(null);
      const department = filterDepartment !== 'all' ? filterDepartment : undefined;
      const semester = filterSemester !== 'all' ? filterSemester : undefined;

      // Map UI date-range dropdown to a trend lookback window
      const trendDays =
        filterCourse === '7' ? 7 :
        filterCourse === '90' ? 90 :
        filterCourse === 'year' ? 365 :
        30;

      const [overview, trends, alerts] = await Promise.all([
        apiClient.getAnalyticsOverview({ department, semester }),
        apiClient.getRiskTrends({ days: trendDays, department }),
        apiClient.getAlerts({ limit: 10 })
      ]);

      // Departments list for filters
      const deptKeys = Object.keys((overview as any)?.department_breakdown || {});
      setDepartments(deptKeys);

      // Build synthetic "risk score trend" from daily distribution (avoids direct Supabase reads)
      const points = (trends || []).slice(-7).map((t: any) => {
        const low = Number(t.low_risk || 0);
        const medium = Number(t.medium_risk || 0);
        const high = Number(t.high_risk || 0);
        const total = Number(t.total_students || (low + medium + high) || 0);

        // Weighted proxy scores for a readable trend line
        const avg = total > 0 ? ((low * 20) + (medium * 60) + (high * 85)) / total : 0;
        const score = Math.max(0, Math.min(100, avg));
        const level: 'low' | 'medium' | 'high' = score < 35 ? 'low' : score < 70 ? 'medium' : 'high';

        return { date: String(t.date || ''), risk_score: score, risk_level: level };
      });
      setRiskTrendData(points);

      // KPI trend for High-Risk Students:
      // Derive from the last two available trend points (percentage of high risk students).
      try {
        const series = (trends || [])
          .map((t: any) => {
            const low = Number(t.low_risk || 0);
            const medium = Number(t.medium_risk || 0);
            const high = Number(t.high_risk || 0);
            const total = Number(t.total_students || (low + medium + high) || 0);
            const pct = total > 0 ? (high / total) * 100 : 0;
            return { total, pct };
          })
          .filter((x: any) => typeof x.pct === 'number');

        const last = series[series.length - 1];
        const prev = series[series.length - 2];
        if (!last || !prev || last.total <= 0) {
          setHighRiskTrend(undefined);
          setHighRiskTrendValue(undefined);
        } else {
          const diff = last.pct - prev.pct;
          const abs = Math.abs(diff);
          const trend: 'up' | 'down' | 'stable' = abs < 0.1 ? 'stable' : diff > 0 ? 'up' : 'down';
          setHighRiskTrend(trend);
          setHighRiskTrendValue(`${diff >= 0 ? '+' : ''}${diff.toFixed(1)}%`);
        }
      } catch {
        setHighRiskTrend(undefined);
        setHighRiskTrendValue(undefined);
      }

      // New risk alerts proxy: number of high+medium in the last 7 days of the trend series
      const newRiskAlerts = (trends || [])
        .slice(-7)
        .reduce((sum: number, t: any) => sum + Number(t.high_risk || 0) + Number(t.medium_risk || 0), 0);

      // Recently flagged: use backend alerts + fetch latest risk per student (best-effort)
      const recent = (alerts || []).slice(0, 5);
      // PERF: Backend alerts now include student_risk (latest risk score/level) so we avoid N+1 requests.
      const riskByStudent = new Map<string, { level: 'low' | 'medium' | 'high'; score: number }>();
      for (const a of recent) {
        const sid = a?.student_id;
        const sr = a?.student_risk;
        if (sid && sr && sr.risk_level && typeof sr.risk_score === 'number') {
          riskByStudent.set(sid, { level: sr.risk_level, score: sr.risk_score });
        }
      }

      const recentFlaggedStudents: RecentFlaggedStudent[] = recent.map((a: any) => {
        const sid = a.student_id;
        const risk = sid ? riskByStudent.get(sid) : undefined;
        const student = a.student || {};

        return {
          studentId: sid,
          studentName: student.full_name || 'Unknown',
          studentIdNumber: student.student_id || 'N/A',
          riskLevel: (risk?.level || 'medium'),
          riskScore: (risk?.score ?? 0),
          detectedAt: a.created_at || new Date().toISOString(),
          reason: a.message || 'Risk factors detected',
          severity: (a.severity || 'medium') as any
        };
      });

      setStats({
        totalStudents: Number((overview as any)?.total_students || 0),
        highRiskStudents: Number((overview as any)?.high_risk_count || 0),
        newRiskAlerts,
        attendanceBreaches: 0, // derived from attendance_records in Supabase previously; keep 0 until a dedicated backend metric is added
        lowRisk: Number((overview as any)?.low_risk_count || 0),
        mediumRisk: Number((overview as any)?.medium_risk_count || 0),
        highRisk: Number((overview as any)?.high_risk_count || 0),
        activeInterventions: Number((overview as any)?.active_interventions || 0),
        unacknowledgedAlerts: Number((overview as any)?.unacknowledged_alerts || 0),
      });

      setRecentFlagged(recentFlaggedStudents);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // Clear stale UI if backend/db is misconfigured
      setStats({
        totalStudents: 0,
        highRiskStudents: 0,
        newRiskAlerts: 0,
        attendanceBreaches: 0,
        lowRisk: 0,
        mediumRisk: 0,
        highRisk: 0,
        activeInterventions: 0,
        unacknowledgedAlerts: 0,
      });
      setRecentFlagged([]);
      setRiskTrendData([]);
      setDepartments([]);
      setHighRiskTrend(undefined);
      setHighRiskTrendValue(undefined);
      setLoadError((error as any)?.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }

  const atRiskPercentage = stats.totalStudents > 0
    ? ((stats.highRiskStudents / stats.totalStudents) * 100).toFixed(1)
    : '0';

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-slate-200 rounded w-48"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }
  
  if (loadError) {
    return (
      <div className="bg-white rounded-xl border border-red-200 p-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Unable to load dashboard</h2>
            <p className="text-sm text-slate-600 mt-1">{loadError}</p>
            <p className="text-sm text-slate-600 mt-2">
              If this is a new database, run the Supabase migrations first, then upload your dataset.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with filters */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Early Warning Dashboard</h1>
          <p className="text-slate-600 mt-1">
            Real-time monitoring and predictive risk assessment for student success
          </p>
          <div className="flex items-center space-x-2 mt-2 text-xs text-slate-500">
            <Activity className="h-3 w-3" />
            <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center space-x-2 mb-3">
          <Filter className="h-4 w-4 text-slate-500" />
          <span className="text-sm font-medium text-slate-700">Filters</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Department</label>
            <select
              value={filterDepartment}
              onChange={(e) => setFilterDepartment(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            >
              <option value="all">All Departments</option>
              {departments.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Semester</label>
            <select
              value={filterSemester}
              onChange={(e) => setFilterSemester(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            >
              <option value="all">All Semesters</option>
              <option value="Fall 2024">Fall 2024</option>
              <option value="Spring 2024">Spring 2024</option>
              <option value="Summer 2024">Summer 2024</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Date Range</label>
            <select
              value={filterCourse}
              onChange={(e) => setFilterCourse(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            >
              <option value="all">Last 30 Days</option>
              <option value="7">Last 7 Days</option>
              <option value="90">Last 90 Days</option>
              <option value="year">This Academic Year</option>
            </select>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Students Monitored"
          value={stats.totalStudents}
          subtitle="Active enrollment"
          icon={Users}
          iconColor="text-blue-600"
          iconBg="bg-blue-100"
        />
        <KPICard
          title="High-Risk Students"
          value={stats.highRiskStudents}
          subtitle={`${atRiskPercentage}% of total`}
          icon={AlertTriangle}
          iconColor="text-red-600"
          iconBg="bg-red-100"
          // IMPORTANT: Never show a hard-coded hike. Only show trend when there is real data.
          trend={stats.totalStudents > 0 ? highRiskTrend : undefined}
          trendValue={stats.totalStudents > 0 ? highRiskTrendValue : undefined}
        />
        <KPICard
          title="New Risk Alerts"
          value={stats.newRiskAlerts}
          subtitle="Last 7 days"
          icon={Bell}
          iconColor="text-amber-600"
          iconBg="bg-amber-100"
        />
        <KPICard
          title="Attendance Breaches"
          value={stats.attendanceBreaches}
          subtitle="Below threshold"
          icon={Calendar}
          iconColor="text-orange-600"
          iconBg="bg-orange-100"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution & Trends */}
        <div className="lg:col-span-2 space-y-6">
          {/* Risk Distribution Chart */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Risk Distribution</h2>
                <p className="text-sm text-slate-600 mt-1">Current risk level breakdown</p>
              </div>
            </div>
            <div className="flex items-center justify-center py-8">
              <RiskDonutChart
                low={stats.lowRisk}
                medium={stats.mediumRisk}
                high={stats.highRisk}
                total={stats.totalStudents}
                size={240}
              />
            </div>
            <div className="mt-8 pt-6 border-t border-slate-200">
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">{stats.lowRisk}</p>
                  <p className="text-xs font-medium text-slate-600 mt-1">Low Risk</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {stats.totalStudents > 0
                      ? `${((stats.lowRisk / stats.totalStudents) * 100).toFixed(1)}%`
                      : '0%'}
                  </p>
                </div>
                <div className="text-center p-4 bg-amber-50 rounded-lg">
                  <p className="text-2xl font-bold text-amber-600">{stats.mediumRisk}</p>
                  <p className="text-xs font-medium text-slate-600 mt-1">Medium Risk</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {stats.totalStudents > 0
                      ? `${((stats.mediumRisk / stats.totalStudents) * 100).toFixed(1)}%`
                      : '0%'}
                  </p>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <p className="text-2xl font-bold text-red-600">{stats.highRisk}</p>
                  <p className="text-xs font-medium text-slate-600 mt-1">High Risk</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {stats.totalStudents > 0
                      ? `${((stats.highRisk / stats.totalStudents) * 100).toFixed(1)}%`
                      : '0%'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Risk Trend Chart - Using Real Data */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Risk Trend</h2>
                <p className="text-sm text-slate-600 mt-1">Risk changes over time (last 7 assessments)</p>
              </div>
            </div>
            {(() => {
              const recentAssessments = (riskTrendData || []).filter((p) => p.date).slice(-7);

              if (recentAssessments.length < 2) {
                return (
                  <div className="h-48 flex items-center justify-center text-slate-500">
                    <p className="text-sm">Insufficient data for trend analysis. Need at least 2 risk assessments.</p>
                  </div>
                );
              }

              // Calculate aggregate trend
              const firstScore = recentAssessments[0].risk_score;
              const lastScore = recentAssessments[recentAssessments.length - 1].risk_score;
              const trend = lastScore - firstScore;
              const trendPercent = firstScore > 0 ? ((trend / firstScore) * 100).toFixed(1) : '0';

              return (
                <>
                  <div className="h-48 flex items-end justify-between space-x-1">
                    {recentAssessments.map((point: any, index: number) => {
                      const barHeight = Math.max((point.risk_score / 100) * 100, 5);
                      const color = point.risk_level === 'high' ? '#ef4444' : 
                                   point.risk_level === 'medium' ? '#f59e0b' : '#10b981';
                      
                      return (
                        <div key={index} className="flex-1 flex flex-col items-center group relative">
                          <div
                            className="w-full rounded-t transition-all duration-300 hover:opacity-80 cursor-pointer"
                            style={{ height: `${barHeight}%`, backgroundColor: color }}
                            title={`${new Date(point.date).toLocaleDateString()}: ${point.risk_score}/100`}
                          />
                          <span className="text-xs text-slate-500 mt-2">
                            {new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-200">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">
                        Trend: {trend > 0 ? 'Increasing' : trend < 0 ? 'Decreasing' : 'Stable'}
                      </span>
                      <span className={`font-semibold ${trend > 0 ? 'text-red-600' : trend < 0 ? 'text-green-600' : 'text-slate-600'}`}>
                        {trend > 0 ? '+' : ''}{trend.toFixed(1)} points ({trendPercent}%)
                      </span>
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        </div>

        {/* Early Warning Panel */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Recently Flagged</h2>
                <p className="text-sm text-slate-600 mt-1">Early warning detections</p>
              </div>
              <div className="h-8 w-8 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
            </div>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {recentFlagged.length === 0 ? (
                <div className="text-center py-8">
                  <AlertTriangle className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-sm text-slate-500">No recent alerts</p>
                </div>
              ) : (
                recentFlagged.map((student) => (
                  <EarlyWarningCard
                    key={student.studentId}
                    {...student}
                    onClick={() => {
                      // Navigate to student profile
                      window.location.href = `#student-${student.studentId}`;
                    }}
                  />
                ))
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-6 text-white">
            <h3 className="text-lg font-semibold mb-4">System Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-300">Monitoring Status</span>
                <span className="font-medium text-green-400">Active</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-300">At-Risk Rate</span>
                <span className="text-xl font-bold">{atRiskPercentage}%</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-300">Active Interventions</span>
                <span className="font-medium">{stats.activeInterventions}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-300">Pending Alerts</span>
                <span className="font-medium">{stats.unacknowledgedAlerts}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
