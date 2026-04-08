"""
Analytics and aggregation logic for educational planning and insights.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from models import AnalyticsOverview, RiskTrend
from database import db
import logging

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Analytics engine for generating insights and reports."""
    
    def __init__(self):
        """Initialize the analytics engine."""
        pass
    
    def get_overview(
        self,
        department: Optional[str] = None,
        semester: Optional[str] = None
    ) -> AnalyticsOverview:
        """Get analytics overview with aggregated statistics."""
        try:
            # Get all students with filters
            filters = {'status': 'active'}
            if department:
                filters['department'] = department
            if semester:
                filters['semester'] = semester
            
            students = db.get_students(filters=filters)
            student_ids = [s['id'] for s in students]
            
            # Get all risk assessments
            all_assessments = db.get_risk_assessments()
            
            # Filter to relevant students and get latest assessment per student
            latest_assessments = {}
            for assessment in all_assessments:
                student_id = assessment['student_id']
                if student_id in student_ids:
                    if student_id not in latest_assessments:
                        latest_assessments[student_id] = assessment
                    else:
                        # Keep most recent
                        current_date = latest_assessments[student_id].get('created_at', '')
                        new_date = assessment.get('created_at', '')
                        if new_date > current_date:
                            latest_assessments[student_id] = assessment
            
            # Count risk levels
            risk_counts = {'low': 0, 'medium': 0, 'high': 0}
            for assessment in latest_assessments.values():
                level = assessment.get('risk_level', 'low')
                if level in risk_counts:
                    risk_counts[level] += 1
            
            # Get interventions
            all_interventions = db.get_interventions(status='in_progress')
            active_interventions = len(all_interventions)
            
            # Get unacknowledged alerts
            unacknowledged_alerts = db.get_alerts(acknowledged=False)
            unacknowledged_count = len(unacknowledged_alerts)
            
            # Department breakdown
            department_breakdown = self._get_department_breakdown(students, latest_assessments)
            
            # Semester trends
            semester_trends = self._get_semester_trends(students, latest_assessments)
            
            return AnalyticsOverview(
                total_students=len(students),
                low_risk_count=risk_counts['low'],
                medium_risk_count=risk_counts['medium'],
                high_risk_count=risk_counts['high'],
                active_interventions=active_interventions,
                unacknowledged_alerts=unacknowledged_count,
                department_breakdown=department_breakdown,
                semester_trends=semester_trends
            )
        except Exception as e:
            logger.error(f"Error generating overview: {e}")
            return AnalyticsOverview(
                total_students=0,
                low_risk_count=0,
                medium_risk_count=0,
                high_risk_count=0,
                active_interventions=0,
                unacknowledged_alerts=0
            )
    
    def _get_department_breakdown(
        self,
        students: List[Dict[str, Any]],
        assessments: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, int]]:
        """Get risk distribution by department."""
        breakdown = defaultdict(lambda: {'low': 0, 'medium': 0, 'high': 0, 'total': 0})
        
        for student in students:
            dept = student.get('department', 'Unknown')
            student_id = student['id']
            
            breakdown[dept]['total'] += 1
            
            if student_id in assessments:
                level = assessments[student_id].get('risk_level', 'low')
                if level in breakdown[dept]:
                    breakdown[dept][level] += 1
            else:
                breakdown[dept]['low'] += 1  # Default to low if no assessment
        
        return {k: dict(v) for k, v in breakdown.items()}
    
    def _get_semester_trends(
        self,
        students: List[Dict[str, Any]],
        assessments: Dict[str, Dict[str, Any]]
    ) -> Dict[str, int]:
        """Get risk distribution by semester."""
        trends = defaultdict(int)
        
        for student in students:
            semester = student.get('semester', 'Unknown')
            student_id = student['id']
            
            if student_id in assessments:
                level = assessments[student_id].get('risk_level', 'low')
                trends[f"{semester}_{level}"] += 1
            else:
                trends[f"{semester}_low"] += 1
        
        return dict(trends)
    
    def get_risk_trends(
        self,
        days: int = 30,
        department: Optional[str] = None
    ) -> List[RiskTrend]:
        """Get risk trends over time."""
        try:
            # Get students with filter
            filters = {'status': 'active'}
            if department:
                filters['department'] = department
            
            students = db.get_students(filters=filters)
            student_ids = [s['id'] for s in students]
            
            # Get all assessments
            all_assessments = db.get_risk_assessments()
            
            # Filter by date and student
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            relevant_assessments = []
            for assessment in all_assessments:
                student_id = assessment['student_id']
                if student_id in student_ids:
                    created_at = assessment.get('created_at', '')
                    try:
                        if isinstance(created_at, str):
                            assess_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            assess_date = created_at
                        
                        if assess_date >= cutoff_date:
                            relevant_assessments.append(assessment)
                    except:
                        continue
            
            # Group by date
            daily_counts = defaultdict(lambda: {'low': 0, 'medium': 0, 'high': 0, 'total': 0})
            
            for assessment in relevant_assessments:
                created_at = assessment.get('created_at', '')
                try:
                    if isinstance(created_at, str):
                        assess_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        assess_date = created_at
                    
                    date_key = assess_date.date()
                    level = assessment.get('risk_level', 'low')
                    
                    daily_counts[date_key][level] += 1
                    daily_counts[date_key]['total'] += 1
                except:
                    continue
            
            # Convert to list and sort
            trends = []
            for date_key in sorted(daily_counts.keys()):
                counts = daily_counts[date_key]
                trends.append(RiskTrend(
                    date=date_key,
                    low_risk=counts['low'],
                    medium_risk=counts['medium'],
                    high_risk=counts['high'],
                    total_students=counts['total']
                ))
            
            return trends
        except Exception as e:
            logger.error(f"Error generating risk trends: {e}")
            return []
    
    def get_department_risk_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Get risk distribution by department."""
        try:
            students = db.get_students(filters={'status': 'active'})
            all_assessments = db.get_risk_assessments()
            
            # Get latest assessment per student
            latest_assessments = {}
            for assessment in all_assessments:
                student_id = assessment['student_id']
                if student_id not in latest_assessments:
                    latest_assessments[student_id] = assessment
                else:
                    current_date = latest_assessments[student_id].get('created_at', '')
                    new_date = assessment.get('created_at', '')
                    if new_date > current_date:
                        latest_assessments[student_id] = assessment
            
            # Group by department
            dept_stats = defaultdict(lambda: {
                'total': 0,
                'low': 0,
                'medium': 0,
                'high': 0,
                'avg_risk_score': 0.0,
                'high_risk_percentage': 0.0
            })
            
            dept_scores = defaultdict(list)
            
            for student in students:
                dept = student.get('department', 'Unknown')
                student_id = student['id']
                
                dept_stats[dept]['total'] += 1
                
                if student_id in latest_assessments:
                    assessment = latest_assessments[student_id]
                    level = assessment.get('risk_level', 'low')
                    score = assessment.get('risk_score', 0.0)
                    
                    dept_stats[dept][level] += 1
                    dept_scores[dept].append(score)
                else:
                    dept_stats[dept]['low'] += 1
            
            # Calculate averages and percentages
            for dept in dept_stats:
                stats = dept_stats[dept]
                if dept_scores[dept]:
                    stats['avg_risk_score'] = sum(dept_scores[dept]) / len(dept_scores[dept])
                
                if stats['total'] > 0:
                    stats['high_risk_percentage'] = (stats['high'] / stats['total']) * 100
            
            return {k: dict(v) for k, v in dept_stats.items()}
        except Exception as e:
            logger.error(f"Error generating department distribution: {e}")
            return {}
    
    def get_course_risk_heatmap(
        self,
        semester: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Get course-level risk heatmap."""
        try:
            # Get academic records
            filters = {}
            if semester:
                filters['semester'] = semester
            
            academic_records = db.get_academic_records()
            if semester:
                academic_records = [r for r in academic_records if r.get('semester') == semester]
            
            # Group by course
            course_stats = defaultdict(lambda: {
                'course_code': '',
                'course_name': '',
                'enrolled': 0,
                'at_risk': 0,
                'avg_grade': 0.0,
                'fail_rate': 0.0,
                'avg_attendance': 0.0
            })
            
            # Get students and their risk assessments
            students = db.get_students(filters={'status': 'active'})
            student_ids = set(s['id'] for s in students)
            
            all_assessments = db.get_risk_assessments()
            latest_assessments = {}
            for assessment in all_assessments:
                student_id = assessment['student_id']
                if student_id in student_ids:
                    if student_id not in latest_assessments:
                        latest_assessments[student_id] = assessment
                    else:
                        current_date = latest_assessments[student_id].get('created_at', '')
                        new_date = assessment.get('created_at', '')
                        if new_date > current_date:
                            latest_assessments[student_id] = assessment
            
            # Process academic records
            course_grades = defaultdict(list)
            course_failures = defaultdict(int)
            
            for record in academic_records:
                student_id = record.get('student_id')
                if student_id in student_ids:
                    course_code = record.get('course_code', '')
                    course_name = record.get('course_name', '')
                    grade = record.get('grade', 0.0)
                    
                    if not course_stats[course_code]['course_code']:
                        course_stats[course_code]['course_code'] = course_code
                        course_stats[course_code]['course_name'] = course_name
                    
                    course_stats[course_code]['enrolled'] += 1
                    course_grades[course_code].append(grade)
                    
                    # Check if student is at risk
                    if student_id in latest_assessments:
                        assessment = latest_assessments[student_id]
                        risk_level = assessment.get('risk_level', 'low')
                        if risk_level in ['medium', 'high']:
                            course_stats[course_code]['at_risk'] += 1
                    
                    # Check for failure
                    if grade < 50 or record.get('gpa', 0) < 2.0:
                        course_failures[course_code] += 1
            
            # Calculate statistics
            for course_code in course_stats:
                stats = course_stats[course_code]
                
                if course_grades[course_code]:
                    stats['avg_grade'] = sum(course_grades[course_code]) / len(course_grades[course_code])
                
                if stats['enrolled'] > 0:
                    stats['fail_rate'] = (course_failures[course_code] / stats['enrolled']) * 100
                    stats['at_risk_percentage'] = (stats['at_risk'] / stats['enrolled']) * 100
                
                # Get attendance for this course
                attendance_records = db.get_attendance_records(course_code=course_code)
                if attendance_records:
                    # Calculate average attendance per student
                    student_attendance = defaultdict(list)
                    for record in attendance_records:
                        student_id = record.get('student_id')
                        status = record.get('status', 'absent')
                        student_attendance[student_id].append(1 if status in ['present', 'excused'] else 0)
                    
                    if student_attendance:
                        avg_attendance_list = [
                            sum(atts) / len(atts) * 100 if atts else 0
                            for atts in student_attendance.values()
                        ]
                        stats['avg_attendance'] = sum(avg_attendance_list) / len(avg_attendance_list) if avg_attendance_list else 0.0
            
            return {k: dict(v) for k, v in course_stats.items()}
        except Exception as e:
            logger.error(f"Error generating course heatmap: {e}")
            return {}
    
    def get_historical_comparison(
        self,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime
    ) -> Dict[str, Any]:
        """Compare risk metrics between two time periods."""
        try:
            # This is a simplified version - in production, would query by date ranges
            all_assessments = db.get_risk_assessments()
            
            period1_assessments = []
            period2_assessments = []
            
            for assessment in all_assessments:
                created_at = assessment.get('created_at', '')
                try:
                    if isinstance(created_at, str):
                        assess_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        assess_date = created_at
                    
                    if period1_start <= assess_date <= period1_end:
                        period1_assessments.append(assessment)
                    elif period2_start <= assess_date <= period2_end:
                        period2_assessments.append(assessment)
                except:
                    continue
            
            def calculate_stats(assessments):
                if not assessments:
                    return {
                        'total': 0,
                        'low': 0,
                        'medium': 0,
                        'high': 0,
                        'avg_score': 0.0
                    }
                
                counts = {'low': 0, 'medium': 0, 'high': 0}
                scores = []
                
                for assessment in assessments:
                    level = assessment.get('risk_level', 'low')
                    if level in counts:
                        counts[level] += 1
                    scores.append(assessment.get('risk_score', 0.0))
                
                return {
                    'total': len(assessments),
                    'low': counts['low'],
                    'medium': counts['medium'],
                    'high': counts['high'],
                    'avg_score': sum(scores) / len(scores) if scores else 0.0
                }
            
            stats1 = calculate_stats(period1_assessments)
            stats2 = calculate_stats(period2_assessments)
            
            return {
                'period1': stats1,
                'period2': stats2,
                'changes': {
                    'total_change': stats2['total'] - stats1['total'],
                    'high_risk_change': stats2['high'] - stats1['high'],
                    'avg_score_change': stats2['avg_score'] - stats1['avg_score']
                }
            }
        except Exception as e:
            logger.error(f"Error generating historical comparison: {e}")
            return {}


# Global analytics engine instance
analytics_engine = AnalyticsEngine()
