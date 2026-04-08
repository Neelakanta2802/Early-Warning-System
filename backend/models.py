"""
Data models for the Early Warning System.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, date


# Type aliases
RiskLevel = Literal["low", "medium", "high"]
AlertType = Literal["high_risk", "attendance_drop", "performance_decline", "behavioral_anomaly"]
AlertSeverity = Literal["low", "medium", "high", "critical"]
InterventionType = Literal["mentoring", "counseling", "remedial", "academic_support"]
InterventionStatus = Literal["pending", "in_progress", "completed"]
AttendanceStatus = Literal["present", "absent", "late", "excused"]


class Student(BaseModel):
    """Student model."""
    id: str
    student_id: str
    full_name: str
    email: str
    department: str
    program: str
    year_level: int
    semester: str
    enrollment_date: date
    status: str


class AcademicRecord(BaseModel):
    """Academic record model."""
    id: str
    student_id: str
    semester: str
    course_code: str
    course_name: str
    grade: float
    credits: int
    gpa: float
    created_at: datetime


class AttendanceRecord(BaseModel):
    """Attendance record model."""
    id: str
    student_id: str
    date: date
    status: AttendanceStatus
    course_code: str
    semester: str
    created_at: datetime


class RiskFactor(BaseModel):
    """Risk factor contributing to risk score."""
    name: str
    weight: float = Field(ge=0, le=1)
    value: float
    impact: str  # Description of impact


class RiskAssessment(BaseModel):
    """Risk assessment model."""
    id: Optional[str] = None
    student_id: str
    risk_level: RiskLevel
    risk_score: float = Field(ge=0, le=100)
    confidence_level: float = Field(ge=0, le=1)
    factors: Dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""
    top_factors: List[RiskFactor] = Field(default_factory=list)
    prediction_date: datetime = Field(default_factory=datetime.utcnow)
    created_at: Optional[datetime] = None


class Alert(BaseModel):
    """Alert model."""
    id: Optional[str] = None
    student_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class Intervention(BaseModel):
    """Intervention model."""
    id: Optional[str] = None
    student_id: str
    assigned_to: str
    intervention_type: InterventionType
    description: str
    status: InterventionStatus = "pending"
    outcome_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class StudentProfile(BaseModel):
    """Complete student profile with all data."""
    student: Student
    latest_risk: Optional[RiskAssessment] = None
    risk_history: List[RiskAssessment] = Field(default_factory=list)
    academic_records: List[AcademicRecord] = Field(default_factory=list)
    attendance_records: List[AttendanceRecord] = Field(default_factory=list)
    alerts: List[Alert] = Field(default_factory=list)
    interventions: List[Intervention] = Field(default_factory=list)


class FeatureSet(BaseModel):
    """Feature set for ML model."""
    # Academic Features
    current_gpa: float = 0.0
    gpa_trend: float = 0.0  # Slope of GPA over time
    gpa_variance: float = 0.0
    recent_grades: List[float] = Field(default_factory=list)
    failed_courses_count: int = 0
    credits_completed: int = 0
    gpa_momentum: float = 0.0  # Recent change rate
    gpa_acceleration: float = 0.0  # Change in trend
    gpa_rolling_avg_3: float = 0.0  # 3-semester rolling average
    gpa_rolling_avg_6: float = 0.0  # 6-semester rolling average
    low_grade_count: int = 0  # Count of grades < 2.0
    subject_variance: float = 0.0  # Performance variance across subjects
    
    # Attendance Features
    overall_attendance: float = 0.0  # Percentage
    attendance_trend: float = 0.0  # Rate of decline
    recent_absent_days: int = 0
    late_count: int = 0
    subject_attendance: Dict[str, float] = Field(default_factory=dict)
    attendance_volatility: float = 0.0  # Standard deviation of weekly attendance
    attendance_momentum: float = 0.0  # Recent change rate
    consecutive_absences: int = 0  # Max consecutive absences
    attendance_rolling_avg_7: float = 0.0  # 7-day rolling average
    attendance_rolling_avg_14: float = 0.0  # 14-day rolling average
    sudden_drop_detected: bool = False  # Sudden drop > 20% in last week
    
    # Behavioral Features
    assignment_submissions_on_time: float = 0.0  # Percentage
    sudden_behavior_change: bool = False
    participation_score: float = 0.0
    
    # Historical Features
    previous_risk_score: float = 0.0
    warning_count: int = 0
    intervention_count: int = 0
    years_enrolled: float = 0.0
    
    # Demographic Features (if available)
    is_first_generation: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_gpa": 2.3,
                "gpa_trend": -0.2,
                "overall_attendance": 65.0,
                "attendance_trend": -5.0,
                "recent_absent_days": 8,
                "assignment_submissions_on_time": 70.0,
                "previous_risk_score": 45.0,
                "warning_count": 2
            }
        }


class AnalyticsOverview(BaseModel):
    """Analytics overview model."""
    total_students: int
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int
    active_interventions: int
    unacknowledged_alerts: int
    department_breakdown: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    semester_trends: Dict[str, int] = Field(default_factory=dict)


class RiskTrend(BaseModel):
    """Risk trend over time."""
    date: date
    low_risk: int
    medium_risk: int
    high_risk: int
    total_students: int
