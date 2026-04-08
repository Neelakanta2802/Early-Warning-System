# API Reference Guide

Complete API reference for the Early Warning System backend.

**Base URL**: `http://localhost:8000/api`

**Interactive Documentation**: 
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Authentication

Currently, authentication is handled by Supabase Row Level Security (RLS). Ensure you're authenticated via Supabase before making API calls.

---

## Endpoints

### Students

#### List Students
```http
GET /api/students
```

**Query Parameters**:
- `department` (optional): Filter by department
- `semester` (optional): Filter by semester
- `status` (optional): Filter by status (default: "active")
- `limit` (optional): Limit results (default: 100, max: 1000)
- `offset` (optional): Offset for pagination (default: 0)

**Response**:
```json
[
  {
    "id": "uuid",
    "student_id": "STU001",
    "full_name": "John Doe",
    "email": "john@example.com",
    "department": "Computer Science",
    "program": "BS Computer Science",
    "year_level": 2,
    "semester": "Fall 2024",
    "status": "active",
    "risk": {
      "risk_level": "medium",
      "risk_score": 45.5,
      "confidence_level": 0.75
    }
  }
]
```

#### Get Student Profile
```http
GET /api/students/{student_id}
```

**Response**:
```json
{
  "student": { ... },
  "latest_risk": { ... },
  "risk_history": [ ... ],
  "academic_records": [ ... ],
  "attendance_records": [ ... ],
  "alerts": [ ... ],
  "interventions": [ ... ]
}
```

#### Get Student Risk Assessment
```http
GET /api/students/{student_id}/risk?recalculate=false
```

**Query Parameters**:
- `recalculate` (optional): Force recalculation (default: false)

**Response**:
```json
{
  "assessment": {
    "id": "uuid",
    "student_id": "uuid",
    "risk_level": "medium",
    "risk_score": 45.5,
    "confidence_level": 0.75,
    "factors": { ... },
    "explanation": "...",
    "top_factors": [ ... ],
    "prediction_date": "2024-01-01T00:00:00Z"
  }
}
```

#### Evaluate Student
```http
POST /api/students/{student_id}/evaluate
```

**Response**:
```json
{
  "success": true,
  "assessment": { ... },
  "alerts_created": 2,
  "risk_change": {
    "score_change": 5.5,
    "level_change": false,
    "previous_level": "medium",
    "current_level": "medium"
  }
}
```

---

### Alerts

#### List Alerts
```http
GET /api/alerts
```

**Query Parameters**:
- `student_id` (optional): Filter by student ID
- `acknowledged` (optional): Filter by acknowledged status
- `severity` (optional): Filter by severity (low, medium, high, critical)
- `limit` (optional): Limit results (default: 100, max: 1000)

