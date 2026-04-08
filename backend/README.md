# Early Warning System - Backend

Complete backend implementation for the Early Warning System (EWS) used to identify at-risk students and support educational planning.

## Overview

This backend provides a comprehensive solution for:
- **Risk Assessment**: ML-powered risk scoring and classification
- **Early Warning Detection**: Automated detection of warning signals
- **Continuous Monitoring**: Scheduled periodic risk re-evaluation
- **Alert Management**: Alert generation and tracking
- **Intervention Tracking**: Intervention management and follow-up
- **Analytics & Insights**: Department-level, course-level, and trend analysis
- **RESTful API**: Complete API for frontend integration

## Architecture

### Core Components

1. **Data Processing Pipeline** (`data_processing.py`)
   - Data cleaning and normalization
   - Feature engineering
   - Behavioral anomaly detection

2. **Risk Scoring Engine** (`risk_engine.py`)
   - ML models (Random Forest, Logistic Regression, Hybrid)
   - Rule-based scoring
   - Explainable risk factors

3. **Early Warning Detector** (`early_warning.py`)
   - Threshold breach detection
   - Risk escalation monitoring
   - Alert generation

4. **Monitoring Engine** (`monitoring.py`)
   - Scheduled periodic assessment
   - Batch processing
   - Automated risk re-evaluation

5. **Analytics Engine** (`analytics.py`)
   - Aggregated statistics
   - Trend analysis
   - Department/course-level insights

6. **REST API** (`main.py`)
   - FastAPI-based endpoints
   - Student, alerts, interventions, analytics APIs

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL or Supabase account
- pip package manager

### Setup

1. **Clone and navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

5. **Run database migrations**:
   - The base schema is in `../project/supabase/migrations/`
   - Additional migrations are in `database_migrations.sql`
   - Apply migrations to your Supabase/PostgreSQL database

6. **Start the server**:
   ```bash
   python main.py
   ```

   Or with uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Configuration

Edit `.env` file with your settings:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_role_key
SUPABASE_ANON_KEY=your_supabase_anon_key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# ML Model Configuration
MODEL_TYPE=random_forest  # random_forest, logistic_regression, hybrid

# Risk Thresholds
RISK_THRESHOLD_LOW=30
RISK_THRESHOLD_MEDIUM=60
RISK_THRESHOLD_HIGH=80

# Attendance Thresholds
ATTENDANCE_THRESHOLD_WARNING=75
ATTENDANCE_THRESHOLD_CRITICAL=60

# GPA Thresholds
GPA_THRESHOLD_WARNING=2.5
GPA_THRESHOLD_CRITICAL=2.0

# Monitoring Configuration
MONITORING_INTERVAL_MINUTES=60
ALERT_COOLDOWN_HOURS=24
```

## API Endpoints

### Students

- `GET /api/students` - List students with filters
- `GET /api/students/{student_id}` - Get student profile with all data
- `GET /api/students/{student_id}/risk` - Get risk assessment
- `POST /api/students/{student_id}/evaluate` - Trigger risk evaluation

### Alerts

- `GET /api/alerts` - List alerts with filters
- `POST /api/alerts/{alert_id}/acknowledge` - Acknowledge an alert

### Interventions

- `GET /api/interventions` - List interventions
- `POST /api/interventions` - Create intervention
- `PUT /api/interventions/{intervention_id}` - Update intervention

### Analytics

- `GET /api/analytics/overview` - Analytics overview
- `GET /api/analytics/trends` - Risk trends over time
- `GET /api/analytics/departments` - Department risk distribution
- `GET /api/analytics/courses` - Course-level risk heatmap

### Health

- `GET /api/health` - Health check

## Usage Examples

### Evaluate a Student

```python
import requests

# Trigger risk evaluation
response = requests.post(
    "http://localhost:8000/api/students/{student_id}/evaluate"
)
result = response.json()
print(f"Risk Score: {result['assessment']['risk_score']}")
print(f"Risk Level: {result['assessment']['risk_level']}")
```

### Get Analytics Overview

```python
import requests

# Get department overview
response = requests.get(
    "http://localhost:8000/api/analytics/overview",
    params={"department": "Computer Science"}
)
overview = response.json()
print(f"Total Students: {overview['total_students']}")
print(f"High Risk: {overview['high_risk_count']}")
```

### Create Intervention

```python
import requests

