"""
Data processing and feature engineering pipeline for risk assessment.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from models import FeatureSet, AcademicRecord, AttendanceRecord
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Handles data cleaning, normalization, and feature engineering."""
    
    def __init__(self):
        """Initialize the data processor."""
        self.attendance_status_weights = {
            'present': 1.0,
            'excused': 0.8,
            'late': 0.5,
            'absent': 0.0
        }
    
    def clean_and_normalize_data(
        self,
        academic_records: List[Dict[str, Any]],
        attendance_records: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Clean and normalize raw data."""
        try:
            # Clean academic records - filter out invalid records first
            cleaned_academic = []
            for record in academic_records:
                # Skip records with None/NoneType for critical fields
                grade = record.get('grade')
                gpa = record.get('gpa')
                
                # Filter out records where grade or gpa is None
                if grade is None or gpa is None:
                    continue  # Skip invalid records
                
                try:
                    cleaned = {
                        'grade': max(0, min(100, float(grade))),
                        'gpa': max(0, min(4.0, float(gpa))),
                        'semester': str(record.get('semester', '')),
                        'course_code': str(record.get('course_code', '')),
                        **record
                    }
                    cleaned_academic.append(cleaned)
                except (ValueError, TypeError) as e:
                    # Skip records that can't be converted
                    logger.debug(f"Skipping invalid academic record: {e}")
                    continue
            
            # Clean attendance records
            cleaned_attendance = []
            for record in attendance_records:
                status = record.get('status', 'absent')
                if status not in ['present', 'absent', 'late', 'excused']:
                    status = 'absent'
                
                cleaned = {
                    'status': status,
                    'date': record.get('date'),
                    'course_code': str(record.get('course_code', '')),
                    **record
                }
                cleaned_attendance.append(cleaned)
            
            return cleaned_academic, cleaned_attendance
        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            return academic_records, attendance_records
    
    def calculate_gpa_features(
        self,
        academic_records: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate GPA-related features with advanced temporal analysis."""
        if not academic_records:
            return {
                'current_gpa': 0.0,
                'gpa_trend': 0.0,
                'gpa_variance': 0.0,
                'recent_grades': [],
                'failed_courses_count': 0,
                'credits_completed': 0,
                'gpa_momentum': 0.0,
                'gpa_acceleration': 0.0,
                'gpa_rolling_avg_3': 0.0,
                'gpa_rolling_avg_6': 0.0,
                'low_grade_count': 0,
                'subject_variance': 0.0
            }
        
        try:
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(academic_records)
            # Try multiple date formats
            df['semester_date'] = pd.to_datetime(df['semester'], errors='coerce', format='%Y-%m')
            if df['semester_date'].isna().all():
                df['semester_date'] = pd.to_datetime(df['semester'], errors='coerce')
            df = df.sort_values('semester_date')
            df = df.dropna(subset=['gpa', 'grade'])
            
            if len(df) == 0:
                return {
                    'current_gpa': 0.0,
                    'gpa_trend': 0.0,
                    'gpa_variance': 0.0,
                    'recent_grades': [],
                    'failed_courses_count': 0,
                    'credits_completed': 0,
                    'gpa_momentum': 0.0,
                    'gpa_acceleration': 0.0,
                    'gpa_rolling_avg_3': 0.0,
                    'gpa_rolling_avg_6': 0.0,
                    'low_grade_count': 0,
                    'subject_variance': 0.0
                }
            
            # Current GPA (most recent)
            current_gpa = float(df['gpa'].iloc[-1])
            
            # GPA trend (slope over time) - linear regression
            if len(df) >= 2:
                semesters_numeric = np.arange(len(df))
                gpa_trend = np.polyfit(semesters_numeric, df['gpa'].values, 1)[0]
            else:
                gpa_trend = 0.0
            
            # GPA variance (volatility indicator)
            gpa_variance = float(df['gpa'].std()) if len(df) > 1 else 0.0
            
            # GPA momentum (recent change rate)
            if len(df) >= 2:
                recent_3 = df['gpa'].tail(3).values
                if len(recent_3) >= 2:
                    gpa_momentum = float(recent_3[-1] - recent_3[0]) / len(recent_3)
                else:
                    gpa_momentum = float(recent_3[-1] - recent_3[0]) if len(recent_3) == 2 else 0.0
            else:
                gpa_momentum = 0.0
            
            # GPA acceleration (change in trend)
            if len(df) >= 3:
                first_half = df['gpa'].iloc[:len(df)//2].mean()
                second_half = df['gpa'].iloc[len(df)//2:].mean()
                gpa_acceleration = float(second_half - first_half)
            else:
                gpa_acceleration = 0.0
            
            # Rolling averages
            gpa_rolling_avg_3 = float(df['gpa'].tail(3).mean()) if len(df) >= 3 else current_gpa
            gpa_rolling_avg_6 = float(df['gpa'].tail(6).mean()) if len(df) >= 6 else current_gpa
            
            # Recent grades (last 6 records)
            recent_grades = df['grade'].tail(6).tolist()
            recent_grades = [float(g) for g in recent_grades]
            
            # Failed courses (grade < 50 or GPA < 2.0)
            failed_courses = df[(df['grade'] < 50) | (df['gpa'] < 2.0)]
            failed_count = len(failed_courses)
            
            # Low grade count (C or below, < 2.0 GPA)
            low_grade_count = len(df[df['gpa'] < 2.0])
            
            # Subject-wise variance (performance consistency across subjects)
            if 'course_code' in df.columns and len(df) > 1:
                subject_gpas = df.groupby('course_code')['gpa'].mean()
                subject_variance = float(subject_gpas.std()) if len(subject_gpas) > 1 else 0.0
            else:
                subject_variance = 0.0
            
            # Total credits completed
            credits_completed = int(df['credits'].sum()) if 'credits' in df.columns else 0
            
            return {
                'current_gpa': current_gpa,
                'gpa_trend': float(gpa_trend),
                'gpa_variance': gpa_variance,
                'recent_grades': recent_grades,
                'failed_courses_count': failed_count,
                'credits_completed': credits_completed,
                'gpa_momentum': gpa_momentum,
                'gpa_acceleration': gpa_acceleration,
                'gpa_rolling_avg_3': gpa_rolling_avg_3,
                'gpa_rolling_avg_6': gpa_rolling_avg_6,
                'low_grade_count': low_grade_count,
                'subject_variance': subject_variance
            }
        except Exception as e:
            logger.error(f"Error calculating GPA features: {e}")
            return {
                'current_gpa': 0.0,
                'gpa_trend': 0.0,
                'gpa_variance': 0.0,
                'recent_grades': [],
                'failed_courses_count': 0,
                'credits_completed': 0,
                'gpa_momentum': 0.0,
                'gpa_acceleration': 0.0,
                'gpa_rolling_avg_3': 0.0,
                'gpa_rolling_avg_6': 0.0,
                'low_grade_count': 0,
                'subject_variance': 0.0
            }
    
    def calculate_attendance_features(
        self,
        attendance_records: List[Dict[str, Any]],
        course_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate attendance-related features with advanced temporal analysis."""
        if not attendance_records:
            return {
                'overall_attendance': 0.0,
                'attendance_trend': 0.0,
                'recent_absent_days': 0,
                'late_count': 0,
                'subject_attendance': {},
                'attendance_volatility': 0.0,
                'attendance_momentum': 0.0,
                'consecutive_absences': 0,
                'attendance_rolling_avg_7': 0.0,
                'attendance_rolling_avg_14': 0.0,
                'sudden_drop_detected': False
            }
        
        try:
            # Filter by course if specified
            filtered_records = [
                r for r in attendance_records
                if not course_code or r.get('course_code') == course_code
            ]
            
            if not filtered_records:
                return {
                    'overall_attendance': 0.0,
                    'attendance_trend': 0.0,
                    'recent_absent_days': 0,
                    'late_count': 0,
                    'subject_attendance': {},
                    'attendance_volatility': 0.0,
                    'attendance_momentum': 0.0,
                    'consecutive_absences': 0,
                    'attendance_rolling_avg_7': 0.0,
                    'attendance_rolling_avg_14': 0.0,
                    'sudden_drop_detected': False
                }
            
            # Convert to DataFrame
            df = pd.DataFrame(filtered_records)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Create binary attendance column (1 = present/excused, 0 = absent/late)
            df['attended'] = df['status'].isin(['present', 'excused']).astype(int)
            
            # Overall attendance percentage
            total_days = len(df)
            present_days = df['attended'].sum()
            overall_attendance = (present_days / total_days * 100) if total_days > 0 else 0.0
            
            # Attendance trend (last 30 days vs previous 30 days)
            if len(df) >= 10:
                recent_df = df.tail(30)
                older_df = df.iloc[:-30] if len(df) > 30 else df.iloc[:10]
                
                recent_attendance = (recent_df['attended'].sum() / len(recent_df) * 100) if len(recent_df) > 0 else 0.0
                older_attendance = (older_df['attended'].sum() / len(older_df) * 100) if len(older_df) > 0 else 0.0
                attendance_trend = recent_attendance - older_attendance
            else:
                attendance_trend = 0.0
            
            # Attendance momentum (recent change rate)
            if len(df) >= 7:
                recent_7 = df.tail(7)['attended'].values
                older_7 = df.iloc[-14:-7]['attended'].values if len(df) >= 14 else df.iloc[:7]['attended'].values
                attendance_momentum = float(recent_7.mean() - older_7.mean()) * 100 if len(older_7) > 0 else 0.0
            else:
                attendance_momentum = 0.0
            
            # Attendance volatility (standard deviation of weekly attendance)
            if len(df) >= 7:
                # Group by week
                df['week'] = df['date'].dt.isocalendar().week
                weekly_attendance = df.groupby('week')['attended'].mean() * 100
                attendance_volatility = float(weekly_attendance.std()) if len(weekly_attendance) > 1 else 0.0
            else:
                attendance_volatility = 0.0
            
            # Recent absent days (last 14 days)
            recent_days = df.tail(14)
            recent_absent_days = len(recent_days[recent_days['status'] == 'absent'])
            
            # Consecutive absences (max streak)
            consecutive_absences = 0
            max_streak = 0
            for status in df['status'].values:
                if status == 'absent':
                    consecutive_absences += 1
                    max_streak = max(max_streak, consecutive_absences)
                else:
                    consecutive_absences = 0
            consecutive_absences = max_streak
            
            # Rolling averages
            attendance_rolling_avg_7 = float(df.tail(7)['attended'].mean() * 100) if len(df) >= 7 else overall_attendance
            attendance_rolling_avg_14 = float(df.tail(14)['attended'].mean() * 100) if len(df) >= 14 else overall_attendance
            
            # Sudden drop detection (drop > 20% in last week vs previous week)
            sudden_drop_detected = False
            if len(df) >= 14:
                last_week = df.tail(7)['attended'].mean() * 100
                prev_week = df.iloc[-14:-7]['attended'].mean() * 100 if len(df) >= 14 else last_week
                if prev_week > 0 and (prev_week - last_week) > 20:
                    sudden_drop_detected = True
            
            # Late count
            late_count = len(df[df['status'] == 'late'])
            
            # Subject-wise attendance
            subject_attendance = {}
            if 'course_code' in df.columns:
                for course in df['course_code'].unique():
                    course_df = df[df['course_code'] == course]
                    course_total = len(course_df)
                    course_present = course_df['attended'].sum()
                    subject_attendance[course] = (course_present / course_total * 100) if course_total > 0 else 0.0
            
            return {
                'overall_attendance': float(overall_attendance),
                'attendance_trend': float(attendance_trend),
                'recent_absent_days': int(recent_absent_days),
                'late_count': int(late_count),
                'subject_attendance': {k: float(v) for k, v in subject_attendance.items()},
                'attendance_volatility': attendance_volatility,
                'attendance_momentum': attendance_momentum,
                'consecutive_absences': consecutive_absences,
                'attendance_rolling_avg_7': attendance_rolling_avg_7,
                'attendance_rolling_avg_14': attendance_rolling_avg_14,
                'sudden_drop_detected': sudden_drop_detected
            }
        except Exception as e:
            logger.error(f"Error calculating attendance features: {e}")
            return {
                'overall_attendance': 0.0,
                'attendance_trend': 0.0,
                'recent_absent_days': 0,
                'late_count': 0,
                'subject_attendance': {},
                'attendance_volatility': 0.0,
                'attendance_momentum': 0.0,
                'consecutive_absences': 0,
                'attendance_rolling_avg_7': 0.0,
                'attendance_rolling_avg_14': 0.0,
                'sudden_drop_detected': False
            }
    
    def detect_behavioral_anomalies(
        self,
        academic_records: List[Dict[str, Any]],
        attendance_records: List[Dict[str, Any]],
        previous_risk_score: float = 0.0
    ) -> Dict[str, Any]:
        """Detect sudden behavioral changes."""
        try:
            anomalies = {
                'sudden_behavior_change': False,
                'assignment_submissions_on_time': 100.0,  # Default assumption
                'participation_score': 50.0  # Default assumption
            }
            
            # Check for sudden GPA drop
            if academic_records and len(academic_records) >= 2:
                recent_gpa = academic_records[-1].get('gpa', 0.0)
                previous_gpa = academic_records[-2].get('gpa', 0.0)
                gpa_drop = previous_gpa - recent_gpa
                
                if gpa_drop > 0.5:  # Significant drop
                    anomalies['sudden_behavior_change'] = True
            
            # Check for sudden attendance drop
            if attendance_records and len(attendance_records) >= 14:
                recent_attendance = self.calculate_attendance_features(
                    attendance_records[-14:]
                )
                older_attendance = self.calculate_attendance_features(
                    attendance_records[:-14] if len(attendance_records) > 14 else attendance_records
                )
                
                drop = older_attendance['overall_attendance'] - recent_attendance['overall_attendance']
                if drop > 20:  # 20% drop
                    anomalies['sudden_behavior_change'] = True
            
            # Estimate assignment submissions (based on academic performance variance)
            if academic_records:
                grades = [r.get('grade', 0) for r in academic_records]
                if len(grades) >= 3:
                    # High variance might indicate irregular submissions
                    variance = np.var(grades)
                    submissions_score = max(0, 100 - (variance / 10))
                    anomalies['assignment_submissions_on_time'] = float(submissions_score)
            
            # Participation score (based on attendance consistency)
            if attendance_records:
                # More consistent attendance = higher participation
                attendance_rate = self.calculate_attendance_features(attendance_records)['overall_attendance']
                anomalies['participation_score'] = float(attendance_rate)
            
            return anomalies
        except Exception as e:
            logger.error(f"Error detecting behavioral anomalies: {e}")
            return {
                'sudden_behavior_change': False,
                'assignment_submissions_on_time': 100.0,
                'participation_score': 50.0
            }
    
    def engineer_features(
        self,
        academic_records: List[Dict[str, Any]],
        attendance_records: List[Dict[str, Any]],
        previous_risk_score: float = 0.0,
        warning_count: int = 0,
        intervention_count: int = 0,
        enrollment_date: Optional[str] = None,
        student_data: Optional[Dict[str, Any]] = None
    ) -> FeatureSet:
        """Engineer complete feature set for ML model."""
        try:
            # Clean data first
            clean_academic, clean_attendance = self.clean_and_normalize_data(
                academic_records, attendance_records
            )
            
            # Calculate all features
            gpa_features = self.calculate_gpa_features(clean_academic)
            attendance_features = self.calculate_attendance_features(clean_attendance)
            behavioral_features = self.detect_behavioral_anomalies(
                clean_academic, clean_attendance, previous_risk_score
            )
            
            # Calculate years enrolled
            years_enrolled = 0.0
            if enrollment_date:
                try:
                    from datetime import datetime
                    enroll_date = datetime.strptime(enrollment_date, '%Y-%m-%d')
                    years_enrolled = (datetime.now() - enroll_date).days / 365.0
                except:
                    pass
            
            # Build feature set with all features
            feature_set = FeatureSet(
                # Academic
                current_gpa=gpa_features['current_gpa'],
                gpa_trend=gpa_features['gpa_trend'],
                gpa_variance=gpa_features['gpa_variance'],
                recent_grades=gpa_features['recent_grades'],
                failed_courses_count=gpa_features['failed_courses_count'],
                credits_completed=gpa_features['credits_completed'],
                gpa_momentum=gpa_features.get('gpa_momentum', 0.0),
                gpa_acceleration=gpa_features.get('gpa_acceleration', 0.0),
                gpa_rolling_avg_3=gpa_features.get('gpa_rolling_avg_3', 0.0),
                gpa_rolling_avg_6=gpa_features.get('gpa_rolling_avg_6', 0.0),
                low_grade_count=gpa_features.get('low_grade_count', 0),
                subject_variance=gpa_features.get('subject_variance', 0.0),
                
                # Attendance
                overall_attendance=attendance_features['overall_attendance'],
                attendance_trend=attendance_features['attendance_trend'],
                recent_absent_days=attendance_features['recent_absent_days'],
                late_count=attendance_features['late_count'],
                subject_attendance=attendance_features['subject_attendance'],
                attendance_volatility=attendance_features.get('attendance_volatility', 0.0),
                attendance_momentum=attendance_features.get('attendance_momentum', 0.0),
                consecutive_absences=attendance_features.get('consecutive_absences', 0),
                attendance_rolling_avg_7=attendance_features.get('attendance_rolling_avg_7', 0.0),
                attendance_rolling_avg_14=attendance_features.get('attendance_rolling_avg_14', 0.0),
                sudden_drop_detected=attendance_features.get('sudden_drop_detected', False),
                
                # Behavioral
                assignment_submissions_on_time=behavioral_features['assignment_submissions_on_time'],
                sudden_behavior_change=behavioral_features['sudden_behavior_change'],
                participation_score=behavioral_features['participation_score'],
                
                # Historical
                previous_risk_score=previous_risk_score,
                warning_count=warning_count,
                intervention_count=intervention_count,
                years_enrolled=years_enrolled,
                
                # Demographic (if available)
                is_first_generation=student_data.get('is_first_generation', False) if student_data else False
            )
            
            return feature_set
        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            return FeatureSet()


# Global processor instance
processor = DataProcessor()
