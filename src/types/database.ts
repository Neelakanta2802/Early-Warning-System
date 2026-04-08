export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type UserRole = 'faculty' | 'administrator' | 'counselor';
export type StudentStatus = 'active' | 'inactive' | 'graduated' | 'dropped';
export type RiskLevel = 'low' | 'medium' | 'high';
export type AttendanceStatus = 'present' | 'absent' | 'late' | 'excused';
export type AlertType = 'high_risk' | 'attendance_drop' | 'performance_decline' | 'behavioral_anomaly';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type InterventionType = 'mentoring' | 'counseling' | 'remedial' | 'academic_support';
export type InterventionStatus = 'pending' | 'in_progress' | 'completed';

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          email: string;
          full_name: string;
          role: UserRole;
          department: string | null;
          created_at: string;
        };
        Insert: {
          id: string;
          email: string;
          full_name: string;
          role: UserRole;
          department?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          email?: string;
          full_name?: string;
          role?: UserRole;
          department?: string | null;
          created_at?: string;
        };
      };
      students: {
        Row: {
          id: string;
          student_id: string;
          full_name: string;
          email: string;
          department: string;
          program: string;
          year_level: number;
          semester: string;
          enrollment_date: string;
          status: StudentStatus;
          created_at: string;
        };
        Insert: {
          id?: string;
          student_id: string;
          full_name: string;
          email: string;
          department: string;
          program: string;
          year_level?: number;
          semester: string;
          enrollment_date?: string;
          status?: StudentStatus;
          created_at?: string;
        };
        Update: {
          id?: string;
          student_id?: string;
          full_name?: string;
          email?: string;
          department?: string;
          program?: string;
          year_level?: number;
          semester?: string;
          enrollment_date?: string;
          status?: StudentStatus;
          created_at?: string;
        };
      };
      risk_assessments: {
        Row: {
          id: string;
          student_id: string;
          risk_level: RiskLevel;
          risk_score: number;
          confidence_level: number;
          factors: Json;
          prediction_date: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          student_id: string;
          risk_level: RiskLevel;
          risk_score: number;
          confidence_level: number;
          factors?: Json;
          prediction_date?: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          student_id?: string;
          risk_level?: RiskLevel;
          risk_score?: number;
          confidence_level?: number;
          factors?: Json;
          prediction_date?: string;
          created_at?: string;
        };
      };
      academic_records: {
        Row: {
          id: string;
          student_id: string;
          semester: string;
          course_code: string;
          course_name: string;
          grade: number;
          credits: number;
          gpa: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          student_id: string;
          semester: string;
          course_code: string;
          course_name: string;
          grade: number;
          credits?: number;
          gpa: number;
          created_at?: string;
        };
        Update: {
          id?: string;
          student_id?: string;
          semester?: string;
          course_code?: string;
          course_name?: string;
          grade?: number;
          credits?: number;
          gpa?: number;
          created_at?: string;
        };
      };
      attendance_records: {
        Row: {
          id: string;
          student_id: string;
          date: string;
          status: AttendanceStatus;
          course_code: string;
          semester: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          student_id: string;
          date: string;
          status: AttendanceStatus;
          course_code: string;
          semester: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          student_id?: string;
          date?: string;
          status?: AttendanceStatus;
          course_code?: string;
          semester?: string;
          created_at?: string;
        };
      };
      alerts: {
        Row: {
          id: string;
          student_id: string;
          alert_type: AlertType;
          severity: AlertSeverity;
          message: string;
          acknowledged: boolean;
          acknowledged_by: string | null;
          acknowledged_at: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          student_id: string;
          alert_type: AlertType;
          severity: AlertSeverity;
          message: string;
          acknowledged?: boolean;
          acknowledged_by?: string | null;
          acknowledged_at?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          student_id?: string;
          alert_type?: AlertType;
          severity?: AlertSeverity;
          message?: string;
          acknowledged?: boolean;
          acknowledged_by?: string | null;
          acknowledged_at?: string | null;
          created_at?: string;
        };
      };
      interventions: {
        Row: {
          id: string;
          student_id: string;
          assigned_to: string;
          intervention_type: InterventionType;
          description: string;
          status: InterventionStatus;
          outcome_notes: string | null;
          created_at: string;
          updated_at: string;
          completed_at: string | null;
        };
        Insert: {
          id?: string;
          student_id: string;
          assigned_to: string;
          intervention_type: InterventionType;
          description: string;
          status?: InterventionStatus;
          outcome_notes?: string | null;
          created_at?: string;
          updated_at?: string;
          completed_at?: string | null;
        };
        Update: {
          id?: string;
          student_id?: string;
          assigned_to?: string;
          intervention_type?: InterventionType;
          description?: string;
          status?: InterventionStatus;
          outcome_notes?: string | null;
          created_at?: string;
          updated_at?: string;
          completed_at?: string | null;
        };
      };
    };
  };
}
