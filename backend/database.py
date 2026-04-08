"""
Database connection and utilities for Supabase integration.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client
from config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database wrapper for Supabase operations."""

    @staticmethod
    def _is_missing_column_error(e: Exception, table: str, column: str) -> bool:
        # Supabase/PostgREST missing-column errors often look like:
        # {'code': 'PGRST204', 'message': "Could not find the 'status' column of 'students' in the schema cache"}
        s = str(e)
        # PostgREST schema-cache error (common right after schema changes)
        if ("PGRST204" in s) and (f"'{column}'" in s) and (f"'{table}'" in s) and ("schema cache" in s):
            return True
        # Postgres error (e.g. when filtering by a missing column)
        if ("42703" in s) and (f"{table}.{column}" in s) and ("does not exist" in s):
            return True
        return False
    
    def __init__(self):
        """Initialize Supabase client."""
        try:
            # Check if credentials are provided
            logger.info(f"DB Init - URL: '{settings.supabase_url[:10]}...', Key length: {len(settings.supabase_key)}")
            if not settings.supabase_url or not settings.supabase_key:
                logger.error("Supabase credentials missing!")
                logger.error(f"SUPABASE_URL: {'Set' if settings.supabase_url else 'MISSING'}")
                logger.error(f"SUPABASE_KEY: {'Set' if settings.supabase_key else 'MISSING'}")
                logger.error("Please set SUPABASE_URL and SUPABASE_KEY environment variables")
                self.client = None
                return
            
            # CRITICAL: Verify we're using service role key (not anon key)
            supabase_key = settings.supabase_key
            # New Supabase keys use sb_secret_/sb_publishable_ format (shorter than old JWTs) — skip length warning for these.
            _is_new_key_format = supabase_key.startswith("sb_secret_") or supabase_key.startswith("sb_publishable_")
            if not supabase_key or (len(supabase_key) < 100 and not _is_new_key_format):
                logger.error("=" * 80)
                logger.error("❌ WARNING: SUPABASE_KEY appears to be too short!")
                logger.error("Service role keys are typically 200+ characters long.")
                logger.error("If you're using the anon key, database operations will fail due to RLS.")
                logger.error("Please verify your .env file contains the SERVICE ROLE KEY.")
                logger.error("=" * 80)
            
            self.client: Client = create_client(
                settings.supabase_url,
                supabase_key
            )
            
            # Test connection by trying a simple query
            try:
                test_response = self.client.table('students').select('id').limit(1).execute()
                logger.info("Database connection established and verified")
                
                # CRITICAL: Test that we can actually INSERT (to verify RLS bypass)
                # We'll do a quick test insert and then delete it
                try:
                    test_insert = {
                        'student_id': '__TEST_RLS_BYPASS__',
                        'full_name': 'RLS Test',
                        'email': 'test@example.com',
                        'department': 'Test',
                        'program': 'Test',
                        'year_level': 1,
                        'semester': 'Test'
                    }
                    # Prefer returning representation so response.data is populated (some PostgREST configs may default to minimal)
                    try:
                        test_result = self.client.table('students').insert(test_insert, returning="representation").execute()
                    except TypeError:
                        test_result = self.client.table('students').insert(test_insert).execute()
                    if test_result.data:
                        # Clean up test record
                        test_id = test_result.data[0].get('id')
                        if test_id:
                            self.client.table('students').delete().eq('id', test_id).execute()
                        logger.info("✅ RLS bypass verified - service role key is working correctly")
                    else:
                        logger.error("=" * 80)
                        logger.error("❌ CRITICAL: RLS bypass test FAILED!")
                        logger.error("The backend cannot insert into students table.")
                        logger.error("This means RLS is blocking operations.")
                        logger.error("Please verify SUPABASE_KEY is the SERVICE ROLE KEY.")
                        logger.error("=" * 80)
                except Exception as rls_test_error:
                    logger.error("=" * 80)
                    logger.error("❌ CRITICAL: RLS bypass test FAILED!")
                    logger.error(f"Error: {rls_test_error}")
                    logger.error("The backend cannot insert into students table.")
                    logger.error("Please verify SUPABASE_KEY is the SERVICE ROLE KEY (not anon key).")
                    logger.error("Service role keys are 200+ characters and start with 'eyJ'")
                    logger.error("=" * 80)
            except Exception as test_error:
                logger.warning(f"Database connection created but test query failed: {test_error}")
                logger.warning("This might indicate table permissions or schema issues")
                # Still set client - might work for inserts
                
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}", exc_info=True)
            logger.error("Backend will start but database operations will fail.")
            logger.error("Please check your Supabase credentials in environment variables or .env file")
            # Don't raise - allow server to start even if DB connection fails
            self.client = None
    
    def get_students(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch students with optional filters."""
        if self.client is None:
            logger.error("Database client not initialized. Check Supabase credentials.")
            return []
        try:
            query = self.client.table('students').select('*')
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            if limit:
                query = query.limit(limit).offset(offset)
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            # Backwards/forwards compatibility: some user-created schemas may omit `students.status`.
            if filters and ("status" in filters) and self._is_missing_column_error(e, table="students", column="status"):
                try:
                    new_filters = {k: v for k, v in filters.items() if k != "status"}
                    query = self.client.table('students').select('*')
                    for key, value in new_filters.items():
                        query = query.eq(key, value)
                    if limit:
                        query = query.limit(limit).offset(offset)
                    response = query.execute()
                    return response.data or []
                except Exception as e2:
                    logger.error(f"Error fetching students (retry without status filter): {e2}")
                    return []

            logger.error(f"Error fetching students: {e}")
            return []

    # ---------------------------------------------------------------------
    # Upload history (file lifecycle)
    # ---------------------------------------------------------------------

    def list_upload_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent uploads (newest first)."""
        if self.client is None:
            logger.error("Database client not initialized. Cannot list upload history.")
            return []
        resp = self.client.table("upload_history").select("*").order("uploaded_at", desc=True).limit(limit).execute()
        return resp.data or []

    def get_upload_history(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single upload history record."""
        if self.client is None:
            logger.error("Database client not initialized. Cannot fetch upload history.")
            return None
        resp = self.client.table("upload_history").select("*").eq("id", upload_id).limit(1).execute()
        if resp.data:
            return resp.data[0]
        return None

    def create_upload_history(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create an upload history row."""
        if self.client is None:
            logger.error("Database client not initialized. Cannot create upload history.")
            return None
        try:
            try:
                resp = self.client.table("upload_history").insert(row, returning="representation").execute()
            except TypeError:
                resp = self.client.table("upload_history").insert(row).execute()
            return (resp.data or [None])[0]
        except Exception as e:
            logger.error(f"Error creating upload history: {e}", exc_info=True)
            return None

    def update_upload_history(self, upload_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an upload history row."""
        if self.client is None:
            logger.error("Database client not initialized. Cannot update upload history.")
            return None
        try:
            resp = self.client.table("upload_history").update(updates).eq("id", upload_id).execute()
            return (resp.data or [None])[0]
        except Exception as e:
            logger.error(f"Error updating upload history {upload_id}: {e}", exc_info=True)
            return None

    def set_active_upload(self, upload_id: str) -> None:
        """Mark exactly one upload as active."""
        if self.client is None:
            logger.error("Database client not initialized. Cannot set active upload.")
            return
        try:
            # Clear active flag from all (best-effort)
            # PostgREST requires a filter; avoid UUID columns with non-UUID sentinel.
            self.client.table("upload_history").update({"is_active": False}).neq("filename", "__NEVER_MATCH__").execute()
            # Set active on chosen one
            self.client.table("upload_history").update({"is_active": True, "applied_at": datetime.utcnow().isoformat()}).eq("id", upload_id).execute()
        except Exception as e:
            logger.error(f"Error setting active upload {upload_id}: {e}", exc_info=True)

    
    def get_student_by_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single student by ID."""
        if self.client is None:
            logger.warning("Database client not initialized. Cannot fetch student.")
            return None
        try:
            response = self.client.table('students').select('*').eq('id', student_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching student {student_id}: {e}")
            return None

    def get_students_by_ids(self, student_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch students by a list of UUID ids (minimal fields for list endpoints)."""
        if self.client is None:
            logger.warning("Database client not initialized. Cannot fetch students.")
            return []
        if not student_ids:
            return []
        try:
            query = self.client.table("students").select("id,student_id,full_name")
            try:
                query = query.in_("id", student_ids)
                resp = query.execute()
                return resp.data or []
            except Exception:
                # Fallback: bounded fetch and filter in Python
                resp = self.client.table("students").select("id,student_id,full_name").limit(max(len(student_ids), 100)).execute()
                rows = resp.data or []
                wanted = set(student_ids)
                return [r for r in rows if r.get("id") in wanted]
        except Exception as e:
            logger.error(f"Error fetching students by ids: {e}")
            return []
    
    def get_student_by_roll_number(self, roll_number: str) -> Optional[Dict[str, Any]]:
        """Fetch a single student by roll number."""
        if self.client is None:
            logger.warning("Database client not initialized. Cannot fetch student.")
            return None
        try:
            response = self.client.table('students').select('*').eq('student_id', roll_number).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching student by roll number {roll_number}: {e}")
            return None
    
    def create_student(self, student: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new student."""
        if self.client is None:
            logger.error("=" * 80)
            logger.error("❌ DATABASE CLIENT NOT INITIALIZED!")
            logger.error("Cannot create student. Database operations will fail.")
            logger.error("Check your .env file for SUPABASE_URL and SUPABASE_KEY")
            logger.error("SUPABASE_KEY must be the SERVICE ROLE KEY (not anon key)")
            logger.error("=" * 80)
            return None
        try:
            logger.debug(f"Creating student: {student.get('full_name', 'Unknown')} (Roll: {student.get('student_id', 'N/A')})")

            # Schema-compat: in the canonical migration `students.status` has a default ('active'),
            # and some user-created schemas omit this column entirely. If status is just 'active',
            # omit it from inserts so both schemas work.
            student_to_insert: Dict[str, Any] = dict(student)
            if student_to_insert.get("status") == "active":
                student_to_insert.pop("status", None)

            # Prefer returning representation so response.data is populated reliably.
            # Also, be resilient to user-created schemas that omit some columns (e.g. enrollment_date).
            response = None
            for _ in range(5):
                try:
                    try:
                        response = self.client.table('students').insert(student_to_insert, returning="representation").execute()
                    except TypeError:
                        response = self.client.table('students').insert(student_to_insert).execute()
                    break
                except Exception as insert_error:
                    s = str(insert_error)
                    if "PGRST204" in s and "Could not find the '" in s and "' column of 'students'" in s:
                        # Parse missing column name and retry without it.
                        try:
                            missing = s.split("Could not find the '", 1)[1].split("' column of 'students'", 1)[0]
                            student_to_insert.pop(missing, None)
                            continue
                        except Exception:
                            raise
                    raise
            if response.data and len(response.data) > 0:
                created_student = response.data[0]
                logger.debug(f"✅ Successfully created student: {student.get('full_name', 'Unknown')} (ID: {created_student.get('id')})")
                return created_student
            else:
                logger.error("=" * 80)
                logger.error(f"❌ Student insert returned no data!")
                logger.error(f"Student data: {student}")
                logger.error(f"Response type: {type(response)}")
                # Try to get error message from response
                if hasattr(response, 'error'):
                    logger.error(f"Supabase error: {response.error}")
                if hasattr(response, 'message'):
                    logger.error(f"Supabase message: {response.message}")
                # Check response.data attribute
                if hasattr(response, 'data'):
                    logger.error(f"Response.data: {response.data}")
                logger.error("This usually indicates:")
                logger.error("  1. RLS (Row Level Security) is blocking the insert")
                logger.error("  2. SUPABASE_KEY is not the service role key")
                logger.error("  3. Table permissions issue")
                logger.error("=" * 80)
                return None
        except Exception as e:
            # Extract detailed error information
            error_msg = str(e)
            error_type = type(e).__name__
            
            # Check for duplicate key error (student_id is UNIQUE)
            if 'duplicate key' in error_msg.lower() or 'unique constraint' in error_msg.lower() or 'already exists' in error_msg.lower():
                logger.warning(f"Student with student_id '{student.get('student_id')}' already exists. Attempting to fetch existing student.")
                # Try to fetch the existing student
                try:
                    existing = self.get_student_by_roll_number(student.get('student_id', ''))
                    if existing:
                        logger.info(f"Found existing student: {student.get('full_name')} (ID: {existing.get('id')})")
                        return existing
                except Exception as fetch_error:
                    logger.error(f"Failed to fetch existing student: {fetch_error}")
            
            # Check for RLS/permission errors
            if 'permission' in error_msg.lower() or 'policy' in error_msg.lower() or 'row level security' in error_msg.lower():
                logger.error("=" * 80)
                logger.error("ROW LEVEL SECURITY (RLS) ERROR DETECTED!")
                logger.error("The backend must use the SERVICE ROLE KEY (not anon key) to bypass RLS.")
                logger.error("Please check your .env file:")
                logger.error("  SUPABASE_KEY should be the SERVICE ROLE KEY (starts with 'eyJ' and is longer)")
                logger.error("  SUPABASE_ANON_KEY is for frontend only")
                logger.error("=" * 80)
            
            logger.error(f"Error creating student ({error_type}): {error_msg}", exc_info=True)
            logger.error(f"Student data that failed: {student}")
            
            # Try to extract more details from the exception
            if hasattr(e, 'message'):
                logger.error(f"Exception message: {e.message}")
            if hasattr(e, 'details'):
                logger.error(f"Exception details: {e.details}")
            if hasattr(e, 'hint'):
                logger.error(f"Exception hint: {e.hint}")
            if hasattr(e, 'code'):
                logger.error(f"Exception code: {e.code}")
            
            return None
    
    def create_academic_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new academic record."""
        if self.client is None:
            logger.error("Database client not initialized. Cannot create academic record.")
            return None
        try:
            try:
                response = self.client.table('academic_records').insert(record, returning="representation").execute()
            except TypeError:
                response = self.client.table('academic_records').insert(record).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                logger.error(f"Academic record insert returned no data. Response: {response}")
                # Try to get error message from response
                if hasattr(response, 'error'):
                    logger.error(f"Supabase error: {response.error}")
                return None
        except Exception as e:
            error_msg = str(e)
            # Check for duplicate or constraint errors
            if 'duplicate key' in error_msg.lower() or 'unique constraint' in error_msg.lower():
                logger.debug(f"Academic record may already exist (duplicate key): {record.get('course_code')}")
                return None  # Not an error - record already exists
            logger.error(f"Error creating academic record: {e}", exc_info=True)
            logger.error(f"Record data that failed: {record}")
            return None
    
    def create_attendance_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new attendance record."""
        if self.client is None:
            logger.error("Database client not initialized. Cannot create attendance record.")
            return None
        try:
            try:
                response = self.client.table('attendance_records').insert(record, returning="representation").execute()
            except TypeError:
                response = self.client.table('attendance_records').insert(record).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                logger.error(f"Attendance record insert returned no data. Response: {response}")
                # Try to get error message from response
                if hasattr(response, 'error'):
                    logger.error(f"Supabase error: {response.error}")
                return None
        except Exception as e:
            error_msg = str(e)
            # Check for duplicate or constraint errors
            if 'duplicate key' in error_msg.lower() or 'unique constraint' in error_msg.lower():
                logger.debug(f"Attendance record may already exist (duplicate key): {record.get('date')}")
                return None  # Not an error - record already exists
            logger.error(f"Error creating attendance record: {e}", exc_info=True)
            logger.error(f"Record data that failed: {record}")
            return None
    
    def bulk_create_academic_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk create academic records."""
        if self.client is None:
            logger.warning("Database client not initialized. Cannot create academic records.")
            return []
        try:
            try:
                response = self.client.table('academic_records').insert(records, returning="representation").execute()
            except TypeError:
                response = self.client.table('academic_records').insert(records).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error bulk creating academic records: {e}")
            return []
    
    def bulk_create_attendance_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk create attendance records."""
        if self.client is None:
            logger.warning("Database client not initialized. Cannot create attendance records.")
            return []
        try:
            try:
                response = self.client.table('attendance_records').insert(records, returning="representation").execute()
            except TypeError:
                response = self.client.table('attendance_records').insert(records).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error bulk creating attendance records: {e}")
            return []
    
    def get_academic_records(
        self,
        student_id: Optional[str] = None,
        semester: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch academic records."""
        if self.client is None:
            logger.warning("Database client not initialized. Cannot fetch academic records.")
            return []
        try:
            query = self.client.table('academic_records').select('*')
            
            if student_id:
                query = query.eq('student_id', student_id)
            if semester:
                query = query.eq('semester', semester)
            
            query = query.order('semester', desc=True)
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching academic records: {e}")
            return []
    
    def get_attendance_records(
        self,
        student_id: Optional[str] = None,
        course_code: Optional[str] = None,
        semester: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch attendance records."""
        if self.client is None:
            logger.warning("Database client not initialized. Cannot fetch attendance records.")
            return []
        try:
            query = self.client.table('attendance_records').select('*')
            
            if student_id:
                query = query.eq('student_id', student_id)
            if course_code:
                query = query.eq('course_code', course_code)
            if semester:
                query = query.eq('semester', semester)
            
            query = query.order('date', desc=True)
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching attendance records: {e}")
            return []
    
    def get_risk_assessments(
        self,
        student_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch risk assessments."""
        if self.client is None:
            logger.warning("Database client not initialized. Cannot fetch risk assessments.")
            return []
        try:
            query = self.client.table('risk_assessments').select('*')
            
            if student_id:
                query = query.eq('student_id', student_id)
            
            query = query.order('created_at', desc=True)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching risk assessments: {e}")
            return []

    def get_risk_assessments_for_students(
        self,
        student_ids: List[str],
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch risk assessments for a set of students (ordered by created_at desc).

        This avoids fetching the entire risk_assessments table for list views.
        """
        if self.client is None:
            logger.warning("Database client not initialized. Cannot fetch risk assessments.")
            return []
        if not student_ids:
            return []
        try:
            # Select only the fields needed for list views (keeps payload smaller).
            query = (
                self.client.table("risk_assessments")
                .select("id,student_id,risk_level,risk_score,confidence_level,factors,prediction_date,created_at")
                .order("created_at", desc=True)
            )
            # Supabase python client uses in_ for IN filters.
            try:
                query = query.in_("student_id", student_ids)
            except Exception:
                # Fallback: limited fetch and filter in Python.
                all_rows = self.get_risk_assessments(limit=limit)
                wanted = set(student_ids)
                return [r for r in all_rows if r.get("student_id") in wanted]

            if limit:
                query = query.limit(limit)
            resp = query.execute()
            return resp.data or []
        except Exception as e:
            logger.error(f"Error fetching risk assessments for students: {e}")
            return []
    
    def create_risk_assessment(self, assessment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new risk assessment."""
        if self.client is None:
            logger.error("Database client not initialized. Cannot create risk assessment.")
            return None
        try:
            logger.info(f"🔵 Attempting to create risk assessment for student {assessment.get('student_id', 'unknown')}")
            logger.debug(f"Assessment data: {assessment}")
            
            # Ensure all required fields are present
            required_fields = ['student_id', 'risk_level', 'risk_score', 'confidence_level']
            for field in required_fields:
                if field not in assessment:
                    logger.error(f"Missing required field '{field}' in risk assessment data")
                    return None
            
            try:
                response = self.client.table('risk_assessments').insert(assessment, returning="representation").execute()
            except TypeError:
                response = self.client.table('risk_assessments').insert(assessment).execute()
            
            if response.data and len(response.data) > 0:
                created_assessment = response.data[0]
                logger.info(f"✅ Successfully created risk assessment: ID={created_assessment.get('id')}, Student={assessment.get('student_id')}, Risk={assessment.get('risk_level')}, Score={assessment.get('risk_score')}")
                return created_assessment
            else:
                logger.error("=" * 80)
                logger.error(f"❌ Risk assessment insert returned no data!")
                logger.error(f"Student ID: {assessment.get('student_id')}")
                logger.error(f"Risk Level: {assessment.get('risk_level')}")
                logger.error(f"Risk Score: {assessment.get('risk_score')}")
                
                # Try to get error message from response
                if hasattr(response, 'error'):
                    logger.error(f"Supabase error object: {response.error}")
                if hasattr(response, 'message'):
                    logger.error(f"Supabase message: {response.message}")
                
                # Try to get error from response attributes
                try:
                    error_info = getattr(response, 'error', None)
                    if error_info:
                        logger.error(f"Full error info: {error_info}")
                except:
                    pass
                
                # Check if response has any error indicators
                response_str = str(response)
                if 'error' in response_str.lower() or 'permission' in response_str.lower():
                    logger.error("Response indicates an error occurred")
                
                logger.error("=" * 80)
                return None
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Error creating risk assessment ({error_type}): {error_msg}", exc_info=True)
            logger.error(f"Assessment data that failed: student_id={assessment.get('student_id')}, risk_level={assessment.get('risk_level')}, risk_score={assessment.get('risk_score')}")
            
            # Check for RLS/permission errors
            if 'permission' in error_msg.lower() or 'policy' in error_msg.lower() or 'row level security' in error_msg.lower() or 'new row violates row-level security policy' in error_msg.lower():
                logger.error("=" * 80)
                logger.error("ROW LEVEL SECURITY (RLS) ERROR DETECTED for risk_assessments!")
                logger.error("The backend must use the SERVICE ROLE KEY (not anon key) to bypass RLS.")
                logger.error("Current SUPABASE_KEY length: " + str(len(settings.supabase_key)) + " characters")
                logger.error("Service role keys are typically 200+ characters.")
                logger.error("Please check your .env file and verify SUPABASE_KEY is the SERVICE ROLE KEY.")
                logger.error("=" * 80)
            
            # Try to extract more details from the exception
            if hasattr(e, 'message'):
                logger.error(f"Exception message: {e.message}")
            if hasattr(e, 'details'):
                logger.error(f"Exception details: {e.details}")
            if hasattr(e, 'hint'):
                logger.error(f"Exception hint: {e.hint}")
            if hasattr(e, 'code'):
                logger.error(f"Exception code: {e.code}")
            
            return None
    
    def create_alert(self, alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new alert."""
        if self.client is None:
            logger.error("Database client not initialized. Cannot create alert.")
            return None
        try:
            try:
                response = self.client.table('alerts').insert(alert, returning="representation").execute()
            except TypeError:
                response = self.client.table('alerts').insert(alert).execute()
            if response.data and len(response.data) > 0:
                logger.debug(f"Successfully created alert: {alert.get('alert_type', 'Unknown')} for student {alert.get('student_id')}")
                return response.data[0]
            else:
                logger.error(f"Alert insert returned no data. Response: {response}")
                # Try to get error message from response
                if hasattr(response, 'error'):
                    logger.error(f"Supabase error: {response.error}")
                return None
        except Exception as e:
            error_msg = str(e)
            # Check for RLS/permission errors
            if 'permission' in error_msg.lower() or 'policy' in error_msg.lower() or 'row level security' in error_msg.lower():
                logger.error("=" * 80)
                logger.error("ROW LEVEL SECURITY (RLS) ERROR DETECTED for alerts!")
                logger.error("The backend must use the SERVICE ROLE KEY (not anon key) to bypass RLS.")
                logger.error("=" * 80)
            logger.error(f"Error creating alert: {e}", exc_info=True)
            logger.error(f"Alert data that failed: {alert}")
            return None
    
    def get_alerts(
        self,
        student_id: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        severity: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch alerts."""
        if self.client is None:
            logger.warning("Database client not initialized. Cannot fetch alerts.")
            return []
        try:
            # Select only what list pages need (smaller payload, faster).
            query = self.client.table('alerts').select(
                "id,student_id,alert_type,severity,message,acknowledged,acknowledged_by,acknowledged_at,created_at"
            )
            
            if student_id:
                query = query.eq('student_id', student_id)
            if acknowledged is not None:
                query = query.eq('acknowledged', acknowledged)
            if severity:
                query = query.eq('severity', severity)
            
            query = query.order('created_at', desc=True)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return []
    
    def update_alert(
        self,
        alert_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an alert."""
        try:
            response = self.client.table('alerts').update(updates).eq('id', alert_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating alert {alert_id}: {e}")
            return None
    
    def get_interventions(
        self,
        student_id: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch interventions."""
        try:
            query = self.client.table('interventions').select('*')
            
            if student_id:
                query = query.eq('student_id', student_id)
            if status:
                query = query.eq('status', status)
            if assigned_to:
                query = query.eq('assigned_to', assigned_to)
            
            query = query.order('created_at', desc=True)
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching interventions: {e}")
            return []
    
    def create_intervention(self, intervention: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new intervention."""
        try:
            row = dict(intervention)
            response = None
            # Be resilient to user-created schemas missing some columns (PGRST204)
            # or having NOT NULL constraints that we can't satisfy in demo mode.
            for attempt in range(6):
                try:
                    try:
                        response = self.client.table('interventions').insert(row, returning="representation").execute()
                    except TypeError:
                        response = self.client.table('interventions').insert(row).execute()
                    
                    if response.data and len(response.data) > 0:
                        return response.data[0]
                    else:
                        # If no data, check for error in response
                        err = getattr(response, 'error', None) or getattr(response, 'message', str(response))
                        raise Exception(f"Insert returned no data. Error: {err}")
                        
                except Exception as insert_error:
                    s = str(insert_error).lower()
                    logger.warning(f"Intervention creation attempt {attempt+1} failed: {s}")
                    
                    # 1. Handle missing columns (PGRST204)
                    if "pgrst204" in s or "could not find the '" in s:
                        try:
                            # Try to extract column name
                            if "could not find the '" in s:
                                missing = s.split("could not find the '", 1)[1].split("'", 1)[0]
                                logger.info(f"Removing missing column '{missing}' from intervention data")
                                row.pop(missing, None)
                                continue
                        except Exception:
                            pass
                    
                    # 2. Handle NOT NULL violations (Postgres 23502)
                    if "null value in column" in s and "violates not-null constraint" in s:
                        try:
                            column = s.split('column "', 1)[1].split('"', 1)[0]
                            logger.error(f"CRITICAL: Column '{column}' in 'interventions' table is NOT NULL but was not provided.")
                            logger.error("FIX: Run 'ALTER TABLE interventions ALTER COLUMN " + column + " DROP NOT NULL;' in Supabase SQL Editor.")
                            # If it's assigned_to, we are stuck unless we have a valid ID.
                            # We'll re-raise to the caller with a better message.
                            break
                        except Exception:
                            pass
                            
                    # 3. Handle Foreign Key violations (Postgres 23503)
                    if "violates foreign key constraint" in s:
                        logger.error(f"CRITICAL: Foreign key violation in 'interventions' table. Data: {row}")
                        break

                    if attempt == 5:
                        raise
                    continue
            return None
        except Exception as e:
            logger.error(f"Final error creating intervention: {e}")
            return None
    
    def update_intervention(
        self,
        intervention_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an intervention."""
        try:
            response = self.client.table('interventions').update(updates).eq('id', intervention_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating intervention {intervention_id}: {e}")
            return None

    def delete_intervention(self, intervention_id: str) -> bool:
        """Delete an intervention by id."""
        if self.client is None:
            logger.warning("Database client not initialized. Cannot delete intervention.")
            return False
        try:
            # PostgREST requires a filter; eq(id, ...) is fine.
            resp = self.client.table("interventions").delete().eq("id", intervention_id).execute()
            return bool(resp.data)
        except Exception as e:
            logger.error(f"Error deleting intervention {intervention_id}: {e}")
            return False
    
    def check_recent_alert(
        self,
        student_id: str,
        alert_type: str,
        hours: int = 24
    ) -> bool:
        """Check if a similar alert was created recently."""
        try:
            from datetime import datetime, timedelta
            cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            response = self.client.table('alerts').select('id').eq(
                'student_id', student_id
            ).eq('alert_type', alert_type).gte('created_at', cutoff).execute()
            
            return len(response.data or []) > 0
        except Exception as e:
            logger.error(f"Error checking recent alert: {e}")
            return False


# Global database instance
db = Database()
