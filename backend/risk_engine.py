"""
Risk scoring engine with ML models for predicting student at-risk status.
"""
from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from models import FeatureSet, RiskAssessment, RiskFactor, RiskLevel
from config import settings
import logging
import pickle
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Import advanced models
try:
    from advanced_ml_models import advanced_ml
    from advanced_ml_models import TENSORFLOW_AVAILABLE
    ADVANCED_ML_AVAILABLE = True
except Exception:
    ADVANCED_ML_AVAILABLE = False
    TENSORFLOW_AVAILABLE = False
    logger.warning("Advanced ML models not available")

try:
    from time_series_forecasting import time_series_forecaster
    TIME_SERIES_AVAILABLE = True
except Exception:
    TIME_SERIES_AVAILABLE = False


class RiskScoringEngine:
    """Risk scoring engine with ML models."""
    
    def __init__(self):
        """Initialize the risk scoring engine."""
        self.model_type = settings.model_type
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = f"models/risk_model_{settings.model_version}.pkl"
        self._load_or_initialize_model()
    
    def _load_or_initialize_model(self):
        """Load existing model or initialize a new one."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    
                    # Handle Keras neural network models (load from .h5 file).
                    # If the saved model is a pickle-safe sklearn NN fallback (e.g. 'neural_network_sklearn'),
                    # it will be loaded normally from model_data['model'].
                    if model_data.get('model_type') == 'neural_network' and model_data.get('model_path'):
                        model_path_h5 = model_data.get('model_path')
                        if model_path_h5 and os.path.exists(model_path_h5):
                            try:
                                if ADVANCED_ML_AVAILABLE and TENSORFLOW_AVAILABLE:
                                    from tensorflow.keras.models import load_model
                                    self.model = load_model(model_path_h5)
                                    logger.info(f"Loaded neural network from {model_path_h5}")
                                else:
                                    logger.warning("TensorFlow not available, cannot load Keras neural network")
                                    self._initialize_model()
                                    return
                            except Exception as e:
                                logger.error(f"Error loading neural network: {e}")
                                self._initialize_model()
                                return
                        else:
                            logger.warning("Neural network model file not found, initializing new")
                            self._initialize_model()
                            return
                    else:
                        self.model = model_data.get('model')
                    
                    self.scaler = model_data.get('scaler', StandardScaler())
                    self.is_trained = model_data.get('is_trained', False)
                    # Update model type if different
                    if 'model_type' in model_data:
                        self.model_type = model_data['model_type']
                    
                logger.info(f"Loaded existing model from {self.model_path} (type: {self.model_type})")
            else:
                self._initialize_model()
                logger.info("Initialized new model")
        except Exception as e:
            logger.warning(f"Could not load model, initializing new: {e}")
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize a new ML model."""
        if self.model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
        elif self.model_type == "logistic_regression":
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                class_weight='balanced'
            )
        elif self.model_type == "gradient_boosting":
            from sklearn.ensemble import GradientBoostingClassifier
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == "xgboost":
            try:
                self.model = advanced_ml.create_xgboost_model()
            except ImportError:
                logger.warning("XGBoost not available, falling back to Random Forest")
                self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
        elif self.model_type == "lightgbm":
            try:
                self.model = advanced_ml.create_lightgbm_model()
            except ImportError:
                logger.warning("LightGBM not available, falling back to Random Forest")
                self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
        elif self.model_type == "catboost":
            try:
                self.model = advanced_ml.create_catboost_model()
            except ImportError:
                logger.warning("CatBoost not available, falling back to Random Forest")
                self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
        elif self.model_type == "neural_network":
            # Neural network will be initialized with input_dim during training
            self.model = None
            self.neural_network_dim = None
        elif self.model_type == "ensemble":
            # Ensemble will be created during training
            self.model = None
        elif self.model_type == "hybrid":
            # Hybrid uses rule-based + simple ML
            self.model = RandomForestClassifier(
                n_estimators=50,
                max_depth=8,
                random_state=42,
                class_weight='balanced'
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        self.is_trained = False
    
    def _extract_features_array(self, feature_set: FeatureSet) -> np.ndarray:
        """Convert FeatureSet to numpy array for ML model."""
        features = [
            feature_set.current_gpa,
            feature_set.gpa_trend,
            feature_set.gpa_variance,
            feature_set.overall_attendance / 100.0,  # Normalize to 0-1
            feature_set.attendance_trend / 100.0,
            feature_set.recent_absent_days / 30.0,  # Normalize
            feature_set.late_count / 30.0,
            feature_set.failed_courses_count,
            feature_set.assignment_submissions_on_time / 100.0,
            1.0 if feature_set.sudden_behavior_change else 0.0,
            feature_set.participation_score / 100.0,
            feature_set.previous_risk_score / 100.0,
            feature_set.warning_count,
            feature_set.intervention_count,
            feature_set.years_enrolled / 4.0,  # Normalize to 4 years
            1.0 if feature_set.is_first_generation else 0.0,
            # Add average of recent grades
            np.mean(feature_set.recent_grades) / 100.0 if feature_set.recent_grades else 0.0,
            # Add number of credits
            min(feature_set.credits_completed / 120.0, 1.0),  # Normalize to typical degree
            # Advanced features
            getattr(feature_set, 'gpa_momentum', 0.0),
            getattr(feature_set, 'gpa_acceleration', 0.0),
            getattr(feature_set, 'gpa_rolling_avg_3', 0.0) / 4.0,
            getattr(feature_set, 'gpa_rolling_avg_6', 0.0) / 4.0,
            getattr(feature_set, 'low_grade_count', 0),
            getattr(feature_set, 'subject_variance', 0.0),
            getattr(feature_set, 'attendance_volatility', 0.0) / 100.0,
            getattr(feature_set, 'attendance_momentum', 0.0) / 100.0,
            getattr(feature_set, 'consecutive_absences', 0) / 10.0,
            getattr(feature_set, 'attendance_rolling_avg_7', 0.0) / 100.0,
            getattr(feature_set, 'attendance_rolling_avg_14', 0.0) / 100.0,
            1.0 if getattr(feature_set, 'sudden_drop_detected', False) else 0.0,
        ]
        
        return np.array(features).reshape(1, -1)
    
    def _rule_based_score(self, feature_set: FeatureSet) -> Tuple[float, List[RiskFactor]]:
        """Calculate rule-based risk score as baseline."""
        factors = []
        score = 0.0
        max_score = 100.0
        
        # Academic factors (40% weight) - only penalize if there's actual GPA data
        # Zero GPA with no data should not be penalized (treated as missing data)
        if feature_set.current_gpa > 0:
            if feature_set.current_gpa < settings.gpa_threshold_critical:
                weight = 0.20
                value = (settings.gpa_threshold_critical - feature_set.current_gpa) * 25
                score += min(value, 25)  # Increased max from 15 to 25
                factors.append(RiskFactor(
                    name="Critical GPA Below Threshold",
                    weight=weight,
                    value=feature_set.current_gpa,
                    impact=f"GPA {feature_set.current_gpa:.2f} is below critical threshold of {settings.gpa_threshold_critical}"
                ))
            elif feature_set.current_gpa < settings.gpa_threshold_warning:
                weight = 0.10
                value = (settings.gpa_threshold_warning - feature_set.current_gpa) * 10
                score += min(value, 10)
                factors.append(RiskFactor(
                    name="GPA Below Warning Threshold",
                    weight=weight,
                    value=feature_set.current_gpa,
                    impact=f"GPA {feature_set.current_gpa:.2f} is below warning threshold"
                ))
        
        if feature_set.gpa_trend < -0.3:
            weight = 0.15
            # More severe decline = more points
            decline_severity = abs(feature_set.gpa_trend)
            score += min(10 + (decline_severity - 0.3) * 5, 15)  # Up to 15 for severe decline
            factors.append(RiskFactor(
                name="Rapid GPA Decline",
                weight=weight,
                value=feature_set.gpa_trend,
                impact=f"GPA declining rapidly at {feature_set.gpa_trend:.2f} per semester"
            ))
        
        # Attendance factors (35% weight) - only penalize if there's actual attendance data
        # Zero attendance with no data should not be penalized (treated as missing data)
        if feature_set.overall_attendance > 0:
            if feature_set.overall_attendance < settings.attendance_threshold_critical:
                weight = 0.20
                value = (settings.attendance_threshold_critical - feature_set.overall_attendance) * 1.5
                score += min(value, 25)  # Increased max from 15 to 25
                factors.append(RiskFactor(
                    name="Critical Attendance Below Threshold",
                    weight=weight,
                    value=feature_set.overall_attendance,
                    impact=f"Attendance {feature_set.overall_attendance:.1f}% is critically low"
                ))
            elif feature_set.overall_attendance < settings.attendance_threshold_warning:
                weight = 0.10
                value = (settings.attendance_threshold_warning - feature_set.overall_attendance) * 1
                score += min(value, 10)
                factors.append(RiskFactor(
                    name="Attendance Below Warning Threshold",
                    weight=weight,
                    value=feature_set.overall_attendance,
                    impact=f"Attendance {feature_set.overall_attendance:.1f}% is below threshold"
                ))
        
        if feature_set.attendance_trend < -10:
            weight = 0.15
            # More severe decline = more points
            decline_severity = abs(feature_set.attendance_trend)
            score += min(10 + (decline_severity - 10) * 0.5, 15)  # Up to 15 for severe decline
            factors.append(RiskFactor(
                name="Rapid Attendance Decline",
                weight=weight,
                value=feature_set.attendance_trend,
                impact=f"Attendance declining by {abs(feature_set.attendance_trend):.1f}% recently"
            ))
        
        # Behavioral factors (15% weight)
        if feature_set.sudden_behavior_change:
            weight = 0.10
            score += 10
            factors.append(RiskFactor(
                name="Sudden Behavioral Change",
                weight=weight,
                value=1.0,
                impact="Detected sudden decline in academic performance or attendance"
            ))
        
        # Only penalize if there's actual data but it's low (not zero/no data)
        if 0 < feature_set.assignment_submissions_on_time < 70:
            weight = 0.05
            score += 5
            factors.append(RiskFactor(
                name="Late Assignment Submissions",
                weight=weight,
                value=feature_set.assignment_submissions_on_time,
                impact=f"Only {feature_set.assignment_submissions_on_time:.1f}% assignments submitted on time"
            ))
        
        # Historical factors (15% weight - increased)
        if feature_set.previous_risk_score > 50:
            weight = 0.10
            score += min(feature_set.previous_risk_score * 0.3, 10)  # Increased from 5 to 10
            factors.append(RiskFactor(
                name="Previous High Risk Score",
                weight=weight,
                value=feature_set.previous_risk_score,
                impact=f"Previous risk score was {feature_set.previous_risk_score:.1f}"
            ))
        
        if feature_set.warning_count > 2:
            weight = 0.08
            score += min(feature_set.warning_count * 2, 8)  # Increased from 5 to 8
            factors.append(RiskFactor(
                name="Multiple Previous Warnings",
                weight=weight,
                value=feature_set.warning_count,
                impact=f"Student has {feature_set.warning_count} previous warnings"
            ))
        
        # Additional factor for recent absences
        if feature_set.recent_absent_days > 10:
            weight = 0.07
            score += min((feature_set.recent_absent_days - 10) * 0.5, 7)
            factors.append(RiskFactor(
                name="High Recent Absences",
                weight=weight,
                value=feature_set.recent_absent_days,
                impact=f"Student has {feature_set.recent_absent_days} recent absent days"
            ))
        
        # Normalize score to 0-100
        score = min(score, max_score)
        
        return score, factors
    
    def train_model(self, X: np.ndarray, y: np.ndarray):
        """Train the ML model with data."""
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            # Save model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'is_trained': True,
                    'model_type': self.model_type,
                    'trained_at': datetime.utcnow().isoformat()
                }, f)
            
            logger.info(f"Model trained and saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def predict_risk(
        self,
        feature_set: FeatureSet,
        use_ml: bool = True
    ) -> RiskAssessment:
        """Predict risk score for a student."""
        try:
            # Always calculate rule-based score for explainability
            rule_score, rule_factors = self._rule_based_score(feature_set)
            
            # Calculate ML score if model is trained and use_ml is True
            ml_score = None
            ml_probability = None
            
            if use_ml and self.is_trained and self.model is not None:
                try:
                    # CRITICAL FIX: Check if scaler is fitted before using transform
                    # StandardScaler from sklearn has mean_ attribute when fitted
                    if not hasattr(self.scaler, 'mean_') or self.scaler.mean_ is None:
                        logger.warning("Scaler is not fitted, cannot use ML model. Using rule-based scoring.")
                        raise ValueError("Scaler not fitted")
                    
                    features_array = self._extract_features_array(feature_set)
                    
                    # CRITICAL FIX: Verify feature dimensions match scaler expectations
                    if features_array.shape[1] != len(self.scaler.mean_):
                        logger.warning(f"Feature dimension mismatch: got {features_array.shape[1]}, expected {len(self.scaler.mean_)}. Using rule-based scoring.")
                        raise ValueError(f"Feature dimension mismatch: {features_array.shape[1]} vs {len(self.scaler.mean_)}")
                    
                    features_scaled = self.scaler.transform(features_array)
                    
                    # Handle different model types
                    if self.model_type == "neural_network":
                        # Neural network prediction
                        probabilities = self.model.predict(features_scaled, verbose=0)[0]
                        if len(probabilities) == 1:  # Binary
                            ml_score = probabilities[0] * 100
                            ml_probability = float(probabilities[0])
                        else:  # Multi-class
                            ml_score = (probabilities[1] * 60 + probabilities[2] * 100) if len(probabilities) > 2 else probabilities[1] * 100
                            ml_probability = float(probabilities[2]) if len(probabilities) > 2 else float(probabilities[1])
                    else:
                        # Standard sklearn-style models (XGBoost, LightGBM, Random Forest, etc.)
                        probabilities = self.model.predict_proba(features_scaled)[0]
                        
                        # Map probabilities to risk score (weighted)
                        if len(probabilities) == 2:  # Binary classification
                            ml_score = probabilities[1] * 100  # High risk probability
                            ml_probability = probabilities[1]
                        else:  # Multi-class
                            ml_score = (probabilities[1] * 60 + probabilities[2] * 100)  # Weighted
                            ml_probability = probabilities[2] if len(probabilities) > 2 else probabilities[1]
                except Exception as e:
                    logger.warning(f"ML prediction failed, using rule-based fallback: {e}", exc_info=True)
            
            # Hybrid approach: combine rule-based and ML
            if self.model_type == "hybrid" and ml_score is not None:
                # Weighted average: 60% rule-based, 40% ML
                final_score = (rule_score * 0.6) + (ml_score * 0.4)
            elif ml_score is not None:
                # Pure ML
                final_score = ml_score
            else:
                # Rule-based fallback
                final_score = rule_score
            
            # Ensure score is in valid range
            final_score = max(0, min(100, final_score))
            
            # Determine risk level
            if final_score < settings.risk_threshold_low:
                risk_level = "low"
            elif final_score < settings.risk_threshold_high:
                risk_level = "medium"
            else:
                risk_level = "high"
            
            # Calculate confidence
            confidence = 0.7  # Default
            if ml_probability is not None:
                confidence = float(ml_probability)
            elif rule_factors:
                # Confidence based on number of strong factors
                strong_factors = [f for f in rule_factors if f.weight >= 0.10]
                confidence = min(0.95, 0.5 + len(strong_factors) * 0.1)
            
            # Sort factors by weight (descending)
            rule_factors.sort(key=lambda x: x.weight, reverse=True)
            top_factors = rule_factors[:5]  # Top 5 factors
            
            # Generate explanation
            explanation = self._generate_explanation(
                final_score, risk_level, top_factors, ml_score is not None
            )
            
            # Build assessment
            assessment = RiskAssessment(
                student_id="",  # Will be set by caller
                risk_level=risk_level,
                risk_score=final_score,
                confidence_level=confidence,
                factors={
                    'rule_score': rule_score,
                    'ml_score': ml_score,
                    'feature_set': feature_set.dict()
                },
                explanation=explanation,
                top_factors=top_factors,
                prediction_date=datetime.utcnow()
            )
            
            return assessment
        except Exception as e:
            logger.error(f"Error predicting risk: {e}")
            # Return a safe default
            return RiskAssessment(
                student_id="",
                risk_level="low",
                risk_score=0.0,
                confidence_level=0.5,
                explanation="Error in risk calculation",
                prediction_date=datetime.utcnow()
            )
    
    def _generate_explanation(
        self,
        score: float,
        level: RiskLevel,
        factors: List[RiskFactor],
        used_ml: bool
    ) -> str:
        """Generate human-readable explanation for risk assessment."""
        parts = []
        
        parts.append(f"Risk Level: {level.upper()} (Score: {score:.1f}/100)")
        
        if factors:
            parts.append("\nTop Contributing Factors:")
            for i, factor in enumerate(factors[:3], 1):
                parts.append(f"{i}. {factor.impact}")
        
        if used_ml:
            parts.append("\nAssessment Method: Machine Learning + Rule-Based Analysis")
        else:
            parts.append("\nAssessment Method: Rule-Based Analysis")
        
        return "\n".join(parts)


# Global risk engine instance
risk_engine = RiskScoringEngine()
