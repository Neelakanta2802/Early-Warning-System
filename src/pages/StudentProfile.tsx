import { useEffect, useState } from 'react';
import { ArrowLeft, Mail, Calendar, AlertTriangle, TrendingDown, BookOpen, FileText, Clock, Activity, Info, Target } from 'lucide-react';
import apiClient from '../lib/api';
import RiskBadge from '../components/RiskBadge';
import TrendIndicator from '../components/TrendIndicator';
import TopFactorsChart from '../components/TopFactorsChart';
import ConfidenceIndicator from '../components/ConfidenceIndicator';
import RiskTrendChart from '../components/RiskTrendChart';
import type { Database } from '../types/database';

type Student = Database['public']['Tables']['students']['Row'];
type RiskAssessment = Database['public']['Tables']['risk_assessments']['Row'];
type AcademicRecord = Database['public']['Tables']['academic_records']['Row'];
type AttendanceRecord = Database['public']['Tables']['attendance_records']['Row'];
type Alert = Database['public']['Tables']['alerts']['Row'];
type Intervention = Database['public']['Tables']['interventions']['Row'];

interface StudentProfileProps {
  studentId: string;
  onBack: () => void;
}

export default function StudentProfile({ studentId, onBack }: StudentProfileProps) {
  const [student, setStudent] = useState<Student | null>(null);
  const [risk, setRisk] = useState<RiskAssessment | null>(null);
  const [riskHistory, setRiskHistory] = useState<RiskAssessment[]>([]);
  const [academicRecords, setAcademicRecords] = useState<AcademicRecord[]>([]);
  const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastMonitored, setLastMonitored] = useState<Date>(new Date());
  
  // ML features from backend API
  const [riskExplanation, setRiskExplanation] = useState<any>(null);
  const [riskTrend, setRiskTrend] = useState<any>(null);

  useEffect(() => {
    loadStudentData();
    const interval = setInterval(() => {
      loadStudentData();
    }, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, [studentId]);

  async function loadStudentData() {
    try {
      // Load core profile data from backend API (service-role DB access)
      const profile: any = await apiClient.getStudent(studentId);

      setStudent(profile?.student || null);
      setRisk(profile?.latest_risk || null);
      setRiskHistory(profile?.risk_history || []);
      setAcademicRecords(profile?.academic_records || []);
      setAttendanceRecords((profile?.attendance_records || []).slice(0, 30));
      setAlerts(profile?.alerts || []);
      setInterventions(profile?.interventions || []);
      
      // Load ML features from backend API (with fallback)
      try {
        const riskData: any = await apiClient.getStudentRisk(studentId, {
          include_trend: true,
          include_explanation: true
        });
        setRiskExplanation(riskData?.explanation || null);
        setRiskTrend(riskData?.trend || null);
      } catch (apiErr) {
        console.warn('Backend API unavailable, using basic explanations:', apiErr);
        // Fallback to basic explanation
        setRiskExplanation(null);
        setRiskTrend(null);
      }
      
      setLastMonitored(new Date());
    } catch (error) {
      console.error('Error loading student data:', error);
    } finally {
      setLoading(false);
    }
  }

  const safeStr = (v: any) => (v === null || v === undefined ? '' : String(v));
  const safeDate = (v: any): Date | null => {
    try {
      const d = new Date(v);
      return Number.isFinite(d.getTime()) ? d : null;
    } catch {
      return null;
    }
  };
  const fmtDate = (v: any) => safeDate(v)?.toLocaleDateString() || '—';
  const fmtTime = (v: any) => safeDate(v)?.toLocaleTimeString() || '';

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-slate-200 rounded w-48"></div>
        <div className="h-64 bg-slate-200 rounded-xl"></div>
      </div>
    );
  }

  if (!student) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">Student not found</p>
        <button onClick={onBack} className="mt-4 text-sm text-slate-900 hover:underline">
          Go back
        </button>
      </div>
    );
  }

  const fullName = safeStr((student as any)?.full_name);
  const avatarLetter = (fullName.trim().charAt(0) || '?').toUpperCase();

  const attendanceRate =
    attendanceRecords.length > 0
      ? (
          (attendanceRecords.filter((r) => r.status === 'present').length / attendanceRecords.length) *
          100
        ).toFixed(1)
      : 'N/A';

  const averageGPA =
    academicRecords.length > 0
      ? (academicRecords.reduce((sum, r) => sum + r.gpa, 0) / academicRecords.length).toFixed(2)
      : 'N/A';

  const getRiskExplanation = (): string[] => {
    // Use ML explanation from backend API if available
    if (riskExplanation && riskExplanation.top_factors) {
      return riskExplanation.top_factors.map((factor: any) => factor.impact || factor.name);
    }
    
    // Fallback to parsing factors from database
    if (!risk || !risk.factors) return ['No risk factors identified'];
    
    const factors = risk.factors as Record<string, any>;
    
    // Check if factors contain top_factors array (from backend)
    if (factors.top_factors && Array.isArray(factors.top_factors)) {
      return factors.top_factors.map((f: any) => f.impact || f.name);
    }
    
    // Check if factors contain explanation string
    if (factors.explanation && typeof factors.explanation === 'string') {
      return factors.explanation.split('\n').filter((line: string) => line.trim());
    }
    
    // Legacy parsing (for backward compatibility)
    const explanations: string[] = [];
    if (factors.low_gpa) explanations.push('GPA below 2.0 threshold');
    if (factors.poor_attendance) explanations.push('Attendance rate below 75%');
    if (factors.declining_grades) explanations.push('Recent grade decline detected');
    if (factors.missing_assignments) explanations.push('Multiple missing assignments');
    if (factors.late_submissions) explanations.push('Frequent late submissions');
    if (factors.low_engagement) explanations.push('Low class engagement');
    
    return explanations.length > 0 ? explanations : ['Risk factors under analysis'];
  };

  const getRiskTrend = (): 'up' | 'down' | 'stable' => {
    // Use ML trend analysis from backend API if available
    if (riskTrend && riskTrend.direction) {
      const direction = riskTrend.direction;
      if (direction.includes('increasing')) return 'up';
      if (direction.includes('decreasing')) return 'down';
      return 'stable';
    }
    
    // Fallback to basic trend calculation
    if (riskHistory.length < 2) return 'stable';
    const current = riskHistory[0];
    const previous = riskHistory[1];
    
    if (current.risk_score > previous.risk_score + 5) return 'up';
    if (current.risk_score < previous.risk_score - 5) return 'down';
    return 'stable';
  };

  const getPerformanceTrend = () => {
    if (academicRecords.length < 2) return 'stable';
    const recent = academicRecords.slice(0, 3);
    const older = academicRecords.slice(3, 6);
    
    if (recent.length === 0 || older.length === 0) return 'stable';
    
    const recentAvg = recent.reduce((sum, r) => sum + r.gpa, 0) / recent.length;
    const olderAvg = older.reduce((sum, r) => sum + r.gpa, 0) / older.length;
    
    if (recentAvg < olderAvg - 0.3) return 'down';
    if (recentAvg > olderAvg + 0.3) return 'up';
    return 'stable';
  };

  const getAttendanceTrend = () => {
    if (attendanceRecords.length < 10) return 'stable';
    const recent = attendanceRecords.slice(0, 10);
    const older = attendanceRecords.slice(10, 20);
    
    if (recent.length === 0 || older.length === 0) return 'stable';
    
    const recentRate = recent.filter((r) => r.status === 'present').length / recent.length;
    const olderRate = older.filter((r) => r.status === 'present').length / older.length;
    
    if (recentRate < olderRate - 0.1) return 'down';
    if (recentRate > olderRate + 0.1) return 'up';
    return 'stable';
  };

  return (
    <div className="space-y-6">
      <button
        onClick={onBack}
        className="flex items-center space-x-2 text-slate-600 hover:text-slate-900"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Back to Students</span>
      </button>

      {/* Student Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4">
            <div className="h-20 w-20 bg-slate-200 rounded-full flex items-center justify-center">
              <span className="text-3xl font-bold text-slate-700">
                {avatarLetter}
              </span>
            </div>
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <h1 className="text-3xl font-bold text-slate-900">{fullName || 'Student'}</h1>
                {risk && <RiskBadge riskLevel={risk.risk_level} size="lg" />}
              </div>
              <div className="mt-2 space-y-1">
                <div className="flex items-center space-x-2 text-sm text-slate-600">
                  <Mail className="h-4 w-4" />
                  <span>{safeStr((student as any)?.email)}</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-slate-600">
                  <FileText className="h-4 w-4" />
                  <span>Student ID: {safeStr((student as any)?.student_id)}</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-slate-600">
                  <Calendar className="h-4 w-4" />
                  <span>Enrolled: {fmtDate((student as any)?.enrollment_date)}</span>
                </div>
                <div className="flex items-center space-x-2 text-xs text-slate-500 mt-2">
                  <Activity className="h-3 w-3" />
                  <span>Last monitored: {lastMonitored.toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-slate-200 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-slate-600">Department</p>
            <p className="font-semibold text-slate-900">{safeStr((student as any)?.department) || '—'}</p>
          </div>
          <div>
            <p className="text-sm text-slate-600">Program</p>
            <p className="font-semibold text-slate-900">{safeStr((student as any)?.program) || '—'}</p>
          </div>
          <div>
            <p className="text-sm text-slate-600">Year Level</p>
            <p className="font-semibold text-slate-900">
              {Number.isFinite(Number((student as any)?.year_level)) ? `Year ${Number((student as any)?.year_level)}` : '—'}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-600">Status</p>
            <p className="font-semibold text-slate-900 capitalize">{safeStr((student as any)?.status) || '—'}</p>
          </div>
        </div>
      </div>

      {/* Risk Summary Card */}
      {risk && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className={`h-12 w-12 rounded-lg flex items-center justify-center ${
                risk.risk_level === 'high' ? 'bg-red-100' :
                risk.risk_level === 'medium' ? 'bg-amber-100' : 'bg-green-100'
              }`}>
                <AlertTriangle className={`h-6 w-6 ${
                  risk.risk_level === 'high' ? 'text-red-600' :
                  risk.risk_level === 'medium' ? 'text-amber-600' : 'text-green-600'
                }`} />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Risk Assessment Summary</h2>
                <p className="text-sm text-slate-600">Current risk level and confidence</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <TrendIndicator trend={getRiskTrend()} />
              {riskTrend && riskTrend.escalation_detected && (
                <span className="text-xs text-red-600 font-medium">⚠️ Escalation Detected</span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="p-4 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-600 mb-1">Risk Score</p>
              <div className="flex items-end space-x-2">
                <span className="text-4xl font-bold text-slate-900">{risk.risk_score}</span>
                <span className="text-slate-500 mb-1">/100</span>
              </div>
              <div className="mt-2 h-2 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    risk.risk_level === 'high' ? 'bg-red-500' :
                    risk.risk_level === 'medium' ? 'bg-amber-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${risk.risk_score}%` }}
                />
              </div>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-600 mb-1">Confidence Level</p>
              <div className="flex items-end space-x-2 mb-2">
                <span className="text-4xl font-bold text-slate-900">
                  {(risk.confidence_level * 100).toFixed(0)}%
                </span>
              </div>
              <ConfidenceIndicator confidence={risk.confidence_level} size="md" showLabel={false} />
              <p className="text-xs text-slate-500 mt-2">ML model confidence</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-600 mb-1">Last Updated</p>
              <p className="text-lg font-semibold text-slate-900">
                {fmtDate((risk as any)?.prediction_date)}
              </p>
              <p className="text-xs text-slate-500 mt-2">
                {fmtTime((risk as any)?.prediction_date)}
              </p>
            </div>
          </div>

          {/* Why at Risk Explanation */}
          <div className="pt-6 border-t border-slate-200">
            <div className="flex items-center space-x-2 mb-4">
              <Info className="h-5 w-5 text-slate-600" />
              <h3 className="text-lg font-semibold text-slate-900">Why This Student Is At Risk</h3>
            </div>
            
            {/* Top Factors Chart from ML Model */}
            {riskExplanation && riskExplanation.top_factors && riskExplanation.top_factors.length > 0 ? (
              <div className="mb-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
                <TopFactorsChart factors={riskExplanation.top_factors} maxDisplay={5} />
              </div>
            ) : null}
            
            {/* Fallback to text explanations */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {getRiskExplanation().map((explanation, index) => (
                <div key={index} className="flex items-start space-x-2 p-3 bg-amber-50 rounded-lg border border-amber-200">
                  <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-slate-700">{explanation}</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Risk Trend Chart */}
          {riskHistory.length >= 2 && (
            <div className="mt-6 pt-6 border-t border-slate-200">
              <div className="flex items-center space-x-2 mb-4">
                <Activity className="h-5 w-5 text-slate-600" />
                <h3 className="text-lg font-semibold text-slate-900">Risk Trend Over Time</h3>
              </div>
              <div className="bg-white rounded-lg p-4 border border-slate-200">
                <RiskTrendChart 
                  data={riskHistory.map(r => ({
                    date: r.created_at,
                    risk_score: r.risk_score,
                    risk_level: r.risk_level as 'low' | 'medium' | 'high'
                  }))} 
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Performance Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <BookOpen className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-slate-900">Academic Performance</h2>
            </div>
            <TrendIndicator trend={getPerformanceTrend()} />
          </div>
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-600">Average GPA</span>
              <span className="text-3xl font-bold text-slate-900">{averageGPA}</span>
            </div>
            {academicRecords.length > 0 && (
              <div className="h-32 flex items-end justify-between space-x-1 mt-4">
                {academicRecords.slice(0, 6).reverse().map((record) => (
                  <div key={record.id} className="flex-1 flex flex-col items-center">
                    <div
                      className="w-full bg-blue-500 rounded-t transition-all duration-500"
                      style={{
                        height: `${
                          Number.isFinite(Number((record as any)?.gpa)) ? (Number((record as any)?.gpa) / 4.0) * 100 : 0
                        }%`,
                      }}
                    />
                    <span className="text-xs text-slate-500 mt-1">{safeStr((record as any)?.semester).slice(0, 3)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {academicRecords.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No academic records available</p>
            ) : (
              academicRecords.slice(0, 5).map((record) => (
                <div key={record.id} className="p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-slate-900">{safeStr((record as any)?.course_name) || '—'}</p>
                      <p className="text-sm text-slate-600">
                        {safeStr((record as any)?.course_code) || '—'} • {safeStr((record as any)?.semester) || '—'}
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <p className="font-bold text-slate-900">
                        {Number.isFinite(Number((record as any)?.grade)) ? Number((record as any)?.grade).toFixed(1) : '—'}
                      </p>
                      <p className="text-xs text-slate-500">
                        GPA: {Number.isFinite(Number((record as any)?.gpa)) ? Number((record as any)?.gpa).toFixed(2) : '—'}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <TrendingDown className="h-5 w-5 text-green-600" />
              <h2 className="text-lg font-semibold text-slate-900">Attendance Record</h2>
            </div>
            <TrendIndicator trend={getAttendanceTrend()} />
          </div>
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-600">Attendance Rate</span>
              <span className="text-3xl font-bold text-slate-900">
                {typeof attendanceRate === 'string' && attendanceRate !== 'N/A' ? `${attendanceRate}%` : attendanceRate}
              </span>
            </div>
            {attendanceRecords.length > 0 && (
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-600 mb-2">
                  <span>Last 30 days</span>
                  <span>
                    {attendanceRecords.filter((r) => r.status === 'present').length} / {attendanceRecords.length} present
                  </span>
                </div>
                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all duration-500"
                    style={{
                      width:
                        typeof attendanceRate === 'string' && attendanceRate !== 'N/A'
                          ? `${attendanceRate}%`
                          : '0%',
                    }}
                  />
                </div>
              </div>
            )}
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {attendanceRecords.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No attendance records available</p>
            ) : (
              attendanceRecords.slice(0, 10).map((record) => (
                <div key={record.id} className="flex items-center justify-between p-2 hover:bg-slate-50 rounded">
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {fmtDate((record as any)?.date)}
                    </p>
                    <p className="text-xs text-slate-600">{record.course_code}</p>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded ${
                      record.status === 'present'
                        ? 'bg-green-100 text-green-700'
                        : record.status === 'absent'
                        ? 'bg-red-100 text-red-700'
                        : record.status === 'late'
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    {(() => {
                      const s = safeStr((record as any)?.status);
                      return s ? s.charAt(0).toUpperCase() + s.slice(1) : '—';
                    })()}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Risk Timeline & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Clock className="h-5 w-5 text-slate-600" />
            <h2 className="text-lg font-semibold text-slate-900">Risk Event Timeline</h2>
          </div>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {riskHistory.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No risk history available</p>
            ) : (
              riskHistory.map((riskEvent) => (
                <div key={riskEvent.id} className="flex items-start space-x-3">
                  <div className={`flex-shrink-0 w-3 h-3 rounded-full mt-1.5 ${
                    riskEvent.risk_level === 'high' ? 'bg-red-500' :
                    riskEvent.risk_level === 'medium' ? 'bg-amber-500' : 'bg-green-500'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <RiskBadge riskLevel={riskEvent.risk_level} size="sm" />
                      <span className="text-xs text-slate-500">
                        {fmtDate((riskEvent as any)?.created_at)}
                      </span>
                    </div>
                    <p className="text-sm text-slate-700">
                      Risk Score: {riskEvent.risk_score}/100
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      Confidence: {(riskEvent.confidence_level * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-amber-600" />
            <h2 className="text-lg font-semibold text-slate-900">Recent Alerts</h2>
          </div>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {alerts.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No alerts</p>
            ) : (
              alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3 rounded-lg border ${
                    alert.severity === 'critical'
                      ? 'bg-red-50 border-red-200'
                      : alert.severity === 'high'
                      ? 'bg-amber-50 border-amber-200'
                      : 'bg-blue-50 border-blue-200'
                  }`}
                >
                  <div className="flex items-start justify-between mb-1">
                    <span
                      className={`text-xs font-semibold uppercase ${
                        alert.severity === 'critical' || alert.severity === 'high'
                          ? 'text-red-700'
                          : 'text-blue-700'
                      }`}
                    >
                      {alert.alert_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs text-slate-500">
                      {fmtDate((alert as any)?.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-slate-700">{alert.message}</p>
                  {alert.acknowledged && (
                    <p className="text-xs text-slate-500 mt-2">✓ Acknowledged</p>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Interventions */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Target className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-slate-900">Interventions</h2>
        </div>
        <div className="space-y-3">
          {interventions.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-4">No interventions</p>
          ) : (
            interventions.map((intervention) => (
              <div key={intervention.id} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-sm font-semibold text-slate-900 capitalize">
                    {intervention.intervention_type.replace(/_/g, ' ')}
                  </span>
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded ${
                      intervention.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : intervention.status === 'in_progress'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    {intervention.status.replace(/_/g, ' ')}
                  </span>
                </div>
                <p className="text-sm text-slate-600 mb-2">{intervention.description}</p>
                <div className="flex items-center space-x-4 text-xs text-slate-500">
                  <span>Created: {fmtDate((intervention as any)?.created_at)}</span>
                  {intervention.completed_at && (
                    <span>Completed: {fmtDate((intervention as any)?.completed_at)}</span>
                  )}
                </div>
                {intervention.outcome_notes && (
                  <div className="mt-3 pt-3 border-t border-slate-200">
                    <p className="text-xs font-medium text-slate-700 mb-1">Outcome Notes:</p>
                    <p className="text-sm text-slate-600">{intervention.outcome_notes}</p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
