-- Additional database migrations for Early Warning System
-- These tables extend the base schema with behavioral indicators and enhanced tracking

-- ============================================================================
-- Behavioral Indicators Table
-- ============================================================================
-- Tracks behavioral indicators that contribute to risk assessment

CREATE TABLE IF NOT EXISTS behavioral_indicators (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  indicator_type text NOT NULL CHECK (indicator_type IN (
    'late_submission', 
    'missed_deadline', 
    'low_participation', 
    'irregular_attendance_pattern',
    'grade_variance',
    'sudden_change'
  )),
  indicator_value numeric NOT NULL,
  indicator_description text,
  semester text NOT NULL,
  detected_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

ALTER TABLE behavioral_indicators ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view behavioral indicators"
  ON behavioral_indicators FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Administrators can manage behavioral indicators"
  ON behavioral_indicators FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role = 'administrator'
    )
  );

CREATE INDEX IF NOT EXISTS idx_behavioral_indicators_student ON behavioral_indicators(student_id);
CREATE INDEX IF NOT EXISTS idx_behavioral_indicators_type ON behavioral_indicators(indicator_type);
CREATE INDEX IF NOT EXISTS idx_behavioral_indicators_detected ON behavioral_indicators(detected_at);

-- ============================================================================
-- Risk Assessment History Table
-- ============================================================================
-- Enhanced tracking of risk assessment history with change tracking
-- Note: This complements the existing risk_assessments table with additional metadata

ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS change_from_previous numeric;
ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS previous_risk_level text CHECK (previous_risk_level IN ('low', 'medium', 'high'));
ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS evaluation_method text DEFAULT 'rule_based' CHECK (evaluation_method IN ('rule_based', 'ml', 'hybrid'));

-- Create a function to track risk history
CREATE OR REPLACE FUNCTION log_risk_assessment_history()
RETURNS TRIGGER AS $$
BEGIN
  -- Update change_from_previous if this is not the first assessment
  IF EXISTS (
    SELECT 1 FROM risk_assessments 
    WHERE student_id = NEW.student_id 
    AND id != NEW.id 
    ORDER BY created_at DESC 
    LIMIT 1
  ) THEN
    SELECT 
      risk_score - NEW.risk_score,
      risk_level
    INTO 
      NEW.change_from_previous,
      NEW.previous_risk_level
    FROM risk_assessments
    WHERE student_id = NEW.student_id
    AND id != NEW.id
    ORDER BY created_at DESC
    LIMIT 1;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically log changes
DROP TRIGGER IF EXISTS trigger_log_risk_history ON risk_assessments;
CREATE TRIGGER trigger_log_risk_history
  BEFORE INSERT ON risk_assessments
  FOR EACH ROW
  EXECUTE FUNCTION log_risk_assessment_history();

-- ============================================================================
-- Alert Escalation Tracking
-- ============================================================================
-- Track alert escalation over time

ALTER TABLE alerts ADD COLUMN IF NOT EXISTS escalation_level integer DEFAULT 0 CHECK (escalation_level >= 0);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS escalated_at timestamptz;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS resolved_at timestamptz;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS resolved_by uuid REFERENCES profiles(id);

-- ============================================================================
-- Intervention Outcomes
-- ============================================================================
-- Enhanced intervention tracking with outcome metrics

ALTER TABLE interventions ADD COLUMN IF NOT EXISTS outcome_rating integer CHECK (outcome_rating >= 1 AND outcome_rating <= 5);
ALTER TABLE interventions ADD COLUMN IF NOT EXISTS risk_score_before numeric;
ALTER TABLE interventions ADD COLUMN IF NOT EXISTS risk_score_after numeric;
ALTER TABLE interventions ADD COLUMN IF NOT EXISTS effectiveness_score numeric;

-- ============================================================================
-- Student Metadata Table
-- ============================================================================
-- Additional metadata for students (first-generation, demographics, etc.)

CREATE TABLE IF NOT EXISTS student_metadata (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
  is_first_generation boolean DEFAULT false,
  demographic_data jsonb DEFAULT '{}',
  additional_notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE student_metadata ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view student metadata"
  ON student_metadata FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Administrators can manage student metadata"
  ON student_metadata FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role = 'administrator'
    )
  );

CREATE INDEX IF NOT EXISTS idx_student_metadata_student ON student_metadata(student_id);

-- ============================================================================
-- Monitoring Log Table
-- ============================================================================
-- Log monitoring activities and automated assessments

CREATE TABLE IF NOT EXISTS monitoring_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  evaluation_type text NOT NULL CHECK (evaluation_type IN ('scheduled', 'manual', 'triggered')),
  students_evaluated integer DEFAULT 0,
  alerts_created integer DEFAULT 0,
  interventions_created integer DEFAULT 0,
  execution_time_seconds numeric,
  status text NOT NULL CHECK (status IN ('success', 'partial', 'failed')),
  error_message text,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE monitoring_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view monitoring logs"
  ON monitoring_logs FOR SELECT
  TO authenticated
  USING (true);

