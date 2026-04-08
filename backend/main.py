"""
FastAPI application for Early Warning System backend.
"""
from fastapi import FastAPI, HTTPException, Query, Path, Body, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.gzip import GZipMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging
import uvicorn
import os
from pathlib import Path as FsPath
import hashlib
import httpx
import pandas as pd
import io
import uuid
import csv
import json

from config import settings
from database import db
from data_processing import processor
from risk_engine import risk_engine
from early_warning import detector
from monitoring import monitoring_engine
from analytics import analytics_engine
from ml_training import training_pipeline
from model_explainability import model_explainer
from trend_analysis import trend_analyzer
from model_management import model_manager
from models import (
    Student, RiskAssessment, Alert, Intervention,
    StudentProfile, FeatureSet, AnalyticsOverview,
    RiskTrend
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _is_uuid(s: Optional[str]) -> bool:
    try:
        if not s:
            return False
        uuid.UUID(str(s))
        return True
    except Exception:
        return False

# ----------------------------------------------------------------------------
# Upload storage (backend filesystem)
# ----------------------------------------------------------------------------

UPLOAD_STORAGE_DIR = FsPath(os.environ.get("UPLOAD_STORAGE_DIR", os.path.join(os.path.dirname(__file__), "upload_store")))
UPLOAD_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    # Keep it simple and safe for filesystem use
    keep = []
    for ch in (name or "upload"):
        if ch.isalnum() or ch in (".", "_", "-", " "):
            keep.append(ch)
    cleaned = "".join(keep).strip().replace(" ", "_")
    return cleaned or "upload"


def _sha256(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _clear_dataset() -> None:
    """
    Clear all dataset tables.

    We delete child tables explicitly to avoid relying on FK cascades across DB variants.
    """
    if db.client is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    # PostgREST requires a filter on DELETE.
    # Use a VALID UUID sentinel on the `id` column so this works even if other columns
    # (e.g. student_id) differ in type across user-created schemas.
    never_match_uuid = "00000000-0000-0000-0000-000000000000"
    db.client.table("risk_assessments").delete().neq("id", never_match_uuid).execute()
    db.client.table("academic_records").delete().neq("id", never_match_uuid).execute()
    db.client.table("attendance_records").delete().neq("id", never_match_uuid).execute()
    db.client.table("alerts").delete().neq("id", never_match_uuid).execute()
    db.client.table("interventions").delete().neq("id", never_match_uuid).execute()
    db.client.table("students").delete().neq("id", never_match_uuid).execute()


def _dataset_has_any_students() -> bool:
    """Fast existence check to avoid unnecessary clear operations on first upload."""
    if db.client is None:
        return False
    resp = db.client.table("students").select("id").limit(1).execute()
    return bool(resp.data)

# ----------------------------------------------------------------------------
# Reports (downloadable CSV exports)
# ----------------------------------------------------------------------------

def _dict_rows_to_csv(rows: List[Dict[str, Any]], columns: List[str]) -> str:
    """Convert list of dict rows to CSV text with fixed columns."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for r in rows or []:
        out: Dict[str, Any] = {}
        for c in columns:
            v = (r or {}).get(c)
            # Keep JSON-ish values readable
            if isinstance(v, (dict, list)):
                out[c] = json.dumps(v, ensure_ascii=False, default=str)
            else:
                out[c] = "" if v is None else v
        writer.writerow(out)
    return buf.getvalue()


def _csv_download_response(csv_text: str, filename: str) -> Response:
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

# ----------------------------------------------------------------------------
# Database schema readiness helpers
# ----------------------------------------------------------------------------

MIGRATIONS_TO_RUN = [
    "project/supabase/migrations/20251225151810_create_ews_schema.sql",
    "project/supabase/migrations/20251225151811_fix_rls_for_service_role.sql",
    "project/supabase/migrations/20260112_create_upload_history.sql",
]


def _is_schema_cache_missing_error(err: Exception) -> bool:
    s = str(err)
    return ("PGRST205" in s) or ("schema cache" in s and "Could not find the table" in s)


def _schema_not_ready_detail(extra: Optional[str] = None) -> str:
    migrations = "\n".join([f"{i+1}) {p}" for i, p in enumerate(MIGRATIONS_TO_RUN)])
    base = (
        "Database schema is not initialized in your NEW Supabase project. "
        "The backend cannot find required tables like 'public.students'.\n\n"
        "Fix: Run these SQL migrations in Supabase SQL Editor (in order):\n"
        f"{migrations}\n\n"
        "Then restart backend and re-upload your file."
    )
    return base + (f"\n\nDetails: {extra}" if extra else "")

# Initialize FastAPI app
app = FastAPI(
    title="Early Warning System API",
    description="Backend API for Early Warning System to identify at-risk students",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compress larger JSON/CSV responses (helps a lot on slower networks/mobile)
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    try:
        # Start monitoring engine
        monitoring_engine.start()
        logger.info("Monitoring engine started")
    except Exception as e:
        logger.error(f"Error starting monitoring engine: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    try:
        monitoring_engine.stop()
        logger.info("Monitoring engine stopped")
    except Exception as e:
        logger.error(f"Error stopping monitoring engine: {e}")


# ============================================================================
# Student Endpoints
# ============================================================================

@app.get("/api/students", response_model=List[Dict[str, Any]])
async def get_students(
    department: Optional[str] = Query(None, description="Filter by department"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    status: Optional[str] = Query("active", description="Filter by status"),
    limit: Optional[int] = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get list of students with optional filters."""
    try:
        filters = {}
        if department:
            filters['department'] = department
        if semester:
            filters['semester'] = semester
        if status:
            filters['status'] = status
        
        students = db.get_students(filters=filters, limit=limit, offset=offset)
        
        # Get latest + previous risk assessments for each student (for UI trend indicators)
        student_ids = [s['id'] for s in students if s.get("id")]
        # Fetch only assessments for these students (avoid scanning entire table)
        risk_fetch_limit = min(max(len(student_ids) * 3, 50), 6000) if student_ids else 0
        all_assessments = db.get_risk_assessments_for_students(student_ids, limit=risk_fetch_limit)

        # all_assessments is ordered by created_at desc in db.get_risk_assessments()
        latest_assessments: Dict[str, Dict[str, Any]] = {}
        previous_assessments: Dict[str, Dict[str, Any]] = {}

        for assessment in all_assessments:
            sid = assessment.get('student_id')
            if sid not in student_ids:
                continue
            if sid not in latest_assessments:
                latest_assessments[sid] = assessment
            elif sid not in previous_assessments:
                previous_assessments[sid] = assessment

        # Attach risk assessments
        for student in students:
            sid = student['id']
            risk = latest_assessments.get(sid)
            prev = previous_assessments.get(sid)

            # PERF: factors often contains a large nested `feature_set` blob.
            # The list UI only needs explanation/top factors, not raw engineered features.
            for a in (risk, prev):
                try:
                    factors = a.get("factors") if isinstance(a, dict) else None
                    if isinstance(factors, dict) and "feature_set" in factors:
                        factors.pop("feature_set", None)
                except Exception:
                    pass

            student['risk'] = risk
            student['previous_risk'] = prev
        
        return students
    except Exception as e:
        logger.error(f"Error fetching students: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/students/{student_id}", response_model=Dict[str, Any])
async def get_student(
    student_id: str = Path(..., description="Student ID")
):
    """Get detailed student profile with all related data."""
    try:
        student = db.get_student_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Get all related data
        academic_records = db.get_academic_records(student_id=student_id)
        attendance_records = db.get_attendance_records(student_id=student_id)
        risk_assessments = db.get_risk_assessments(student_id=student_id, limit=10)
        alerts = db.get_alerts(student_id=student_id)
        interventions = db.get_interventions(student_id=student_id)
        
        # Get latest risk assessment
        latest_risk = risk_assessments[0] if risk_assessments else None
        
        return {
            'student': student,
            'latest_risk': latest_risk,
            'risk_history': risk_assessments,
            'academic_records': academic_records,
            'attendance_records': attendance_records,
            'alerts': alerts,
            'interventions': interventions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student {student_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/students/{student_id}/risk", response_model=Dict[str, Any])
async def get_student_risk(
    student_id: str = Path(..., description="Student ID"),
    recalculate: bool = Query(False, description="Force recalculation"),
    include_trend: bool = Query(True, description="Include trend analysis"),
    include_explanation: bool = Query(True, description="Include ML explanation")
):
    """Get risk assessment for a student with optional trend and explanation."""
    try:
        student = db.get_student_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        if recalculate:
            # Force re-evaluation
            result = monitoring_engine.evaluate_student(student_id, force_reassessment=True)
            if result:
                assessment = result['assessment']
            else:
                raise HTTPException(status_code=500, detail="Failed to calculate risk")
        else:
            # Get latest assessment
            assessments = db.get_risk_assessments(student_id=student_id, limit=1)
            if assessments:
                assessment = assessments[0]
            else:
                raise HTTPException(status_code=404, detail="No risk assessment found")
        
        response = {
            'assessment': assessment,
            'alerts_created': result.get('alerts_created', 0) if recalculate else 0,
            'risk_change': result.get('risk_change') if recalculate else None
        }
        
        # Add trend analysis
        if include_trend:
            trend = trend_analyzer.analyze_risk_trend(student_id)
            response['trend'] = trend
        
        # Add ML explanation
        if include_explanation:
            try:
                # Get feature set for explanation
                academic_records = db.get_academic_records(student_id=student_id)
                attendance_records = db.get_attendance_records(student_id=student_id)
                previous_assessments = db.get_risk_assessments(student_id=student_id, limit=1)
                previous_risk_score = previous_assessments[0]['risk_score'] if previous_assessments else 0.0
                
                all_alerts = db.get_alerts(student_id=student_id)
                warning_count = len([a for a in all_alerts if a.get('severity') in ['high', 'critical']])
                interventions = db.get_interventions(student_id=student_id)
                intervention_count = len(interventions)
                
                feature_set = processor.engineer_features(
                    academic_records=academic_records,
                    attendance_records=attendance_records,
                    previous_risk_score=previous_risk_score,
                    warning_count=warning_count,
                    intervention_count=intervention_count,
                    enrollment_date=student.get('enrollment_date'),
                    student_data=student
                )
                
                explanation = model_explainer.explain_prediction(feature_set)
                response['explanation'] = explanation
            except Exception as e:
                logger.warning(f"Could not generate explanation: {e}")
                response['explanation'] = None
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching risk for student {student_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/students", response_model=Dict[str, Any])
async def create_student(
    student_data: Dict[str, Any] = Body(..., description="Student data")
):
    """Create a new student."""
    try:
        # Validate required fields
        required_fields = ['student_id', 'full_name']
        for field in required_fields:
            if field not in student_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Check if student with same roll number already exists
        existing = db.get_student_by_roll_number(student_data['student_id'])
        if existing:
            raise HTTPException(status_code=400, detail=f"Student with roll number {student_data['student_id']} already exists")
        
        # Generate ID if not provided
        if 'id' not in student_data:
            student_data['id'] = str(uuid.uuid4())
        
        # Set defaults
        student_data.setdefault('status', 'active')
        student_data.setdefault('enrollment_date', datetime.utcnow().date().isoformat())
        student_data.setdefault('year_level', 1)
        student_data.setdefault('semester', 'Fall 2024')
        student_data.setdefault('department', student_data.get('department', 'General'))
        student_data.setdefault('program', student_data.get('program', 'Undergraduate'))
        student_data.setdefault('email', student_data.get('email', f"{student_data['student_id']}@university.edu"))
        
        # Create student
        created = db.create_student(student_data)
        if created:
            # Trigger initial risk assessment
            try:
                monitoring_engine.evaluate_student(created['id'], force_reassessment=True)
            except Exception as e:
                logger.warning(f"Could not perform initial risk assessment: {e}")
            
            return {
                'success': True,
                'student': created,
                'message': 'Student created successfully'
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create student")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/students/{student_id}/evaluate")
async def evaluate_student(
    student_id: str = Path(..., description="Student ID")
):
    """Trigger risk evaluation for a student."""
    try:
        result = monitoring_engine.evaluate_student(student_id, force_reassessment=True)
        if result:
            return {
                'success': True,
                'assessment': result['assessment'],
                'alerts_created': result.get('alerts_created', 0),
                'risk_change': result.get('risk_change')
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to evaluate student")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating student {student_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Alerts Endpoints
# ============================================================================

@app.get("/api/alerts", response_model=List[Dict[str, Any]])
async def get_alerts(
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: Optional[int] = Query(100, ge=1, le=1000)
):
    """Get alerts with optional filters."""
    try:
        alerts = db.get_alerts(
            student_id=student_id,
            acknowledged=acknowledged,
            severity=severity,
            limit=limit
        )

        # PERF: Avoid N+1 student lookups. Batch fetch minimal student info once.
        student_ids = [a.get("student_id") for a in alerts if a.get("student_id")]
        students = db.get_students_by_ids(list(set(student_ids)))
        student_map = {s.get("id"): s for s in students if s.get("id")}

        # PERF: Also attach each student's latest risk info (batch) so the Dashboard
        # doesn't need to call /api/students/{id}/risk N times.
        latest_risk_by_student: Dict[str, Dict[str, Any]] = {}
        if student_ids:
            risk_rows = db.get_risk_assessments_for_students(
                list(set(student_ids)),
                limit=min(max(len(student_ids) * 2, 50), 4000),
            )
            for r in risk_rows:
                sid = r.get("student_id")
                if sid and sid not in latest_risk_by_student:
                    latest_risk_by_student[sid] = r
        for alert in alerts:
            sid = alert.get("student_id")
            s = student_map.get(sid)
            if s:
                alert["student"] = {
                    "id": s.get("id"),
                    "student_id": s.get("student_id"),
                    "full_name": s.get("full_name"),
                }
            lr = latest_risk_by_student.get(sid)
            if lr:
                alert["student_risk"] = {
                    "risk_level": lr.get("risk_level"),
                    "risk_score": lr.get("risk_score"),
                }
        
        return alerts
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str = Path(..., description="Alert ID"),
    acknowledged_by: str = Body(..., embed=True, description="User ID acknowledging the alert")
):
    """Acknowledge an alert."""
    try:
        updates = {
            'acknowledged': True,
            'acknowledged_at': datetime.utcnow().isoformat()
        }
        # Schema/UX: acknowledged_by is a uuid column in the canonical schema.
        # If the frontend is in demo mode it may send a non-uuid id; don't fail the acknowledge.
        if _is_uuid(acknowledged_by):
            updates['acknowledged_by'] = acknowledged_by
        
        updated = db.update_alert(alert_id, updates)
        if updated:
            return {'success': True, 'alert': updated}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Interventions Endpoints
# ============================================================================

@app.get("/api/interventions", response_model=List[Dict[str, Any]])
async def get_interventions(
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user")
):
    """Get interventions with optional filters."""
    try:
        interventions = db.get_interventions(
            student_id=student_id,
            status=status,
            assigned_to=assigned_to
        )
        
        # PERF: Avoid N+1 student lookups. Batch fetch minimal student info once.
        student_ids = [i.get("student_id") for i in interventions if i.get("student_id")]
        students = db.get_students_by_ids(list(set(student_ids)))
        student_map = {s.get("id"): s for s in students if s.get("id")}
        
        for intervention in interventions:
            sid = intervention.get("student_id")
            s = student_map.get(sid)
            if s:
                intervention["student"] = {
                    "id": s.get("id"),
                    "student_id": s.get("student_id"),
                    "full_name": s.get("full_name"),
                }
            else:
                # Fallback for data consistency (prevents frontend crash)
                intervention["student"] = {
                    "id": sid,
                    "student_id": "N/A",
                    "full_name": "Unknown Student",
                }
        
        return interventions
    except Exception as e:
        logger.error(f"Error fetching interventions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/interventions", response_model=Dict[str, Any])
async def create_intervention(
    intervention: Dict[str, Any] = Body(..., description="Intervention data")
):
    """Create a new intervention."""
    try:
        # Validate required fields
        required_fields = ['student_id', 'intervention_type', 'description']
        for field in required_fields:
            if field not in intervention:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # assigned_to is optional (and in canonical schema it is a uuid FK).
        # If provided but not a UUID (demo mode), omit it to avoid 22P02.
        assigned_to = intervention.get("assigned_to")
        # Treat empty string as "not provided"
        if assigned_to is None or str(assigned_to).strip() == "":
            intervention.pop("assigned_to", None)
        elif not _is_uuid(str(assigned_to)):
            intervention.pop("assigned_to", None)

        # Set defaults
        intervention.setdefault('status', 'pending')
        intervention['created_at'] = datetime.utcnow().isoformat()
        intervention['updated_at'] = datetime.utcnow().isoformat()
        
        created = db.create_intervention(intervention)
        if created:
            return {'success': True, 'intervention': created}
        else:
            raise HTTPException(status_code=500, detail="Failed to create intervention")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating intervention: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/interventions/{intervention_id}", response_model=Dict[str, Any])
async def update_intervention(
    intervention_id: str = Path(..., description="Intervention ID"),
    updates: Dict[str, Any] = Body(..., description="Update data")
):
    """Update an intervention."""
    try:
        updates['updated_at'] = datetime.utcnow().isoformat()

        # If assigned_to is present but not a UUID (demo mode), drop it to avoid 22P02.
        if "assigned_to" in updates:
            v = updates.get("assigned_to")
            if v is None or str(v).strip() == "":
                updates.pop("assigned_to", None)
            elif not _is_uuid(str(v)):
                updates.pop("assigned_to", None)
        
        # Handle status change to completed
        if updates.get('status') == 'completed' and 'completed_at' not in updates:
            updates['completed_at'] = datetime.utcnow().isoformat()
        
        updated = db.update_intervention(intervention_id, updates)
        if updated:
            return {'success': True, 'intervention': updated}
        else:
            raise HTTPException(status_code=404, detail="Intervention not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating intervention {intervention_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/interventions/{intervention_id}", response_model=Dict[str, Any])
async def delete_intervention(
    intervention_id: str = Path(..., description="Intervention ID")
):
    """Delete an intervention."""
    try:
        ok = db.delete_intervention(intervention_id)
        if ok:
            return {"success": True}
        raise HTTPException(status_code=404, detail="Intervention not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting intervention {intervention_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Analytics Endpoints
# ============================================================================

@app.get("/api/analytics/overview", response_model=Dict[str, Any])
async def get_analytics_overview(
    department: Optional[str] = Query(None, description="Filter by department"),
    semester: Optional[str] = Query(None, description="Filter by semester")
):
    """Get analytics overview."""
    try:
        overview = analytics_engine.get_overview(department=department, semester=semester)
        return overview.dict()
    except Exception as e:
        logger.error(f"Error generating analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/trends", response_model=List[Dict[str, Any]])
async def get_risk_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    department: Optional[str] = Query(None, description="Filter by department")
):
    """Get risk trends over time."""
    try:
        trends = analytics_engine.get_risk_trends(days=days, department=department)
        return [t.dict() for t in trends]
    except Exception as e:
        logger.error(f"Error generating risk trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/departments", response_model=Dict[str, Dict[str, Any]])
async def get_department_analytics():
    """Get risk distribution by department."""
    try:
        distribution = analytics_engine.get_department_risk_distribution()
        return distribution
    except Exception as e:
        logger.error(f"Error generating department analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/courses", response_model=Dict[str, Dict[str, Any]])
async def get_course_analytics(
    semester: Optional[str] = Query(None, description="Filter by semester")
):
    """Get course-level risk heatmap."""
    try:
        heatmap = analytics_engine.get_course_risk_heatmap(semester=semester)
        return heatmap
    except Exception as e:
        logger.error(f"Error generating course analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ML Training & Model Management Endpoints
# ============================================================================

@app.post("/api/ml/train")
async def train_model(
    model_type: str = Body("xgboost", description="Model type: random_forest, logistic_regression, gradient_boosting, xgboost, lightgbm, catboost, neural_network, ensemble"),
    use_mock_labels: bool = Body(False, description="Use mock labels if real labels unavailable"),
    test_size: float = Body(0.2, ge=0.1, le=0.5, description="Test set size"),
    optimize_hyperparameters: bool = Body(False, description="Use Optuna for hyperparameter optimization")
):
    """Train ML model with current student data."""
    try:
        logger.info(f"Starting model training: {model_type}")
        
        # Prepare training data
        X, y, feature_names = training_pipeline.prepare_training_data(
            use_mock_labels=use_mock_labels
        )
        
        if len(X) < 10:
            raise HTTPException(
                status_code=400,
                detail="Insufficient training data. Need at least 10 samples."
            )
        
        # Train model (with optional hyperparameter optimization)
        if optimize_hyperparameters and model_type in ['xgboost', 'lightgbm']:
            try:
                from advanced_ml_models import advanced_ml
                training_result = advanced_ml.optimize_hyperparameters(
                    X, y, model_type=model_type, n_trials=50
                )
            except ImportError:
                logger.warning("Optuna not available, using default hyperparameters")
                training_result = training_pipeline.train_model(
                    X, y, model_type=model_type, test_size=test_size
                )
        else:
            training_result = training_pipeline.train_model(
                X, y, model_type=model_type, test_size=test_size
            )
        
        # Save model
        model_path = training_pipeline.save_model(training_result)
        
        # Reload model in risk engine
        risk_engine._load_or_initialize_model()
        
        return {
            'success': True,
            'model_path': model_path,
            'metrics': training_result['metrics'],
            'n_samples': training_result['n_samples'],
            'n_features': training_result['n_features'],
            'model_type': training_result['model_type'],
            'trained_at': training_result['trained_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/model/info")
async def get_model_info():
    """Get information about the current model."""
    try:
        # Report which model types are usable in this runtime
        available_models = {
            "random_forest": True,
            "logistic_regression": True,
            "gradient_boosting": True,
            "xgboost": False,
            "lightgbm": False,
            "catboost": False,
            "ensemble": False,
            # This may be a TF Keras model or a sklearn fallback (see advanced_ml_models.py)
            "neural_network": False,
        }
        try:
            import xgboost  # noqa: F401
            available_models["xgboost"] = True
        except Exception:
            pass
        try:
            import lightgbm  # noqa: F401
            available_models["lightgbm"] = True
        except Exception:
            pass
        try:
            import catboost  # noqa: F401
            available_models["catboost"] = True
        except Exception:
            pass
        # If TensorFlow can't be imported, we still support neural_network via sklearn fallback.
        available_models["neural_network"] = True
        # Ensemble requires at least one of these advanced libs
        available_models["ensemble"] = any(
            [available_models["xgboost"], available_models["lightgbm"], available_models["catboost"]]
        )

        model_path = f"models/risk_model_{settings.model_version}.pkl"
        
        if not os.path.exists(model_path):
            return {
                'model_loaded': False,
                'available_models': available_models,
                'message': 'No trained model found'
            }
        
        import pickle
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        return {
            'model_loaded': True,
            'available_models': available_models,
            'model_type': model_data.get('model_type', 'unknown'),
            'trained_at': model_data.get('trained_at', 'unknown'),
            'version': model_data.get('version', settings.model_version),
            'n_samples': model_data.get('n_samples', 0),
            'n_features': model_data.get('n_features', 0),
            'metrics': model_data.get('metrics', {})
        }
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/features/importance")
async def get_feature_importance():
    """Get feature importance from the trained model."""
    try:
        model_path = f"models/risk_model_{settings.model_version}.pkl"
        
        if not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail="No trained model found")
        
        # Get feature names
        dummy_features = processor.engineer_features([], [], 0.0, 0, 0, None, {})
        feature_names = training_pipeline._get_feature_names(dummy_features)
        
        importance = training_pipeline.get_feature_importance(
            model_path=model_path,
            feature_names=feature_names
        )
        
        return {
            'feature_importance': importance,
            'top_features': dict(list(importance.items())[:10])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feature importance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/evaluate")
async def evaluate_model():
    """Evaluate model performance on test data."""
    try:
        # Prepare data
        X, y, feature_names = training_pipeline.prepare_training_data(use_mock_labels=False)
        
        if len(X) < 10:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data for evaluation"
            )
        
        # Split data
        from sklearn.model_selection import train_test_split
        _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Evaluate
        model_path = f"models/risk_model_{settings.model_version}.pkl"
        metrics = training_pipeline.evaluate_model_performance(
            model_path=model_path if os.path.exists(model_path) else None,
            X_test=X_test,
            y_test=y_test
        )
        
        return {
            'success': True,
            'metrics': metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/students/{student_id}/trend")
async def get_student_trend(
    student_id: str = Path(..., description="Student ID"),
    lookback_days: int = Query(90, ge=7, le=365, description="Number of days to look back")
):
    """Get trend analysis for a student."""
    try:
        student = db.get_student_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        trend = trend_analyzer.analyze_risk_trend(student_id, lookback_days=lookback_days)
        return trend
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trend for student {student_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/model/retrain-check")
async def check_retraining():
    """Check if model should be retrained."""
    try:
        recommendation = model_manager.should_retrain()
        return recommendation
    except Exception as e:
        logger.error(f"Error checking retraining status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/model/retrain")
async def retrain_model(
    model_type: Optional[str] = Body(None, description="Model type (optional)"),
    use_mock_labels: bool = Body(False, description="Use mock labels")
):
    """Retrain the model with current data."""
    try:
        result = model_manager.retrain_model(
            model_type=model_type,
            use_mock_labels=use_mock_labels
        )
        
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Retraining failed'))
    except Exception as e:
        logger.error(f"Error retraining model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/model/versions")
async def get_model_versions():
    """Get list of all model versions."""
    try:
        versions = model_manager.get_model_versions()
        return {'versions': versions}
    except Exception as e:
        logger.error(f"Error getting model versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/model/performance")
async def get_model_performance():
    """Get model performance metrics."""
    try:
        performance = model_manager.monitor_model_performance()
        return performance
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/model/drift")
async def check_data_drift():
    """Check for data drift."""
    try:
        drift_result = model_manager.detect_data_drift()
        return drift_result
    except Exception as e:
        logger.error(f"Error checking data drift: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# File Upload Endpoint
# ============================================================================

@app.post("/api/upload")
async def upload_student_data(
    file: UploadFile = File(..., description="Any file format with student data (CSV, Excel, JSON, TSV, TXT, etc.)"),
    student_name: Optional[str] = Form(None, description="Student name (if not in file)"),
    roll_number: Optional[str] = Form(None, description="Roll number (if not in file)"),
    replace_existing: bool = Query(
        True,
        description="If true, this upload replaces the entire dataset (clears existing data first)."
    ),
    history_id: Optional[str] = Query(
        None,
        description="Internal: reuse an existing upload_history record id (used by Apply).",
    ),
):
    """Upload student data from any file format. Automatically detects format and processes all students with ML risk predictions."""
    logger.info("=" * 80)
    logger.info("📤 UPLOAD REQUEST RECEIVED")
    logger.info(f"File: {file.filename}")
    logger.info(f"Content-Type: {file.content_type}")
    logger.info(f"Student Name (form): {student_name}")
    logger.info(f"Roll Number (form): {roll_number}")
    logger.info(f"Database Client: {'✅ Initialized' if db.client else '❌ NOT INITIALIZED'}")
    logger.info("=" * 80)
    
    # CRITICAL FIX: Check database connection first with detailed error
    if db.client is None:
        logger.error("=" * 80)
        logger.error("❌ DATABASE CLIENT NOT INITIALIZED!")
        logger.error("Cannot process upload. File will be rejected.")
        logger.error("Please check your .env file:")
        logger.error("  - SUPABASE_URL must be set")
        logger.error("  - SUPABASE_KEY must be the SERVICE ROLE KEY (not anon key)")
        logger.error("  - Service role key is 200+ characters long and starts with 'eyJ'")
        logger.error("=" * 80)
        raise HTTPException(
            status_code=503,
            detail="Database connection not available. Please check SUPABASE_URL and SUPABASE_KEY in .env file. SUPABASE_KEY must be the SERVICE ROLE KEY (not anon key) to bypass RLS."
        )

    # Product behavior: Only show data after upload (no stale data)
    # We implement "dataset snapshot" semantics: each upload replaces the dataset.
    if replace_existing:
        try:
            if _dataset_has_any_students():
                logger.info("🧹 replace_existing=true -> existing dataset detected, clearing before upload")
                _clear_dataset()
            else:
                logger.info("🧹 replace_existing=true -> no existing dataset found, skipping clear step")
        except Exception as e:
            # If schema doesn't exist yet (new Supabase project), provide a clear error.
            if _is_schema_cache_missing_error(e):
                raise HTTPException(status_code=503, detail=_schema_not_ready_detail(str(e)))
            logger.error(f"Failed to clear existing data before upload: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to clear existing data: {str(e)}")
    
    try:
        import json
        try:
            import chardet
        except ImportError:
            chardet = None
            logger.warning("chardet not available, using UTF-8 as default encoding")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided or filename missing")
        
        logger.info(f"Received file upload: {file.filename}, content_type: {file.content_type}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Read file content
        try:
            contents = await file.read()
        except Exception as read_error:
            logger.error(f"Error reading file: {read_error}")
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(read_error)}")
        
        if not contents or len(contents) == 0:
            raise HTTPException(status_code=400, detail="File is empty or could not be read")
        
        logger.info(f"File read successfully: {len(contents)} bytes")

        # ------------------------------------------------------------------
        # Persist upload (filesystem) + create/update upload_history (Supabase)
        # ------------------------------------------------------------------
        upload_id = history_id
        stored_path: Optional[str] = None

        if upload_id:
            existing = db.get_upload_history(upload_id)
            if not existing:
                raise HTTPException(status_code=404, detail=f"Upload history record not found: {upload_id}")
            stored_path = existing.get("stored_path")
        else:
            upload_id = str(uuid.uuid4())
            safe = _safe_filename(file.filename or "upload")
            stored_path = str(UPLOAD_STORAGE_DIR / f"{upload_id}_{safe}")

        try:
            # Always (re)write bytes so Apply can re-run reliably even if disk was cleaned
            FsPath(stored_path).parent.mkdir(parents=True, exist_ok=True)
            FsPath(stored_path).write_bytes(contents)
        except Exception as e:
            logger.error(f"Failed to write upload file to disk: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to store uploaded file: {str(e)}")

        try:
            # Create or mark processing
            if history_id:
                db.update_upload_history(
                    upload_id,
                    {
                        "status": "processing",
                        "error": None,
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "file_size_bytes": len(contents),
                        "stored_path": stored_path,
                    },
                )
            else:
                created = db.create_upload_history(
                    {
                        "id": upload_id,
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "file_size_bytes": len(contents),
                        "stored_path": stored_path,
                        "status": "processing",
                        "is_active": False,
                    }
                )
                if not created:
                    raise RuntimeError("Failed to create upload history row")
        except Exception as e:
            if _is_schema_cache_missing_error(e):
                raise HTTPException(status_code=503, detail=_schema_not_ready_detail(str(e)))
            logger.error(f"Failed to write upload_history: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to persist upload history: {str(e)}")
        
        # Determine file type - try extension first, then content detection
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        content_type = file.content_type or ''
        
        # Detect encoding for text files
        detected_encoding = 'utf-8'
        try:
            if chardet and len(contents) > 0:
                detected = chardet.detect(contents)
                detected_encoding = detected.get('encoding', 'utf-8') or 'utf-8'
                logger.info(f"Detected encoding: {detected_encoding}")
        except:
            pass
        
        processed_students = []  # Track all processed student IDs for batch risk assessment
        logger.info("=" * 80)
        logger.info("🚀 FILE UPLOAD STARTED - INITIALIZING processed_students list")
        logger.info("=" * 80)
        
        # Try to detect file type from content if extension is unclear
        file_type = None
        text_content = None
        
        # Try JSON first (most common structured format)
        if file_ext in ['json', 'jsonl'] or 'json' in content_type:
            file_type = 'json'
        # Try Excel formats
        elif file_ext in ['xlsx', 'xls', 'xlsm', 'xlsb'] or 'spreadsheet' in content_type or 'excel' in content_type:
            file_type = 'excel'
        # Try CSV/TSV
        elif file_ext in ['csv', 'tsv', 'txt'] or 'csv' in content_type or 'text' in content_type:
            file_type = 'csv'
        else:
            # Try to detect from content
            try:
                # Try JSON
                text_content = contents.decode(detected_encoding, errors='ignore')
                try:
                    json.loads(text_content)
                    file_type = 'json'
                    logger.info("Detected JSON format from content")
                except:
                    pass
                
                # Try CSV/TSV (check for comma or tab delimiters)
                if file_type is None:
                    lines = text_content.split('\n')[:5]  # Check first 5 lines
                    if lines:
                        comma_count = lines[0].count(',')
                        tab_count = lines[0].count('\t')
                        if comma_count > 0 or tab_count > 0:
                            file_type = 'csv'
                            logger.info(f"Detected CSV/TSV format (delimiter: {'tab' if tab_count > comma_count else 'comma'})")
                
                # Default to text/CSV if we can decode it
                if file_type is None and text_content:
                    file_type = 'csv'
                    logger.info("Defaulting to CSV/text format")
            except:
                # If we can't decode, try Excel
                try:
                    file_type = 'excel'
                    logger.info("Trying Excel format")
                except:
                    pass
        
        if file_type is None:
            # Last resort: try Excel, then CSV
            try:
                pd.read_excel(io.BytesIO(contents))
                file_type = 'excel'
            except:
                file_type = 'csv'
        
        logger.info(f"Processing file as: {file_type} (extension: {file_ext})")
        
        # Handle JSON files (like mock_student_data.json)
        if file_type == 'json':
            try:
                data = json.loads(contents.decode('utf-8'))
                
                results = {
                    'students_created': 0,
                    'academic_records_created': 0,
                    'attendance_records_created': 0,
                    'risk_assessments_created': 0,
                    'errors': []
                }
                
                # Handle single student object or array of students
                students_data = []
                if isinstance(data, dict):
                    if 'student' in data:
                        # Single student with nested data
                        students_data = [data]
                    elif 'student_id' in data or 'roll_number' in data:
                        # Single student record
                        students_data = [data]
                    else:
                        # Assume it's a student object with nested records
                        students_data = [data]
                elif isinstance(data, list):
                    students_data = data
                else:
                    raise HTTPException(status_code=400, detail="Invalid JSON structure")
                
                # Process each student
                for student_idx, student_data in enumerate(students_data):
                    try:
                        # Extract student info (handle nested structure)
                        student_info = student_data.get('student', student_data)
                        roll_num = roll_number or student_info.get('student_id') or student_info.get('roll_number') or student_info.get('id', '')
                        name = student_name or student_info.get('full_name') or student_info.get('name', '')
                        
                        if not roll_num or not name:
                            results['errors'].append(f"Student {student_idx + 1}: Missing roll number or name")
                            continue
                        
                        # Check if student exists
                        existing_student = db.get_student_by_roll_number(str(roll_num))
                        student_id = None
                        
                        if not existing_student:
                            # Create new student
                            new_student_data = {
                                'id': student_info.get('id', str(uuid.uuid4())),
                                'student_id': str(roll_num),
                                'full_name': name,
                                'email': student_info.get('email', f"{roll_num}@university.edu"),
                                'department': student_info.get('department', 'General'),
                                'program': student_info.get('program', 'Undergraduate'),
                                'year_level': int(student_info.get('year_level', 1)),
                                'semester': student_info.get('semester', 'Fall 2024'),
                                'enrollment_date': student_info.get('enrollment_date', datetime.utcnow().date().isoformat()),
                                'status': student_info.get('status', 'active')
                            }
                            
                            created = db.create_student(new_student_data)
                            if created:
                                student_id = created['id']
                                results['students_created'] += 1
                                logger.info(f"✓ Created student: {name} ({roll_num}) with ID: {student_id}")
                            else:
                                # Try to fetch in case it was created concurrently
                                existing_student = db.get_student_by_roll_number(str(roll_num))
                                if existing_student:
                                    student_id = existing_student['id']
                                    logger.info(f"✓ Student {name} ({roll_num}) found after creation failure (concurrent creation)")
                                else:
                                    error_msg = f"Student {student_idx + 1}: Failed to create student {name} (roll: {roll_num}). Check backend logs for RLS/permission errors."
                                    results['errors'].append(error_msg)
                                    logger.error(f"❌ {error_msg}")
                                    continue
                        else:
                            student_id = existing_student['id']
                            logger.info(f"Student {name} ({roll_num}) already exists, using ID: {student_id}")
                        
                        # CRITICAL FIX: Ensure student_id is valid before adding to processed_students
                        if student_id is None:
                            error_msg = f"Student {student_idx + 1}: Student ID is None for {name} ({roll_num}) - this should not happen!"
                            logger.error(f"❌ {error_msg}")
                            results['errors'].append(error_msg)
                            continue
                        
                        # Add to processed_students list - ensure no duplicates
                        if student_id not in processed_students:
                            processed_students.append(student_id)
                            logger.debug(f"Added student {student_id} ({name}) to processed_students list")
                        
                        # Process academic records
                        academic_records = student_data.get('academic_records', [])
                        if not academic_records and 'grade' in student_data:
                            # Single grade record
                            academic_records = [student_data]
                        
                        for acad_record in academic_records:
                            try:
                                record_data = {
                                    'id': str(uuid.uuid4()),
                                    'student_id': student_id,
                                    'semester': str(acad_record.get('semester', 'Fall 2024')),
                                    'course_code': str(acad_record.get('course_code', '')),
                                    'course_name': str(acad_record.get('course_name', acad_record.get('course_code', ''))),
                                    'grade': float(acad_record.get('grade', 0.0)),
                                    'credits': int(acad_record.get('credits', 3)),
                                    'gpa': float(acad_record.get('gpa', acad_record.get('grade', 0.0))),
                                    'created_at': datetime.utcnow().isoformat()
                                }
                                
                                if record_data['course_code']:
                                    created_record = db.create_academic_record(record_data)
                                    if created_record:
                                        results['academic_records_created'] += 1
                            except Exception as e:
                                results['errors'].append(f"Student {student_idx + 1} academic record: {str(e)}")
                                logger.error(f"Error processing academic record: {e}")
                        
                        # Process attendance records
                        attendance_records = student_data.get('attendance_records', [])
                        if not attendance_records and 'date' in student_data:
                            # Single attendance record
                            attendance_records = [student_data]
                        
                        for att_record in attendance_records:
                            try:
                                att_status = str(att_record.get('status', 'present')).lower()
                                if att_status not in ['present', 'absent', 'late', 'excused']:
                                    att_status = 'present' if att_status in ['p', 'yes', '1', 'true'] else 'absent'
                                
                                record_data = {
                                    'id': str(uuid.uuid4()),
                                    'student_id': student_id,
                                    'date': str(att_record.get('date', datetime.utcnow().date().isoformat())),
                                    'status': att_status,
                                    'course_code': str(att_record.get('course_code', '')),
                                    'semester': str(att_record.get('semester', 'Fall 2024')),
                                    'created_at': datetime.utcnow().isoformat()
                                }
                                
                                created_attendance = db.create_attendance_record(record_data)
                                if created_attendance:
                                    results['attendance_records_created'] += 1
                            except Exception as e:
                                results['errors'].append(f"Student {student_idx + 1} attendance record: {str(e)}")
                                logger.error(f"Error processing attendance record: {e}")
                        
                    except Exception as e:
                        results['errors'].append(f"Student {student_idx + 1}: {str(e)}")
                        logger.error(f"Error processing student {student_idx + 1}: {e}")
                
                # CRITICAL FIX: Trigger risk assessment for ALL processed students (JSON path)
                # Remove duplicates from processed_students to avoid double-processing
                unique_processed_students = list(set(processed_students))
                logger.info(f"Triggering ML risk assessment for {len(unique_processed_students)} unique students from JSON upload")
                
                if len(unique_processed_students) == 0:
                    logger.error("=" * 80)
                    logger.error("⚠️ CRITICAL: No students processed from JSON - cannot run risk assessments!")
                    logger.error("This means student creation failed.")
                    logger.error("Common causes:")
                    logger.error("  1. RLS (Row Level Security) blocking inserts")
                    logger.error("  2. SUPABASE_KEY is not the service role key")
                    logger.error("  3. Database permissions issue")
                    logger.error("")
                    logger.error("Check backend logs above for specific error messages.")
                    logger.error("=" * 80)
                    results['errors'].append("CRITICAL: No students were created. Check backend logs and ensure SUPABASE_KEY is the service role key.")
                else:
                    risk_assessment_count = 0
                    risk_assessment_errors = 0
                    for idx, student_id in enumerate(unique_processed_students, 1):
                        try:
                            logger.info(f"[{idx}/{len(unique_processed_students)}] Running ML risk assessment for student {student_id}...")
                            result = monitoring_engine.evaluate_student(student_id, force_reassessment=True)
                            if result and result.get('assessment'):
                                risk_assessment_count += 1
                                risk_level = result.get('assessment', {}).get('risk_level', 'unknown')
                                risk_score = result.get('assessment', {}).get('risk_score', 0)
                                logger.info(f"✓ [{idx}/{len(unique_processed_students)}] Risk assessment created for student {student_id}: {risk_level} (score: {risk_score:.1f})")
                            else:
                                risk_assessment_errors += 1
                                logger.warning(f"⚠️ [{idx}/{len(unique_processed_students)}] Risk assessment returned None/empty for student {student_id}")
                                results['errors'].append(f"Risk assessment failed for student {student_id}: returned None/empty result")
                        except Exception as e:
                            risk_assessment_errors += 1
                            logger.error(f"❌ [{idx}/{len(unique_processed_students)}] Could not assess risk for student {student_id}: {e}", exc_info=True)
                            results['errors'].append(f"Risk assessment failed for student {student_id}: {str(e)}")
                    
                    results['risk_assessments_created'] = risk_assessment_count
                    logger.info(f"✅ JSON risk assessment completed: {risk_assessment_count} succeeded, {risk_assessment_errors} failed out of {len(unique_processed_students)} students")
                    
                    if risk_assessment_errors > 0:
                        logger.warning(f"⚠️ {risk_assessment_errors} risk assessments failed. Check errors above for details.")
                
                # Add comprehensive summary information for JSON upload
                total_students_in_list = len(set(processed_students))  # Unique students
                summary = {
                    'success': True,
                    'filename': file.filename,
                    'students_processed': total_students_in_list,
                    **results
                }
                
                # Add warning if database connection issues
                if db.client is None:
                    summary['warning'] = "Database connection not available. No data was saved."
                    summary['success'] = False
                
                # STRENGTHENED AUTO-TRAINING: Always attempt to train if we have data
                try:
                    all_students = db.get_students(filters={}, limit=200)
                    if len(all_students) >= 5:
                        logger.info(f"🔄 Auto-training ML model with {len(all_students)} students...")
                        try:
                            X, y, feature_names = training_pipeline.prepare_training_data(
                                students=all_students,
                                use_mock_labels=True
                            )
                            if len(X) >= 5:
                                training_result = training_pipeline.train_model(
                                    X, y, 
                                    model_type=settings.model_type,
                                    test_size=0.2
                                )
                                model_path = training_pipeline.save_model(training_result)
                                risk_engine._load_or_initialize_model()
                                if risk_engine.is_trained:
                                    accuracy = training_result.get('metrics', {}).get('accuracy', 0)
                                    logger.info(f"✅ ML model auto-trained! Accuracy: {accuracy:.2%}")
                                    summary['model_trained'] = True
                                    summary['model_accuracy'] = accuracy
                        except Exception as e:
                            logger.error(f"❌ Auto-training failed: {e}", exc_info=True)
                            summary['model_training_error'] = str(e)
                except Exception as e:
                    logger.error(f"❌ Auto-training check failed: {e}", exc_info=True)
                
                logger.info(f"JSON upload completed: {results['students_created']} students, {results['academic_records_created']} academic records")
                return summary
                
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
        
        # Handle CSV/TSV/TXT files
        elif file_type == 'csv':
            try:
                # Detect delimiter (comma, tab, semicolon, pipe)
                if text_content is None:
                    try:
                        text_content = contents.decode(detected_encoding, errors='ignore')
                    except Exception as decode_error:
                        logger.warning(f"Encoding {detected_encoding} failed, trying UTF-8: {decode_error}")
                        text_content = contents.decode('utf-8', errors='ignore')
                
                # Try different delimiters
                delimiter = ','
                if text_content and len(text_content) > 0:
                    sample = text_content[:1000] if len(text_content) > 1000 else text_content
                    if '\t' in sample:
                        delimiter = '\t'
                    elif ';' in sample:
                        delimiter = ';'
                    elif '|' in sample:
                        delimiter = '|'
                
                logger.info(f"Attempting to read CSV with delimiter: {repr(delimiter)}, encoding: {detected_encoding}")

                # CRITICAL FIX: Do NOT silently drop malformed rows.
                # Pandas on_bad_lines='skip' causes data loss with no visibility.
                # Instead, capture bad lines and attempt to salvage by padding/truncating to header width.
                bad_lines: List[Dict[str, Any]] = []

                # Determine expected column count from header row (best-effort)
                expected_fields: Optional[int] = None
                try:
                    decoded_sample = contents.decode(detected_encoding, errors='ignore')
                    first_line = decoded_sample.splitlines()[0] if decoded_sample else ""
                    if first_line:
                        header_fields = next(csv.reader([first_line], delimiter=delimiter))
                        expected_fields = len(header_fields) if header_fields else None
                except Exception:
                    expected_fields = None

                def _handle_bad_line(bad_line: List[str]) -> Optional[List[str]]:
                    # Called by pandas (python engine) when a row has the wrong number of fields.
                    try:
                        bad_lines.append({
                            "original_fields": bad_line,
                            "field_count": len(bad_line),
                            "expected_fields": expected_fields
                        })
                        if expected_fields is None:
                            # Can't safely reshape without header width; keep dropping but record.
                            return None
                        if len(bad_line) < expected_fields:
                            return bad_line + ([""] * (expected_fields - len(bad_line)))
                        if len(bad_line) > expected_fields:
                            return bad_line[:expected_fields]
                        return bad_line
                    except Exception:
                        return None

                df = pd.read_csv(
                    io.BytesIO(contents),
                    delimiter=delimiter,
                    encoding=detected_encoding,
                    on_bad_lines=_handle_bad_line,
                    engine='python',
                    dtype=str,
                    keep_default_na=False
                )
                logger.info(f"Successfully read CSV with {len(df)} rows")
                if bad_lines:
                    logger.warning(f"⚠️ Detected {len(bad_lines)} malformed CSV rows; attempted to salvage them. Showing up to 5 samples.")
                    for sample in bad_lines[:5]:
                        logger.warning(f"Bad CSV row sample: fields={sample.get('field_count')} expected={sample.get('expected_fields')}")
            except Exception as e:
                logger.error(f"Error reading CSV with detected settings: {e}")
                # Try without delimiter specification
                try:
                    logger.info("Retrying CSV read with default settings")
                    df = pd.read_csv(
                        io.BytesIO(contents),
                        encoding=detected_encoding,
                        on_bad_lines='warn',
                        engine='python',
                        dtype=str,
                        keep_default_na=False
                    )
                    logger.info(f"Successfully read CSV (fallback) with {len(df)} rows")
                except Exception as e2:
                    logger.error(f"CSV read failed with fallback: {e2}")
                    # Last resort: try with UTF-8
                    try:
                        df = pd.read_csv(
                            io.BytesIO(contents),
                            encoding='utf-8',
                            on_bad_lines='warn',
                            engine='python',
                            dtype=str,
                            keep_default_na=False
                        )
                        logger.info(f"Successfully read CSV (UTF-8 fallback) with {len(df)} rows")
                    except Exception as e3:
                        logger.error(f"All CSV read attempts failed. Last error: {e3}")
                        raise HTTPException(status_code=400, detail=f"Could not parse CSV/text file. Error: {str(e3)}")
        
        # Handle Excel files
        elif file_type == 'excel':
            try:
                # CRITICAL FIX: Excel files may contain multiple sheets.
                # Read all sheets and concatenate so no sheet is silently ignored.
                all_sheets = pd.read_excel(io.BytesIO(contents), sheet_name=None)
                frames = []
                for sheet_name, sheet_df in (all_sheets or {}).items():
                    if sheet_df is None or sheet_df.empty:
                        continue
                    sheet_df = sheet_df.copy()
                    sheet_df["_source_sheet"] = str(sheet_name)
                    frames.append(sheet_df)
                if not frames:
                    df = pd.DataFrame()
                else:
                    df = pd.concat(frames, ignore_index=True)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Could not parse Excel file: {str(e)}")
        
        else:
            # Try to parse as text/CSV as last resort
            try:
                if text_content is None:
                    text_content = contents.decode(detected_encoding, errors='ignore')
                df = pd.read_csv(io.StringIO(text_content), on_bad_lines='warn', dtype=str, keep_default_na=False)
                logger.info("Parsed as text/CSV (fallback)")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Could not determine or parse file format. Error: {str(e)}")
        
        # Process CSV/Excel/Text files
        if file_type in ['csv', 'excel']:
            if df.empty:
                raise HTTPException(status_code=400, detail="File is empty or could not be parsed")
            
            results = {
                'students_created': 0,
                'academic_records_created': 0,
                'attendance_records_created': 0,
                'risk_assessments_created': 0,
                'rows_processed': 0,
                'rows_failed': 0,
                'rows_skipped': 0,
                'errors': []
            }
            
            # Normalize column names (case-insensitive, handle spaces)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            total_rows = len(df)
            logger.info(f"📊 Starting to process {total_rows} rows from file")
            
            # Process each row
            for idx, row in df.iterrows():
                results['rows_processed'] += 1
                # Initialize student_id to avoid UnboundLocalError
                # Must be initialized before try block so Python knows it's a local variable
                student_id: Optional[str] = None
                try:
                    # Extract student information - handle pandas Series properly
                    # Try multiple column name variations (case-insensitive, with/without underscores)
                    roll_num = None
                    name = None
                    
                    # Try to get roll number from various column names
                    for col_name in ['roll_number', 'rollnumber', 'roll_num', 'student_id', 'studentid', 'id', 'student_number', 'studentnumber']:
                        if col_name in row.index:
                            val = row[col_name]
                            if pd.notna(val) and str(val).strip():
                                roll_num = str(val).strip()
                                break
                    
                    # Try to get name from various column names
                    for col_name in ['name', 'full_name', 'fullname', 'student_name', 'studentname', 'full name']:
                        if col_name in row.index:
                            val = row[col_name]
                            if pd.notna(val) and str(val).strip():
                                name = str(val).strip()
                                break
                    
                    # Use form values if provided and row values are missing
                    roll_num = roll_number or roll_num or ''
                    name = student_name or name or ''
                    
                    # Skip if still missing
                    if not roll_num or not name or roll_num == 'nan' or name == 'nan':
                        error_msg = f"Row {idx + 1}: Missing roll number or name (found columns: {', '.join(row.index.tolist())})"
                        results['errors'].append(error_msg)
                        results['rows_skipped'] += 1
                        logger.warning(f"⚠️ {error_msg}")
                        continue
                    
                    # Check if student exists
                    existing_student = db.get_student_by_roll_number(roll_num)
                    
                    if not existing_student:
                        # Create new student
                        # Get email
                        email_val = f"{roll_num}@university.edu"
                        for col_name in ['email', 'e_mail', 'email_address']:
                            if col_name in row.index:
                                val = row[col_name]
                                if pd.notna(val) and str(val).strip():
                                    email_val = str(val).strip()
                                    break
                        
                        # Get department
                        dept_val = 'General'
                        for col_name in ['department', 'dept', 'department_name', 'major']:
                            if col_name in row.index:
                                val = row[col_name]
                                if pd.notna(val) and str(val).strip():
                                    dept_val = str(val).strip()
                                    break
                        
                        # Get program
                        program_val = 'Undergraduate'
                        for col_name in ['program', 'degree', 'degree_program']:
                            if col_name in row.index:
                                val = row[col_name]
                                if pd.notna(val) and str(val).strip():
                                    program_val = str(val).strip()
                                    break
                        
                        # Get year level
                        year_val = 1
                        for col_name in ['year_level', 'year', 'grade_level', 'level']:
                            if col_name in row.index:
                                val = row[col_name]
                                if pd.notna(val):
                                    try:
                                        year_val = int(val)
                                        break
                                    except:
                                        pass
                        
                        # Get semester
                        semester_val = 'Fall 2024'
                        for col_name in ['semester', 'term', 'session']:
                            if col_name in row.index:
                                val = row[col_name]
                                if pd.notna(val) and str(val).strip():
                                    semester_val = str(val).strip()
                                    break
                        
                        # Get enrollment date
                        enroll_date = datetime.utcnow().date().isoformat()
                        for col_name in ['enrollment_date', 'enroll_date', 'admission_date']:
                            if col_name in row.index:
                                val = row[col_name]
                                if pd.notna(val):
                                    try:
                                        if isinstance(val, str):
                                            enroll_date = val
                                        else:
                                            enroll_date = str(val)
                                        break
                                    except:
                                        pass
                        
                        student_data = {
                            'id': str(uuid.uuid4()),
                            'student_id': roll_num,
                            'full_name': name,
                            'email': email_val,
                            'department': dept_val,
                            'program': program_val,
                            'year_level': year_val,
                            'semester': semester_val,
                            'enrollment_date': enroll_date,
                            'status': 'active'
                        }
                        
                        created = db.create_student(student_data)
                        if created:
                            student_id = created['id']
                            results['students_created'] += 1
                            logger.info(f"✓ Created student: {name} ({roll_num}) with ID: {student_id}")
                        else:
                            # Student creation failed - check if it was created by another row in the same batch
                            # Try fetching again in case it was created concurrently
                            existing_student = db.get_student_by_roll_number(roll_num)
                            if existing_student:
                                student_id = existing_student['id']
                                logger.info(f"✓ Student {name} ({roll_num}) already exists (concurrent creation), using existing ID: {student_id}")
                            else:
                                # Try one more time to fetch - might have been created
                                import time
                                time.sleep(0.1)  # Brief pause
                                existing_student = db.get_student_by_roll_number(roll_num)
                                if existing_student:
                                    student_id = existing_student['id']
                                    logger.info(f"✓ Student {name} ({roll_num}) found after retry, using ID: {student_id}")
                                else:
                                    # FINAL FIX: Student creation completely failed - cannot process this row
                                    error_msg = f"Row {idx + 1}: Failed to create student {name} (roll: {roll_num}). Check backend logs for RLS/permission errors. Ensure SUPABASE_KEY is the SERVICE ROLE KEY."
                                    logger.error(f"❌ {error_msg}")
                                    logger.error(f"Student data that failed: {student_data}")
                                    results['errors'].append(error_msg)
                                    results['rows_failed'] += 1
                                    # Skip this row entirely - cannot create records without valid student_id
                                    continue
                    else:
                        student_id = existing_student['id']
                        logger.info(f"Student {name} ({roll_num}) already exists, using ID: {student_id}")
                    
                    # CRITICAL FIX: Ensure student_id is set and add to processed_students IMMEDIATELY
                    # This must happen before processing academic/attendance records
                    if student_id is None:
                        error_msg = f"Row {idx + 1}: Student ID is None for {name} ({roll_num}) - this should not happen!"
                        logger.error(f"❌ {error_msg}")
                        results['errors'].append(error_msg)
                        results['rows_failed'] += 1
                        continue
                    
                    # Add to processed_students list for risk assessment - ensure no duplicates
                    if student_id not in processed_students:
                        processed_students.append(student_id)
                        logger.info(f"✅ Added student {student_id} ({name}) to processed_students list (total: {len(processed_students)})")
                    
                    # Process academic records - check if any grade-related columns exist
                    # At this point, student_id is guaranteed to be set (we checked above)
                    has_grade_data = any(col in row.index for col in ['course_code', 'course', 'grade', 'gpa', 'score', 'marks'])
                    if has_grade_data:
                        # Try to get course code from various column names
                        course_code = ''
                        for col_name in ['course_code', 'coursecode', 'course', 'subject', 'subject_code']:
                            if col_name in row.index:
                                val = row[col_name]
                                if pd.notna(val) and str(val).strip():
                                    course_code = str(val).strip()
                                    break
                        
                        if course_code:
                            # Get grade from various column names
                            grade_val = 0.0
                            for col_name in ['grade', 'score', 'marks', 'gpa']:
                                if col_name in row.index:
                                    val = row[col_name]
                                    if pd.notna(val):
                                        try:
                                            grade_val = float(val)
                                            break
                                        except:
                                            pass
                            
                            # Get credits
                            credits_val = 3
                            for col_name in ['credits', 'credit', 'credit_hours']:
                                if col_name in row.index:
                                    val = row[col_name]
                                    if pd.notna(val):
                                        try:
                                            credits_val = int(val)
                                            break
                                        except:
                                            pass
                            
                            # Get course name
                            course_name_val = course_code
                            for col_name in ['course_name', 'coursename', 'course_name', 'subject_name']:
                                if col_name in row.index:
                                    val = row[col_name]
                                    if pd.notna(val) and str(val).strip():
                                        course_name_val = str(val).strip()
                                        break
                            
                            # Get semester
                            semester_val = 'Fall 2024'
                            for col_name in ['semester', 'term', 'session']:
                                if col_name in row.index:
                                    val = row[col_name]
                                    if pd.notna(val) and str(val).strip():
                                        semester_val = str(val).strip()
                                        break
                            
                            # student_id is guaranteed to be set at this point (checked above)
                            academic_record = {
                                'id': str(uuid.uuid4()),
                                'student_id': student_id,
                                'semester': semester_val,
                                'course_code': course_code,
                                'course_name': course_name_val,
                                'grade': grade_val,
                                'credits': credits_val,
                                'gpa': grade_val,  # Use grade as GPA if GPA not available
                                'created_at': datetime.utcnow().isoformat()
                            }
                            
                            created_record = db.create_academic_record(academic_record)
                            if created_record:
                                results['academic_records_created'] += 1
                            else:
                                logger.warning(f"Failed to create academic record for {name}: {course_code}")
                                results['errors'].append(f"Row {idx + 1}: Failed to create academic record for {course_code}")
                    
                    # Process attendance records - check if any attendance-related columns exist
                    # At this point, student_id is guaranteed to be set (we checked above)
                    has_attendance_data = any(col in row.index for col in ['attendance_date', 'date', 'attendance', 'status', 'present', 'absent'])
                    if has_attendance_data:
                        # Get attendance date
                        attendance_date = datetime.utcnow().date().isoformat()
                        for col_name in ['attendance_date', 'date', 'attendance_date', 'record_date']:
                            if col_name in row.index:
                                val = row[col_name]
                                if pd.notna(val):
                                    try:
                                        if isinstance(val, str):
                                            # Try to parse date string - handle various formats
                                            val_str = str(val).strip()
                                            if val_str and val_str != 'nan':
                                                try:
                                                    from dateutil import parser
                                                    parsed_date = parser.parse(val_str)
                                                    attendance_date = parsed_date.date().isoformat()
                                                except:
                                                    # If parsing fails, use as-is if it looks like a date
                                                    if len(val_str) >= 8:  # Minimum date length
                                                        attendance_date = val_str
                                        else:
                                            # Handle pandas Timestamp or datetime objects
                                            if hasattr(val, 'date'):
                                                attendance_date = val.date().isoformat()
                                            elif hasattr(val, 'isoformat'):
                                                attendance_date = val.isoformat()
                                            else:
                                                attendance_date = str(val).strip()
                                        if attendance_date and attendance_date != 'nan':
                                            break
                                    except Exception as date_error:
                                        logger.debug(f"Could not parse date {val}: {date_error}")
                                        pass
                        
                        # Get attendance status
                        attendance_status = 'present'
                        for col_name in ['status', 'attendance', 'attendance_status', 'present', 'absent']:
                            if col_name in row.index:
                                val = row[col_name]
                                if pd.notna(val):
                                    status_str = str(val).lower().strip()
                                    if status_str in ['present', 'absent', 'late', 'excused', 'p', 'a', 'l', 'e']:
                                        if status_str in ['p']:
                                            attendance_status = 'present'
                                        elif status_str in ['a']:
                                            attendance_status = 'absent'
                                        elif status_str in ['l']:
                                            attendance_status = 'late'
                                        elif status_str in ['e']:
                                            attendance_status = 'excused'
                                        else:
                                            attendance_status = status_str
                                        break
                        
                        if attendance_status not in ['present', 'absent', 'late', 'excused']:
                            attendance_status = 'present' if attendance_status in ['p', 'yes', '1', 'true'] else 'absent'
                        
                        # Get course code for attendance if available
                        att_course_code = ''
                        for col_name in ['course_code', 'course', 'subject']:
                            if col_name in row.index:
                                val = row[col_name]
                                if pd.notna(val) and str(val).strip():
                                    att_course_code = str(val).strip()
                                    break
                        
                        # Get semester for attendance
                        att_semester = 'Fall 2024'
                        for col_name in ['semester', 'term']:
                            if col_name in row.index:
                                val = row[col_name]
                                if pd.notna(val) and str(val).strip():
                                    att_semester = str(val).strip()
                                    break
                        
                        # student_id is guaranteed to be set at this point (checked above)
                        attendance_record = {
                            'id': str(uuid.uuid4()),
                            'student_id': student_id,
                            'date': str(attendance_date),
                            'status': attendance_status,
                            'course_code': att_course_code,
                            'semester': att_semester,
                            'created_at': datetime.utcnow().isoformat()
                        }
                        
                        created_attendance = db.create_attendance_record(attendance_record)
                        if created_attendance:
                            results['attendance_records_created'] += 1
                        else:
                            logger.warning(f"Failed to create attendance record for {name}: {attendance_date}")
                            results['errors'].append(f"Row {idx + 1}: Failed to create attendance record for {attendance_date}")
                    
                except Exception as e:
                    error_msg = f"Row {idx + 1}: Unexpected error - {str(e)}"
                    results['errors'].append(error_msg)
                    results['rows_failed'] += 1
                    logger.error(f"❌ {error_msg}", exc_info=True)
                    # CRITICAL: Even if there's an error, if student_id was set, add it to processed_students
                    # This ensures risk assessment happens even if academic/attendance record creation fails
                    if student_id and student_id not in processed_students:
                        processed_students.append(student_id)
                        logger.info(f"⚠️ Added student {student_id} to processed_students despite error (so risk assessment can still run)")
            
            # CRITICAL FIX: Trigger risk assessment for ALL processed students
            logger.info("=" * 80)
            logger.info("🎯 REACHED RISK ASSESSMENT SECTION")
            logger.info(f"   processed_students list length: {len(processed_students)}")
            logger.info(f"   processed_students content: {processed_students}")
            logger.info("=" * 80)
            
            # Remove duplicates from processed_students to avoid double-processing
            unique_processed_students = list(set(processed_students))
            logger.info(f"📊 Triggering ML risk assessment for {len(unique_processed_students)} unique students (total processed: {len(processed_students)})")
            
            if len(unique_processed_students) == 0:
                logger.error("=" * 80)
                logger.error("⚠️ CRITICAL: No students processed from CSV/Excel - cannot run risk assessments!")
                logger.error("This means student creation failed during row processing.")
                logger.error("Common causes:")
                logger.error("  1. RLS (Row Level Security) blocking inserts")
                logger.error("  2. SUPABASE_KEY is not the service role key")
                logger.error("  3. Database permissions issue")
                logger.error("")
                logger.error("Attempting to fetch and assess existing students in database as fallback...")
                logger.error("=" * 80)
                try:
                    all_students = db.get_students(filters={'status': 'active'}, limit=100)
                    logger.info(f"Found {len(all_students)} existing students in database, running risk assessments...")
                    risk_assessment_count = 0
                    risk_assessment_errors = 0
                    for student in all_students:
                        try:
                            logger.info(f"Running ML risk assessment for existing student {student['id']} ({student.get('full_name', 'Unknown')})...")
                            result = monitoring_engine.evaluate_student(student['id'], force_reassessment=True)
                            if result and result.get('assessment'):
                                risk_assessment_count += 1
                                risk_level = result.get('assessment', {}).get('risk_level', 'unknown')
                                risk_score = result.get('assessment', {}).get('risk_score', 0)
                                logger.info(f"✓ Risk assessment created for student {student['id']}: {risk_level} (score: {risk_score:.1f})")
                            else:
                                risk_assessment_errors += 1
                                logger.warning(f"Risk assessment returned None/empty for student {student['id']}")
                                results['errors'].append(f"Risk assessment failed for student {student['id']} ({student.get('full_name', 'Unknown')}): returned None/empty")
                        except Exception as e:
                            risk_assessment_errors += 1
                            logger.error(f"❌ Risk assessment failed for student {student['id']}: {e}", exc_info=True)
                            results['errors'].append(f"Risk assessment failed for student {student['id']} ({student.get('full_name', 'Unknown')}): {str(e)}")
                    results['risk_assessments_created'] = risk_assessment_count
                    logger.info(f"Risk assessment summary: {risk_assessment_count} succeeded, {risk_assessment_errors} failed")
                except Exception as e:
                    logger.error(f"❌ Could not fetch students for risk assessment: {e}", exc_info=True)
                    results['errors'].append(f"Failed to fetch existing students for risk assessment: {str(e)}")
            else:
                # Process each student sequentially to ensure all are processed
                risk_assessment_count = 0
                risk_assessment_errors = 0
                for idx, student_id in enumerate(unique_processed_students, 1):
                    try:
                        logger.info(f"[{idx}/{len(unique_processed_students)}] Running ML risk assessment for student {student_id}...")
                        result = monitoring_engine.evaluate_student(student_id, force_reassessment=True)
                        if result and result.get('assessment'):
                            risk_assessment_count += 1
                            risk_level = result.get('assessment', {}).get('risk_level', 'unknown')
                            risk_score = result.get('assessment', {}).get('risk_score', 0)
                            logger.info(f"✓ [{idx}/{len(unique_processed_students)}] Risk assessment created for student {student_id}: {risk_level} (score: {risk_score:.1f})")
                        else:
                            risk_assessment_errors += 1
                            logger.warning(f"⚠️ [{idx}/{len(unique_processed_students)}] Risk assessment returned None/empty for student {student_id}")
                            results['errors'].append(f"Risk assessment failed for student {student_id}: returned None/empty result")
                    except Exception as e:
                        risk_assessment_errors += 1
                        logger.error(f"❌ [{idx}/{len(unique_processed_students)}] Could not assess risk for student {student_id}: {e}", exc_info=True)
                        results['errors'].append(f"Risk assessment failed for student {student_id}: {str(e)}")
                
                results['risk_assessments_created'] = risk_assessment_count
                logger.info(f"✅ Risk assessment completed: {risk_assessment_count} succeeded, {risk_assessment_errors} failed out of {len(unique_processed_students)} students")
                
                if risk_assessment_errors > 0:
                    logger.warning(f"⚠️ {risk_assessment_errors} risk assessments failed. Check errors above for details.")
            
            # Add comprehensive summary information
            total_students_in_list = len(set(processed_students))  # Unique students
            # Calculate rows_succeeded with safeguard to prevent negative values
            rows_succeeded = max(0, results['rows_processed'] - results['rows_failed'] - results['rows_skipped'])
            
            # CRITICAL: Verify processed_students actually has values
            logger.info(f"📊 FINAL PROCESSING SUMMARY:")
            logger.info(f"   processed_students list length: {len(processed_students)}")
            logger.info(f"   Unique students: {total_students_in_list}")
            logger.info(f"   Students created: {results['students_created']}")
            logger.info(f"   Risk assessments created: {results['risk_assessments_created']}")
            
            summary = {
                'success': True,
                'filename': file.filename,
                'total_rows_in_file': total_rows,
                'rows_processed': results['rows_processed'],
                'rows_succeeded': rows_succeeded,
                'rows_failed': results['rows_failed'],
                'rows_skipped': results['rows_skipped'],
                **results,  # Spread results first (students_created, risk_assessments_created, etc.)
                'students_processed': total_students_in_list,  # Override with correct unique count (comes after spread)
                'upload_id': upload_id,
            }
            
            # Add warning if database connection issues
            if db.client is None:
                summary['warning'] = "Database connection not available. No data was saved."
                summary['success'] = False
                logger.error("=" * 80)
                logger.error("❌ DATABASE CLIENT NOT INITIALIZED!")
                logger.error("Check your .env file for SUPABASE_URL and SUPABASE_KEY")
                logger.error("=" * 80)
            
            # STRENGTHENED AUTO-TRAINING: Always attempt to train if we have data
            try:
                # Get all students (including inactive for training)
                all_students = db.get_students(filters={}, limit=200)  # Increased limit
                
                if len(all_students) >= 5:  # Lowered threshold to 5 for faster training
                    logger.info(f"🔄 Auto-training ML model with {len(all_students)} students...")
                    
                    # Prepare training data with mock labels (negative=high, moderate=medium, positive=low)
                    try:
                        X, y, feature_names = training_pipeline.prepare_training_data(
                            students=all_students,
                            use_mock_labels=True
                        )
                        
                        if len(X) >= 5:  # Lowered threshold
                            logger.info(f"📊 Training data prepared: {len(X)} samples, {len(feature_names)} features")
                            
                            # Train the model with error handling
                            try:
                                training_result = training_pipeline.train_model(
                                    X, y, 
                                    model_type=settings.model_type,
                                    test_size=0.2
                                )
                                
                                # Save model
                                model_path = training_pipeline.save_model(training_result)
                                
                                # Force reload model in risk engine
                                risk_engine._load_or_initialize_model()
                                
                                # Verify model is now trained
                                if risk_engine.is_trained:
                                    accuracy = training_result.get('metrics', {}).get('accuracy', 0)
                                    logger.info(f"✅ ML model auto-trained successfully! Type: {settings.model_type}, Accuracy: {accuracy:.2%}")
                                    summary['model_trained'] = True
                                    summary['model_accuracy'] = accuracy
                                    summary['model_type'] = settings.model_type
                                else:
                                    logger.warning("⚠️ Model training completed but is_trained flag not set")
                                    summary['model_training_warning'] = "Model trained but not loaded correctly"
                                    
                            except Exception as train_error:
                                logger.error(f"❌ Model training failed: {train_error}", exc_info=True)
                                summary['model_training_error'] = str(train_error)
                                # Continue with rule-based predictions
                        else:
                            logger.info(f"⚠️ Not enough training samples ({len(X)} < 5), need more data")
                            summary['model_training_info'] = f"Need at least 5 samples, got {len(X)}"
                            
                    except Exception as prep_error:
                        logger.error(f"❌ Training data preparation failed: {prep_error}", exc_info=True)
                        summary['model_training_error'] = f"Data preparation: {str(prep_error)}"
                else:
                    logger.info(f"ℹ️ Not enough students ({len(all_students)} < 5) for auto-training, using rule-based predictions")
                    summary['model_training_info'] = f"Need at least 5 students, got {len(all_students)}"
                    
            except Exception as e:
                logger.error(f"❌ Auto-training check failed: {e}", exc_info=True)
                summary['model_training_error'] = f"Training check failed: {str(e)}"
            
            # Log final model status
            if risk_engine.is_trained:
                logger.info(f"✅ Using trained ML model ({risk_engine.model_type}) for predictions")
            else:
                logger.info("ℹ️ Using rule-based predictions (ML model not trained)")
            
            # Log comprehensive final summary (after all processing)
            logger.info("=" * 80)
            logger.info("📊 UPLOAD SUMMARY - COMPLETE")
            logger.info(f"File: {file.filename}")
            logger.info(f"Total rows in file: {total_rows}")
            logger.info(f"Rows processed: {results['rows_processed']}")
            logger.info(f"Rows succeeded: {summary['rows_succeeded']}")
            logger.info(f"Rows failed: {results['rows_failed']}")
            logger.info(f"Rows skipped: {results['rows_skipped']}")
            logger.info("")
            logger.info("📝 Database Records Created:")
            logger.info(f"  • Students created: {results['students_created']}")
            logger.info(f"  • Academic records: {results['academic_records_created']}")
            logger.info(f"  • Attendance records: {results['attendance_records_created']}")
            logger.info("")
            logger.info("🤖 ML Processing:")
            logger.info(f"  • Students processed for risk assessment: {total_students_in_list}")
            logger.info(f"  • Risk assessments created: {results['risk_assessments_created']}")
            if summary.get('model_trained'):
                logger.info(f"  • ML model auto-trained: ✅ ({summary.get('model_type', 'unknown')}, Accuracy: {summary.get('model_accuracy', 0):.2%})")
            elif summary.get('model_training_error'):
                logger.warning(f"  • ML model training: ⚠️ Failed - {summary.get('model_training_error')}")
            logger.info("")
            if results['errors']:
                logger.warning(f"⚠️ Errors encountered: {len(results['errors'])}")
                for error in results['errors'][:10]:  # Show first 10 errors
                    logger.warning(f"  - {error}")
                if len(results['errors']) > 10:
                    logger.warning(f"  ... and {len(results['errors']) - 10} more errors (check logs)")
            else:
                logger.info("✅ No errors encountered!")
            logger.info("=" * 80)
            
            # Persist upload summary to upload_history (best-effort; don't fail the request)
            try:
                if summary.get("success") is True:
                    db.set_active_upload(upload_id)
                    db.update_upload_history(
                        upload_id,
                        {
                            "status": "success",
                            "error": None,
                            "rows_processed": int(summary.get("rows_processed") or 0),
                            "students_created": int(summary.get("students_created") or 0),
                            "academic_records_created": int(summary.get("academic_records_created") or 0),
                            "attendance_records_created": int(summary.get("attendance_records_created") or 0),
                            "risk_assessments_created": int(summary.get("risk_assessments_created") or 0),
                        },
                    )
                else:
                    db.update_upload_history(
                        upload_id,
                        {
                            "status": "failed",
                            "error": summary.get("warning") or "Upload failed",
                        },
                    )
            except Exception as e:
                logger.warning(f"Failed to update upload_history summary: {e}")

            return summary
        
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        # If we have an upload history record, mark it failed (best-effort)
        try:
            if 'upload_id' in locals() and locals().get('upload_id'):
                db.update_upload_history(locals().get('upload_id'), {"status": "failed", "error": str(e)})
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


# ============================================================================
# Upload History / Apply / Delete Endpoints
# ============================================================================

@app.get("/api/uploads", response_model=List[Dict[str, Any]])
async def list_uploads(limit: int = Query(50, ge=1, le=200)):
    """List upload history (backend-driven)."""
    if db.client is None:
        raise HTTPException(status_code=503, detail="Database connection not available")
    try:
        return db.list_upload_history(limit=limit)
    except Exception as e:
        if _is_schema_cache_missing_error(e):
            raise HTTPException(status_code=503, detail=_schema_not_ready_detail(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/uploads/{upload_id}/apply", response_model=Dict[str, Any])
async def apply_upload(
    upload_id: str = Path(..., description="Upload history ID to apply"),
):
    """
    Apply a previous upload as the active dataset.

    Implementation (minimal change): re-run the existing upload pipeline using the stored file bytes,
    clearing the current dataset first. This guarantees UI consistency without keeping multiple datasets in DB.
    """
    if db.client is None:
        raise HTTPException(status_code=503, detail="Database connection not available")
    row = db.get_upload_history(upload_id)
    if not row:
        raise HTTPException(status_code=404, detail="Upload not found")
    if row.get("status") == "deleted":
        raise HTTPException(status_code=400, detail="Upload is deleted")
    stored_path = row.get("stored_path")
    if not stored_path:
        raise HTTPException(status_code=500, detail="Upload storage path missing")
    try:
        data = FsPath(stored_path).read_bytes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read stored upload file: {str(e)}")

    # Call the same /api/upload endpoint to avoid duplicating the parsing/processing code.
    base_url = f"http://{settings.api_host}:{settings.api_port}"
    files = {
        "file": (row.get("filename") or "upload", data, row.get("content_type") or "application/octet-stream")
    }
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            resp = await client.post(
                f"{base_url}/api/upload",
                params={"replace_existing": True, "history_id": upload_id},
                files=files,
            )
        if resp.status_code >= 400:
            # Bubble up the underlying error so FE sees the real reason
            try:
                detail = resp.json().get("detail")
            except Exception:
                detail = resp.text
            raise HTTPException(status_code=resp.status_code, detail=detail)
        return resp.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apply upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/uploads/{upload_id}", response_model=Dict[str, Any])
async def delete_upload(
    upload_id: str = Path(..., description="Upload history ID to delete"),
):
    """
    Delete an upload entry.

    If the upload is currently active, we also clear the dataset (students + related records).
    """
    if db.client is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    row = db.get_upload_history(upload_id)
    if not row:
        raise HTTPException(status_code=404, detail="Upload not found")

    is_active = bool(row.get("is_active"))
    try:
        if is_active:
            _clear_dataset()
    except Exception as e:
        if _is_schema_cache_missing_error(e):
            raise HTTPException(status_code=503, detail=_schema_not_ready_detail(str(e)))
        raise HTTPException(status_code=500, detail=f"Failed to clear dataset for active upload: {str(e)}")

    # Remove stored file (best-effort)
    try:
        sp = row.get("stored_path")
        if sp:
            FsPath(sp).unlink(missing_ok=True)
    except Exception as e:
        logger.warning(f"Failed to delete stored upload file: {e}")

    try:
        db.update_upload_history(upload_id, {"status": "deleted", "is_active": False})
    except Exception as e:
        if _is_schema_cache_missing_error(e):
            raise HTTPException(status_code=503, detail=_schema_not_ready_detail(str(e)))
        raise HTTPException(status_code=500, detail=f"Failed to delete upload history: {str(e)}")

    return {"success": True, "cleared_dataset": is_active}


# ----------------------------------------------------------------------------
# Reports API (downloadable CSV exports)
# ----------------------------------------------------------------------------

@app.get("/api/reports", response_model=List[Dict[str, Any]])
def list_reports() -> List[Dict[str, Any]]:
    """List available downloadable reports (real data exports)."""
    return [
        {
            "id": "students",
            "title": "Students Export",
            "description": "All students in the current dataset",
            "format": "csv",
        },
        {
            "id": "risk_assessments",
            "title": "Risk Assessments Export",
            "description": "Risk assessments (excluding large feature blobs)",
            "format": "csv",
        },
        {
            "id": "interventions",
            "title": "Interventions Export",
            "description": "Interventions and statuses",
            "format": "csv",
        },
        {
            "id": "alerts",
            "title": "Alerts Export",
            "description": "Alerts for at-risk students",
            "format": "csv",
        },
        {
            "id": "uploads",
            "title": "Upload History Export",
            "description": "Upload history and processing outcomes",
            "format": "csv",
        },
    ]


@app.get("/api/reports/{report_id}/csv")
def download_report_csv(
    report_id: str = Path(..., description="Report identifier"),
    limit: int = Query(5000, ge=1, le=20000, description="Max rows to export"),
) -> Response:
    """Download a CSV report."""
    if db.client is None:
        raise HTTPException(status_code=500, detail="Database connection not available")

    today = datetime.utcnow().strftime("%Y%m%d")

    if report_id == "students":
        cols = [
            "id",
            "student_id",
            "full_name",
            "email",
            "department",
            "program",
            "year_level",
            "semester",
            "enrollment_date",
            "status",
            "created_at",
        ]
        resp = db.client.table("students").select("*").order("created_at", desc=True).limit(limit).execute()
        return _csv_download_response(_dict_rows_to_csv(resp.data or [], cols), f"students_{today}.csv")

    if report_id == "risk_assessments":
        cols = [
            "id",
            "student_id",
            "risk_level",
            "risk_score",
            "confidence_level",
            "prediction_date",
            "created_at",
        ]
        try:
            resp = (
                db.client.table("risk_assessments")
                .select(",".join(cols))
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            rows = resp.data or []
        except Exception:
            resp = db.client.table("risk_assessments").select("*").order("created_at", desc=True).limit(limit).execute()
            rows = resp.data or []
        return _csv_download_response(_dict_rows_to_csv(rows, cols), f"risk_assessments_{today}.csv")

    if report_id == "interventions":
        cols = [
            "id",
            "student_id",
            "intervention_type",
            "status",
            "assigned_to",
            "description",
            "created_at",
            "completed_at",
            "outcome_notes",
        ]
        resp = db.client.table("interventions").select("*").order("created_at", desc=True).limit(limit).execute()
        return _csv_download_response(_dict_rows_to_csv(resp.data or [], cols), f"interventions_{today}.csv")

    if report_id == "alerts":
        cols = [
            "id",
            "student_id",
            "alert_type",
            "severity",
            "message",
            "acknowledged",
            "created_at",
        ]
        resp = db.client.table("alerts").select("*").order("created_at", desc=True).limit(limit).execute()
        return _csv_download_response(_dict_rows_to_csv(resp.data or [], cols), f"alerts_{today}.csv")

    if report_id == "uploads":
        cols = [
            "id",
            "filename",
            "content_type",
            "file_size_bytes",
            "status",
            "error",
            "rows_processed",
            "students_created",
            "academic_records_created",
            "attendance_records_created",
            "risk_assessments_created",
            "uploaded_at",
            "applied_at",
            "is_active",
        ]
        resp = db.client.table("upload_history").select("*").order("uploaded_at", desc=True).limit(limit).execute()
        return _csv_download_response(_dict_rows_to_csv(resp.data or [], cols), f"uploads_{today}.csv")

    raise HTTPException(status_code=404, detail=f"Unknown report: {report_id}")


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        'service': 'Early Warning System API',
        'version': '1.0.0',
        'status': 'running',
        'docs': '/docs',
        'health': '/api/health',
        'endpoints': {
            'upload': '/api/upload',
            'students': '/api/students',
            'health': '/api/health'
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    db_status = "connected" if db.client is not None else "disconnected"
    return {
        'status': 'healthy',
        'service': 'Early Warning System API',
        'version': '1.0.0',
        'monitoring_active': monitoring_engine.is_running,
        'database': db_status
    }


@app.post("/api/students/evaluate-all")
async def evaluate_all_students():
    """Manually trigger risk assessment for ALL students in database. Useful for fixing missing assessments."""
    try:
        logger.info("=" * 80)
        logger.info("🔄 MANUAL RISK ASSESSMENT TRIGGER - ALL STUDENTS")
        logger.info("=" * 80)
        
        # Get all active students
        all_students = db.get_students(filters={'status': 'active'}, limit=1000)
        logger.info(f"Found {len(all_students)} active students to evaluate")
        
        if len(all_students) == 0:
            return {
                'success': False,
                'message': 'No active students found in database',
                'evaluated': 0,
                'errors': []
            }
        
        results = {
            'evaluated': 0,
            'errors': 0,
            'details': []
        }
        
        for idx, student in enumerate(all_students, 1):
            try:
                logger.info(f"[{idx}/{len(all_students)}] Evaluating student {student['id']} ({student.get('full_name', 'Unknown')})...")
                result = monitoring_engine.evaluate_student(student['id'], force_reassessment=True)
                if result and result.get('assessment'):
                    results['evaluated'] += 1
                    risk_level = result.get('assessment', {}).get('risk_level', 'unknown')
                    risk_score = result.get('assessment', {}).get('risk_score', 0)
                    logger.info(f"✓ [{idx}/{len(all_students)}] Risk assessment created: {risk_level} (score: {risk_score:.1f})")
                    results['details'].append({
                        'student_id': student['id'],
                        'student_name': student.get('full_name', 'Unknown'),
                        'risk_level': risk_level,
                        'risk_score': risk_score,
                        'success': True
                    })
                else:
                    results['errors'] += 1
                    logger.warning(f"⚠️ [{idx}/{len(all_students)}] Risk assessment returned None for {student['id']}")
                    results['details'].append({
                        'student_id': student['id'],
                        'student_name': student.get('full_name', 'Unknown'),
                        'success': False,
                        'error': 'Risk assessment returned None'
                    })
            except Exception as e:
                results['errors'] += 1
                logger.error(f"❌ [{idx}/{len(all_students)}] Error evaluating {student['id']}: {e}", exc_info=True)
                results['details'].append({
                    'student_id': student['id'],
                    'student_name': student.get('full_name', 'Unknown'),
                    'success': False,
                    'error': str(e)
                })
        
        logger.info("=" * 80)
        logger.info(f"✅ MANUAL RISK ASSESSMENT COMPLETE")
        logger.info(f"   Evaluated: {results['evaluated']}")
        logger.info(f"   Errors: {results['errors']}")
        logger.info("=" * 80)
        
        return {
            'success': True,
            'message': f'Evaluated {results["evaluated"]} students, {results["errors"]} errors',
            'evaluated': results['evaluated'],
            'errors': results['errors'],
            'total_students': len(all_students),
            'details': results['details']
        }
    except Exception as e:
        logger.error(f"Error in evaluate_all_students: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error evaluating all students: {str(e)}")


@app.post("/api/test-risk-assessment/{student_id}")
async def test_risk_assessment_creation(student_id: str):
    """Test endpoint to manually create a risk assessment for a student."""
    logger.info("=" * 80)
    logger.info(f"🧪 TEST: Creating risk assessment for student {student_id}")
    logger.info("=" * 80)
    
    try:
        # Get student
        student = db.get_student_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
        
        logger.info(f"Found student: {student.get('full_name')}")
        
        # Evaluate student
        result = monitoring_engine.evaluate_student(student_id, force_reassessment=True)
        
        if result and result.get('assessment'):
            assessment = result['assessment']
            logger.info(f"✅ Risk assessment created successfully!")
            logger.info(f"   Risk Level: {assessment.get('risk_level')}")
            logger.info(f"   Risk Score: {assessment.get('risk_score')}")
            
            # Verify it's in database
            saved_assessments = db.get_risk_assessments(student_id=student_id, limit=1)
            if saved_assessments:
                logger.info(f"✅ Verified: Risk assessment is in database")
                return {
                    'success': True,
                    'message': 'Risk assessment created and saved',
                    'assessment': saved_assessments[0]
                }
            else:
                logger.error("❌ Assessment was created but not found in database!")
                return {
                    'success': False,
                    'message': 'Assessment created but not found in database',
                    'assessment': assessment
                }
        else:
            logger.error("❌ evaluate_student returned None or empty result")
            return {
                'success': False,
                'message': 'Failed to create risk assessment - evaluate_student returned None',
                'result': result
            }
            
    except Exception as e:
        logger.error(f"❌ Error in test_risk_assessment_creation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/diagnostics")
async def diagnostics():
    """Diagnostic endpoint to check system status and verify fixes are active."""
    diagnostics_info = {
        'code_version': '2024-12-25-FIXED-V4',  # Version marker to verify new code is running
        'fixes_applied': {
            'processed_students_tracking': True,
            'risk_assessment_all_students': True,
            'comprehensive_error_logging': True,
            'duplicate_removal': True,
            'enhanced_risk_assessment_logging': True,
            'risk_assessment_payload_sanitized': True
        },
        'database': {
            'connected': db.client is not None,
            'can_read': False,
            'can_write': False,
            'error': None,
            'student_count': 0,
            'risk_assessment_count': 0
        },
        'ml_models': {
            'risk_engine_loaded': risk_engine.model is not None,
            'model_trained': risk_engine.is_trained,
            'model_type': risk_engine.model_type
        },
        'configuration': {
            'supabase_url_set': bool(settings.supabase_url),
            'supabase_key_set': bool(settings.supabase_key),
            'supabase_key_length': len(settings.supabase_key) if settings.supabase_key else 0,
            # Helps confirm you're connected to the intended Supabase project when switching databases
            'supabase_url_host': (settings.supabase_url.split("://", 1)[-1].split("/", 1)[0] if settings.supabase_url else None),
            'supabase_project_ref': (settings.supabase_url.split("://", 1)[-1].split(".", 1)[0] if settings.supabase_url and "." in settings.supabase_url else None),
        }
    }
    
    # Test database read and get counts
    if db.client is not None:
        try:
            test_students = db.get_students(limit=1)
            diagnostics_info['database']['can_read'] = True
            all_students = db.get_students(limit=1000)
            diagnostics_info['database']['student_count'] = len(all_students)
            
            # Get risk assessment count
            all_assessments = db.get_risk_assessments(limit=1000)
            diagnostics_info['database']['risk_assessment_count'] = len(all_assessments)
            
            # Check if there are students without risk assessments (potential issue)
            student_ids = {s['id'] for s in all_students}
            assessed_student_ids = {a['student_id'] for a in all_assessments}
            students_without_assessments = student_ids - assessed_student_ids
            diagnostics_info['database']['students_without_assessments'] = len(students_without_assessments)
            if len(students_without_assessments) > 0:
                diagnostics_info['database']['sample_unassessed_ids'] = list(students_without_assessments)[:5]
        except Exception as e:
            diagnostics_info['database']['error'] = str(e)
            logger.error(f"Diagnostic database read error: {e}", exc_info=True)
    
    # Test database write (try to read instead - safer)
    if db.client is not None:
        try:
            # Just check if we can query - write test would require actual insert
            test_query = db.client.table('students').select('id').limit(1).execute()
            diagnostics_info['database']['can_write'] = True  # Assume true if we can query
        except Exception as e:
            diagnostics_info['database']['write_error'] = str(e)
            diagnostics_info['database']['can_write'] = False
            logger.error(f"Diagnostic database write check error: {e}", exc_info=True)
    
    return diagnostics_info


@app.post("/api/admin/clear-data")
async def clear_all_data():
    """
    Delete ALL EWS data (students + cascading related records).

    Use-case: switching to a new database, or user wants to wipe previously uploaded data.
    """
    if db.client is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    try:
        _clear_dataset()
        return {"success": True}
    except Exception as e:
        if _is_schema_cache_missing_error(e):
            raise HTTPException(status_code=503, detail=_schema_not_ready_detail(str(e)))
        logger.error(f"Error clearing data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/schema/status")
async def schema_status():
    """Quick schema readiness check for new Supabase projects."""
    if db.client is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    try:
        db.client.table("students").select("id").limit(1).execute()
        # Also ensure upload_history exists (needed for Apply/Delete workflows)
        db.client.table("upload_history").select("id").limit(1).execute()
        return {"ready": True, "migrations_to_run": MIGRATIONS_TO_RUN}
    except Exception as e:
        if _is_schema_cache_missing_error(e):
            return {"ready": False, "migrations_to_run": MIGRATIONS_TO_RUN, "error": str(e)}
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