**Response**:
```json
[
  {
    "id": "uuid",
    "student_id": "uuid",
    "alert_type": "high_risk",
    "severity": "high",
    "message": "...",
    "acknowledged": false,
    "student": {
      "id": "uuid",
      "student_id": "STU001",
      "full_name": "John Doe"
    },
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### Acknowledge Alert
```http
POST /api/alerts/{alert_id}/acknowledge
```

**Request Body**:
```json
{
  "acknowledged_by": "user-uuid"
}
```

**Response**:
```json
{
  "success": true,
  "alert": { ... }
}
```

---

### Interventions

#### List Interventions
```http
GET /api/interventions
```

**Query Parameters**:
- `student_id` (optional): Filter by student ID
- `status` (optional): Filter by status (pending, in_progress, completed)
- `assigned_to` (optional): Filter by assigned user ID

**Response**:
```json
[
  {
    "id": "uuid",
    "student_id": "uuid",
    "assigned_to": "uuid",
    "intervention_type": "counseling",
    "description": "...",
    "status": "in_progress",
    "student": {
      "id": "uuid",
      "student_id": "STU001",
      "full_name": "John Doe"
    },
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### Create Intervention
```http
POST /api/interventions
```

**Request Body**:
```json
{
  "student_id": "uuid",
  "assigned_to": "uuid",
  "intervention_type": "counseling",
  "description": "Weekly counseling sessions",
  "status": "pending"
}
```

**Response**:
```json
{
  "success": true,
  "intervention": { ... }
}
```

#### Update Intervention
```http
PUT /api/interventions/{intervention_id}
```

**Request Body**:
```json
{
  "status": "completed",
  "outcome_notes": "Student improved significantly",
  "outcome_rating": 4
}
```

**Response**:
```json
{
  "success": true,
  "intervention": { ... }
}
```

---

### Analytics

#### Get Overview
```http
GET /api/analytics/overview?department=Computer Science&semester=Fall 2024
```

**Query Parameters**:
- `department` (optional): Filter by department
- `semester` (optional): Filter by semester

**Response**:
```json
{
  "total_students": 150,
  "low_risk_count": 80,
  "medium_risk_count": 50,
  "high_risk_count": 20,
  "active_interventions": 15,
  "unacknowledged_alerts": 8,
  "department_breakdown": {
    "Computer Science": {
      "total": 50,
      "low": 25,
      "medium": 20,
      "high": 5
    }
  },
  "semester_trends": {
    "Fall 2024_low": 80,
    "Fall 2024_medium": 50,
    "Fall 2024_high": 20
  }
}
```

#### Get Risk Trends
```http
GET /api/analytics/trends?days=30&department=Computer Science
```

**Query Parameters**:
- `days` (optional): Number of days to analyze (default: 30, max: 365)
- `department` (optional): Filter by department

**Response**:
```json
[
  {
    "date": "2024-01-01",
    "low_risk": 80,
    "medium_risk": 50,
    "high_risk": 20,
    "total_students": 150
  },
  ...
]
```

#### Get Department Distribution
```http
GET /api/analytics/departments
```

**Response**:
```json
{
  "Computer Science": {
    "total": 50,
    "low": 25,
    "medium": 20,
    "high": 5,
    "avg_risk_score": 35.5,
    "high_risk_percentage": 10.0
  },
  ...
}
```

#### Get Course Heatmap
```http
GET /api/analytics/courses?semester=Fall 2024
```

**Query Parameters**:
- `semester` (optional): Filter by semester

**Response**:
```json
{
  "CS101": {
    "course_code": "CS101",
    "course_name": "Introduction to Computer Science",
    "enrolled": 100,
    "at_risk": 20,
    "avg_grade": 75.5,
    "fail_rate": 5.0,
    "avg_attendance": 85.0,
    "at_risk_percentage": 20.0
  },
  ...
}
```

---

### Health Check

#### Health Check
```http
GET /api/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "Early Warning System API",
  "version": "1.0.0",
  "monitoring_active": true
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Missing required field: student_id"
}
```

### 404 Not Found
```json
{
  "detail": "Student not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message"
}
```

---

## Example Usage

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Get all students
response = requests.get(f"{BASE_URL}/students")
students = response.json()

# Get student risk
response = requests.get(f"{BASE_URL}/students/{student_id}/risk")
risk = response.json()

# Trigger evaluation
response = requests.post(f"{BASE_URL}/students/{student_id}/evaluate")
result = response.json()

# Get analytics overview
response = requests.get(f"{BASE_URL}/analytics/overview")
overview = response.json()

# Create intervention
intervention = {
    "student_id": student_id,
    "assigned_to": counselor_id,
    "intervention_type": "counseling",
    "description": "Weekly sessions"
}
response = requests.post(f"{BASE_URL}/interventions", json=intervention)
```

### cURL

```bash
# Get students
curl http://localhost:8000/api/students

# Get student risk
curl http://localhost:8000/api/students/{student_id}/risk

# Evaluate student
curl -X POST http://localhost:8000/api/students/{student_id}/evaluate

# Get analytics
curl http://localhost:8000/api/analytics/overview
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000/api';

// Get students
const response = await fetch(`${BASE_URL}/students`);
const students = await response.json();

// Evaluate student
const evaluateResponse = await fetch(
  `${BASE_URL}/students/${studentId}/evaluate`,
  { method: 'POST' }
);
const result = await evaluateResponse.json();
```

---

## Rate Limiting

Currently, no rate limiting is implemented. For production, implement rate limiting middleware.

---

## CORS

CORS is enabled for all origins. For production, configure allowed origins in `main.py`.

---

For interactive API testing, visit `http://localhost:8000/docs` when the server is running.
