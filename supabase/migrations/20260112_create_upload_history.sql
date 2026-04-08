/*
  Upload history tracking for the EWS app.

  Goal: support reliable file history UI + Delete + Apply workflows without redesigning
  the rest of the schema.

  Notes:
  - We store the file payload on the backend filesystem (not in Supabase) and persist
    metadata/status here.
  - We keep a single "active" upload at a time (applied/current dataset).
*/

CREATE TABLE IF NOT EXISTS upload_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  filename text NOT NULL,
  content_type text,
  file_size_bytes bigint,
  stored_path text NOT NULL,

  status text NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'success', 'failed', 'deleted')),
  error text,

  rows_processed integer NOT NULL DEFAULT 0,
  students_created integer NOT NULL DEFAULT 0,
  academic_records_created integer NOT NULL DEFAULT 0,
  attendance_records_created integer NOT NULL DEFAULT 0,
  risk_assessments_created integer NOT NULL DEFAULT 0,

  uploaded_at timestamptz NOT NULL DEFAULT now(),
  applied_at timestamptz,
  is_active boolean NOT NULL DEFAULT false
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_upload_history_uploaded_at ON upload_history(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_upload_history_is_active ON upload_history(is_active);