intervention = {
    "student_id": "uuid-here",
    "assigned_to": "counselor-uuid",
    "intervention_type": "counseling",
    "description": "Weekly counseling sessions",
    "status": "pending"
}

response = requests.post(
    "http://localhost:8000/api/interventions",
    json=intervention
)
```

## Risk Scoring

The system uses a hybrid approach combining:

1. **Rule-Based Scoring**: Threshold-based detection for:
   - GPA below thresholds
   - Attendance below thresholds
   - Rapid declines
   - Behavioral anomalies

2. **ML Models**:
   - **Random Forest**: Default, handles non-linear relationships
   - **Logistic Regression**: Interpretable, linear relationships
   - **Hybrid**: Combines rule-based and ML (60/40 weight)

Risk scores range from 0-100:
- **0-29**: Low Risk
- **30-79**: Medium Risk
- **80-100**: High Risk

## Monitoring

The monitoring engine runs automatically and:
- Re-evaluates all active students periodically
- Creates alerts for detected warnings
- Tracks risk changes over time
- Logs monitoring activities

Configure the interval in `.env`:
```env
MONITORING_INTERVAL_MINUTES=60
```

## Data Processing

The system processes:

1. **Academic Data**:
   - Exam scores
   - GPA/CGPA
   - Course grades
   - Credits completed

2. **Attendance Data**:
   - Overall attendance percentage
   - Subject-wise attendance
   - Attendance trends
   - Late/absent patterns

3. **Behavioral Indicators**:
   - Assignment submission rates
   - Participation scores
   - Sudden changes
   - Pattern deviations

## Explainability

For every risk assessment, the system provides:
- **Top Contributing Factors**: Key reasons for risk
- **Human-Readable Explanations**: Clear descriptions
- **Confidence Levels**: Prediction certainty
- **Factor Weights**: Importance of each factor

## Alert System

Alerts are automatically generated for:
- High risk detection (score ≥ 80)
- Attendance threshold breaches
- GPA threshold breaches
- Rapid performance decline
- Behavioral anomalies
- Risk escalation

Alerts have:
- **Type**: high_risk, attendance_drop, performance_decline, behavioral_anomaly
- **Severity**: low, medium, high, critical
- **Cooldown**: Prevents duplicate alerts within configured hours

## Development

### Project Structure

```
backend/
├── main.py                 # FastAPI application
├── config.py              # Configuration settings
├── database.py            # Database connection and utilities
├── models.py              # Data models (Pydantic)
├── data_processing.py     # Feature engineering pipeline
├── risk_engine.py         # Risk scoring engine
├── early_warning.py       # Early warning detection
├── monitoring.py          # Continuous monitoring
├── analytics.py           # Analytics and aggregation
├── database_migrations.sql # Additional database schema
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

### Testing

Test endpoints using:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **cURL** or **Postman**

### Logging

Logs are configured in `config.py`:
- Level: Set via `LOG_LEVEL` in `.env`
- Format: Timestamp, logger name, level, message
- Output: Console

## Production Deployment

For production:

1. **Set environment variables** properly
2. **Disable auto-reload**: `API_RELOAD=false`
3. **Use production WSGI server**: Gunicorn with Uvicorn workers
4. **Configure logging**: File-based logging
5. **Enable monitoring**: Health checks and metrics
6. **Secure API**: Add authentication/authorization middleware
7. **Rate limiting**: Prevent abuse
8. **Database connection pooling**: Optimize connections

Example with Gunicorn:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Model Training

The ML models use default configurations suitable for academic projects. For production:

1. **Collect labeled data**: Historical student outcomes
2. **Feature selection**: Identify most predictive features
3. **Hyperparameter tuning**: Optimize model parameters
4. **Cross-validation**: Validate model performance
5. **Retrain periodically**: Update with new data

The system supports model replacement - save new models to `models/` directory.

## Troubleshooting

### Database Connection Issues
- Verify Supabase credentials in `.env`
- Check network connectivity
- Verify database permissions

### Model Loading Errors
- Models are auto-initialized if not found
- Check `models/` directory permissions
- Verify scikit-learn version compatibility

### Monitoring Not Running
- Check scheduler is started in `startup_event`
- Verify `MONITORING_INTERVAL_MINUTES` in `.env`
- Check logs for errors

## License

Academic project - See main project license

## Support

For issues or questions:
1. Check logs for error messages
2. Verify configuration settings
3. Review API documentation at `/docs`
4. Check database schema matches migrations