CREATE INDEX IF NOT EXISTS idx_monitoring_logs_created ON monitoring_logs(created_at);

-- ============================================================================
-- Views for Common Queries
-- ============================================================================

-- View: Students with latest risk assessment
CREATE OR REPLACE VIEW students_with_risk AS
SELECT 
  s.*,
  ra.risk_level,
  ra.risk_score,
  ra.confidence_level,
  ra.created_at as last_risk_assessment_date
FROM students s
LEFT JOIN LATERAL (
  SELECT * FROM risk_assessments
  WHERE student_id = s.id
  ORDER BY created_at DESC
  LIMIT 1
) ra ON true;

-- View: Active alerts by department
CREATE OR REPLACE VIEW department_alerts AS
SELECT 
  s.department,
  COUNT(a.id) as total_alerts,
  COUNT(CASE WHEN a.acknowledged = false THEN 1 END) as unacknowledged_alerts,
  COUNT(CASE WHEN a.severity = 'critical' THEN 1 END) as critical_alerts,
  COUNT(CASE WHEN a.severity = 'high' THEN 1 END) as high_alerts
FROM students s
JOIN alerts a ON a.student_id = s.id
WHERE s.status = 'active'
GROUP BY s.department;

-- View: Intervention effectiveness
CREATE OR REPLACE VIEW intervention_effectiveness AS
SELECT 
  i.intervention_type,
  COUNT(*) as total_interventions,
  COUNT(CASE WHEN i.status = 'completed' THEN 1 END) as completed,
  AVG(i.effectiveness_score) as avg_effectiveness,
  AVG(CASE WHEN i.risk_score_before IS NOT NULL AND i.risk_score_after IS NOT NULL 
    THEN (i.risk_score_before - i.risk_score_after) 
    END) as avg_risk_reduction
FROM interventions i
GROUP BY i.intervention_type;

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Get student risk summary
CREATE OR REPLACE FUNCTION get_student_risk_summary(student_uuid uuid)
RETURNS TABLE (
  student_id uuid,
  current_risk_level text,
  current_risk_score numeric,
  risk_trend text,
  alert_count integer,
  intervention_count integer,
  last_assessment_date timestamptz
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    s.id,
    ra.risk_level,
    ra.risk_score,
    CASE 
      WHEN ra.change_from_previous > 10 THEN 'increasing'
      WHEN ra.change_from_previous < -10 THEN 'decreasing'
      ELSE 'stable'
    END as risk_trend,
    COUNT(DISTINCT a.id)::integer as alert_count,
    COUNT(DISTINCT i.id)::integer as intervention_count,
    ra.created_at as last_assessment_date
  FROM students s
  LEFT JOIN LATERAL (
    SELECT * FROM risk_assessments
    WHERE risk_assessments.student_id = s.id
    ORDER BY created_at DESC
    LIMIT 1
  ) ra ON true
  LEFT JOIN alerts a ON a.student_id = s.id AND a.acknowledged = false
  LEFT JOIN interventions i ON i.student_id = s.id AND i.status IN ('pending', 'in_progress')
  WHERE s.id = student_uuid
  GROUP BY s.id, ra.risk_level, ra.risk_score, ra.change_from_previous, ra.created_at;
END;
$$ LANGUAGE plpgsql;

-- Function: Get department risk statistics
CREATE OR REPLACE FUNCTION get_department_risk_stats(dept_name text)
RETURNS TABLE (
  department text,
  total_students bigint,
  low_risk bigint,
  medium_risk bigint,
  high_risk bigint,
  avg_risk_score numeric,
  high_risk_percentage numeric
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    s.department,
    COUNT(DISTINCT s.id) as total_students,
    COUNT(DISTINCT CASE WHEN ra.risk_level = 'low' THEN s.id END) as low_risk,
    COUNT(DISTINCT CASE WHEN ra.risk_level = 'medium' THEN s.id END) as medium_risk,
    COUNT(DISTINCT CASE WHEN ra.risk_level = 'high' THEN s.id END) as high_risk,
    AVG(ra.risk_score) as avg_risk_score,
    (COUNT(DISTINCT CASE WHEN ra.risk_level = 'high' THEN s.id END)::numeric / 
     NULLIF(COUNT(DISTINCT s.id), 0) * 100) as high_risk_percentage
  FROM students s
  LEFT JOIN LATERAL (
    SELECT * FROM risk_assessments
    WHERE risk_assessments.student_id = s.id
    ORDER BY created_at DESC
    LIMIT 1
  ) ra ON true
  WHERE s.status = 'active'
  AND (dept_name IS NULL OR s.department = dept_name)
  GROUP BY s.department;
END;
$$ LANGUAGE plpgsql;
