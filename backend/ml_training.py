"""
Comprehensive ML training pipeline for Early Warning System.
Includes model training, evaluation, cross-validation, and model management.
"""
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    accuracy_score, classification_report, confusion_matrix,
    precision_recall_curve, roc_curve
)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pickle
import os
import json
from datetime import datetime
import logging

from database import db
from data_processing import processor
from risk_engine import risk_engine
from config import settings

# Import advanced models
try:
    from advanced_ml_models import advanced_ml
    ADVANCED_ML_AVAILABLE = True
except Exception:
    ADVANCED_ML_AVAILABLE = False

logger = logging.getLogger(__name__)


class MLTrainingPipeline:
    """Comprehensive ML training pipeline with evaluation and model management."""
    
    def __init__(self):
        """Initialize the training pipeline."""
        self.models_dir = "models"
        os.makedirs(self.models_dir, exist_ok=True)
        self.scaler = StandardScaler()
        self.best_model = None
        self.best_model_metrics = {}
        self.model_version = settings.model_version
        
    def prepare_training_data(
        self,
        students: Optional[List[Dict[str, Any]]] = None,
        use_mock_labels: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare training data from student records.
        
        Args:
            students: List of student records. If None, fetches from database.
            use_mock_labels: If True, generates mock risk labels for training.
        
        Returns:
            X: Feature matrix
            y: Target labels (0=low, 1=medium, 2=high)
            feature_names: List of feature names
        """
        try:
            if students is None:
                students = db.get_students(filters={'status': 'active'})
            
            logger.info(f"Preparing training data for {len(students)} students...")
            
            X_list = []
            y_list = []
            feature_names = []
            
            for student in students:
                student_id = student['id']
                
                # Get student data
                academic_records = db.get_academic_records(student_id=student_id)
                attendance_records = db.get_attendance_records(student_id=student_id)
                
                # Get previous risk assessment for historical context
                previous_assessments = db.get_risk_assessments(student_id=student_id, limit=1)
                previous_risk_score = previous_assessments[0]['risk_score'] if previous_assessments else 0.0
                
                # Get warning and intervention counts
                all_alerts = db.get_alerts(student_id=student_id)
                warning_count = len([a for a in all_alerts if a.get('severity') in ['high', 'critical']])
                interventions = db.get_interventions(student_id=student_id)
                intervention_count = len(interventions)
                
                # Engineer features
                feature_set = processor.engineer_features(
                    academic_records=academic_records,
                    attendance_records=attendance_records,
                    previous_risk_score=previous_risk_score,
                    warning_count=warning_count,
                    intervention_count=intervention_count,
                    enrollment_date=student.get('enrollment_date'),
                    student_data=student
                )
                
                # Extract features as array
                features_array = self._extract_features_array(feature_set)
                
                # Get or generate label
                if use_mock_labels:
                    label = self._generate_mock_label(feature_set)
                else:
                    # Use actual risk assessment if available
                    latest_assessment = db.get_risk_assessments(student_id=student_id, limit=1)
                    if latest_assessment:
                        risk_level = latest_assessment[0].get('risk_level', 'low')
                        label = {'low': 0, 'medium': 1, 'high': 2}[risk_level]
                    else:
                        # Skip if no label available
                        continue
                
                X_list.append(features_array.flatten())
                y_list.append(label)
            
            # Store feature names (first time only)
            if not feature_names:
                # Create a dummy feature set to get names
                dummy_features = processor.engineer_features([], [], 0.0, 0, 0, None, {})
                feature_names = self._get_feature_names(dummy_features)
            
            X = np.array(X_list)
            y = np.array(y_list)
            
            logger.info(f"Prepared {len(X)} samples with {X.shape[1]} features")
            logger.info(f"Class distribution: {np.bincount(y)}")
            
            return X, y, feature_names
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            raise
    
    def _extract_features_array(self, feature_set) -> np.ndarray:
        """Extract features from FeatureSet to numpy array."""
        features = [
            feature_set.current_gpa,
            feature_set.gpa_trend,
            feature_set.gpa_variance,
            feature_set.overall_attendance / 100.0,
            feature_set.attendance_trend / 100.0,
            feature_set.recent_absent_days / 30.0,
            feature_set.late_count / 30.0,
            feature_set.failed_courses_count,
            feature_set.assignment_submissions_on_time / 100.0,
            1.0 if feature_set.sudden_behavior_change else 0.0,
            feature_set.participation_score / 100.0,
            feature_set.previous_risk_score / 100.0,
            feature_set.warning_count,
            feature_set.intervention_count,
            feature_set.years_enrolled / 4.0,
            1.0 if feature_set.is_first_generation else 0.0,
            np.mean(feature_set.recent_grades) / 100.0 if feature_set.recent_grades else 0.0,
            min(feature_set.credits_completed / 120.0, 1.0),
            # New advanced features
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
    
    def _get_feature_names(self, feature_set) -> List[str]:
        """Get feature names for interpretability."""
        return [
            'current_gpa', 'gpa_trend', 'gpa_variance',
            'overall_attendance', 'attendance_trend', 'recent_absent_days',
            'late_count', 'failed_courses_count', 'assignment_submissions_on_time',
            'sudden_behavior_change', 'participation_score', 'previous_risk_score',
            'warning_count', 'intervention_count', 'years_enrolled',
            'is_first_generation', 'avg_recent_grades', 'credits_completed',
            'gpa_momentum', 'gpa_acceleration', 'gpa_rolling_avg_3',
            'gpa_rolling_avg_6', 'low_grade_count', 'subject_variance',
            'attendance_volatility', 'attendance_momentum', 'consecutive_absences',
            'attendance_rolling_avg_7', 'attendance_rolling_avg_14', 'sudden_drop_detected'
        ]
    
    def _generate_mock_label(self, feature_set) -> int:
        """
        Generate mock risk label based on simple logic:
        - Negative results (bad grades, low attendance) = High risk (2)
        - Moderate results = Medium risk (1)
        - Positive/good results (good grades, high attendance) = Low risk (0)
        """
        negative_indicators = 0
        positive_indicators = 0
        
        # NEGATIVE INDICATORS (High Risk)
        # Academic: Low GPA, declining GPA, failed courses
        if feature_set.current_gpa < 2.0:  # Very low GPA
            negative_indicators += 3
        elif feature_set.current_gpa < 2.5:  # Low GPA
            negative_indicators += 2
        
        if feature_set.gpa_trend < -0.3:  # Declining GPA
            negative_indicators += 2
        
        if feature_set.failed_courses_count > 2:  # Multiple failures
            negative_indicators += 2
        elif feature_set.failed_courses_count > 0:
            negative_indicators += 1
        
        # Attendance: Low attendance, declining attendance
        if feature_set.overall_attendance < 60:  # Very low attendance
            negative_indicators += 3
        elif feature_set.overall_attendance < 75:  # Low attendance
            negative_indicators += 2
        
        if feature_set.attendance_trend < -15:  # Declining attendance
            negative_indicators += 2
        
        # Behavioral: Sudden changes, late submissions
        if feature_set.sudden_behavior_change:
            negative_indicators += 2
        
        if feature_set.assignment_submissions_on_time < 70:
            negative_indicators += 1
        
        # POSITIVE INDICATORS (Low Risk)
        # Academic: Good GPA, improving GPA, no failures
        if feature_set.current_gpa >= 3.0:  # Good GPA
            positive_indicators += 2
        elif feature_set.current_gpa >= 2.5:  # Decent GPA
            positive_indicators += 1
        
        if feature_set.gpa_trend > 0.2:  # Improving GPA
            positive_indicators += 1
        
        if feature_set.failed_courses_count == 0:  # No failures
            positive_indicators += 1
        
        # Attendance: Good attendance, improving attendance
        if feature_set.overall_attendance >= 85:  # Good attendance
            positive_indicators += 2
        elif feature_set.overall_attendance >= 75:  # Decent attendance
            positive_indicators += 1
        
        if feature_set.attendance_trend > 5:  # Improving attendance
            positive_indicators += 1
        
        if feature_set.assignment_submissions_on_time >= 90:
            positive_indicators += 1
        
        # Determine risk level based on simple logic
        # More negative indicators = higher risk
        # More positive indicators = lower risk
        net_risk = negative_indicators - positive_indicators
        
        if net_risk >= 4:  # Strongly negative
            return 2  # High risk
        elif net_risk >= 1:  # Moderately negative or neutral
            return 1  # Medium risk
        else:  # Positive or neutral-positive
            return 0  # Low risk
    
    def train_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_type: str = "random_forest",
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Train ML model with train/validation split and evaluation.
        
        Args:
            X: Feature matrix
            y: Target labels
            model_type: Type of model ('random_forest', 'logistic_regression', 'gradient_boosting')
            test_size: Proportion of data for testing
            random_state: Random seed
        
        Returns:
            Dictionary with training results and metrics
        """
        try:
            logger.info(f"Training {model_type} model on {len(X)} samples...")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Initialize model - support advanced models
            if model_type == "random_forest":
                model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=random_state,
                    class_weight='balanced',
                    n_jobs=-1
                )
            elif model_type == "logistic_regression":
                model = LogisticRegression(
                    max_iter=1000,
                    random_state=random_state,
                    class_weight='balanced',
                    solver='lbfgs'
                )
            elif model_type == "gradient_boosting":
                model = GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=random_state
                )
            elif model_type == "xgboost" and ADVANCED_ML_AVAILABLE:
                # Use advanced XGBoost
                try:
                    training_result = advanced_ml.train_xgboost(X, y, test_size=test_size, random_state=random_state)
                    # Add missing fields for compatibility
                    training_result['n_samples'] = len(X)
                    training_result['n_features'] = X.shape[1]
                    training_result['train_size'] = int(len(X) * (1 - test_size))
                    training_result['test_size'] = int(len(X) * test_size)
                    return training_result
                except Exception as e:
                    logger.error(f"XGBoost training failed: {e}")
                    raise ValueError(f"XGBoost training failed: {str(e)}")
            elif model_type == "lightgbm" and ADVANCED_ML_AVAILABLE:
                # Use advanced LightGBM
                try:
                    training_result = advanced_ml.train_lightgbm(X, y, test_size=test_size, random_state=random_state)
                    # Add missing fields for compatibility
                    training_result['n_samples'] = len(X)
                    training_result['n_features'] = X.shape[1]
                    training_result['train_size'] = int(len(X) * (1 - test_size))
                    training_result['test_size'] = int(len(X) * test_size)
                    return training_result
                except Exception as e:
                    logger.error(f"LightGBM training failed: {e}")
                    raise ValueError(f"LightGBM training failed: {str(e)}")
            elif model_type == "catboost" and ADVANCED_ML_AVAILABLE:
                # Use advanced CatBoost
                try:
                    training_result = advanced_ml.train_catboost(X, y, test_size=test_size, random_state=random_state)
                    # Add missing fields for compatibility
                    training_result['n_samples'] = len(X)
                    training_result['n_features'] = X.shape[1]
                    training_result['train_size'] = int(len(X) * (1 - test_size))
                    training_result['test_size'] = int(len(X) * test_size)
                    return training_result
                except Exception as e:
                    logger.error(f"CatBoost training failed: {e}")
                    raise ValueError(f"CatBoost training failed: {str(e)}")
            elif model_type == "neural_network" and ADVANCED_ML_AVAILABLE:
                # Use neural network
                try:
                    training_result = advanced_ml.train_neural_network(X, y, test_size=test_size, random_state=random_state)
                    # Add missing fields for compatibility
                    training_result['n_samples'] = len(X)
                    training_result['n_features'] = X.shape[1]
                    training_result['train_size'] = int(len(X) * (1 - test_size))
                    training_result['test_size'] = int(len(X) * test_size)
                    return training_result
                except Exception as e:
                    logger.error(f"Neural network training failed: {e}")
                    raise ValueError(f"Neural network training failed: {str(e)}")
            elif model_type == "ensemble" and ADVANCED_ML_AVAILABLE:
                # Use ensemble
                try:
                    training_result = advanced_ml.train_ensemble(X, y, test_size=test_size, random_state=random_state)
                    # Add missing fields for compatibility
                    training_result['n_samples'] = len(X)
                    training_result['n_features'] = X.shape[1]
                    training_result['train_size'] = int(len(X) * (1 - test_size))
                    training_result['test_size'] = int(len(X) * test_size)
                    return training_result
                except Exception as e:
                    logger.error(f"Ensemble training failed: {e}")
                    raise ValueError(f"Ensemble training failed: {str(e)}")
            else:
                if model_type in ["xgboost", "lightgbm", "catboost", "neural_network", "ensemble"]:
                    raise ValueError(f"Advanced model {model_type} requested but not available. Install required packages.")
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Train model
            model.fit(X_train_scaled, y_train)
            
            # Evaluate on test set
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)
            
            # Calculate metrics
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
                'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
                'f1_score': f1_score(y_test, y_pred, average='weighted', zero_division=0),
                'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
                'classification_report': classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            }
            
            # Calculate ROC-AUC (for binary classification, use one-vs-rest)
            try:
                if len(np.unique(y_test)) == 2:
                    metrics['roc_auc'] = roc_auc_score(y_test, y_pred_proba[:, 1])
                else:
                    metrics['roc_auc'] = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
            except:
                metrics['roc_auc'] = 0.0
            
            # Cross-validation
            cv_scores = cross_val_score(
                model, X_train_scaled, y_train,
                cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state),
                scoring='f1_weighted'
            )
            metrics['cv_f1_mean'] = float(cv_scores.mean())
            metrics['cv_f1_std'] = float(cv_scores.std())
            
            # Store best model
            self.best_model = model
            self.best_model_metrics = metrics
            
            logger.info(f"Model training completed. F1 Score: {metrics['f1_score']:.3f}")
            logger.info(f"Cross-validation F1: {metrics['cv_f1_mean']:.3f} (+/- {metrics['cv_f1_std']:.3f})")
            
            return {
                'model': model,
                'metrics': metrics,
                'scaler': self.scaler,
                'model_type': model_type,
                'trained_at': datetime.utcnow().isoformat(),
                'n_samples': len(X),
                'n_features': X.shape[1],
                'train_size': len(X_train),
                'test_size': len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def save_model(
        self,
        training_result: Dict[str, Any],
        version: Optional[str] = None
    ) -> str:
        """Save trained model to disk."""
        try:
            if version is None:
                version = self.model_version
            
            model_path = os.path.join(self.models_dir, f"risk_model_{version}.pkl")
            
            # Handle TensorFlow/Keras models separately
            model = training_result.get('model')
            model_type = training_result.get('model_type', 'unknown')
            
            if model_type == 'neural_network' and hasattr(model, 'save'):
                # Save Keras model separately
                keras_path = os.path.join(self.models_dir, f"neural_network_{version}.h5")
                try:
                    model.save(keras_path)
                    logger.info(f"Saved Keras model to {keras_path}")
                except Exception as e:
                    logger.warning(f"Could not save Keras model: {e}")
            
            model_data = {
                'model': model,
                'scaler': training_result.get('scaler', self.scaler),
                'metrics': training_result.get('metrics', {}),
                'model_type': model_type,
                'trained_at': training_result.get('trained_at', datetime.utcnow().isoformat()),
                'version': version,
                'n_samples': training_result.get('n_samples', 0),
                'n_features': training_result.get('n_features', 0),
                'is_trained': True
            }
            
            # For Keras neural networks, don't pickle the model (save path instead).
            # For sklearn fallbacks (e.g. 'neural_network_sklearn'), normal pickling is fine.
            if model_type == 'neural_network' and hasattr(model, 'save'):
                model_data['model_path'] = keras_path if 'keras_path' in locals() else None
                model_data['model'] = None  # Don't pickle Keras model
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            # Save metadata
            metadata_path = os.path.join(self.models_dir, f"model_metadata_{version}.json")
            with open(metadata_path, 'w') as f:
                json.dump({
                    'version': version,
                    'model_type': training_result['model_type'],
                    'trained_at': training_result['trained_at'],
                    'metrics': training_result['metrics'],
                    'n_samples': training_result['n_samples'],
                    'n_features': training_result['n_features']
                }, f, indent=2)
            
            logger.info(f"Model saved to {model_path}")
            return model_path
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise
    
    def evaluate_model_performance(
        self,
        model_path: Optional[str] = None,
        X_test: Optional[np.ndarray] = None,
        y_test: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Evaluate model performance on test data."""
        try:
            if model_path:
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                model = model_data['model']
                scaler = model_data['scaler']
            else:
                model = self.best_model
                scaler = self.scaler
            
            if model is None:
                raise ValueError("No model available for evaluation")
            
            if X_test is None or y_test is None:
                raise ValueError("Test data required for evaluation")
            
            X_test_scaled = scaler.transform(X_test)
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)
            
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
                'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
                'f1_score': f1_score(y_test, y_pred, average='weighted', zero_division=0),
                'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
                'classification_report': classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            raise
    
    def get_feature_importance(
        self,
        model_path: Optional[str] = None,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Get feature importance from trained model."""
        try:
            if model_path:
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                model = model_data['model']
            else:
                model = self.best_model
            
            if model is None:
                raise ValueError("No model available")
            
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            elif hasattr(model, 'coef_'):
                # For logistic regression, use absolute coefficients
                importances = np.abs(model.coef_[0])
            else:
                return {}
            
            if feature_names is None:
                feature_names = [f'feature_{i}' for i in range(len(importances))]
            
            # Create dictionary sorted by importance
            importance_dict = dict(zip(feature_names, importances))
            sorted_importance = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            
            return sorted_importance
            
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}


# Global training pipeline instance
training_pipeline = MLTrainingPipeline()
