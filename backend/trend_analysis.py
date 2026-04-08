"""
Trend detection and temporal analysis for risk escalation.
Detects worsening trajectories and sudden changes in student performance.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import logging

from database import db
from models import RiskAssessment

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyzes temporal trends in student risk and performance."""
    
    def __init__(self):
        """Initialize the trend analyzer."""
        self.escalation_threshold = 15.0  # Risk score increase threshold
        self.decline_threshold = -0.3  # GPA decline threshold
        self.attendance_drop_threshold = -15.0  # Attendance drop threshold
    
    def analyze_risk_trend(
        self,
        student_id: str,
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze risk trend for a student over time.
        
        Args:
            student_id: Student ID
            lookback_days: Number of days to look back
        
        Returns:
            Dictionary with trend analysis
        """
        try:
            # Get risk assessments
            assessments = db.get_risk_assessments(student_id=student_id, limit=50)
            
            if len(assessments) < 2:
                return {
                    'trend': 'insufficient_data',
                    'direction': 'stable',
                    'escalation_detected': False,
                    'message': 'Insufficient historical data for trend analysis'
                }
            
            # Convert to DataFrame
            df = pd.DataFrame(assessments)
            # Supabase returns timestamptz; normalize everything to UTC to avoid
            # "Invalid comparison between dtype=datetime64[ns, UTC] and datetime"
            df['created_at'] = pd.to_datetime(df['created_at'], utc=True, errors='coerce')
            df = df.sort_values('created_at')
            
            # Filter by lookback period
            cutoff_date = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=lookback_days)
            df = df[df['created_at'] >= cutoff_date]
            
            if len(df) < 2:
                return {
                    'trend': 'insufficient_data',
                    'direction': 'stable',
                    'escalation_detected': False,
                    'message': 'Insufficient data in lookback period'
                }
            
            # Extract risk scores and dates
            risk_scores = df['risk_score'].values
            # Use python datetimes for robust timedelta.days behavior
            dates = df['created_at'].dt.to_pydatetime()
            
            # Calculate trend
            trend_slope = self._calculate_trend_slope(risk_scores, dates)
            trend_direction = self._determine_direction(trend_slope)
            
            # Detect escalation
            escalation_detected = bool(self._detect_escalation(risk_scores))
            
            # Calculate momentum (recent change rate)
            momentum = self._calculate_momentum(risk_scores)
            
            # Detect sudden changes
            sudden_change = bool(self._detect_sudden_change(risk_scores))
            
            # Predict future risk (simple linear projection)
            projected_risk = self._project_future_risk(risk_scores, days_ahead=30)
            
            # Risk level changes
            risk_level_changes = self._analyze_risk_level_changes(df)
            
            return {
                'trend': trend_direction,
                'direction': trend_direction,
                'slope': float(trend_slope),
                'momentum': float(momentum),
                'escalation_detected': bool(escalation_detected),
                'sudden_change_detected': bool(sudden_change),
                'current_risk_score': float(risk_scores[-1]),
                'previous_risk_score': float(risk_scores[-2]) if len(risk_scores) >= 2 else None,
                'risk_change': float(risk_scores[-1] - risk_scores[0]) if len(risk_scores) >= 2 else 0.0,
                'projected_risk_30d': float(projected_risk),
                'risk_level_changes': risk_level_changes,
                'n_assessments': len(df),
                'time_span_days': (dates[-1] - dates[0]).days if len(dates) >= 2 else 0,
                'message': self._generate_trend_message(trend_direction, escalation_detected, sudden_change)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing risk trend for student {student_id}: {e}")
            return {
                'trend': 'error',
                'direction': 'unknown',
                'escalation_detected': False,
                'message': f'Error analyzing trend: {str(e)}'
            }
    
    def _calculate_trend_slope(self, values: np.ndarray, dates: np.ndarray) -> float:
        """Calculate linear trend slope."""
        if len(values) < 2:
            return 0.0
        
        # Convert dates to numeric (days since first date)
        first_date = dates[0]
        numeric_dates = np.array([(d - first_date).days for d in dates])
        
        # Linear regression
        if len(numeric_dates) > 1 and numeric_dates[-1] != numeric_dates[0]:
            slope = np.polyfit(numeric_dates, values, 1)[0]
            return float(slope)
        else:
            return 0.0
    
    def _determine_direction(self, slope: float) -> str:
        """Determine trend direction from slope."""
        if slope > 2.0:
            return 'increasing_rapidly'
        elif slope > 0.5:
            return 'increasing'
        elif slope < -2.0:
            return 'decreasing_rapidly'
        elif slope < -0.5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _detect_escalation(self, risk_scores: np.ndarray) -> bool:
        """Detect if risk is escalating."""
        if len(risk_scores) < 2:
            return False
        
        # Check if recent increase exceeds threshold
        recent_change = risk_scores[-1] - risk_scores[-2] if len(risk_scores) >= 2 else 0
        
        # Check overall trend
        if len(risk_scores) >= 3:
            recent_avg = np.mean(risk_scores[-3:])
            older_avg = np.mean(risk_scores[:-3]) if len(risk_scores) > 3 else risk_scores[0]
            overall_increase = recent_avg - older_avg
        else:
            overall_increase = recent_change
        
        return recent_change >= self.escalation_threshold or overall_increase >= self.escalation_threshold
    
    def _calculate_momentum(self, values: np.ndarray) -> float:
        """Calculate momentum (rate of change)."""
        if len(values) < 2:
            return 0.0
        
        # Use recent values (last 3 if available)
        recent = values[-3:] if len(values) >= 3 else values
        older = values[-6:-3] if len(values) >= 6 else values[:len(recent)]
        
        if len(older) > 0:
            momentum = np.mean(recent) - np.mean(older)
        else:
            momentum = values[-1] - values[0] if len(values) >= 2 else 0.0
        
        return float(momentum)
    
    def _detect_sudden_change(self, values: np.ndarray) -> bool:
        """Detect sudden changes in values."""
        if len(values) < 3:
            return False
        
        # Check if last value is significantly different from recent average
        recent_avg = np.mean(values[-3:-1]) if len(values) >= 3 else values[0]
        last_value = values[-1]
        
        change = abs(last_value - recent_avg)
        threshold = np.std(values) * 2  # 2 standard deviations
        
        return change > threshold
    
    def _project_future_risk(self, risk_scores: np.ndarray, days_ahead: int = 30) -> float:
        """Project future risk using linear trend."""
        if len(risk_scores) < 2:
            return float(risk_scores[0]) if len(risk_scores) > 0 else 50.0
        
        # Simple linear projection
        dates = np.arange(len(risk_scores))
        slope = np.polyfit(dates, risk_scores, 1)[0]
        
        # Project forward
        future_index = len(risk_scores) + (days_ahead / 7)  # Approximate weeks
        projected = risk_scores[-1] + (slope * (future_index - len(risk_scores)))
        
        # Clamp to valid range
        projected = max(0, min(100, projected))
        
        return float(projected)
    
    def _analyze_risk_level_changes(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze changes in risk level over time."""
        if len(df) < 2:
            return {
                'level_changes': 0,
                'current_level': df['risk_level'].iloc[-1] if len(df) > 0 else 'low',
                'previous_level': None,
                'level_escalated': False
            }
        
        risk_levels = df['risk_level'].values
        current_level = risk_levels[-1]
        previous_level = risk_levels[-2] if len(risk_levels) >= 2 else None
        
        # Count level changes
        level_changes = sum(1 for i in range(1, len(risk_levels)) if risk_levels[i] != risk_levels[i-1])
        
        # Check if escalated
        level_order = {'low': 0, 'medium': 1, 'high': 2}
        level_escalated = (
            previous_level is not None and
            level_order.get(current_level, 0) > level_order.get(previous_level, 0)
        )
        
        return {
            'level_changes': int(level_changes),
            'current_level': str(current_level),
            'previous_level': str(previous_level) if previous_level else None,
            'level_escalated': bool(level_escalated)
        }
    
    def _generate_trend_message(
        self,
        direction: str,
        escalation_detected: bool,
        sudden_change: bool
    ) -> str:
        """Generate human-readable trend message."""
        messages = []
        
        if escalation_detected:
            messages.append("⚠️ Risk escalation detected - immediate attention required.")
        
        if sudden_change:
            messages.append("⚠️ Sudden change in risk detected - may indicate new issues.")
        
        if direction == 'increasing_rapidly':
            messages.append("Risk is increasing rapidly over time.")
        elif direction == 'increasing':
            messages.append("Risk is gradually increasing.")
        elif direction == 'decreasing_rapidly':
            messages.append("Risk is decreasing rapidly - positive trend.")
        elif direction == 'decreasing':
            messages.append("Risk is gradually decreasing - improvement noted.")
        else:
            messages.append("Risk level is relatively stable.")
        
        return " ".join(messages) if messages else "No significant trend detected."
    
    def compare_periods(
        self,
        student_id: str,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime
    ) -> Dict[str, Any]:
        """Compare risk metrics between two time periods."""
        try:
            assessments = db.get_risk_assessments(student_id=student_id, limit=100)
            
            if len(assessments) == 0:
                return {'error': 'No assessments found'}
            
            df = pd.DataFrame(assessments)
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Filter periods
            period1 = df[(df['created_at'] >= period1_start) & (df['created_at'] <= period1_end)]
            period2 = df[(df['created_at'] >= period2_start) & (df['created_at'] <= period2_end)]
            
            if len(period1) == 0 or len(period2) == 0:
                return {'error': 'Insufficient data for comparison'}
            
            # Calculate statistics
            p1_avg = period1['risk_score'].mean()
            p2_avg = period2['risk_score'].mean()
            p1_max = period1['risk_score'].max()
            p2_max = period2['risk_score'].max()
            
            return {
                'period1': {
                    'avg_risk_score': float(p1_avg),
                    'max_risk_score': float(p1_max),
                    'n_assessments': len(period1)
                },
                'period2': {
                    'avg_risk_score': float(p2_avg),
                    'max_risk_score': float(p2_max),
                    'n_assessments': len(period2)
                },
                'change': {
                    'avg_change': float(p2_avg - p1_avg),
                    'max_change': float(p2_max - p1_max),
                    'percent_change': float((p2_avg - p1_avg) / p1_avg * 100) if p1_avg > 0 else 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing periods: {e}")
            return {'error': str(e)}


# Global trend analyzer instance
trend_analyzer = TrendAnalyzer()
