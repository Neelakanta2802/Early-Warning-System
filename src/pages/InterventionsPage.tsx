import { useEffect, useMemo, useState } from 'react';
import { Heart, Filter, CheckCircle, Clock, AlertCircle, Target, Users, Activity, Plus, Trash2 } from 'lucide-react';
import apiClient from '../lib/api';
import RiskBadge from '../components/RiskBadge';
import { useAuth } from '../contexts/AuthContext';
import type { Database } from '../types/database';

type Intervention = Database['public']['Tables']['interventions']['Row'];

interface InterventionWithDetails extends Intervention {
  student: {
    full_name: string;
    student_id: string;
  };
}

interface StudentNeedingAction {
  studentId: string;
  studentName: string;
  studentIdNumber: string;
  riskLevel: 'low' | 'medium' | 'high';
  riskScore: number;
  recommendedIntervention: string;
  priority: 'high' | 'medium' | 'low';
}

export default function InterventionsPage() {
  const { user, profile } = useAuth();
  const [interventions, setInterventions] = useState<InterventionWithDetails[]>([]);
  const [studentsNeedingAction, setStudentsNeedingAction] = useState<StudentNeedingAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Create / edit controls
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [selectedStudentId, setSelectedStudentId] = useState<string>('');
  const [interventionType, setInterventionType] = useState<string>('academic_support');
  const [assignedTo, setAssignedTo] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [studentOptions, setStudentOptions] = useState<any[]>([]);

  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const uuidRe = useMemo(
    () => /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
    []
  );
  const effectiveAssignee = useMemo(() => {
    const maybe = (profile as any)?.id || (user as any)?.id || '';
    return uuidRe.test(String(maybe)) ? String(maybe) : '';
  }, [profile, user, uuidRe]);

  useEffect(() => {
    loadInterventions();
    loadStudentsNeedingAction();
    loadStudentOptions();
    const interval = setInterval(() => {
      loadInterventions();
      loadStudentsNeedingAction();
    }, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, [statusFilter]);

  async function loadInterventions() {
    try {
      const params: any = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      const data = await apiClient.getInterventions(params);
      setInterventions((data as InterventionWithDetails[]) || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error loading interventions:', error);
    } finally {
      setLoading(false);
    }
  }

  async function loadStudentsNeedingAction() {
    try {
      const [students, allInterventions] = await Promise.all([
        apiClient.getStudents({ status: 'active', limit: 200 }),
        apiClient.getInterventions({})
      ]);

      const activeStudentIds = new Set(
        (allInterventions || [])
          .filter((i: any) => ['pending', 'in_progress'].includes(i.status))
          .map((i: any) => i.student_id)
      );

      const highRiskStudents = (students || [])
        .filter((s: any) => ['high', 'medium'].includes((s.risk as any)?.risk_level))
        .sort((a: any, b: any) => ((b.risk as any)?.risk_score || 0) - ((a.risk as any)?.risk_score || 0))
        .slice(0, 10);

      const needingAction: StudentNeedingAction[] = highRiskStudents
        .filter((s: any) => !activeStudentIds.has(s.id))
        .slice(0, 5)
        .map((s: any) => {
          const level = (s.risk as any)?.risk_level as 'low' | 'medium' | 'high';
          const score = Number((s.risk as any)?.risk_score || 0);
          return {
            studentId: s.id,
            studentName: s.full_name || 'Unknown',
            studentIdNumber: s.student_id || 'N/A',
            riskLevel: level || 'medium',
            riskScore: score,
            recommendedIntervention: getRecommendedIntervention(level, score),
            priority: level === 'high' ? 'high' : 'medium',
          };
        });

      setStudentsNeedingAction(needingAction);
    } catch (error) {
      console.error('Error loading students needing action:', error);
    }
  }

  async function loadStudentOptions() {
    try {
      const students = await apiClient.getStudents({ status: 'active', limit: 200 });
      setStudentOptions(Array.isArray(students) ? students : []);
    } catch {
      // ignore
    }
  }

  function openCreateModalForStudent(s?: StudentNeedingAction) {
    setCreateError(null);
    setShowCreateModal(true);
    setSelectedStudentId(s?.studentId || '');
    setInterventionType(s?.riskLevel === 'high' ? 'counseling' : 'academic_support');
    setDescription(s?.recommendedIntervention || '');
    setAssignedTo(effectiveAssignee || '');
  }

  async function handleCreateIntervention() {
    try {
      setCreateError(null);
      if (!selectedStudentId) {
        setCreateError('Please select a student.');
        return;
      }
      if (!description.trim()) {
        setCreateError('Please enter a description.');
        return;
      }

      setCreating(true);
      await apiClient.createIntervention({
        student_id: selectedStudentId,
        ...(assignedTo.trim() ? { assigned_to: assignedTo.trim() } : {}),
        intervention_type: interventionType,
        description: description.trim(),
        status: 'pending',
      });
      setShowCreateModal(false);
      setDescription('');
      setSelectedStudentId('');
      await Promise.all([loadInterventions(), loadStudentsNeedingAction()]);
    } catch (e: any) {
      setCreateError(e?.message || 'Failed to create intervention');
    } finally {
      setCreating(false);
    }
  }

  async function handleUpdateStatus(interventionId: string, status: string) {
    try {
      setUpdatingId(interventionId);
      await apiClient.updateIntervention(interventionId, { status });
      await loadInterventions();
    } catch (e) {
      console.error('Failed to update intervention', e);
    } finally {
      setUpdatingId(null);
    }
  }

  async function handleDeleteIntervention(interventionId: string) {
    try {
      setDeletingId(interventionId);
      await apiClient.deleteIntervention(interventionId);
      await Promise.all([loadInterventions(), loadStudentsNeedingAction()]);
    } catch (e) {
      console.error('Failed to delete intervention', e);
    } finally {
      setDeletingId(null);
    }
  }

  function getRecommendedIntervention(riskLevel: string, riskScore: number): string {
    if (riskLevel === 'high' && riskScore > 80) {
      return 'Immediate counseling and academic support';
    } else if (riskLevel === 'high') {
      return 'Mentoring program and attendance monitoring';
    } else if (riskLevel === 'medium' && riskScore > 60) {
      return 'Academic support and progress check-ins';
    } else {
      return 'Regular monitoring and check-ins';
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'in_progress':
        return <Clock className="h-5 w-5 text-blue-600" />;
      default:
        return <AlertCircle className="h-5 w-5 text-slate-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700';
      case 'in_progress':
        return 'bg-blue-100 text-blue-700';
      default:
        return 'bg-slate-100 text-slate-700';
    }
  };

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

  const stats = {
    total: interventions.length,
    pending: interventions.filter((i) => i.status === 'pending').length,
    inProgress: interventions.filter((i) => i.status === 'in_progress').length,
    completed: interventions.filter((i) => i.status === 'completed').length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Intervention Planning</h1>
          <p className="text-slate-600 mt-1">
            Track and manage student support interventions and action plans
          </p>
          <div className="flex items-center space-x-2 mt-2 text-xs text-slate-500">
            <Activity className="h-3 w-3" />
            <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
          </div>
        </div>
        <button
          onClick={() => openCreateModalForStudent()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 text-white font-medium hover:bg-slate-800 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Intervention
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <p className="text-sm font-medium text-slate-600 mb-2">Total Interventions</p>
          <p className="text-3xl font-bold text-slate-900">{stats.total}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <p className="text-sm font-medium text-slate-600 mb-2">Pending</p>
          <p className="text-3xl font-bold text-slate-600">{stats.pending}</p>
          <p className="text-xs text-slate-500 mt-1">Awaiting action</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <p className="text-sm font-medium text-slate-600 mb-2">In Progress</p>
          <p className="text-3xl font-bold text-blue-600">{stats.inProgress}</p>
          <p className="text-xs text-slate-500 mt-1">Active support</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <p className="text-sm font-medium text-slate-600 mb-2">Completed</p>
          <p className="text-3xl font-bold text-green-600">{stats.completed}</p>
          <p className="text-xs text-slate-500 mt-1">Successfully resolved</p>
        </div>
      </div>

      {/* Students Needing Action */}
      {studentsNeedingAction.length > 0 && (
        <div className="bg-gradient-to-r from-red-50 to-amber-50 rounded-xl border-2 border-red-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Target className="h-6 w-6 text-red-600" />
            <h2 className="text-xl font-semibold text-slate-900">Students Needing Immediate Action</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {studentsNeedingAction.map((student) => (
              <div
                key={student.studentId}
                className="bg-white rounded-lg border border-slate-200 p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-900 mb-1">{student.studentName}</h3>
                    <p className="text-sm text-slate-600 mb-2">{student.studentIdNumber}</p>
                    <RiskBadge riskLevel={student.riskLevel} size="sm" />
                  </div>
                </div>
                <div className="pt-3 border-t border-slate-200">
                  <p className="text-xs font-medium text-slate-600 mb-1">Recommended Action:</p>
                  <p className="text-sm text-slate-700">{student.recommendedIntervention}</p>
                  <button
                    onClick={() => openCreateModalForStudent(student)}
                    className="mt-3 w-full px-3 py-1.5 text-xs font-medium bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
                  >
                    Create Intervention
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center space-x-2 mb-3">
          <Filter className="h-4 w-4 text-slate-500" />
          <span className="text-sm font-medium text-slate-700">Filter Interventions</span>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="w-full md:w-auto px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      {/* Interventions List */}
      {interventions.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <Heart className="h-16 w-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No Interventions</h3>
          <p className="text-slate-500">
            {statusFilter === 'all'
              ? 'No interventions have been created yet.'
              : `No interventions with status "${statusFilter}".`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {interventions.map((intervention) => (
            <div key={intervention.id} className="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="flex-shrink-0 mt-1">{getStatusIcon(intervention.status)}</div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-semibold text-slate-900">
                        {intervention.student?.full_name || 'Unknown Student'} ({intervention.student?.student_id || 'N/A'})
                      </h3>
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadge(
                          intervention.status
                        )}`}
                      >
                        {intervention.status.replace(/_/g, ' ').toUpperCase()}
                      </span>
                    </div>
                    <div className="mb-3">
                      <span className="text-sm font-medium text-slate-700 capitalize">
                        {intervention.intervention_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-slate-700 mb-3">{intervention.description}</p>
                    <div className="flex items-center space-x-4 text-sm text-slate-500">
                      <div className="flex items-center space-x-1">
                        <Users className="h-4 w-4" />
                        <span>Assigned to: {(intervention as any).assigned_user?.full_name || (intervention as any).assigned_to || 'Unassigned'}</span>
                      </div>
                      <span>•</span>
                      <div className="flex items-center space-x-1">
                        <Clock className="h-4 w-4" />
                        <span>Created: {new Date(intervention.created_at).toLocaleDateString()}</span>
                      </div>
                      {intervention.completed_at && (
                        <>
                          <span>•</span>
                          <span>
                            Completed: {new Date(intervention.completed_at).toLocaleDateString()}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={intervention.status}
                    disabled={updatingId === intervention.id}
                    onChange={(e) => handleUpdateStatus(intervention.id, e.target.value)}
                    className="px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
                  >
                    <option value="pending">Pending</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                  </select>
                  <button
                    onClick={() => handleDeleteIntervention(intervention.id)}
                    disabled={deletingId === intervention.id}
                    className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4" />
                    {deletingId === intervention.id ? 'Deleting…' : 'Delete'}
                  </button>
                </div>
              </div>
              {intervention.outcome_notes && (
                <div className="pt-4 border-t border-slate-200">
                  <p className="text-sm font-medium text-slate-700 mb-1">Outcome Notes:</p>
                  <p className="text-sm text-slate-600">{intervention.outcome_notes}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create Intervention Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/50" onClick={() => !creating && setShowCreateModal(false)} />
          <div className="relative w-full max-w-xl bg-white rounded-2xl border border-slate-200 shadow-xl">
            <div className="p-6 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Create Intervention</h2>
                <p className="text-sm text-slate-600 mt-1">Plan support actions and track progress</p>
              </div>
              <button
                onClick={() => !creating && setShowCreateModal(false)}
                className="text-slate-500 hover:text-slate-900"
              >
                ✕
              </button>
            </div>
            <div className="p-6 space-y-4">
              {createError && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg p-3">
                  {createError}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Student</label>
                <select
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                >
                  <option value="">Select a student…</option>
                  {studentOptions.map((s: any) => (
                    <option key={s.id} value={s.id}>
                      {s.full_name} ({s.student_id})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Type</label>
                  <select
                    value={interventionType}
                    onChange={(e) => setInterventionType(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                  >
                    <option value="mentoring">Mentoring</option>
                    <option value="counseling">Counseling</option>
                    <option value="remedial">Remedial</option>
                    <option value="academic_support">Academic Support</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Assigned To (optional)</label>
                  <input
                    value={assignedTo}
                    onChange={(e) => setAssignedTo(e.target.value)}
                    placeholder={effectiveAssignee ? `Default: ${effectiveAssignee}` : 'Leave blank to keep unassigned'}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    If your DB schema uses UUIDs for assignees, non‑UUID values will be ignored automatically.
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                  placeholder="Describe the plan, timeline, and success criteria…"
                />
              </div>
            </div>
            <div className="p-6 border-t border-slate-200 flex items-center justify-end gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                disabled={creating}
                className="px-4 py-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateIntervention}
                disabled={creating}
                className="px-4 py-2 rounded-lg bg-slate-900 text-white font-medium hover:bg-slate-800 disabled:opacity-50"
              >
                {creating ? 'Creating…' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
