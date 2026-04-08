"""
Comprehensive tests for UI display functionality.
Tests API endpoints used by frontend to display students, risk assessments, and dashboard data.
"""
import pytest
import requests
import time
from typing import Dict, Any, List


def check_backend_available(api_url):
    """Check if backend is available, skip test if not."""
    try:
        requests.get(f"{api_url}/api/health", timeout=2)
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pytest.skip(f"Backend API not running at {api_url}. Start backend server to run this test.")
        return False


class TestStudentsAPI:
    """Test suite for students API endpoints used by UI."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_base_url):
        """Setup test fixture."""
        self.api_url = api_base_url
        self.students_endpoint = f"{api_base_url}/api/students"
    
    def test_get_all_students(self):
        """Test fetching all students."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(self.students_endpoint, timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # If students exist, verify structure
        if len(data) > 0:
            student = data[0]
            required_fields = ['id', 'student_id', 'full_name', 'email', 'department']
            for field in required_fields:
                assert field in student, f"Missing field: {field}"
    
    def test_get_students_with_filters(self):
        """Test fetching students with filters."""
        if not check_backend_available(self.api_url):
            return
        # Test department filter
        response = requests.get(
            self.students_endpoint,
            params={'department': 'Computer Science'},
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # If results, verify filter worked
        if len(data) > 0:
            for student in data:
                assert student.get('department') == 'Computer Science'
    
    def test_get_student_by_id(self):
        """Test fetching a specific student by ID."""
        if not check_backend_available(self.api_url):
            return
        # First get all students to find an ID
        response = requests.get(self.students_endpoint, timeout=10)
        assert response.status_code == 200
        students = response.json()
        
        if len(students) > 0:
            student_id = students[0]['id']
            
            # Get specific student
            response = requests.get(
                f"{self.students_endpoint}/{student_id}",
                timeout=10
            )
            
            assert response.status_code == 200
            student = response.json()
            assert student['id'] == student_id
    
    def test_get_student_risk_assessment(self):
        """Test fetching student risk assessment."""
        if not check_backend_available(self.api_url):
            return
        # First get all students
        response = requests.get(self.students_endpoint, timeout=10)
        assert response.status_code == 200
        students = response.json()
        
        if len(students) > 0:
            student_id = students[0]['id']
            
            # Get risk assessment
            response = requests.get(
                f"{self.students_endpoint}/{student_id}/risk",
                timeout=10
            )
            
            assert response.status_code == 200
            risk_data = response.json()
            
            # Should have risk information
            assert 'risk_level' in risk_data or 'assessment' in risk_data
    
    def test_students_response_structure(self):
        """Test that students API response has correct structure."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(self.students_endpoint, timeout=10)
        assert response.status_code == 200
        
        students = response.json()
        assert isinstance(students, list)
        
        for student in students:
            assert 'id' in student
            assert 'full_name' in student
            assert 'student_id' in student


class TestDashboardAPI:
    """Test suite for dashboard API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_base_url):
        """Setup test fixture."""
        self.api_url = api_base_url
    
    def test_analytics_overview(self):
        """Test analytics overview endpoint."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(
            f"{self.api_url}/api/analytics/overview",
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have analytics data
        assert isinstance(data, dict)
    
    def test_analytics_trends(self):
        """Test analytics trends endpoint."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(
            f"{self.api_url}/api/analytics/trends",
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_analytics_departments(self):
        """Test department analytics endpoint."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(
            f"{self.api_url}/api/analytics/departments",
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_analytics_courses(self):
        """Test course analytics endpoint."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(
            f"{self.api_url}/api/analytics/courses",
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestAlertsAPI:
    """Test suite for alerts API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_base_url):
        """Setup test fixture."""
        self.api_url = api_base_url
        self.alerts_endpoint = f"{self.api_url}/api/alerts"
    
    def test_get_all_alerts(self):
        """Test fetching all alerts."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(self.alerts_endpoint, timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # If alerts exist, verify structure
        if len(data) > 0:
            alert = data[0]
            assert 'id' in alert
            assert 'student_id' in alert
            assert 'alert_type' in alert
            assert 'severity' in alert
    
    def test_get_alerts_with_filters(self):
        """Test fetching alerts with filters."""
        if not check_backend_available(self.api_url):
            return
        # Test by severity
        response = requests.get(
            self.alerts_endpoint,
            params={'severity': 'high'},
            timeout=10
        )
        
        assert response.status_code == 200
        alerts = response.json()
        assert isinstance(alerts, list)


