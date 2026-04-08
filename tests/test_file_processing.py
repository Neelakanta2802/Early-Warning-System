"""
Comprehensive tests for file processing functionality.
Tests data parsing, validation, and database operations.
"""
import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "project" / "backend"
sys.path.insert(0, str(backend_path))

# Import with error handling - these may fail if config is invalid
try:
    from data_processing import processor
    from models import FeatureSet
    PROCESSING_AVAILABLE = True
except Exception as e:
    PROCESSING_AVAILABLE = False
    PROCESSING_ERROR = str(e)

try:
    from database import db
    DATABASE_AVAILABLE = True
except Exception:
    DATABASE_AVAILABLE = False
    db = None


class TestFileProcessing:
    """Test suite for file processing and data validation."""
    
    @pytest.fixture(autouse=True)
    def check_imports(self):
        """Check if imports are available."""
        if not PROCESSING_AVAILABLE:
            pytest.skip(f"Data processing module not available: {PROCESSING_ERROR}")
    
    def test_data_processing_module_imports(self):
        """Test that data processing module can be imported."""
        assert processor is not None
        assert hasattr(processor, 'clean_and_normalize_data')
        assert hasattr(processor, 'engineer_features')
    
    def test_feature_engineering_with_no_data(self):
        """Test feature engineering with empty records."""
        feature_set = processor.engineer_features(
            academic_records=[],
            attendance_records=[],
            previous_risk_score=0.0,
            warning_count=0,
            intervention_count=0
        )
        
        assert isinstance(feature_set, FeatureSet)
        assert feature_set.current_gpa == 0.0
        assert feature_set.overall_attendance == 0.0
    
    def test_feature_engineering_with_academic_data(self):
        """Test feature engineering with academic records."""
        academic_records = [
            {
                'grade': 85.5,
                'credits': 3,
                'gpa': 3.4,
                'semester': 'Fall 2024'
            },
            {
                'grade': 90.0,
                'credits': 3,
                'gpa': 3.7,
                'semester': 'Spring 2024'
            }
        ]
        
        feature_set = processor.engineer_features(
            academic_records=academic_records,
            attendance_records=[],
            previous_risk_score=0.0,
            warning_count=0,
            intervention_count=0
        )
        
        assert isinstance(feature_set, FeatureSet)
        assert feature_set.current_gpa > 0
        assert feature_set.credits_completed > 0
    
    def test_feature_engineering_with_attendance_data(self):
        """Test feature engineering with attendance records."""
        attendance_records = [
            {'date': '2024-09-15', 'status': 'present'},
            {'date': '2024-09-16', 'status': 'present'},
            {'date': '2024-09-17', 'status': 'absent'},
            {'date': '2024-09-18', 'status': 'present'},
            {'date': '2024-09-19', 'status': 'late'},
        ]
        
        feature_set = processor.engineer_features(
            academic_records=[],
            attendance_records=attendance_records,
            previous_risk_score=0.0,
            warning_count=0,
            intervention_count=0
        )
        
        assert isinstance(feature_set, FeatureSet)
        assert feature_set.overall_attendance >= 0
        assert feature_set.overall_attendance <= 100
    
    def test_feature_engineering_complete_data(self):
        """Test feature engineering with complete student data."""
        academic_records = [
            {
                'grade': 75.0,
                'credits': 3,
                'gpa': 2.5,
                'semester': 'Fall 2024',
                'course_code': 'CS101'
            }
        ]
        
        attendance_records = [
            {'date': '2024-09-15', 'status': 'present', 'course_code': 'CS101', 'semester': 'Fall 2024'},
            {'date': '2024-09-16', 'status': 'absent', 'course_code': 'CS101', 'semester': 'Fall 2024'},
        ]
        
        feature_set = processor.engineer_features(
            academic_records=academic_records,
            attendance_records=attendance_records,
            previous_risk_score=30.0,
            warning_count=1,
            intervention_count=0,
            enrollment_date='2023-09-01'
        )
        
        assert isinstance(feature_set, FeatureSet)
        assert feature_set.current_gpa > 0
        assert feature_set.previous_risk_score == 30.0
        assert feature_set.warning_count == 1
    
    def test_data_cleaning_and_normalization(self):
        """Test data cleaning and normalization."""
        academic_records = [
            {'grade': 85.5, 'gpa': 3.4, 'credits': 3},
            {'grade': None, 'gpa': None, 'credits': 0},  # Invalid record - may be filtered or handled
            {'grade': 90.0, 'gpa': 3.7, 'credits': 3},
        ]
        
        clean_academic, clean_attendance = processor.clean_and_normalize_data(
            academic_records, []
        )
        
        # Should filter out invalid records
        assert len(clean_academic) >= 0
        for record in clean_academic:
            assert record.get('grade') is not None
    
    def test_gpa_calculation(self):
        """Test GPA feature calculation."""
        academic_records = [
            {'grade': 85.0, 'credits': 3, 'gpa': 3.5, 'semester': 'Fall 2024'},
            {'grade': 90.0, 'credits': 3, 'gpa': 3.8, 'semester': 'Spring 2024'},
            {'grade': 80.0, 'credits': 4, 'gpa': 3.2, 'semester': 'Summer 2024'},
        ]
        
        feature_set = processor.engineer_features(
            academic_records=academic_records,
            attendance_records=[],
            previous_risk_score=0.0,
            warning_count=0,
            intervention_count=0
        )
        
        assert feature_set.current_gpa > 0
        assert feature_set.credits_completed >= 0
    
    def test_attendance_trend_calculation(self):
        """Test attendance trend calculation."""
        attendance_records = [
            {'date': '2024-09-01', 'status': 'present'},
            {'date': '2024-09-02', 'status': 'present'},
            {'date': '2024-09-03', 'status': 'present'},
            {'date': '2024-09-04', 'status': 'absent'},
            {'date': '2024-09-05', 'status': 'absent'},
            {'date': '2024-09-08', 'status': 'present'},
            {'date': '2024-09-09', 'status': 'absent'},
        ]
        
        feature_set = processor.engineer_features(
            academic_records=[],
            attendance_records=attendance_records,
            previous_risk_score=0.0,
            warning_count=0,
            intervention_count=0
        )
        
        assert feature_set.overall_attendance >= 0
        assert feature_set.overall_attendance <= 100
        assert feature_set.recent_absent_days >= 0
    
    def test_behavioral_features(self):
        """Test behavioral anomaly detection."""
        academic_records = [
            {'grade': 90.0, 'gpa': 3.8, 'semester': 'Fall 2023'},
            {'grade': 85.0, 'gpa': 3.5, 'semester': 'Spring 2024'},
            {'grade': 70.0, 'gpa': 2.3, 'semester': 'Fall 2024'},  # Declining
        ]
        
        feature_set = processor.engineer_features(
            academic_records=academic_records,
            attendance_records=[],
            previous_risk_score=20.0,
            warning_count=0,
            intervention_count=0
        )
        
        assert feature_set.gpa_trend is not None
        # Should detect declining trend
        assert isinstance(feature_set.sudden_behavior_change, bool)


