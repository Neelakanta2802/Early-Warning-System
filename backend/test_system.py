"""
Comprehensive system test script to verify all components are working.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from database import db
from risk_engine import risk_engine
from data_processing import processor
from early_warning import detector
from monitoring import monitoring_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection."""
    print("\n" + "="*80)
    print("TEST 1: Database Connection")
    print("="*80)
    
    if not settings.supabase_url or not settings.supabase_key:
        print("[FAILED] Supabase credentials missing!")
        print(f"   SUPABASE_URL: {'SET' if settings.supabase_url else 'MISSING'}")
        print(f"   SUPABASE_KEY: {'SET' if settings.supabase_key else 'MISSING'}")
        return False
    
    # Check if key looks like service role key (should be long, starts with eyJ)
    key_length = len(settings.supabase_key)
    if key_length < 100:
        print(f"[WARNING] SUPABASE_KEY is only {key_length} characters long.")
        print("   Service role keys are typically 200+ characters.")
        print("   You may be using the anon key instead of the service role key!")
    
    print(f"[OK] SUPABASE_URL: {settings.supabase_url[:30]}...")
    print(f"[OK] SUPABASE_KEY: {'*' * 20}... (length: {len(settings.supabase_key)})")
    
    if db.client is None:
        print("[FAILED] Database client not initialized")
        return False
    
    print("[OK] Database client initialized")
    
    # Test query
    try:
        result = db.client.table('students').select('id').limit(1).execute()
        print("[OK] Database query successful")
        return True
    except Exception as e:
        print(f"[FAILED] Database query error: {e}")
        if 'permission' in str(e).lower() or 'policy' in str(e).lower():
            print("   [WARNING] This looks like an RLS (Row Level Security) error!")
            print("   [WARNING] Make sure you're using the SERVICE ROLE KEY, not the anon key")
        return False

def test_ml_models():
    """Test ML models."""
    print("\n" + "="*80)
    print("TEST 2: ML Models")
    print("="*80)
    
    print(f"[OK] Model type: {risk_engine.model_type}")
    print(f"[OK] Model initialized: {risk_engine.model is not None}")
    print(f"[OK] Model trained: {risk_engine.is_trained}")
    
    # Test with dummy features
    try:
        from models import FeatureSet
        dummy_features = FeatureSet(
            current_gpa=2.5,
            gpa_trend=-0.2,
            overall_attendance=70.0,
            attendance_trend=-10.0,
            recent_grades=[65, 70, 68],
            failed_courses_count=1,
            credits_completed=30,
            gpa_variance=0.3,
            gpa_momentum=-0.1,
            gpa_acceleration=-0.05,
            gpa_rolling_avg_3=2.4,
            gpa_rolling_avg_6=2.5,
            low_grade_count=2,
            subject_variance=0.5,
            attendance_rate_recent=65.0,
            attendance_rate_historical=75.0,
            attendance_trend_recent=-15.0,
            consecutive_absences=3,
            total_absences=15,
            total_present=35,
            sudden_drop_detected=True,
            sudden_behavior_change=False,
            previous_risk_score=60.0,
            warning_count=2,
            intervention_count=0
        )
        
        result = risk_engine.predict_risk(dummy_features, use_ml=True)
        print(f"[OK] Risk prediction successful")
        print(f"  - Risk Level: {result.risk_level}")
        print(f"  - Risk Score: {result.risk_score:.1f}")
        print(f"  - Confidence: {result.confidence_level:.2f}")
        return True
    except Exception as e:
        print(f"[FAILED] ML model prediction error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_processing():
    """Test data processing."""
    print("\n" + "="*80)
    print("TEST 3: Data Processing")
    print("="*80)
    
    try:
        # Test with dummy data
        academic_records = [
            {'gpa': 3.0, 'grade': 85, 'semester': 'Fall 2024', 'course_code': 'CS101'},
            {'gpa': 2.8, 'grade': 78, 'semester': 'Spring 2024', 'course_code': 'CS102'},
        ]
        attendance_records = [
            {'status': 'present', 'date': '2024-09-15'},
            {'status': 'absent', 'date': '2024-09-16'},
            {'status': 'present', 'date': '2024-09-17'},
        ]
        
        features = processor.engineer_features(
            academic_records=academic_records,
            attendance_records=attendance_records,
            previous_risk_score=50.0,
            warning_count=0,
            intervention_count=0
        )
        
        print("[OK] Feature engineering successful")
        print(f"  - Current GPA: {features.current_gpa:.2f}")
        print(f"  - GPA Trend: {features.gpa_trend:.2f}")
        print(f"  - Attendance: {features.overall_attendance:.1f}%")
        return True
    except Exception as e:
        print(f"[FAILED] Data processing error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_early_warning():
    """Test early warning detection."""
    print("\n" + "="*80)
    print("TEST 4: Early Warning System")
    print("="*80)
    
    try:
        from models import RiskAssessment, FeatureSet
        risk_assessment = RiskAssessment(
            student_id="test-student-id",
            risk_level="high",
            risk_score=85.0,
            confidence_level=0.9,
            factors={}
        )
        feature_set = FeatureSet(
            current_gpa=1.8,
            overall_attendance=55.0,
            gpa_trend=-0.5,
            attendance_trend=-20.0
        )
        
        warnings = detector.detect_warnings(
            student_id="test-student-id",
            feature_set=feature_set,
            risk_assessment=risk_assessment
        )
        
        print(f"[OK] Early warning detection successful")
        print(f"  - Warnings detected: {len(warnings)}")
        for warning in warnings:
            print(f"    - {warning.alert_type} ({warning.severity})")
        return True
    except Exception as e:
        print(f"[FAILED] Early warning detection error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_operations():
    """Test database operations."""
    print("\n" + "="*80)
    print("TEST 5: Database Operations")
    print("="*80)
    
    if db.client is None:
        print("[SKIPPED] Database client not initialized")
        return False
    
    # Test get_students
    try:
        students = db.get_students(limit=5)
        print(f"[OK] get_students: {len(students)} students found")
    except Exception as e:
        print(f"[FAILED] get_students failed: {e}")
    
    # Test get_risk_assessments
    try:
        assessments = db.get_risk_assessments(limit=5)
        print(f"[OK] get_risk_assessments: {len(assessments)} assessments found")
    except Exception as e:
        print(f"[FAILED] get_risk_assessments failed: {e}")
    
    # Test get_alerts
    try:
        alerts = db.get_alerts(limit=5)
        print(f"[OK] get_alerts: {len(alerts)} alerts found")
    except Exception as e:
        print(f"[FAILED] get_alerts failed: {e}")
    
    return True

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("COMPREHENSIVE SYSTEM TEST")
    print("="*80)
    
    results = []
    
    results.append(("Database Connection", test_database_connection()))
    results.append(("ML Models", test_ml_models()))
    results.append(("Data Processing", test_data_processing()))
    results.append(("Early Warning", test_early_warning()))
    results.append(("Database Operations", test_database_operations()))
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASSED]" if result else "[FAILED]"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! System is ready.")
    else:
        print("\n[WARNING] Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
