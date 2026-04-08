"""
Pytest configuration and shared fixtures for Early Warning System tests.
"""
import pytest
import os
import sys
import json
import pandas as pd
import io
from typing import Dict, Any, List
from pathlib import Path

# Add project backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "project" / "backend"
sys.path.insert(0, str(backend_path))

# Set test environment variables BEFORE any imports
os.environ.setdefault("API_HOST", "0.0.0.0")
os.environ.setdefault("API_PORT", "8000")
os.environ.setdefault("LOG_LEVEL", "INFO")

# Set dummy Supabase credentials for tests that don't need real database
# Tests that need real DB will override these
os.environ.setdefault("SUPABASE_URL", "https://dummy-test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "dummy-test-key-for-testing-only")


@pytest.fixture
def api_base_url():
    """Base URL for API tests."""
    return os.environ.get("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
def test_data_dir():
    """Directory containing test data files."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def sample_student_data():
    """Sample student data for testing."""
    return {
        "student_id": "TEST001",
        "full_name": "Test Student",
        "email": "test.student@university.edu",
        "department": "Computer Science",
        "program": "BS Computer Science",
        "year_level": 2,
        "semester": "Fall 2024",
        "enrollment_date": "2023-09-01",
        "status": "active"
    }


@pytest.fixture
def sample_academic_record():
    """Sample academic record for testing."""
    return {
        "student_id": "TEST001",
        "semester": "Fall 2024",
        "course_code": "CS101",
        "course_name": "Introduction to Programming",
        "grade": 85.5,
        "credits": 3,
        "gpa": 3.4
    }


@pytest.fixture
def sample_attendance_record():
    """Sample attendance record for testing."""
    return {
        "student_id": "TEST001",
        "date": "2024-09-15",
        "status": "present",
        "course_code": "CS101",
        "semester": "Fall 2024"
    }


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing."""
    return """roll_number,full_name,email,department,program,year_level,semester,course_code,course_name,grade,credits,gpa,attendance_date,attendance_status
TEST001,Test Student,test@university.edu,Computer Science,Undergraduate,2,Fall 2024,CS201,Data Structures,3.2,3,3.2,2024-09-15,present
TEST002,Another Student,another@university.edu,Mathematics,Undergraduate,1,Fall 2024,MATH101,Calculus I,2.1,4,2.1,2024-09-15,absent"""


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return {
        "students": [
            {
                "student_id": "TEST001",
                "full_name": "Test Student One",
                "email": "test1@university.edu",
                "department": "Computer Science",
                "program": "BS Computer Science",
                "year_level": 2,
                "semester": "Fall 2024",
                "enrollment_date": "2023-09-01",
                "status": "active",
                "academic_records": [
                    {
                        "semester": "Fall 2024",
                        "course_code": "CS201",
                        "course_name": "Data Structures",
                        "grade": 85.5,
                        "credits": 3,
                        "gpa": 3.4
                    }
                ],
                "attendance_records": [
                    {
                        "date": "2024-09-15",
                        "status": "present",
                        "course_code": "CS201",
                        "semester": "Fall 2024"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_excel_file(tmp_path):
    """Create a sample Excel file for testing."""
    df = pd.DataFrame({
        'roll_number': ['TEST001', 'TEST002'],
        'full_name': ['Test Student', 'Another Student'],
        'email': ['test@university.edu', 'another@university.edu'],
        'department': ['Computer Science', 'Mathematics'],
        'program': ['Undergraduate', 'Undergraduate'],
        'year_level': [2, 1],
        'semester': ['Fall 2024', 'Fall 2024'],
        'course_code': ['CS201', 'MATH101'],
        'course_name': ['Data Structures', 'Calculus I'],
        'grade': [3.2, 2.1],
        'credits': [3, 4],
        'gpa': [3.2, 2.1],
        'attendance_date': ['2024-09-15', '2024-09-15'],
        'attendance_status': ['present', 'absent']
    })
    
    file_path = tmp_path / "test_data.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def mock_students_list():
    """List of mock students for testing."""
    return [
        {
            "student_id": f"TEST{i:03d}",
            "full_name": f"Test Student {i}",
            "email": f"test{i}@university.edu",
            "department": "Computer Science" if i % 2 == 0 else "Mathematics",
            "program": "BS Computer Science",
            "year_level": (i % 4) + 1,
            "semester": "Fall 2024",
            "enrollment_date": "2023-09-01",
            "status": "active"
        }
        for i in range(1, 11)  # 10 students
    ]


@pytest.fixture
def mock_risk_assessment():
    """Mock risk assessment for testing."""
    return {
        "student_id": "TEST001",
        "risk_level": "medium",
        "risk_score": 45.5,
        "confidence_level": 0.75,
        "factors": {
            "rule_score": 40.0,
            "ml_score": 50.0,
            "gpa_trend": -0.2
        },
        "explanation": "Student shows declining GPA trend",
        "prediction_date": "2024-09-15T10:00:00Z"
    }