class TestInterventionsAPI:
    """Test suite for interventions API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_base_url):
        """Setup test fixture."""
        self.api_url = api_base_url
        self.interventions_endpoint = f"{self.api_url}/api/interventions"
    
    def test_get_all_interventions(self):
        """Test fetching all interventions."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(self.interventions_endpoint, timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # If interventions exist, verify structure
        if len(data) > 0:
            intervention = data[0]
            assert 'id' in intervention
            assert 'student_id' in intervention
            assert 'intervention_type' in intervention
            assert 'status' in intervention
    
    def test_get_interventions_with_filters(self):
        """Test fetching interventions with filters."""
        if not check_backend_available(self.api_url):
            return
        # Test by status
        response = requests.get(
            self.interventions_endpoint,
            params={'status': 'pending'},
            timeout=10
        )
        
        assert response.status_code == 200
        interventions = response.json()
        assert isinstance(interventions, list)


class TestStudentProfileAPI:
    """Test suite for student profile endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_base_url):
        """Setup test fixture."""
        self.api_url = api_base_url
    
    def test_get_student_profile_data(self):
        """Test fetching complete student profile data."""
        if not check_backend_available(self.api_url):
            return
        # First get a student ID
        response = requests.get(f"{self.api_url}/api/students", timeout=10)
        assert response.status_code == 200
        students = response.json()
        
        if len(students) > 0:
            student_id = students[0]['id']
            
            # Get student profile (should include risk, academic records, etc.)
            student_response = requests.get(
                f"{self.api_url}/api/students/{student_id}",
                timeout=10
            )
            assert student_response.status_code == 200
            
            # Get risk assessment
            risk_response = requests.get(
                f"{self.api_url}/api/students/{student_id}/risk",
                timeout=10
            )
            assert risk_response.status_code == 200
    
    def test_get_student_trend(self):
        """Test fetching student risk trend over time."""
        if not check_backend_available(self.api_url):
            return
        # First get a student ID
        response = requests.get(f"{self.api_url}/api/students", timeout=10)
        assert response.status_code == 200
        students = response.json()
        
        if len(students) > 0:
            student_id = students[0]['id']
            
            # Get trend
            response = requests.get(
                f"{self.api_url}/api/students/{student_id}/trend",
                timeout=10
            )
            
            assert response.status_code == 200
            trend_data = response.json()
            assert isinstance(trend_data, dict) or isinstance(trend_data, list)


class TestDataDisplayIntegration:
    """Integration tests for data display workflows."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_base_url):
        """Setup test fixture."""
        self.api_url = api_base_url
    
    def test_dashboard_data_availability(self):
        """Test that all dashboard data endpoints are accessible."""
        if not check_backend_available(self.api_url):
            return
        endpoints = [
            "/api/analytics/overview",
            "/api/analytics/trends",
            "/api/analytics/departments",
            "/api/students",
            "/api/alerts",
            "/api/interventions"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
    
    def test_students_page_data_flow(self):
        """Test complete data flow for students page."""
        if not check_backend_available(self.api_url):
            return
        # Get students
        response = requests.get(f"{self.api_url}/api/students", timeout=10)
        assert response.status_code == 200
        students = response.json()
        
        # For each student, verify we can get risk assessment
        for student in students[:5]:  # Test first 5 students
            student_id = student['id']
            risk_response = requests.get(
                f"{self.api_url}/api/students/{student_id}/risk",
                timeout=10
            )
            # Should either succeed or return 404 if no assessment yet
            assert risk_response.status_code in [200, 404]
    
    def test_data_consistency(self):
        """Test that data is consistent across related endpoints."""
        if not check_backend_available(self.api_url):
            return
        # Get students
        students_response = requests.get(f"{self.api_url}/api/students", timeout=10)
        assert students_response.status_code == 200
        students = students_response.json()
        
        if len(students) > 0:
            student = students[0]
            student_id = student['id']
            
            # Get student detail
            detail_response = requests.get(
                f"{self.api_url}/api/students/{student_id}",
                timeout=10
            )
            assert detail_response.status_code == 200
            detail = detail_response.json()
            
            # IDs should match
            assert detail['id'] == student['id']
            assert detail['student_id'] == student['student_id']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
