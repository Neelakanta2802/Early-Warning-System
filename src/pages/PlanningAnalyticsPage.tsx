import { useEffect, useState } from 'react';
import { TrendingUp, BarChart3, Map, Users, Target, Activity } from 'lucide-react';
import apiClient from '../lib/api';

interface DepartmentRisk {
  department: string;
  total: number;
  lowRisk: number;
  mediumRisk: number;
  highRisk: number;
  atRiskPercentage: number;
}

interface ResourcePlanning {
  department: string;
  highRiskCount: number;
  recommendedCounselors: number;
  estimatedHours: number;
}

export default function PlanningAnalyticsPage() {
  const [departmentRisks, setDepartmentRisks] = useState<DepartmentRisk[]>([]);
  const [resourcePlanning, setResourcePlanning] = useState<ResourcePlanning[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    loadPlanningData();
    const interval = setInterval(() => {
      loadPlanningData();
    }, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, []);

  async function loadPlanningData() {
    try {
      const distribution: any = await apiClient.getDepartmentAnalytics();
      const deptArray: DepartmentRisk[] = Object.entries(distribution || {}).map(([dept, stats]: any) => {
        const total = Number(stats.total || 0);
        const lowRisk = Number(stats.low || 0);
        const mediumRisk = Number(stats.medium || 0);
        const highRisk = Number(stats.high || 0);
        const atRiskPercentage = total > 0 ? ((mediumRisk + highRisk) / total) * 100 : 0;
        return {
          department: String(dept),
          total,
          lowRisk,
          mediumRisk,
          highRisk,
          atRiskPercentage
        };
      }).sort((a, b) => b.atRiskPercentage - a.atRiskPercentage);

      setDepartmentRisks(deptArray);

      // Calculate resource planning
      const resourceData: ResourcePlanning[] = deptArray.map((dept) => ({
        department: dept.department,
        highRiskCount: dept.highRisk,
        recommendedCounselors: Math.ceil(dept.highRisk / 10), // 1 counselor per 10 high-risk students
        estimatedHours: dept.highRisk * 2 + dept.mediumRisk * 1, // 2 hours per high-risk, 1 per medium
      }));

      setResourcePlanning(resourceData);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error loading planning data:', error);
    } finally {
      setLoading(false);
    }
  }


  const totalAtRisk = departmentRisks.reduce((sum, d) => sum + d.mediumRisk + d.highRisk, 0);
  const totalStudents = departmentRisks.reduce((sum, d) => sum + d.total, 0);
  const overallAtRiskPercentage = totalStudents > 0 ? (totalAtRisk / totalStudents) * 100 : 0;

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
          <h1 className="text-3xl font-bold text-slate-900">Educational Planning & Analytics</h1>
          <p className="text-slate-600 mt-1">
            Aggregate risk analysis and resource planning for institutional decision-making
          </p>
          <div className="flex items-center space-x-2 mt-2 text-xs text-slate-500">
            <Activity className="h-3 w-3" />
            <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <p className="text-sm font-medium text-slate-600 mb-1">Total Students</p>
          <p className="text-3xl font-bold text-slate-900">{totalStudents}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="h-12 w-12 bg-red-100 rounded-lg flex items-center justify-center">
              <Target className="h-6 w-6 text-red-600" />
            </div>
          </div>
          <p className="text-sm font-medium text-slate-600 mb-1">At-Risk Students</p>
          <p className="text-3xl font-bold text-red-600">{totalAtRisk}</p>
          <p className="text-xs text-slate-500 mt-1">{overallAtRiskPercentage.toFixed(1)}% of total</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="h-12 w-12 bg-amber-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="h-6 w-6 text-amber-600" />
            </div>
          </div>
          <p className="text-sm font-medium text-slate-600 mb-1">Departments Monitored</p>
          <p className="text-3xl font-bold text-slate-900">{departmentRisks.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="h-6 w-6 text-green-600" />
            </div>
          </div>
          <p className="text-sm font-medium text-slate-600 mb-1">Avg. Risk Rate</p>
          <p className="text-3xl font-bold text-slate-900">{overallAtRiskPercentage.toFixed(1)}%</p>
        </div>
      </div>

      {/* Risk Heatmap by Department */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center space-x-2 mb-6">
          <Map className="h-5 w-5 text-slate-600" />
          <h2 className="text-xl font-semibold text-slate-900">Risk Concentration Heatmap</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {departmentRisks.map((dept) => (
            <div
              key={dept.department}
              className="border-2 rounded-lg p-4 hover:shadow-md transition-shadow"
              style={{
                borderColor: dept.atRiskPercentage >= 30 ? '#ef4444' :
                             dept.atRiskPercentage >= 15 ? '#f59e0b' : '#10b981',
              }}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-slate-900">{dept.department}</h3>
                <span className={`px-2 py-1 text-xs font-bold rounded ${
                  dept.atRiskPercentage >= 30 ? 'bg-red-100 text-red-700' :
                  dept.atRiskPercentage >= 15 ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
                }`}>
                  {dept.atRiskPercentage.toFixed(1)}%
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">Total Students</span>
                  <span className="font-medium text-slate-900">{dept.total}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-green-600">Low Risk</span>
                  <span className="font-medium">{dept.lowRisk}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-amber-600">Medium Risk</span>
                  <span className="font-medium">{dept.mediumRisk}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-red-600">High Risk</span>
                  <span className="font-medium">{dept.highRisk}</span>
                </div>
                <div className="mt-3 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full flex">
                    <div
                      className="bg-green-500"
                      style={{ width: `${(dept.lowRisk / dept.total) * 100}%` }}
                    />
                    <div
                      className="bg-amber-500"
                      style={{ width: `${(dept.mediumRisk / dept.total) * 100}%` }}
                    />
                    <div
                      className="bg-red-500"
                      style={{ width: `${(dept.highRisk / dept.total) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resource Planning */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center space-x-2 mb-6">
          <Target className="h-5 w-5 text-slate-600" />
          <h2 className="text-xl font-semibold text-slate-900">Resource Planning Indicators</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">Department</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">High-Risk Count</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">Recommended Counselors</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">Estimated Hours/Week</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase">Priority</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {resourcePlanning.map((resource) => (
                <tr key={resource.department} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-medium text-slate-900">{resource.department}</td>
                  <td className="px-6 py-4">
                    <span className="text-lg font-bold text-red-600">{resource.highRiskCount}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-medium text-slate-900">{resource.recommendedCounselors}</span>
                    <span className="text-sm text-slate-500 ml-1">counselors</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-medium text-slate-900">{resource.estimatedHours}</span>
                    <span className="text-sm text-slate-500 ml-1">hours</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                      resource.highRiskCount >= 20 ? 'bg-red-100 text-red-700' :
                      resource.highRiskCount >= 10 ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
                    }`}>
                      {resource.highRiskCount >= 20 ? 'High' :
                       resource.highRiskCount >= 10 ? 'Medium' : 'Low'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Trend Insights */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-8 text-white">
        <h2 className="text-2xl font-bold mb-6">Planning Insights</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="font-semibold mb-3 text-lg">Risk Trends</h3>
            <p className="text-slate-300 text-sm mb-2">
              Overall at-risk rate: <span className="font-bold text-white">{overallAtRiskPercentage.toFixed(1)}%</span>
            </p>
            <p className="text-slate-300 text-sm">
              {overallAtRiskPercentage > 20
                ? '⚠️ Above institutional target. Consider increasing support resources.'
                : overallAtRiskPercentage > 15
                ? '⚠️ Approaching threshold. Monitor closely.'
                : '✓ Within acceptable range. Maintain current support levels.'}
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-3 text-lg">Resource Allocation</h3>
            <p className="text-slate-300 text-sm mb-2">
              Total estimated hours needed: <span className="font-bold text-white">
                {resourcePlanning.reduce((sum, r) => sum + r.estimatedHours, 0)} hours/week
              </span>
            </p>
            <p className="text-slate-300 text-sm">
              Recommended counselors: <span className="font-bold text-white">
                {resourcePlanning.reduce((sum, r) => sum + r.recommendedCounselors, 0)}
              </span>
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-3 text-lg">Department Priorities</h3>
            <p className="text-slate-300 text-sm">
              {departmentRisks.length > 0 && (
                <>
                  Highest risk: <span className="font-bold text-white">{departmentRisks[0].department}</span>
                  <br />
                  ({departmentRisks[0].atRiskPercentage.toFixed(1)}% at-risk)
                </>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

