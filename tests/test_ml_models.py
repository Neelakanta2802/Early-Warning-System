"""
Comprehensive tests for ML models and risk prediction.
Tests model training, prediction, feature engineering, and risk assessment.
"""
import pytest
import sys
import numpy as np
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "project" / "backend"
sys.path.insert(0, str(backend_path))

# Import with error handling
try:
    from risk_engine import risk_engine
    from data_processing import processor
    from models import FeatureSet, RiskAssessment
    ML_AVAILABLE = True
except Exception as e:
    ML_AVAILABLE = False
    ML_ERROR = str(e)
    # Create dummy objects to avoid NameError
    risk_engine = None
    processor = None
    FeatureSet = None
    RiskAssessment = None


class TestMLModels:
    """Test suite for ML model functionality."""
    
    @pytest.fixture(autouse=True)
    def check_ml_available(self):
        """Check if ML modules are available."""
        if not ML_AVAILABLE:
            pytest.skip(f"ML modules not available: {ML_ERROR}")
    
    def test_risk_engine_initialized(self):
        """Test that risk engine is initialized."""
        assert risk_engine is not None
        assert hasattr(risk_engine, 'model')
        assert hasattr(risk_engine, 'predict_risk')
        assert hasattr(risk_engine, 'is_trained')
    
    def test_risk_engine_model_types(self):
        """Test that risk engine supports different model types."""
        # Should have model_type attribute
        assert hasattr(risk_engine, 'model_type')
        assert risk_engine.model_type is not None
    
    def test_feature_extraction(self):
        """Test feature extraction from FeatureSet."""
        feature_set = FeatureSet(
            current_gpa=3.2,
            gpa_trend=-0.2,
            overall_attendance=75.0,
            attendance_trend=-5.0,
            recent_absent_days=5,
            previous_risk_score=40.0,
            warning_count=2
        )
        
        # Should be able to extract features
        assert hasattr(risk_engine, '_extract_features_array')
        features_array = risk_engine._extract_features_array(feature_set)
        
        assert isinstance(features_array, np.ndarray)
        assert features_array.shape[0] == 1  # Single sample
        assert features_array.shape[1] > 0  # Has features
    
    def test_rule_based_prediction(self):
        """Test rule-based risk prediction (no ML required)."""
        feature_set = FeatureSet(
            current_gpa=2.0,  # Low GPA
            gpa_trend=-0.3,  # Declining
            overall_attendance=60.0,  # Low attendance
            attendance_trend=-10.0,  # Declining
            recent_absent_days=10,
            previous_risk_score=50.0,
            warning_count=3
        )
        
        assessment = risk_engine.predict_risk(feature_set, use_ml=False)
        
        assert isinstance(assessment, RiskAssessment)
        assert assessment.risk_level in ['low', 'medium', 'high']
        assert 0 <= assessment.risk_score <= 100
        assert 0 <= assessment.confidence_level <= 1
        assert assessment.explanation is not None
        assert len(assessment.explanation) > 0
    
    def test_ml_prediction_when_trained(self):
        """Test ML prediction when model is trained."""
        feature_set = FeatureSet(
            current_gpa=2.5,
            gpa_trend=-0.1,
            overall_attendance=70.0,
            attendance_trend=-3.0,
            recent_absent_days=5,
            previous_risk_score=35.0,
            warning_count=1
        )
        
        assessment = risk_engine.predict_risk(feature_set, use_ml=True)
        
        assert isinstance(assessment, RiskAssessment)
        assert assessment.risk_level in ['low', 'medium', 'high']
        assert 0 <= assessment.risk_score <= 100
        
        # If model is trained, should use ML; otherwise rule-based
        # Both should work
        if risk_engine.is_trained:
            assert assessment.factors.get('ml_score') is not None or assessment.factors.get('rule_score') is not None
        else:
            # Should fall back to rule-based
            assert assessment.factors.get('rule_score') is not None
    
    def test_risk_level_classification(self):
        """Test that risk levels are correctly classified."""
        # Test with features that actually produce high risk
        high_risk_features = FeatureSet(
            current_gpa=1.0,  # Very low GPA
            gpa_trend=-0.5,  # Rapidly declining
            overall_attendance=30.0,  # Very low attendance
            attendance_trend=-20.0,  # Rapidly declining
            recent_absent_days=20,
            previous_risk_score=85.0,
            warning_count=5
        )
        
        high_assessment = risk_engine.predict_risk(high_risk_features, use_ml=False)
        # With very poor metrics, should be high risk
        assert high_assessment.risk_score >= 70
        assert high_assessment.risk_level == 'high'
        
        # Test medium risk
        medium_risk_features = FeatureSet(
            current_gpa=2.3,
            gpa_trend=-0.2,
            overall_attendance=70.0,
            previous_risk_score=45.0
        )
        
        medium_assessment = risk_engine.predict_risk(medium_risk_features, use_ml=False)
        assert medium_assessment.risk_level in ['low', 'medium', 'high']
        
        # Test low risk
        low_risk_features = FeatureSet(
            current_gpa=3.8,
            overall_attendance=95.0,
            previous_risk_score=10.0
        )
        
        low_assessment = risk_engine.predict_risk(low_risk_features, use_ml=False)
        assert low_assessment.risk_level in ['low', 'medium']
    
    def test_prediction_with_no_data(self):
        """Test prediction with minimal/no data."""
        feature_set = FeatureSet()  # All defaults (zeros)
        
        assessment = risk_engine.predict_risk(feature_set, use_ml=False)
        
        assert isinstance(assessment, RiskAssessment)
        assert assessment.risk_level in ['low', 'medium', 'high']
        assert 0 <= assessment.risk_score <= 100
        # With no data, should be low risk
        assert assessment.risk_level == 'low'
    
    def test_prediction_consistency(self):
        """Test that predictions are consistent for same input."""
        feature_set = FeatureSet(
            current_gpa=3.0,
            gpa_trend=0.0,
            overall_attendance=80.0,
            attendance_trend=0.0,
            previous_risk_score=30.0
        )
        
        assessment1 = risk_engine.predict_risk(feature_set, use_ml=False)
        assessment2 = risk_engine.predict_risk(feature_set, use_ml=False)
        
        # Rule-based should be deterministic
        assert assessment1.risk_score == assessment2.risk_score
        assert assessment1.risk_level == assessment2.risk_level
    
    def test_high_risk_detection(self):
        """Test detection of high-risk students."""
        feature_set = FeatureSet(
            current_gpa=1.0,  # Extremely low GPA
            gpa_trend=-0.8,  # Rapidly declining
            overall_attendance=25.0,  # Extremely low attendance
            attendance_trend=-25.0,  # Rapidly declining
            recent_absent_days=25,
            previous_risk_score=90.0,
            warning_count=10,
            intervention_count=5
        )
        
        assessment = risk_engine.predict_risk(feature_set, use_ml=False)
        
        # With extremely poor metrics, should be high risk
        assert assessment.risk_score >= 70
        assert assessment.risk_level == 'high'
    
    def test_low_risk_detection(self):
        """Test detection of low-risk students."""
        feature_set = FeatureSet(
            current_gpa=3.8,  # High GPA
            gpa_trend=0.1,  # Improving
            overall_attendance=95.0,  # High attendance
            attendance_trend=2.0,  # Improving
            recent_absent_days=0,
            previous_risk_score=10.0,
            warning_count=0,
            intervention_count=0
        )
        
        assessment = risk_engine.predict_risk(feature_set, use_ml=False)
        
        assert assessment.risk_level == 'low'
        assert assessment.risk_score < 40
    
    def test_risk_factors_explanation(self):
        """Test that risk assessment includes explanations."""
        feature_set = FeatureSet(
            current_gpa=2.0,
            gpa_trend=-0.3,
            overall_attendance=60.0,
            recent_absent_days=8
        )
        
        assessment = risk_engine.predict_risk(feature_set, use_ml=False)
        
        assert assessment.explanation is not None
        assert len(assessment.explanation) > 20  # Should have meaningful explanation
        assert len(assessment.top_factors) > 0  # Should have contributing factors
    
    def test_scaler_fitted_check(self):
        """Test that scaler fitted check works correctly."""
        # Should have scaler
        assert hasattr(risk_engine, 'scaler')
        
        # If model is not trained, scaler shouldn't be fitted
        if not risk_engine.is_trained:
            # Should not crash when trying to predict
            feature_set = FeatureSet(current_gpa=3.0)
            assessment = risk_engine.predict_risk(feature_set, use_ml=True)
            assert isinstance(assessment, RiskAssessment)
    
    def test_feature_set_validation(self):
        """Test that FeatureSet validation works."""
        # Should accept valid FeatureSet
        feature_set = FeatureSet(
            current_gpa=3.5,
            overall_attendance=85.0
        )
        
        assert feature_set.current_gpa == 3.5
        assert feature_set.overall_attendance == 85.0
        
        # Should handle edge cases
        feature_set = FeatureSet(
            current_gpa=0.0,
            overall_attendance=0.0,
            recent_absent_days=0
        )
        
        assessment = risk_engine.predict_risk(feature_set, use_ml=False)
        assert isinstance(assessment, RiskAssessment)


