"""
Continuous monitoring engine for periodic risk re-evaluation.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import json

from database import db
from data_processing import processor
from risk_engine import risk_engine
from early_warning import detector
from models import RiskAssessment
from config import settings

logger = logging.getLogger(__name__)


class MonitoringEngine:
    """Continuous monitoring engine for student risk assessment."""
    
    def __init__(self):
        """Initialize the monitoring engine."""
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self):
        """Start the monitoring engine."""
        if not self.is_running:
            try:
                # Schedule periodic risk assessment
                interval_minutes = settings.monitoring_interval_minutes
                trigger = IntervalTrigger(minutes=interval_minutes)
                self.scheduler.add_job(
                    self.evaluate_all_students,
                    trigger=trigger,
                    id='risk_assessment',
                    name='Periodic Risk Assessment',
                    replace_existing=True
                )
                
                self.scheduler.start()
                self.is_running = True
                logger.info(f"Monitoring engine started (interval: {interval_minutes} minutes)")
            except Exception as e:
                logger.error(f"Error starting monitoring engine: {e}")
                raise
    
    def stop(self):
        """Stop the monitoring engine."""
        if self.is_running:
            try:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Monitoring engine stopped")
            except Exception as e:
                logger.error(f"Error stopping monitoring engine: {e}")
    
    def evaluate_all_students(self):
        """Evaluate risk for all active students."""
        try:
            logger.info("Starting periodic risk assessment for all students...")
            
            # Get all active students
            students = db.get_students(filters={'status': 'active'})
            
            logger.info(f"Evaluating {len(students)} active students...")
            
            evaluated = 0
            alerts_created = 0
            
            for student in students:
                try:
                    result = self.evaluate_student(student['id'])
                    if result:
                        evaluated += 1
                        alerts_created += result.get('alerts_created', 0)
                except Exception as e:
                    logger.error(f"Error evaluating student {student['id']}: {e}")
                    continue
            
            logger.info(
                f"Risk assessment completed. "
                f"Evaluated: {evaluated}, Alerts created: {alerts_created}"
            )
        except Exception as e:
            logger.error(f"Error in periodic risk assessment: {e}")
    
    def evaluate_student(
        self,
        student_id: str,
        force_reassessment: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Evaluate risk for a single student."""
        try:
            # Get student data
            student = db.get_student_by_id(student_id)
            if not student:
                logger.warning(f"Student {student_id} not found")
                return None
            
            # Get academic records
            academic_records = db.get_academic_records(student_id=student_id)
            
            # Get attendance records
            attendance_records = db.get_attendance_records(student_id=student_id)
            
            # Get previous risk assessment
            previous_assessments = db.get_risk_assessments(student_id=student_id, limit=1)
            previous_risk = None
            if previous_assessments:
                try:
                    # Handle both dict and RiskAssessment object
                    prev_data = previous_assessments[0]
                    if isinstance(prev_data, dict):
                        # Ensure created_at is set if None
                        if prev_data.get('created_at') is None:
                            prev_data['created_at'] = datetime.utcnow().isoformat()
                        previous_risk = RiskAssessment(**prev_data)
                    else:
                        previous_risk = prev_data
                        # Ensure created_at is set
                        if not previous_risk.created_at:
                            previous_risk.created_at = datetime.utcnow()
                except Exception as e:
                    logger.warning(f"Could not parse previous risk assessment: {e}")
                    logger.debug(f"Previous assessment data: {previous_assessments[0] if previous_assessments else None}")
                    previous_risk = None
            
            # Check if we need to reassess (if data has changed or force)
            if not force_reassessment and previous_risk:
                # Check if data has changed significantly
                try:
                    last_assessment_time_str = previous_risk.created_at
                    if last_assessment_time_str:
                        # Handle both string and datetime objects
                        if isinstance(last_assessment_time_str, str):
                            # Try parsing with timezone, fallback to without
                            try:
                                last_assessment_time = datetime.fromisoformat(
                                    last_assessment_time_str.replace('Z', '+00:00')
                                )
                            except:
                                try:
                                    last_assessment_time = datetime.fromisoformat(last_assessment_time_str)
                                except:
                                    last_assessment_time = datetime.utcnow()
                        else:
                            last_assessment_time = last_assessment_time_str
                    else:
                        last_assessment_time = datetime.utcnow()
                    
                    # Only reassess if enough time has passed or data has changed
                    time_since_assessment = (datetime.utcnow() - last_assessment_time).total_seconds() / 60
                    if time_since_assessment < settings.monitoring_interval_minutes:
                        logger.debug(f"Skipping student {student_id} - recently assessed ({time_since_assessment:.1f} minutes ago)")
                        # Return existing assessment
                        return {
                            'assessment': previous_assessments[0],
                            'alerts_created': 0,
                            'risk_change': None,
                            'feature_set': {}
                        }
                except Exception as time_error:
                    logger.warning(f"Error parsing previous assessment time: {time_error}. Force reassessing.")
                    # Continue with reassessment
            
            # Get warning and intervention counts
            all_alerts = db.get_alerts(student_id=student_id)
            warning_count = len([a for a in all_alerts if a.get('severity') in ['high', 'critical']])
            
            interventions = db.get_interventions(student_id=student_id)
            intervention_count = len(interventions)
            
            # Engineer features
            feature_set = processor.engineer_features(
                academic_records=academic_records,
                attendance_records=attendance_records,
                previous_risk_score=previous_risk.risk_score if previous_risk else 0.0,
                warning_count=warning_count,
                intervention_count=intervention_count,
                enrollment_date=student.get('enrollment_date'),
                student_data=student
            )
            
            # CRITICAL FIX: Ensure feature set is valid even with no data
            # If student has no academic/attendance records, create baseline features
            if not academic_records and not attendance_records:
                logger.warning(f"Student {student_id} has no academic or attendance records. Creating baseline risk assessment.")
                # FeatureSet will have default values (zeros), which is fine for initial assessment
            
            # Predict risk (will use rule-based if ML not trained)
            risk_assessment = risk_engine.predict_risk(feature_set, use_ml=True)
            risk_assessment.student_id = student_id
            
            # CRITICAL FIX: Ensure created_at is set before saving
            if not risk_assessment.created_at:
                risk_assessment.created_at = datetime.utcnow()
            
            # Convert to dict for database
            try:
                assessment_dict = risk_assessment.dict(exclude_none=True)
                
                # Handle prediction_date conversion safely
                if 'prediction_date' in assessment_dict and assessment_dict['prediction_date']:
                    if hasattr(assessment_dict['prediction_date'], 'isoformat'):
                        assessment_dict['prediction_date'] = assessment_dict['prediction_date'].isoformat()
                    elif isinstance(assessment_dict['prediction_date'], str):
                        # Already a string, keep as is
                        pass
                    else:
                        # Fallback: convert to string
                        assessment_dict['prediction_date'] = str(assessment_dict['prediction_date'])
                else:
                    # Use current time if missing
                    assessment_dict['prediction_date'] = datetime.utcnow().isoformat()
                
                # CRITICAL FIX: Ensure created_at is set for database
                if 'created_at' not in assessment_dict or assessment_dict['created_at'] is None:
                    assessment_dict['created_at'] = datetime.utcnow().isoformat()
                else:
                    # Convert datetime objects to ISO strings for JSON transport
                    try:
                        if hasattr(assessment_dict['created_at'], 'isoformat') and not isinstance(assessment_dict['created_at'], str):
                            assessment_dict['created_at'] = assessment_dict['created_at'].isoformat()
                    except Exception:
                        # Fallback: stringify
                        assessment_dict['created_at'] = str(assessment_dict['created_at'])
                
                # Store explanation and top_factors in factors JSONB for database
                factors_dict = assessment_dict.get('factors', {})
                if not isinstance(factors_dict, dict):
                    factors_dict = {}
                    
                if risk_assessment.explanation:
                    factors_dict['explanation'] = risk_assessment.explanation
                if risk_assessment.top_factors:
                    factors_dict['top_factors'] = [
                        {
                            'name': str(f.name) if hasattr(f, 'name') else '',
                            'weight': float(f.weight) if hasattr(f, 'weight') else 0.0,
                            'value': float(f.value) if hasattr(f, 'value') else 0.0,
                            'impact': str(f.impact) if hasattr(f, 'impact') else ''
                        }
                        for f in risk_assessment.top_factors
                    ]
                assessment_dict['factors'] = factors_dict

                # CRITICAL FIX: Remove non-column fields before inserting into Supabase table.
                # The `risk_assessments` table schema stores extra details inside `factors` (jsonb),
                # and does NOT have dedicated `explanation` / `top_factors` columns.
                assessment_dict.pop('explanation', None)
                assessment_dict.pop('top_factors', None)

                # CRITICAL FIX: Ensure we only send columns that exist in the DB schema.
                # This prevents silent failures when extra Pydantic fields are present.
                allowed_keys = {
                    'student_id',
                    'risk_level',
                    'risk_score',
                    'confidence_level',
                    'factors',
                    'prediction_date',
                    'created_at',
                }
                assessment_dict = {k: v for k, v in assessment_dict.items() if k in allowed_keys and v is not None}

                # Ensure JSON-serializable payload (Supabase client sends JSON over HTTP)
                try:
                    assessment_dict['factors'] = json.loads(json.dumps(assessment_dict.get('factors', {}), default=str))
                except Exception:
                    assessment_dict['factors'] = {}

                # Ensure numeric types are plain Python floats (avoid numpy/pandas scalar issues)
                try:
                    if 'risk_score' in assessment_dict:
                        assessment_dict['risk_score'] = float(assessment_dict['risk_score'])
                    if 'confidence_level' in assessment_dict:
                        assessment_dict['confidence_level'] = float(assessment_dict['confidence_level'])
                except Exception:
                    pass
                
                logger.debug(f"Prepared risk assessment dict for student {student_id}: risk_level={assessment_dict.get('risk_level')}, risk_score={assessment_dict.get('risk_score')}")
            except Exception as dict_error:
                logger.error(f"Error converting risk assessment to dict for student {student_id}: {dict_error}", exc_info=True)
                logger.error(f"RiskAssessment object: {risk_assessment}")
                return None
            
            # CRITICAL FIX: Save risk assessment with retry and better error handling
            saved_assessment = db.create_risk_assessment(assessment_dict)
            if not saved_assessment:
                logger.error("=" * 80)
                logger.error(f"❌ CRITICAL: Failed to save risk assessment for student {student_id}")
                logger.error(f"Assessment data: risk_level={assessment_dict.get('risk_level')}, risk_score={assessment_dict.get('risk_score')}")
                logger.error("Common causes:")
                logger.error("  1. RLS (Row Level Security) blocking inserts")
                logger.error("  2. SUPABASE_KEY is not the service role key")
                logger.error("  3. Database permissions issue")
                logger.error("  4. Invalid data format")
                logger.error("=" * 80)
                
                # Try one more time after a brief delay
                import time
                time.sleep(0.5)
                saved_assessment = db.create_risk_assessment(assessment_dict)
                if not saved_assessment:
                    logger.error(f"❌ Retry also failed. Risk assessment NOT saved for student {student_id}")
                    return None
                else:
                    logger.info(f"✅ Retry succeeded. Risk assessment saved for student {student_id}")
            
            logger.info(
                f"Student {student_id}: Risk={risk_assessment.risk_level} "
                f"(Score: {risk_assessment.risk_score:.1f}, "
                f"Confidence: {risk_assessment.confidence_level:.2f})"
            )
            
            # Detect early warnings
            warnings = detector.detect_warnings(
                student_id=student_id,
                feature_set=feature_set,
                risk_assessment=risk_assessment,
                previous_risk=previous_risk
            )
            
            # Save alerts
            alerts_created = 0
            if warnings:
                saved_alerts = detector.save_alerts(warnings)
                alerts_created = len(saved_alerts)
                if alerts_created > 0:
                    logger.info(f"Created {alerts_created} alerts for student {student_id}")
            
            # Check for risk changes
            risk_change = None
            if previous_risk:
                risk_change = {
                    'score_change': risk_assessment.risk_score - previous_risk.risk_score,
                    'level_change': risk_assessment.risk_level != previous_risk.risk_level,
                    'previous_level': previous_risk.risk_level,
                    'current_level': risk_assessment.risk_level
                }
            
            return {
                'assessment': saved_assessment,
                'alerts_created': alerts_created,
                'risk_change': risk_change,
                'feature_set': feature_set.dict()
            }
        except Exception as e:
            logger.error(f"Error evaluating student {student_id}: {e}")
            return None
    
    def evaluate_students_batch(
        self,
        student_ids: List[str]
    ) -> Dict[str, Any]:
        """Evaluate risk for a batch of students."""
        results = {
            'evaluated': 0,
            'alerts_created': 0,
            'errors': 0,
            'details': []
        }
        
        for student_id in student_ids:
            try:
                result = self.evaluate_student(student_id, force_reassessment=True)
                if result:
                    results['evaluated'] += 1
                    results['alerts_created'] += result.get('alerts_created', 0)
                    results['details'].append({
                        'student_id': student_id,
                        'risk_level': result['assessment'].get('risk_level'),
                        'risk_score': result['assessment'].get('risk_score')
                    })
                else:
                    results['errors'] += 1
            except Exception as e:
                logger.error(f"Error in batch evaluation for student {student_id}: {e}")
                results['errors'] += 1
        
        return results


# Global monitoring engine instance
monitoring_engine = MonitoringEngine()
