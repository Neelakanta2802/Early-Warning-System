import { useEffect, useMemo, useState, useDeferredValue } from 'react';
import { Search, Filter, AlertCircle, ArrowUpDown, Eye } from 'lucide-react';
import apiClient from '../lib/api';
import RiskBadge from '../components/RiskBadge';
import TrendIndicator from '../components/TrendIndicator';
import type { Database } from '../types/database';

type Student = Database['public']['Tables']['students']['Row'];
type RiskAssessment = Database['public']['Tables']['risk_assessments']['Row'];

interface StudentWithRisk extends Student {
  risk?: RiskAssessment;
  previousRisk?: RiskAssessment;
}

type SortOption = 'risk' | 'name' | 'department' | 'score';

interface StudentsPageProps {
  onViewStudent: (studentId: string) => void;
}

export default function StudentsPage({ onViewStudent }: StudentsPageProps) {
  const [students, setStudents] = useState<StudentWithRisk[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRisk, setFilterRisk] = useState<string>('all');
  const [filterDepartment, setFilterDepartment] = useState<string>('all');
  const [sortBy, setSortBy] = useState<SortOption>('risk');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [departments, setDepartments] = useState<string[]>([]);
  const [hoveredStudentId, setHoveredStudentId] = useState<string | null>(null);
  const deferredSearch = useDeferredValue(searchQuery);

  useEffect(() => {
    loadStudents();
    
    // CRITICAL FIX: Listen for data upload events with polling mechanism
    const handleDataUploaded = (event?: CustomEvent) => {
      console.log('📥 Data upload event received, refreshing students list...');
      const uploadResult = event?.detail || null;
      const studentsCreated = uploadResult?.students_created || 0;
      const riskAssessmentsCreated = uploadResult?.risk_assessments_created || 0;
      
      console.log(`Upload summary: ${studentsCreated} students, ${riskAssessmentsCreated} risk assessments`);
      
      // Poll a few times against backend API (avoids Supabase client/RLS differences)
      let attempts = 0;
      const maxAttempts = 6;
      const pollInterval = (attempt: number) => Math.min(1000 * (attempt + 1), 4000);
      
      const pollForData = async () => {
        attempts++;
        console.log(`🔄 Polling attempt ${attempts}/${maxAttempts} for updated data (backend API)...`);
        try {
          await loadStudents();
        } catch {
          // loadStudents already logs; keep polling
        }

        if (attempts < maxAttempts && (studentsCreated > 0 || riskAssessmentsCreated > 0)) {
            setTimeout(pollForData, pollInterval(attempts));
        }
      };
      
      setTimeout(pollForData, 750);
    };
    
    window.addEventListener('dataUploaded', handleDataUploaded);
    window.addEventListener('dataUploadedWithResult', handleDataUploaded);
    
    return () => {
      window.removeEventListener('dataUploaded', handleDataUploaded);
      window.removeEventListener('dataUploadedWithResult', handleDataUploaded);
    };
  }, []);

  async function loadStudents() {
    try {
      setLoadError(null);
      // PERF/SAFETY: Load a reasonable page size first; avoid fetching 1000 rows up front.
      // If you need more later, we can add pagination or a "Load more" UI.
      const studentsData = await apiClient.getStudents({ status: 'active', limit: 200 });
      const normalized = (studentsData || []).map((s: any) => ({
        ...s,
        // backend provides both latest and previous for trend
        risk: (s as any).risk || undefined,
        previousRisk: (s as any).previous_risk || undefined,
      })) as StudentWithRisk[];

      setStudents(normalized);

      const uniqueDepts = Array.from(
        new Set((normalized || []).map((s: any) => String(s?.department || '').trim()).filter(Boolean))
      ).sort((a, b) => a.localeCompare(b));
      setDepartments(uniqueDepts);
    } catch (error) {
      console.error('Error loading students:', error);
      // Important: clear stale UI data if backend/db is misconfigured or empty
      setStudents([]);
      setDepartments([]);
      setLoadError((error as any)?.message || 'Failed to load students');
    } finally {
      setLoading(false);
    }
  }

  const getRiskTrend = (student: StudentWithRisk): 'up' | 'down' | 'stable' => {
    if (!student.risk || !student.previousRisk) return 'stable';
    if (!student.risk || !student.previousRisk) return 'stable';
    
    const riskOrder = { low: 1, medium: 2, high: 3 };
    const current = riskOrder[student.risk.risk_level as keyof typeof riskOrder] || 0;
    const previous = riskOrder[student.previousRisk.risk_level as keyof typeof riskOrder] || 0;
    
    if (current > previous) return 'up';
    if (current < previous) return 'down';
    return 'stable';
  };

  const getRiskPriority = (risk?: RiskAssessment): number => {
    if (!risk) return 0;
    const levelPriority = { high: 3, medium: 2, low: 1 };
    return (levelPriority[risk.risk_level as keyof typeof levelPriority] || 0) * 100 + risk.risk_score;
  };

  const filteredAndSortedStudents = useMemo(() => {
    const q = String(deferredSearch || '').toLowerCase().trim();
    const base = (students || []).filter((student) => {
      const fullName = String((student as any)?.full_name || '');
      const roll = String((student as any)?.student_id || '');
      const email = String((student as any)?.email || '');
      const dept = String((student as any)?.department || '');

      const matchesSearch =
        !q ||
        fullName.toLowerCase().includes(q) ||
        roll.toLowerCase().includes(q) ||
        email.toLowerCase().includes(q);

      const matchesRisk = filterRisk === 'all' || student.risk?.risk_level === filterRisk;
      const matchesDepartment = filterDepartment === 'all' || dept === filterDepartment;

      return matchesSearch && matchesRisk && matchesDepartment;
    });

    const sorted = [...base].sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'risk':
          comparison = getRiskPriority(b.risk) - getRiskPriority(a.risk);
          break;
        case 'name':
          comparison = String((a as any)?.full_name || '').localeCompare(String((b as any)?.full_name || ''));
          break;
        case 'department':
          comparison = String((a as any)?.department || '').localeCompare(String((b as any)?.department || ''));
          break;
        case 'score':
          comparison = (b.risk?.risk_score || 0) - (a.risk?.risk_score || 0);
          break;
      }

      return sortDirection === 'asc' ? -comparison : comparison;
    });

    return sorted;
  }, [students, deferredSearch, filterRisk, filterDepartment, sortBy, sortDirection]);


  const getRiskExplanation = (student: StudentWithRisk): string => {
    if (!student.risk) return 'No risk assessment available';
    
    const factors = student.risk.factors as Record<string, unknown> | null;
    if (!factors || Object.keys(factors).length === 0) {
      return `Risk score: ${student.risk.risk_score}/100`;
    }

    // Check if factors contain top_factors array (from ML model)
    if (factors.top_factors && Array.isArray(factors.top_factors) && factors.top_factors.length > 0) {
      const topFactors = factors.top_factors.slice(0, 3);
      return topFactors.map((f: any) => {
        const name = f.name?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()) || 'Unknown factor';
        return f.impact || name;
      }).join(', ');
    }
    
    // Check if factors contain explanation string
    if (factors.explanation && typeof factors.explanation === 'string') {
      return factors.explanation.split('\n')[0]; // First line
    }

    // Legacy parsing (for backward compatibility)
    const reasons: string[] = [];
    if (factors.low_gpa) reasons.push('Low GPA');
    if (factors.poor_attendance) reasons.push('Poor attendance');
    if (factors.declining_grades) reasons.push('Declining grades');
    if (factors.missing_assignments) reasons.push('Missing assignments');
    
    return reasons.length > 0 
      ? reasons.join(', ') 
      : `Risk score: ${student.risk.risk_score}/100 (Confidence: ${((student.risk.confidence_level || 0) * 100).toFixed(0)}%)`;
  };

  const { highRiskCount, mediumRiskCount } = useMemo(() => {
    let high = 0;
    let medium = 0;
    for (const s of filteredAndSortedStudents) {
      if (s.risk?.risk_level === 'high') high++;
      else if (s.risk?.risk_level === 'medium') medium++;
    }
    return { highRiskCount: high, mediumRiskCount: medium };
  }, [filteredAndSortedStudents]);

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-slate-200 rounded w-48"></div>
        <div className="h-12 bg-slate-200 rounded"></div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-20 bg-slate-200 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }
  
  if (loadError) {
    return (
      <div className="bg-white rounded-xl border border-red-200 p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Unable to load students</h2>
            <p className="text-sm text-slate-600 mt-1">{loadError}</p>
            <p className="text-sm text-slate-600 mt-2">
              If you just switched to a new database, make sure your Supabase schema is created and then upload a file.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Student Risk Monitoring</h1>
        <p className="text-slate-600 mt-1">
          Identify and prioritize at-risk students requiring immediate attention
        </p>
      </div>

      {/* Risk Summary Banner */}
      <div className="bg-gradient-to-r from-red-50 via-amber-50 to-green-50 rounded-xl border border-slate-200 p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-white rounded-lg">
            <p className="text-3xl font-bold text-red-600">{highRiskCount}</p>
            <p className="text-sm font-medium text-slate-600 mt-1">High Risk</p>
            <p className="text-xs text-slate-500 mt-1">Requires immediate action</p>
          </div>
          <div className="text-center p-4 bg-white rounded-lg">
            <p className="text-3xl font-bold text-amber-600">{mediumRiskCount}</p>
            <p className="text-sm font-medium text-slate-600 mt-1">Medium Risk</p>
            <p className="text-xs text-slate-500 mt-1">Monitor closely</p>
          </div>
          <div className="text-center p-4 bg-white rounded-lg">
            <p className="text-3xl font-bold text-green-600">
              {filteredAndSortedStudents.length - highRiskCount - mediumRiskCount}
            </p>
            <p className="text-sm font-medium text-slate-600 mt-1">Low/No Risk</p>
            <p className="text-xs text-slate-500 mt-1">On track</p>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search students..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <select
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent appearance-none"
            >
              <option value="all">All Risk Levels</option>
              <option value="high">High Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="low">Low Risk</option>
            </select>
          </div>

          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <select
              value={filterDepartment}
              onChange={(e) => setFilterDepartment(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent appearance-none"
            >
              <option value="all">All Departments</option>
              {departments.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>

          <div className="relative">
            <ArrowUpDown className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <select
              value={`${sortBy}-${sortDirection}`}
              onChange={(e) => {
                const [option, direction] = e.target.value.split('-');
                setSortBy(option as SortOption);
                setSortDirection(direction as 'asc' | 'desc');
              }}
              className="w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent appearance-none"
            >
              <option value="risk-desc">Sort: Risk (High First)</option>
              <option value="risk-asc">Sort: Risk (Low First)</option>
              <option value="score-desc">Sort: Score (High First)</option>
              <option value="name-asc">Sort: Name (A-Z)</option>
              <option value="department-asc">Sort: Department</option>
            </select>
          </div>
        </div>
      </div>

      {/* Student List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Risk Level
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Student
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Risk Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Trend
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {filteredAndSortedStudents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <AlertCircle className="h-12 w-12 text-slate-400 mx-auto mb-3" />
                    <p className="text-slate-500">No students found</p>
                  </td>
                </tr>
              ) : (
                filteredAndSortedStudents.map((student) => {
                  const trend = getRiskTrend(student);
                  const isHighRisk = student.risk?.risk_level === 'high';
                  const status = String((student as any)?.status || 'active');
                  
                  return (
                    <tr
                      key={student.id}
                      className={`hover:bg-slate-50 transition-colors ${
                        isHighRisk ? 'bg-red-50/30' : ''
                      }`}
                      onMouseEnter={() => setHoveredStudentId(student.id)}
                      onMouseLeave={() => setHoveredStudentId(null)}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <RiskBadge
                          riskLevel={student.risk?.risk_level || 'none'}
                          size="md"
                        />
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="font-semibold text-slate-900">{String((student as any)?.full_name || '')}</div>
                          <div className="text-sm text-slate-500">{String((student as any)?.email || '')}</div>
                          <div className="text-xs text-slate-400 mt-1">{String((student as any)?.student_id || '')}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-slate-900">{String((student as any)?.department || '')}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {student.risk ? (
                          <div>
                            <span className="text-lg font-bold text-slate-900">
                              {student.risk.risk_score}
                            </span>
                            <span className="text-sm text-slate-500">/100</span>
                          </div>
                        ) : (
                          <span className="text-sm text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <TrendIndicator trend={trend} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded ${
                            status === 'active'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {status.charAt(0).toUpperCase() + status.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => onViewStudent(student.id)}
                          className="flex items-center space-x-1 text-sm font-medium text-slate-900 hover:text-slate-700"
                        >
                          <Eye className="h-4 w-4" />
                          <span>View Details</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Hover Preview Tooltip */}
        {hoveredStudentId && (
          <div className="fixed z-50 bg-slate-900 text-white p-3 rounded-lg shadow-xl max-w-xs pointer-events-none"
               style={{
                 top: `${window.scrollY + 100}px`,
                 left: `${window.innerWidth / 2}px`,
                 transform: 'translateX(-50%)',
               }}>
            {(() => {
              const student = students.find((s: any) => s.id === hoveredStudentId);
              if (!student) return null;
              return (
                <div>
                  <p className="font-semibold mb-1">{student.full_name}</p>
                  <p className="text-xs text-slate-300">{getRiskExplanation(student)}</p>
                </div>
              );
            })()}
          </div>
        )}
      </div>

      <div className="text-sm text-slate-500">
        Showing {filteredAndSortedStudents.length} of {students.length} students
        {highRiskCount > 0 && (
          <span className="ml-2 font-semibold text-red-600">
            • {highRiskCount} require immediate attention
          </span>
        )}
      </div>
    </div>
  );
}
