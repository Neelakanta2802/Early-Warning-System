"""
Time Series Forecasting for Student Risk Trends.
Predicts future risk levels based on historical patterns.
"""
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    logger.warning("Statsmodels not available for time series forecasting")

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class TimeSeriesForecaster:
    """Time series forecasting for student risk trends."""
    
    def __init__(self):
        """Initialize the forecaster."""
        pass
    
    def forecast_risk_trend(
        self,
        historical_scores: List[float],
        historical_dates: List[datetime],
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """
        Forecast future risk scores based on historical data.
        
        Args:
            historical_scores: List of historical risk scores
            historical_dates: List of corresponding dates
            forecast_days: Number of days to forecast ahead
        
        Returns:
            Dictionary with forecast results
        """
        if len(historical_scores) < 3:
            # Not enough data for forecasting
            return {
                'forecast': historical_scores[-1] if historical_scores else 0.0,
                'trend': 'stable',
                'confidence': 0.5,
                'forecast_dates': [],
                'forecast_scores': []
            }
        
        try:
            # Convert to pandas Series
            df = pd.DataFrame({
                'date': historical_dates,
                'score': historical_scores
            })
            df = df.sort_values('date')
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            # Fill missing dates (interpolate)
            date_range = pd.date_range(
                start=df.index.min(),
                end=df.index.max(),
                freq='D'
            )
            df = df.reindex(date_range)
            df['score'] = df['score'].interpolate(method='linear')
            
            # Simple trend analysis
            trend = self._calculate_trend(df['score'].values)
            
            # Forecast using linear regression
            if SKLEARN_AVAILABLE:
                forecast_result = self._linear_forecast(df['score'].values, forecast_days)
            else:
                # Simple extrapolation
                recent_avg = df['score'].tail(7).mean()
                forecast_result = {
                    'forecast': float(recent_avg),
                    'forecast_scores': [float(recent_avg)] * forecast_days,
                    'confidence': 0.6
                }
            
            # Generate forecast dates
            last_date = df.index.max()
            forecast_dates = [
                (last_date + timedelta(days=i)).isoformat()
                for i in range(1, forecast_days + 1)
            ]
            
            return {
                'forecast': forecast_result['forecast'],
                'trend': trend,
                'confidence': forecast_result['confidence'],
                'forecast_dates': forecast_dates,
                'forecast_scores': forecast_result['forecast_scores'],
                'historical_trend': float(trend.split()[0]) if 'increasing' in trend or 'decreasing' in trend else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error in time series forecasting: {e}")
            # Fallback to simple average
            avg_score = np.mean(historical_scores) if historical_scores else 0.0
            return {
                'forecast': float(avg_score),
                'trend': 'stable',
                'confidence': 0.5,
                'forecast_dates': [],
                'forecast_scores': []
            }
    
    def _calculate_trend(self, scores: np.ndarray) -> str:
        """Calculate trend direction."""
        if len(scores) < 2:
            return 'stable'
        
        # Linear regression to find trend
        x = np.arange(len(scores))
        slope = np.polyfit(x, scores, 1)[0]
        
        if slope > 2:
            return 'increasing (high risk)'
        elif slope > 0.5:
            return 'increasing (moderate)'
        elif slope < -2:
            return 'decreasing (improving)'
        elif slope < -0.5:
            return 'decreasing (slight improvement)'
        else:
            return 'stable'
    
    def _linear_forecast(
        self,
        historical: np.ndarray,
        forecast_periods: int
    ) -> Dict[str, Any]:
        """Forecast using linear regression."""
        try:
            from sklearn.linear_model import LinearRegression
            
            # Prepare data
            X = np.arange(len(historical)).reshape(-1, 1)
            y = historical.reshape(-1, 1)
            
            # Fit model
            model = LinearRegression()
            model.fit(X, y)
            
            # Forecast
            future_X = np.arange(len(historical), len(historical) + forecast_periods).reshape(-1, 1)
            forecast = model.predict(future_X).flatten()
            
            # Calculate confidence (based on R²)
            r2 = model.score(X, y)
            confidence = max(0.5, min(0.95, r2))
            
            # Clip forecast to valid range [0, 100]
            forecast = np.clip(forecast, 0, 100)
            
            return {
                'forecast': float(forecast[-1]),
                'forecast_scores': [float(x) for x in forecast],
                'confidence': float(confidence)
            }
        except Exception as e:
            logger.error(f"Error in linear forecast: {e}")
            avg = np.mean(historical)
            return {
                'forecast': float(avg),
                'forecast_scores': [float(avg)] * forecast_periods,
                'confidence': 0.5
            }
    
    def predict_dropout_probability(
        self,
        risk_history: List[float],
        attendance_history: List[float],
        gpa_history: List[float]
    ) -> float:
        """Predict probability of student dropping out."""
        if not risk_history:
            return 0.0
        
        # Weighted combination of factors
        recent_risk = np.mean(risk_history[-3:]) if len(risk_history) >= 3 else risk_history[-1]
        risk_trend = (risk_history[-1] - risk_history[0]) / len(risk_history) if len(risk_history) > 1 else 0
        
        attendance_factor = 0.0
        if attendance_history:
            recent_attendance = np.mean(attendance_history[-7:]) if len(attendance_history) >= 7 else attendance_history[-1]
            attendance_factor = max(0, (75 - recent_attendance) / 75)  # Higher if attendance is low
        
        gpa_factor = 0.0
        if gpa_history:
            recent_gpa = np.mean(gpa_history[-2:]) if len(gpa_history) >= 2 else gpa_history[-1]
            gpa_factor = max(0, (2.0 - recent_gpa) / 2.0)  # Higher if GPA is low
        
        # Combine factors
        dropout_prob = (
            (recent_risk / 100.0) * 0.5 +
            attendance_factor * 0.3 +
            gpa_factor * 0.2
        )
        
        # Adjust for trend
        if risk_trend > 5:
            dropout_prob += 0.1
        elif risk_trend < -5:
            dropout_prob -= 0.1
        
        return min(1.0, max(0.0, dropout_prob))


# Global instance
time_series_forecaster = TimeSeriesForecaster()
