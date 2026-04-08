/*
  # Early Warning System Database Schema

  ## Overview
  This migration creates the complete database schema for an AI-powered Early Warning System
  that identifies at-risk students for educational intervention.

  ## New Tables

  ### 1. profiles
  Extended user profiles with role-based access
  - `id` (uuid, FK to auth.users)
  - `email` (text)
  - `full_name` (text)
  - `role` (text) - faculty, administrator, counselor
  - `department` (text)
  - `created_at` (timestamptz)

  ### 2. students
  Student records with demographic and enrollment data
  - `id` (uuid, primary key)
  - `student_id` (text, unique)
  - `full_name` (text)
  - `email` (text)
  - `department` (text)
  - `program` (text)
  - `year_level` (integer)
  - `semester` (text)
  - `enrollment_date` (date)
  - `status` (text) - active, inactive, graduated, dropped
  - `created_at` (timestamptz)

  ### 3. risk_assessments
  AI-generated risk predictions and scores
  - `id` (uuid, primary key)
  - `student_id` (uuid, FK)
  - `risk_level` (text) - low, medium, high
  - `risk_score` (numeric) - 0-100
  - `confidence_level` (numeric) - 0-1
  - `factors` (jsonb) - contributing factors
  - `prediction_date` (timestamptz)
  - `created_at` (timestamptz)

  ### 4. academic_records
  Historical academic performance data
  - `id` (uuid, primary key)
  - `student_id` (uuid, FK)
  - `semester` (text)
  - `course_code` (text)
  - `course_name` (text)
  - `grade` (numeric)
  - `credits` (integer)
  - `gpa` (numeric)
  - `created_at` (timestamptz)

  ### 5. attendance_records
  Attendance tracking for students
  - `id` (uuid, primary key)
  - `student_id` (uuid, FK)
  - `date` (date)
  - `status` (text) - present, absent, late, excused
  - `course_code` (text)
  - `semester` (text)
  - `created_at` (timestamptz)

  ### 6. alerts
  System-generated alerts for at-risk students
  - `id` (uuid, primary key)
  - `student_id` (uuid, FK)
  - `alert_type` (text) - high_risk, attendance_drop, performance_decline, behavioral_anomaly
  - `severity` (text) - low, medium, high, critical
  - `message` (text)
  - `acknowledged` (boolean)
  - `acknowledged_by` (uuid, FK to profiles)
  - `acknowledged_at` (timestamptz)
  - `created_at` (timestamptz)

  ### 7. interventions
  Intervention actions and tracking
  - `id` (uuid, primary key)
  - `student_id` (uuid, FK)
  - `assigned_to` (uuid, FK to profiles)
  - `intervention_type` (text) - mentoring, counseling, remedial, academic_support
  - `description` (text)
  - `status` (text) - pending, in_progress, completed
  - `outcome_notes` (text)
  - `created_at` (timestamptz)
  - `updated_at` (timestamptz)
  - `completed_at` (timestamptz)

  ## Security
  - Enable RLS on all tables
  - Policies for role-based access (faculty, administrator, counselor)
  - Authentication required for all data access
*/

-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text NOT NULL,
  full_name text NOT NULL,
  role text NOT NULL CHECK (role IN ('faculty', 'administrator', 'counselor')),
  department text,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Create students table
CREATE TABLE IF NOT EXISTS students (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id text UNIQUE NOT NULL,
  full_name text NOT NULL,
  email text NOT NULL,
  department text NOT NULL,
  program text NOT NULL,
  year_level integer NOT NULL DEFAULT 1,
  semester text NOT NULL,
  enrollment_date date DEFAULT CURRENT_DATE,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'graduated', 'dropped')),
  created_at timestamptz DEFAULT now()
);

ALTER TABLE students ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view students"
  ON students FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Administrators can insert students"
  ON students FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role = 'administrator'
    )
  );

CREATE POLICY "Administrators can update students"
  ON students FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role = 'administrator'
    )
  );

-- Create risk_assessments table
CREATE TABLE IF NOT EXISTS risk_assessments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  risk_level text NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
  risk_score numeric NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
  confidence_level numeric NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 1),
  factors jsonb DEFAULT '{}',
  prediction_date timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

ALTER TABLE risk_assessments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view risk assessments"
  ON risk_assessments FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Administrators can manage risk assessments"
  ON risk_assessments FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role = 'administrator'
    )
  );

-- Create academic_records table
CREATE TABLE IF NOT EXISTS academic_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  semester text NOT NULL,
  course_code text NOT NULL,
  course_name text NOT NULL,
  grade numeric NOT NULL,
  credits integer NOT NULL DEFAULT 3,
  gpa numeric NOT NULL,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE academic_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view academic records"
  ON academic_records FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Administrators can manage academic records"
  ON academic_records FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role = 'administrator'
    )
  );

-- Create attendance_records table
CREATE TABLE IF NOT EXISTS attendance_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  date date NOT NULL,
  status text NOT NULL CHECK (status IN ('present', 'absent', 'late', 'excused')),
  course_code text NOT NULL,
  semester text NOT NULL,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE attendance_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view attendance records"
  ON attendance_records FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Faculty and administrators can manage attendance"
  ON attendance_records FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('faculty', 'administrator')
    )
  );

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  alert_type text NOT NULL CHECK (alert_type IN ('high_risk', 'attendance_drop', 'performance_decline', 'behavioral_anomaly')),
  severity text NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  message text NOT NULL,
  acknowledged boolean DEFAULT false,
  acknowledged_by uuid REFERENCES profiles(id),
  acknowledged_at timestamptz,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view alerts"
  ON alerts FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can acknowledge alerts"
  ON alerts FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (acknowledged_by = auth.uid());

CREATE POLICY "Administrators can create alerts"
  ON alerts FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role = 'administrator'
    )
  );

-- Create interventions table
CREATE TABLE IF NOT EXISTS interventions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  assigned_to uuid NOT NULL REFERENCES profiles(id),
  intervention_type text NOT NULL CHECK (intervention_type IN ('mentoring', 'counseling', 'remedial', 'academic_support')),
  description text NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
  outcome_notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  completed_at timestamptz
);

ALTER TABLE interventions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view interventions"
  ON interventions FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Assigned users can update interventions"
  ON interventions FOR UPDATE
  TO authenticated
  USING (assigned_to = auth.uid())
  WITH CHECK (assigned_to = auth.uid());

CREATE POLICY "Administrators and counselors can create interventions"
  ON interventions FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('administrator', 'counselor')
    )
  );

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_students_department ON students(department);
CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_student ON risk_assessments(student_id);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_level ON risk_assessments(risk_level);
CREATE INDEX IF NOT EXISTS idx_academic_records_student ON academic_records(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_records_student ON attendance_records(student_id);
CREATE INDEX IF NOT EXISTS idx_alerts_student ON alerts(student_id);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_interventions_student ON interventions(student_id);
CREATE INDEX IF NOT EXISTS idx_interventions_assigned ON interventions(assigned_to);
CREATE INDEX IF NOT EXISTS idx_interventions_status ON interventions(status);