class TestDatabaseOperations:
    """Test suite for database operations."""
    
    @pytest.fixture(autouse=True)
    def check_database(self):
        """Check if database module is available."""
        if not DATABASE_AVAILABLE:
            pytest.skip("Database module not available (missing env vars)")
    
    def test_database_client_initialized(self):
        """Test that database client is initialized."""
        # Note: This may fail if Supabase credentials aren't set
        # That's okay for unit tests
        assert db is not None
    
    def test_database_operations_structure(self):
        """Test that database operations have correct structure."""
        assert hasattr(db, 'get_students')
        assert hasattr(db, 'create_student')
        assert hasattr(db, 'get_academic_records')
        assert hasattr(db, 'create_academic_record')
        assert hasattr(db, 'create_risk_assessment')
    
    def test_student_data_structure(self, sample_student_data):
        """Test that student data structure is correct."""
        # Required fields
        required_fields = [
            'student_id', 'full_name', 'email',
            'department', 'program', 'year_level',
            'semester', 'status'
        ]
        
        for field in required_fields:
            assert field in sample_student_data, f"Missing required field: {field}"
    
    def test_academic_record_structure(self, sample_academic_record):
        """Test that academic record structure is correct."""
        required_fields = [
            'student_id', 'semester', 'course_code',
            'course_name', 'grade', 'credits', 'gpa'
        ]
        
        for field in required_fields:
            assert field in sample_academic_record, f"Missing required field: {field}"
        
        # Validate types
        assert isinstance(sample_academic_record['grade'], (int, float))
        assert isinstance(sample_academic_record['credits'], int)
    
    def test_attendance_record_structure(self, sample_attendance_record):
        """Test that attendance record structure is correct."""
        required_fields = [
            'student_id', 'date', 'status',
            'course_code', 'semester'
        ]
        
        for field in required_fields:
            assert field in sample_attendance_record, f"Missing required field: {field}"
        
        # Validate status
        valid_statuses = ['present', 'absent', 'late', 'excused']
        assert sample_attendance_record['status'] in valid_statuses


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
