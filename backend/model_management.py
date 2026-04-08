"""
Model management, retraining strategy, and data drift detection.
Handles periodic retraining, performance monitoring, and model versioning.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pickle
import os
import json
import logging

from database import db
from ml_training import training_pipeline
from risk_engine import risk_engine
from config import settings

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model lifecycle, retraining, and versioning."""
    
    def __init__(self):
        """Initialize the model manager."""
        self.models_dir = "models"
        self.retraining_interval_days = 30  # Retrain every 30 days
        self.performance_threshold = 0.7  # Minimum F1 score
        self.drift_threshold = 0.15  # Feature distribution change threshold
        
    def should_retrain(self) -> Dict[str, Any]:
        """
        Determine if model should be retrained.
        
        Returns:
            Dictionary with retraining recommendation
        """
        try:
            model_path = f"{self.models_dir}/risk_model_{settings.model_version}.pkl"
            
            if not os.path.exists(model_path):
                return {
                    'should_retrain': True,
                    'reason': 'No trained model found',
                    'priority': 'high'
                }
            
            # Load model metadata
            metadata_path = f"{self.models_dir}/model_metadata_{settings.model_version}.json"
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                trained_at = datetime.fromisoformat(metadata.get('trained_at', datetime.utcnow().isoformat()))
                days_since_training = (datetime.utcnow() - trained_at).days
                
                # Check if retraining interval has passed
                if days_since_training >= self.retraining_interval_days:
                    return {
                        'should_retrain': True,
                        'reason': f'Retraining interval reached ({days_since_training} days)',
                        'priority': 'medium',
                        'days_since_training': days_since_training
                    }
                
                # Check model performance
                metrics = metadata.get('metrics', {})
                f1_score = metrics.get('f1_score', 0.0)
                
                if f1_score < self.performance_threshold:
                    return {
                        'should_retrain': True,
                        'reason': f'Model performance below threshold (F1: {f1_score:.3f})',
                        'priority': 'high',
                        'current_f1': f1_score
                    }
            
            # Check for data drift
            drift_detected = self.detect_data_drift()
            if drift_detected.get('drift_detected', False):
                return {
                    'should_retrain': True,
                    'reason': 'Data drift detected',
                    'priority': 'high',
                    'drift_details': drift_detected
                }
            
            return {
                'should_retrain': False,
                'reason': 'Model is up to date',
                'priority': 'low'
            }
            
        except Exception as e:
            logger.error(f"Error checking retraining status: {e}")
            return {
                'should_retrain': True,
                'reason': f'Error checking status: {str(e)}',
                'priority': 'medium'
            }
    
    def detect_data_drift(self) -> Dict[str, Any]:
        """
        Detect data drift by comparing current data distribution with training data.
        
        Returns:
            Dictionary with drift detection results
        """
        try:
            # Get current student data
            students = db.get_students(filters={'status': 'active'})
            
            if len(students) < 10:
                return {
                    'drift_detected': False,
                    'reason': 'Insufficient data for drift detection'
                }
            
            # Extract features for current data
            current_features = []
            for student in students[:100]:  # Sample up to 100 students
                student_id = student['id']
                academic_records = db.get_academic_records(student_id=student_id)
                attendance_records = db.get_attendance_records(student_id=student_id)
                
                previous_assessments = db.get_risk_assessments(student_id=student_id, limit=1)
                previous_risk_score = previous_assessments[0]['risk_score'] if previous_assessments else 0.0
                
                all_alerts = db.get_alerts(student_id=student_id)
                warning_count = len([a for a in all_alerts if a.get('severity') in ['high', 'critical']])
                interventions = db.get_interventions(student_id=student_id)
                intervention_count = len(interventions)
                
                from data_processing import processor
                feature_set = processor.engineer_features(
                    academic_records=academic_records,
                    attendance_records=attendance_records,
                    previous_risk_score=previous_risk_score,
                    warning_count=warning_count,
                    intervention_count=intervention_count,
                    enrollment_date=student.get('enrollment_date'),
                    student_data=student
                )
                
                # Extract key features
                from risk_engine import risk_engine
                features_array = risk_engine._extract_features_array(feature_set)
                current_features.append(features_array.flatten())
            
            if len(current_features) == 0:
                return {
                    'drift_detected': False,
                    'reason': 'No features extracted'
                }
            
            current_features = np.array(current_features)
            
            # Get training data statistics (if available)
            training_stats_path = f"{self.models_dir}/training_stats_{settings.model_version}.json"
            if os.path.exists(training_stats_path):
                with open(training_stats_path, 'r') as f:
                    training_stats = json.load(f)
                
                # Compare distributions
                drift_scores = {}
                for i, feature_name in enumerate(training_stats.get('feature_names', [])):
                    if i < current_features.shape[1]:
                        training_mean = training_stats.get('feature_means', [])[i] if i < len(training_stats.get('feature_means', [])) else 0
                        training_std = training_stats.get('feature_stds', [])[i] if i < len(training_stats.get('feature_stds', [])) else 1
                        
                        current_mean = np.mean(current_features[:, i])
                        current_std = np.std(current_features[:, i])
                        
                        # Calculate drift score (normalized difference)
                        if training_std > 0:
                            drift_score = abs(current_mean - training_mean) / training_std
                            drift_scores[feature_name] = drift_score
                
                # Check if any feature has significant drift
                max_drift = max(drift_scores.values()) if drift_scores else 0
                drift_detected = max_drift > self.drift_threshold
                
                return {
                    'drift_detected': drift_detected,
                    'max_drift_score': float(max_drift),
                    'drift_scores': {k: float(v) for k, v in list(drift_scores.items())[:10]},
                    'threshold': self.drift_threshold
                }
            else:
                # No training stats available, can't detect drift
                return {
                    'drift_detected': False,
                    'reason': 'No training statistics available for comparison'
                }
                
        except Exception as e:
            logger.error(f"Error detecting data drift: {e}")
            return {
                'drift_detected': False,
                'reason': f'Error: {str(e)}'
            }
    
    def retrain_model(
        self,
        model_type: Optional[str] = None,
        use_mock_labels: bool = False,
        save_training_stats: bool = True
    ) -> Dict[str, Any]:
        """
        Retrain the model with current data.
        
        Args:
            model_type: Type of model to train (defaults to config)
            use_mock_labels: Use mock labels if real labels unavailable
            save_training_stats: Save training statistics for drift detection
        
        Returns:
            Dictionary with retraining results
        """
        try:
            logger.info("Starting model retraining...")
            
            # Determine model type
            if model_type is None:
                model_type = settings.model_type
            
            # Prepare training data
            X, y, feature_names = training_pipeline.prepare_training_data(use_mock_labels=use_mock_labels)
            
            if len(X) < 10:
                raise ValueError("Insufficient training data")
            
            # Save training statistics for drift detection
            if save_training_stats:
                training_stats = {
                    'feature_names': feature_names,
                    'feature_means': [float(np.mean(X[:, i])) for i in range(X.shape[1])],
                    'feature_stds': [float(np.std(X[:, i])) for i in range(X.shape[1])],
                    'n_samples': len(X),
                    'created_at': datetime.utcnow().isoformat()
                }
                
                stats_path = f"{self.models_dir}/training_stats_{settings.model_version}.json"
                with open(stats_path, 'w') as f:
                    json.dump(training_stats, f, indent=2)
            
            # Train model
            training_result = training_pipeline.train_model(
                X, y, model_type=model_type, test_size=0.2
            )
            
            # Save model with new version
            new_version = self._increment_version()
            model_path = training_pipeline.save_model(training_result, version=new_version)
            
            # Update risk engine
            risk_engine._load_or_initialize_model()
            
            return {
                'success': True,
                'model_path': model_path,
                'version': new_version,
                'metrics': training_result['metrics'],
                'n_samples': training_result['n_samples'],
                'trained_at': training_result['trained_at']
            }
            
        except Exception as e:
            logger.error(f"Error retraining model: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _increment_version(self) -> str:
        """Increment model version."""
        try:
            # Get current version
            current_version = settings.model_version
            parts = current_version.split('.')
            
            # Increment patch version
            if len(parts) >= 3:
                major, minor, patch = parts[0], parts[1], int(parts[2])
                new_version = f"{major}.{minor}.{patch + 1}"
            elif len(parts) == 2:
                major, minor = parts[0], int(parts[1])
                new_version = f"{major}.{minor + 1}.0"
            else:
                new_version = f"{current_version}.1"
            
            return new_version
        except:
            return f"{settings.model_version}.1"
    
    def get_model_versions(self) -> List[Dict[str, Any]]:
        """Get list of all model versions."""
        versions = []
        
        try:
            if not os.path.exists(self.models_dir):
                return versions
            
            for filename in os.listdir(self.models_dir):
                if filename.startswith("model_metadata_") and filename.endswith(".json"):
                    version = filename.replace("model_metadata_", "").replace(".json", "")
                    metadata_path = os.path.join(self.models_dir, filename)
                    
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    versions.append({
                        'version': version,
                        'model_type': metadata.get('model_type', 'unknown'),
                        'trained_at': metadata.get('trained_at', 'unknown'),
                        'metrics': metadata.get('metrics', {}),
                        'n_samples': metadata.get('n_samples', 0),
                        'is_current': version == settings.model_version
                    })
            
            # Sort by version (newest first)
            versions.sort(key=lambda x: x['trained_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting model versions: {e}")
        
        return versions
    
    def monitor_model_performance(self) -> Dict[str, Any]:
        """
        Monitor model performance over time.
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            # Get recent predictions and actual outcomes
            # This would require tracking predictions vs actual outcomes
            # For now, return basic metrics
            
            model_path = f"{self.models_dir}/risk_model_{settings.model_version}.pkl"
            if not os.path.exists(model_path):
                return {
                    'status': 'no_model',
                    'message': 'No trained model found'
                }
            
            # Load model metadata
            metadata_path = f"{self.models_dir}/model_metadata_{settings.model_version}.json"
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                metrics = metadata.get('metrics', {})
                trained_at = metadata.get('trained_at', 'unknown')
                
                return {
                    'status': 'monitoring',
                    'model_version': settings.model_version,
                    'trained_at': trained_at,
                    'metrics': metrics,
                    'performance_status': 'good' if metrics.get('f1_score', 0) >= self.performance_threshold else 'needs_attention'
                }
            else:
                return {
                    'status': 'no_metadata',
                    'message': 'No model metadata found'
                }
                
        except Exception as e:
            logger.error(f"Error monitoring model performance: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }


# Global model manager instance
model_manager = ModelManager()
