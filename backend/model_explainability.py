"""
Model explainability and interpretability module using SHAP values.
Provides human-readable explanations for risk predictions.
"""
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import pickle
import os
import logging

try:
    import shap
    SHAP_AVAILABLE = True
except Exception:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available. Model explainability will be limited.")

from risk_engine import risk_engine
from models import FeatureSet, RiskFactor
from config import settings

logger = logging.getLogger(__name__)


class ModelExplainer:
    """Provides explainability for ML model predictions."""
    
    def __init__(self):
        """Initialize the explainer."""
        self.explainer = None
        self.model = None
        self.scaler = None
        self.feature_names = None
        self._initialize_explainer()
    
    def _initialize_explainer(self):
        """Initialize SHAP explainer from trained model."""
        try:
            model_path = f"models/risk_model_{settings.model_version}.pkl"
            
            if not os.path.exists(model_path):
                logger.warning("No trained model found for explainability")
                return
            
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            
            # Get feature names
            from data_processing import processor
            dummy_features = processor.engineer_features([], [], 0.0, 0, 0, None, {})
            from ml_training import training_pipeline
            self.feature_names = training_pipeline._get_feature_names(dummy_features)
            
            # Initialize SHAP explainer
            if SHAP_AVAILABLE and self.model is not None:
                # Use TreeExplainer for tree-based models
                if hasattr(self.model, 'tree_'):
                    self.explainer = shap.TreeExplainer(self.model)
                elif hasattr(self.model, 'estimators_'):
                    # Random Forest
                    self.explainer = shap.TreeExplainer(self.model)
                else:
                    # For linear models, use LinearExplainer
                    self.explainer = shap.LinearExplainer(self.model, self.scaler.transform(np.zeros((1, len(self.feature_names)))))
                
                logger.info("SHAP explainer initialized")
            else:
                logger.warning("SHAP not available or model not loaded")
                
        except Exception as e:
            logger.error(f"Error initializing explainer: {e}")
    
    def explain_prediction(
        self,
        feature_set: FeatureSet,
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Explain a risk prediction using SHAP values.
        
        Args:
            feature_set: FeatureSet for the student
            top_n: Number of top contributing factors to return
        
        Returns:
            Dictionary with explanation details
        """
        try:
            if self.explainer is None or self.model is None:
                # Fallback to rule-based explanation
                return self._rule_based_explanation(feature_set, top_n)
            
            # Extract features
            from risk_engine import risk_engine
            features_array = risk_engine._extract_features_array(feature_set)
            features_scaled = self.scaler.transform(features_array)
            
            # Get SHAP values
            shap_values = self.explainer.shap_values(features_scaled)
            
            # Handle multi-class output
            if isinstance(shap_values, list):
                # Multi-class: use the class with highest probability
                probabilities = self.model.predict_proba(features_scaled)[0]
                predicted_class = np.argmax(probabilities)
                shap_values = shap_values[predicted_class]
            else:
                shap_values = shap_values[0]
            
            # Get feature importance
            feature_importance = dict(zip(self.feature_names, shap_values))
            sorted_importance = sorted(
                feature_importance.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            # Create explanation
            top_factors = []
            for feature_name, importance in sorted_importance[:top_n]:
                impact = self._get_feature_impact_description(feature_name, feature_set, importance)
                top_factors.append({
                    'feature': feature_name,
                    'importance': float(importance),
                    'impact': impact
                })
            
            # Generate summary
            summary = self._generate_summary(feature_set, top_factors)
            
            return {
                'explanation_type': 'shap',
                'top_factors': top_factors,
                'summary': summary,
                'feature_importance': {k: float(v) for k, v in feature_importance.items()}
            }
            
        except Exception as e:
            logger.error(f"Error explaining prediction: {e}")
            # Fallback to rule-based
            return self._rule_based_explanation(feature_set, top_n)
    
    def _rule_based_explanation(
        self,
        feature_set: FeatureSet,
        top_n: int = 5
    ) -> Dict[str, Any]:
        """Generate rule-based explanation as fallback."""
        factors = []
        
        # Academic factors
        if feature_set.current_gpa < 2.0:
            factors.append({
                'feature': 'current_gpa',
                'importance': 0.3,
                'impact': f"Critical GPA: {feature_set.current_gpa:.2f} is below threshold (2.0)"
            })
        
        if feature_set.gpa_trend < -0.3:
            factors.append({
                'feature': 'gpa_trend',
                'importance': 0.25,
                'impact': f"Rapid GPA decline: {feature_set.gpa_trend:.2f} per semester"
            })
        
        # Attendance factors
        if feature_set.overall_attendance < 60:
            factors.append({
                'feature': 'overall_attendance',
                'importance': 0.3,
                'impact': f"Low attendance: {feature_set.overall_attendance:.1f}%"
            })
        
        if feature_set.attendance_trend < -15:
            factors.append({
                'feature': 'attendance_trend',
                'importance': 0.2,
                'impact': f"Attendance declining: {feature_set.attendance_trend:.1f}%"
            })
        
        # Behavioral factors
        if feature_set.sudden_behavior_change:
            factors.append({
                'feature': 'sudden_behavior_change',
                'importance': 0.15,
                'impact': "Sudden behavioral change detected"
            })
        
        # Sort by importance
        factors.sort(key=lambda x: x['importance'], reverse=True)
        top_factors = factors[:top_n]
        
        summary = self._generate_summary(feature_set, top_factors)
        
        return {
            'explanation_type': 'rule_based',
            'top_factors': top_factors,
            'summary': summary
        }
    
    def _get_feature_impact_description(
        self,
        feature_name: str,
        feature_set: FeatureSet,
        importance: float
    ) -> str:
        """Generate human-readable impact description for a feature."""
        feature_value = getattr(feature_set, feature_name, None)
        
        if feature_name == 'current_gpa':
            if feature_value < 2.0:
                return f"Critical GPA of {feature_value:.2f} significantly increases risk"
            elif feature_value < 2.5:
                return f"GPA of {feature_value:.2f} is below warning threshold"
            else:
                return f"GPA of {feature_value:.2f} is within acceptable range"
        
        elif feature_name == 'overall_attendance':
            if feature_value < 60:
                return f"Very low attendance at {feature_value:.1f}% is a major risk factor"
            elif feature_value < 75:
                return f"Attendance of {feature_value:.1f}% is below recommended threshold"
            else:
                return f"Attendance of {feature_value:.1f}% is satisfactory"
        
        elif feature_name == 'gpa_trend':
            if feature_value < -0.3:
                return f"Rapid GPA decline of {feature_value:.2f} indicates deteriorating performance"
            elif feature_value < 0:
                return f"GPA declining at {feature_value:.2f} per semester"
            else:
                return f"GPA trend is stable or improving"
        
        elif feature_name == 'attendance_trend':
            if feature_value < -15:
                return f"Attendance dropping rapidly by {abs(feature_value):.1f}%"
            elif feature_value < 0:
                return f"Attendance declining by {abs(feature_value):.1f}%"
            else:
                return f"Attendance trend is stable"
        
        elif feature_name == 'failed_courses_count':
            if feature_value > 2:
                return f"{int(feature_value)} failed courses is a significant concern"
            elif feature_value > 0:
                return f"{int(feature_value)} failed course(s) noted"
            else:
                return "No failed courses"
        
        elif feature_name == 'sudden_behavior_change':
            if feature_value:
                return "Sudden behavioral change detected - may indicate external issues"
            else:
                return "No sudden behavioral changes"
        
        elif feature_name == 'consecutive_absences':
            if feature_value > 3:
                return f"{int(feature_value)} consecutive absences is concerning"
            elif feature_value > 0:
                return f"{int(feature_value)} consecutive absence(s)"
            else:
                return "No consecutive absences"
        
        else:
            # Generic description
            direction = "increases" if importance > 0 else "decreases"
            return f"This factor {direction} the risk assessment"
    
    def _generate_summary(
        self,
        feature_set: FeatureSet,
        top_factors: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable summary explanation."""
        parts = []
        
        if top_factors:
            parts.append("Primary risk factors:")
            for i, factor in enumerate(top_factors[:3], 1):
                parts.append(f"{i}. {factor['impact']}")
        else:
            parts.append("No significant risk factors identified.")
        
        # Add context
        if feature_set.current_gpa < 2.0:
            parts.append(f"\nAcademic performance is critically low (GPA: {feature_set.current_gpa:.2f}).")
        
        if feature_set.overall_attendance < 60:
            parts.append(f"\nAttendance is critically low ({feature_set.overall_attendance:.1f}%).")
        
        if feature_set.sudden_behavior_change:
            parts.append("\nSudden behavioral changes detected - may require immediate attention.")
        
        return "\n".join(parts)
    
    def get_global_feature_importance(self) -> Dict[str, float]:
        """Get global feature importance across all predictions."""
        try:
            if self.model is None:
                return {}
            
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
            elif hasattr(self.model, 'coef_'):
                importances = np.abs(self.model.coef_[0])
            else:
                return {}
            
            importance_dict = dict(zip(self.feature_names, importances))
            return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            
        except Exception as e:
            logger.error(f"Error getting global feature importance: {e}")
            return {}


# Global explainer instance
model_explainer = ModelExplainer()
