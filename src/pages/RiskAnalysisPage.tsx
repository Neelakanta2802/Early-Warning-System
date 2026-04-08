import { useEffect, useState } from 'react';
import { TrendingUp, AlertTriangle, Users } from 'lucide-react';
import apiClient from '../lib/api';

interface DepartmentRisk {
  department: string;
  total: number;
  lowRisk: number;
  mediumRisk: number;
  highRisk: number;
}

export default function RiskAnalysisPage() {
  const [departmentRisks, setDepartmentRisks] = useState<DepartmentRisk[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRiskAnalysis();
  }, []);

  async function loadRiskAnalysis() {
    try {
      const distribution: any = await apiClient.getDepartmentAnalytics();
      const deptArray: DepartmentRisk[] = Object.entries(distribution || {}).map(([dept, stats]: any) => ({
        department: String(dept),
        total: Number(stats.total || 0),
        lowRisk: Number(stats.low || 0),
        mediumRisk: Number(stats.medium || 0),
        highRisk: Number(stats.high || 0),
      }));
      setDepartmentRisks(deptArray.sort((a, b) => b.total - a.total));
    } catch (error) {
      console.error('Error loading risk analysis:', error);
    } finally {
      setLoading(false);
    }
  }

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
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Risk Analysis</h1>
        <p className="text-slate-600 mt-1">Comprehensive risk assessment and trends across departments</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
          </div>
          <h3 className="text-sm font-medium text-slate-600 mb-2">Low Risk Students</h3>
          <p className="text-3xl font-bold text-green-600">
            {departmentRisks.reduce((sum, d) => sum + d.lowRisk, 0)}
          </p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="h-12 w-12 bg-amber-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="h-6 w-6 text-amber-600" />
            </div>
          </div>
          <h3 className="text-sm font-medium text-slate-600 mb-2">Medium Risk Students</h3>
          <p className="text-3xl font-bold text-amber-600">
            {departmentRisks.reduce((sum, d) => sum + d.mediumRisk, 0)}
          </p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="h-12 w-12 bg-red-100 rounded-lg flex items-center justify-center">
              <Users className="h-6 w-6 text-red-600" />
            </div>
          </div>
          <h3 className="text-sm font-medium text-slate-600 mb-2">High Risk Students</h3>
          <p className="text-3xl font-bold text-red-600">
            {departmentRisks.reduce((sum, d) => sum + d.highRisk, 0)}
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-6">Department Risk Distribution</h2>
        <div className="space-y-6">
          {departmentRisks.map((dept) => {
            const atRiskPercentage =
              dept.total > 0 ? (((dept.mediumRisk + dept.highRisk) / dept.total) * 100).toFixed(1) : '0';

            return (
              <div key={dept.department}>
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-slate-900">{dept.department}</h3>
                    <p className="text-sm text-slate-600">
                      {dept.total} students • {atRiskPercentage}% at-risk
                    </p>
                  </div>
                  <div className="flex items-center space-x-4 text-sm">
                    <div className="text-center">
                      <p className="font-bold text-green-600">{dept.lowRisk}</p>
                      <p className="text-xs text-slate-500">Low</p>
                    </div>
                    <div className="text-center">
                      <p className="font-bold text-amber-600">{dept.mediumRisk}</p>
                      <p className="text-xs text-slate-500">Medium</p>
                    </div>
                    <div className="text-center">
                      <p className="font-bold text-red-600">{dept.highRisk}</p>
                      <p className="text-xs text-slate-500">High</p>
                    </div>
                  </div>
                </div>
                <div className="h-4 bg-slate-100 rounded-full overflow-hidden flex">
                  <div
                    className="bg-green-500 h-full"
                    style={{ width: `${(dept.lowRisk / dept.total) * 100}%` }}
                  />
                  <div
                    className="bg-amber-500 h-full"
                    style={{ width: `${(dept.mediumRisk / dept.total) * 100}%` }}
                  />
                  <div
                    className="bg-red-500 h-full"
                    style={{ width: `${(dept.highRisk / dept.total) * 100}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-8 text-white">
        <h2 className="text-xl font-bold mb-4">Risk Assessment Methodology</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
          <div>
            <h3 className="font-semibold mb-2">Academic Performance</h3>
            <p className="text-slate-300 text-sm">
              GPA trends, course completion rates, and grade patterns are analyzed to identify academic struggles.
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Attendance Patterns</h3>
            <p className="text-slate-300 text-sm">
              Attendance records and absence trends are monitored to detect early warning signs of disengagement.
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Behavioral Indicators</h3>
            <p className="text-slate-300 text-sm">
              Historical data and behavioral patterns help predict students who may need additional support.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