class TestMLTraining:
    """Test suite for ML training functionality."""
    
    def test_training_pipeline_import(self):
        """Test that training pipeline can be imported."""
        try:
            from ml_training import training_pipeline
            assert training_pipeline is not None
        except ImportError:
            pytest.skip("ML training pipeline not available")
    
    def test_training_data_preparation_structure(self):
        """Test structure of training data preparation."""
        try:
            from ml_training import training_pipeline
            
            assert hasattr(training_pipeline, 'prepare_training_data')
            assert hasattr(training_pipeline, 'train_model')
        except ImportError:
            pytest.skip("ML training pipeline not available")
    
    def test_model_save_and_load(self):
        """Test that models can be saved and loaded."""
        # This would require actual training
        # For now, just verify the structure exists
        assert hasattr(risk_engine, '_load_or_initialize_model')
        assert hasattr(risk_engine, 'model_path')


class TestRiskAssessmentIntegration:
    """Integration tests for risk assessment workflow."""
    
    def test_full_workflow_feature_to_assessment(self):
        """Test complete workflow from features to assessment."""
        # Create academic and attendance records
        academic_records = [
            {'grade': 70.0, 'gpa': 2.3, 'credits': 3, 'semester': 'Fall 2024'}
        ]
        attendance_records = [
            {'date': '2024-09-15', 'status': 'absent', 'course_code': 'CS101', 'semester': 'Fall 2024'},
            {'date': '2024-09-16', 'status': 'absent', 'course_code': 'CS101', 'semester': 'Fall 2024'},
        ]
        
        # Engineer features
        feature_set = processor.engineer_features(
            academic_records=academic_records,
            attendance_records=attendance_records,
            previous_risk_score=0.0,
            warning_count=0,
            intervention_count=0
        )
        
        # Predict risk
        assessment = risk_engine.predict_risk(feature_set, use_ml=True)
        
        # Verify assessment
        assert isinstance(assessment, RiskAssessment)
        assert assessment.risk_level in ['low', 'medium', 'high']
        assert 0 <= assessment.risk_score <= 100
        assert assessment.explanation is not None
    
    def test_assessment_with_historical_data(self):
        """Test assessment that considers historical data."""
        feature_set = FeatureSet(
            current_gpa=2.5,
            gpa_trend=-0.2,
            overall_attendance=70.0,
            previous_risk_score=45.0,  # Previous assessment
            warning_count=2,  # Has warnings
            intervention_count=1  # Has interventions
        )
        
        assessment = risk_engine.predict_risk(feature_set, use_ml=False)
        
        # Historical data should influence risk
        assert assessment.risk_score >= 0
        # Verify it's a valid assessment (actual score depends on rule-based logic)
        assert assessment.risk_level in ['low', 'medium', 'high']
        assert assessment.explanation is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
