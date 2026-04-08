"""
Early warning detection logic for identifying at-risk students.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from models import Alert, AlertType, AlertSeverity, FeatureSet, RiskAssessment
from config import settings
from database import db
import logging

logger = logging.getLogger(__name__)


class EarlyWarningDetector:
    """Detects early warning signals for students."""
    
    def __init__(self):
        """Initialize the early warning detector."""
        self.attendance_threshold_warning = settings.attendance_threshold_warning
        self.attendance_threshold_critical = settings.attendance_threshold_critical
        self.gpa_threshold_warning = settings.gpa_threshold_warning
        self.gpa_threshold_critical = settings.gpa_threshold_critical
    
    def detect_warnings(
        self,
        student_id: str,
        feature_set: FeatureSet,
        risk_assessment: RiskAssessment,
        previous_risk: Optional[RiskAssessment] = None
    ) -> List[Alert]:
        """Detect all early warning signals for a student."""
        warnings = []
        
        try:
            # 1. High risk detection
            if risk_assessment.risk_score >= settings.risk_threshold_high:
                if not db.check_recent_alert(student_id, "high_risk", settings.alert_cooldown_hours):
                    warnings.append(self._create_high_risk_alert(
                        student_id, risk_assessment
                    ))
            
            # 2. Attendance threshold breach
            if feature_set.overall_attendance < self.attendance_threshold_critical:
                if not db.check_recent_alert(student_id, "attendance_drop", settings.alert_cooldown_hours):
                    warnings.append(self._create_attendance_alert(
                        student_id, feature_set, "critical"
                    ))
            elif feature_set.overall_attendance < self.attendance_threshold_warning:
                if not db.check_recent_alert(student_id, "attendance_drop", settings.alert_cooldown_hours):
                    warnings.append(self._create_attendance_alert(
                        student_id, feature_set, "high"
                    ))
            
            # 3. Performance decline
            if feature_set.current_gpa < self.gpa_threshold_critical:
                if not db.check_recent_alert(student_id, "performance_decline", settings.alert_cooldown_hours):
                    warnings.append(self._create_performance_alert(
                        student_id, feature_set, "critical"
                    ))
            elif feature_set.current_gpa < self.gpa_threshold_warning:
                if not db.check_recent_alert(student_id, "performance_decline", settings.alert_cooldown_hours):
                    warnings.append(self._create_performance_alert(
                        student_id, feature_set, "high"
                    ))
            
            # 4. Rapid GPA decline
            if feature_set.gpa_trend < -0.3:
                if not db.check_recent_alert(student_id, "performance_decline", settings.alert_cooldown_hours):
                    warnings.append(self._create_gpa_decline_alert(
                        student_id, feature_set
                    ))
            
            # 5. Rapid attendance decline
            if feature_set.attendance_trend < -15:
                if not db.check_recent_alert(student_id, "attendance_drop", settings.alert_cooldown_hours):
                    warnings.append(self._create_attendance_decline_alert(
                        student_id, feature_set
                    ))
            
            # 5b. Sudden attendance drop (new feature)
            if getattr(feature_set, 'sudden_drop_detected', False):
                if not db.check_recent_alert(student_id, "attendance_drop", settings.alert_cooldown_hours):
                    warnings.append(self._create_sudden_drop_alert(
                        student_id, feature_set
                    ))
            
            # 5c. Consecutive absences
            consecutive_absences = getattr(feature_set, 'consecutive_absences', 0)
            if consecutive_absences >= 3:
                if not db.check_recent_alert(student_id, "attendance_drop", settings.alert_cooldown_hours):
                    warnings.append(self._create_consecutive_absence_alert(
                        student_id, feature_set, consecutive_absences
                    ))
            
            # 6. Behavioral anomalies
            if feature_set.sudden_behavior_change:
                if not db.check_recent_alert(student_id, "behavioral_anomaly", settings.alert_cooldown_hours):
                    warnings.append(self._create_behavioral_alert(
                        student_id, feature_set
                    ))
            
            # 6b. GPA momentum decline
            gpa_momentum = getattr(feature_set, 'gpa_momentum', 0.0)
            if gpa_momentum < -0.2:
                if not db.check_recent_alert(student_id, "performance_decline", settings.alert_cooldown_hours):
                    warnings.append(self._create_gpa_momentum_alert(
                        student_id, feature_set, gpa_momentum
                    ))
            
            # 7. Risk escalation (if previous risk exists)
            if previous_risk and risk_assessment.risk_score > previous_risk.risk_score + 15:
                if not db.check_recent_alert(student_id, "high_risk", settings.alert_cooldown_hours):
                    warnings.append(self._create_risk_escalation_alert(
                        student_id, previous_risk, risk_assessment
                    ))
            
            return warnings
        except Exception as e:
            logger.error(f"Error detecting warnings for student {student_id}: {e}")
            return []
    
    def _create_high_risk_alert(
        self,
        student_id: str,
        risk_assessment: RiskAssessment
    ) -> Alert:
        """Create high risk alert."""
        severity = "critical" if risk_assessment.risk_score >= 85 else "high"
        
        message = (
            f"Student flagged as HIGH RISK (Score: {risk_assessment.risk_score:.1f}/100). "
            f"Immediate intervention recommended. "
            f"Top factors: {', '.join([f.name for f in risk_assessment.top_factors[:2]])}"
        )
        
        return Alert(
            student_id=student_id,
            alert_type="high_risk",
            severity=severity,
            message=message,
            created_at=datetime.utcnow()
        )
    
    def _create_attendance_alert(
        self,
        student_id: str,
        feature_set: FeatureSet,
        level: str
    ) -> Alert:
        """Create attendance threshold breach alert."""
        severity = "critical" if level == "critical" else "high"
        
        message = (
            f"Attendance below threshold: {feature_set.overall_attendance:.1f}% "
            f"(Threshold: {self.attendance_threshold_critical if level == 'critical' else self.attendance_threshold_warning}%). "
            f"Recent absent days: {feature_set.recent_absent_days}. "
            f"Attendance trend: {feature_set.attendance_trend:.1f}%"
        )
        
        return Alert(
            student_id=student_id,
            alert_type="attendance_drop",
            severity=severity,
            message=message,
            created_at=datetime.utcnow()
        )
    
    def _create_performance_alert(
        self,
        student_id: str,
        feature_set: FeatureSet,
        level: str
    ) -> Alert:
        """Create performance decline alert."""
        severity = "critical" if level == "critical" else "high"
        
        message = (
            f"GPA below threshold: {feature_set.current_gpa:.2f} "
            f"(Threshold: {self.gpa_threshold_critical if level == 'critical' else self.gpa_threshold_warning}). "
            f"Failed courses: {feature_set.failed_courses_count}. "
            f"GPA trend: {feature_set.gpa_trend:.2f}"
        )
        
        return Alert(
            student_id=student_id,
            alert_type="performance_decline",
            severity=severity,
            message=message,
            created_at=datetime.utcnow()
        )
    
    def _create_gpa_decline_alert(
        self,
        student_id: str,
        feature_set: FeatureSet
    ) -> Alert:
        """Create rapid GPA decline alert."""
        message = (
            f"Rapid GPA decline detected: Trend of {feature_set.gpa_trend:.2f} per semester. "
            f"Current GPA: {feature_set.current_gpa:.2f}. "
            f"This indicates significant academic performance deterioration."
        )
        
        return Alert(
            student_id=student_id,
            alert_type="performance_decline",
            severity="high",
            message=message,
            created_at=datetime.utcnow()
        )
    
    def _create_attendance_decline_alert(
        self,
        student_id: str,
        feature_set: FeatureSet
    ) -> Alert:
        """Create rapid attendance decline alert."""
        message = (
            f"Rapid attendance decline detected: {abs(feature_set.attendance_trend):.1f}% drop recently. "
            f"Current attendance: {feature_set.overall_attendance:.1f}%. "
            f"Recent absent days: {feature_set.recent_absent_days}. "
            f"This may indicate disengagement or external issues."
        )
        
        return Alert(
            student_id=student_id,
            alert_type="attendance_drop",
            severity="high",
            message=message,
            created_at=datetime.utcnow()
        )
    
    def _create_behavioral_alert(
        self,
        student_id: str,
        feature_set: FeatureSet
    ) -> Alert:
        """Create behavioral anomaly alert."""
        message = (
            f"Sudden behavioral change detected. "
            f"Assignment submissions: {feature_set.assignment_submissions_on_time:.1f}%. "
            f"Participation score: {feature_set.participation_score:.1f}%. "
            f"This may indicate personal issues, health problems, or other concerns."
        )
        
        return Alert(
            student_id=student_id,
            alert_type="behavioral_anomaly",
            severity="medium",
            message=message,
            created_at=datetime.utcnow()
        )
    
    def _create_risk_escalation_alert(
        self,
        student_id: str,
        previous_risk: RiskAssessment,
        current_risk: RiskAssessment
    ) -> Alert:
        """Create risk escalation alert."""
        escalation = current_risk.risk_score - previous_risk.risk_score
        
        message = (
            f"Risk escalation detected: Score increased from {previous_risk.risk_score:.1f} "
            f"to {current_risk.risk_score:.1f} (+{escalation:.1f}). "
            f"Risk level changed from {previous_risk.risk_level.upper()} to {current_risk.risk_level.upper()}. "
            f"Immediate attention required."
        )
        
        severity = "critical" if escalation > 30 else "high"
        
        return Alert(
            student_id=student_id,
            alert_type="high_risk",
            severity=severity,
            message=message,
            created_at=datetime.utcnow()
        )
    
    def _create_sudden_drop_alert(
        self,
        student_id: str,
        feature_set: FeatureSet
    ) -> Alert:
        """Create sudden attendance drop alert."""
        message = (
            f"Sudden attendance drop detected: Drop of >20% in last week. "
            f"Current attendance: {feature_set.overall_attendance:.1f}%. "
            f"Recent absent days: {feature_set.recent_absent_days}. "
            f"This may indicate immediate intervention is needed."
        )
        
        return Alert(
            student_id=student_id,
            alert_type="attendance_drop",
            severity="high",
            message=message,
            created_at=datetime.utcnow()
        )
    
    def _create_consecutive_absence_alert(
        self,
        student_id: str,
        feature_set: FeatureSet,
        consecutive_days: int
    ) -> Alert:
        """Create consecutive absence alert."""
        message = (
            f"{consecutive_days} consecutive absences detected. "
            f"Current attendance: {feature_set.overall_attendance:.1f}%. "
            f"This pattern may indicate disengagement or external issues."
        )
        
        return Alert(
            student_id=student_id,
            alert_type="attendance_drop",
            severity="high" if consecutive_days >= 5 else "medium",
            message=message,
            created_at=datetime.utcnow()
        )
    
    def _create_gpa_momentum_alert(
        self,
        student_id: str,
        feature_set: FeatureSet,
        momentum: float
    ) -> Alert:
        """Create GPA momentum decline alert."""
        message = (
            f"Rapid GPA momentum decline: {momentum:.2f} per period. "
            f"Current GPA: {feature_set.current_gpa:.2f}. "
            f"This indicates accelerating academic performance deterioration."
        )
        
        return Alert(
            student_id=student_id,
            alert_type="performance_decline",
            severity="high",
            message=message,
            created_at=datetime.utcnow()
        )
    
    def save_alerts(self, alerts: List[Alert]) -> List[Dict[str, Any]]:
        """Save alerts to database."""
        saved_alerts = []
        
        for alert in alerts:
            try:
                alert_dict = alert.dict(exclude_none=True)
                # Convert datetime to ISO string
                if 'created_at' in alert_dict and alert_dict['created_at']:
                    alert_dict['created_at'] = alert_dict['created_at'].isoformat()
                
                saved = db.create_alert(alert_dict)
                if saved:
                    saved_alerts.append(saved)
                    logger.info(f"Created alert {saved['id']} for student {alert.student_id}")
            except Exception as e:
                logger.error(f"Error saving alert for student {alert.student_id}: {e}")
        
        return saved_alerts


# Global detector instance
detector = EarlyWarningDetector()
