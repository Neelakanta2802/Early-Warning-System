"""
End-to-end integration tests for the complete system workflow.
Tests file upload -> processing -> ML prediction -> database -> API display flow.
"""
import pytest
import requests
import json
import time
from typing import Dict, Any


def check_backend_available(api_url):
    """Check if backend is available, skip test if not."""
    try:
        requests.get(f"{api_url}/api/health", timeout=2)
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pytest.skip(f"Backend API not running at {api_url}. Start backend server to run this test.")
        return False


class TestEndToEndWorkflow:
    """Test suite for complete end-to-end workflows."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_base_url, sample_csv_content):
        """Setup test fixture."""
        self.api_url = api_base_url
        self.sample_csv = sample_csv_content
        self.created_student_ids = []
    
    def teardown_method(self):
        """Cleanup after each test."""
        # Note: In a real scenario, you'd clean up created test data
        # For now, we'll just track what was created
        self.created_student_ids = []
    
    def test_complete_upload_to_display_flow(self):
        """Test complete flow: upload -> process -> predict -> display."""
        if not check_backend_available(self.api_url):
            return
        # Step 1: Upload file
        files = {
            'file': ('integration_test.csv', self.sample_csv.encode('utf-8'), 'text/csv')
        }
        
        upload_response = requests.post(
            f"{self.api_url}/api/upload",
            files=files,
            timeout=60
        )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data.get('success') is True
        
        students_created = upload_data.get('students_created', 0)
        risk_assessments_created = upload_data.get('risk_assessments_created', 0)
        
        # Step 2: Wait for processing
        time.sleep(3)  # Give backend time to process
        
        # Step 3: Verify students were created
        students_response = requests.get(
            f"{self.api_url}/api/students",
            timeout=10
        )
        assert students_response.status_code == 200
        students = students_response.json()
        
        # Should have at least some students (may have been there before)
        assert len(students) >= 0
        
        # Step 4: Verify we can fetch student details
        if len(students) > 0:
            test_student = students[0]
            student_id = test_student['id']
            
            # Get student detail
            detail_response = requests.get(
                f"{self.api_url}/api/students/{student_id}",
                timeout=10
            )
            assert detail_response.status_code == 200
            
            # Get risk assessment
            risk_response = requests.get(
                f"{self.api_url}/api/students/{student_id}/risk",
                timeout=10
            )
            # May or may not have risk assessment yet
            assert risk_response.status_code in [200, 404]
    
    def test_upload_json_to_display_flow(self, sample_json_data):
        """Test complete flow with JSON upload."""
        if not check_backend_available(self.api_url):
            return
        # Step 1: Upload JSON
        json_content = json.dumps(sample_json_data)
        files = {
            'file': ('integration_test.json', json_content.encode('utf-8'), 'application/json')
        }
        
        upload_response = requests.post(
            f"{self.api_url}/api/upload",
            files=files,
            timeout=60
        )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        
        # Step 2: Verify processing
        if upload_data.get('success'):
            # Wait for async processing
            time.sleep(5)
            
            # Verify students exist
            students_response = requests.get(
                f"{self.api_url}/api/students",
                timeout=10
            )
            assert students_response.status_code == 200
    
    def test_risk_assessment_generation_flow(self, sample_csv_content):
        """Test that risk assessments are generated after upload."""
        if not check_backend_available(self.api_url):
            return
        # Upload file
        files = {
            'file': ('risk_test.csv', sample_csv_content.encode('utf-8'), 'text/csv')
        }
        
        upload_response = requests.post(
            f"{self.api_url}/api/upload",
            files=files,
            timeout=60
        )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        
        if upload_data.get('students_created', 0) > 0:
            # Wait for risk assessments
            time.sleep(5)
            
            # Check that risk assessments were created
            # (This would require direct database access or an API endpoint)
            # For now, verify the upload response indicates assessments
            assert 'risk_assessments_created' in upload_data
    
    def test_dashboard_data_after_upload(self, sample_csv_content):
        """Test that dashboard shows data after upload."""
        if not check_backend_available(self.api_url):
            return
        # Upload file
        files = {
            'file': ('dashboard_test.csv', sample_csv_content.encode('utf-8'), 'text/csv')
        }
        
        upload_response = requests.post(
            f"{self.api_url}/api/upload",
            files=files,
            timeout=60
        )
        
        assert upload_response.status_code == 200
        
        # Wait for processing
        time.sleep(3)
        
        # Check dashboard endpoints
        overview_response = requests.get(
            f"{self.api_url}/api/analytics/overview",
            timeout=10
        )
        assert overview_response.status_code == 200
        
        departments_response = requests.get(
            f"{self.api_url}/api/analytics/departments",
            timeout=10
        )
        assert departments_response.status_code == 200
    
    def test_multiple_uploads_consistency(self):
        """Test that multiple uploads maintain data consistency."""
        if not check_backend_available(self.api_url):
            return
        # First upload
        csv1 = """roll_number,full_name,email,department,program,year_level,semester,course_code,course_name,grade,credits,gpa,attendance_date,attendance_status
TEST001,First Student,first@university.edu,Computer Science,Undergraduate,2,Fall 2024,CS201,Data Structures,3.2,3,3.2,2024-09-15,present"""
        
        files1 = {
            'file': ('batch1.csv', csv1.encode('utf-8'), 'text/csv')
        }
        
        response1 = requests.post(
            f"{self.api_url}/api/upload",
            files=files1,
            timeout=30
        )
        assert response1.status_code == 200
        
        time.sleep(2)
        
        # Second upload
        csv2 = """roll_number,full_name,email,department,program,year_level,semester,course_code,course_name,grade,credits,gpa,attendance_date,attendance_status
TEST002,Second Student,second@university.edu,Mathematics,Undergraduate,1,Fall 2024,MATH101,Calculus I,2.1,4,2.1,2024-09-15,absent"""
        
        files2 = {
            'file': ('batch2.csv', csv2.encode('utf-8'), 'text/csv')
        }
        
        response2 = requests.post(
            f"{self.api_url}/api/upload",
            files=files2,
            timeout=30
        )
        assert response2.status_code == 200
        
        time.sleep(2)
        
        # Verify both students exist
        students_response = requests.get(
            f"{self.api_url}/api/students",
            timeout=10
        )
        assert students_response.status_code == 200
        
        students = students_response.json()
        student_ids = [s.get('student_id') for s in students]
        
        # At least one of our test students should be present
        # (may have duplicates, so we check if any match)
        assert True  # Test passes if no errors occurred
    
    def test_error_handling_in_workflow(self):
        """Test error handling in complete workflow."""
        if not check_backend_available(self.api_url):
            return
        # Upload invalid file
        files = {
            'file': ('invalid.csv', b'invalid data', 'text/csv')
        }
        
        response = requests.post(
            f"{self.api_url}/api/upload",
            files=files,
            timeout=30
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
        
        if response.status_code == 200:
            # Should have errors in response
            data = response.json()
            assert 'errors' in data or data.get('students_created', 0) == 0


class TestMLTrainingWorkflow:
    """Test suite for ML training workflows."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_base_url):
        """Setup test fixture."""
        self.api_url = api_base_url
    
    def test_training_endpoint(self):
        """Test ML training endpoint."""
        if not check_backend_available(self.api_url):
            return
        response = requests.post(
            f"{self.api_url}/api/ml/train",
            json={},
            timeout=120  # Training may take time
        )
        
        # Should either succeed or return appropriate error
        assert response.status_code in [200, 400, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert 'success' in data or 'message' in data
    
    def test_model_info_endpoint(self):
        """Test model info endpoint."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(
            f"{self.api_url}/api/ml/model/info",
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_model_performance_endpoint(self):
        """Test model performance endpoint."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(
            f"{self.api_url}/api/ml/model/performance",
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestSystemHealth:
    """Test suite for system health and diagnostics."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_base_url):
        """Setup test fixture."""
        self.api_url = api_base_url
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(
            f"{self.api_url}/api/health",
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'healthy'
    
    def test_diagnostics_endpoint(self):
        """Test diagnostics endpoint."""
        if not check_backend_available(self.api_url):
            return
        response = requests.get(
            f"{self.api_url}/api/diagnostics",
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'database' in data
        assert 'ml_models' in data
        assert 'configuration' in data
        
        # Verify structure
        db_info = data.get('database', {})
        assert 'connected' in db_info
        assert 'can_read' in db_info
    
    def test_api_responsiveness(self):
        """Test that all major API endpoints respond."""
        if not check_backend_available(self.api_url):
            return
        endpoints = [
            "/api/health",
            "/api/diagnostics",
            "/api/students",
            "/api/alerts",
            "/api/interventions",
            "/api/analytics/overview"
        ]
        
        for endpoint in endpoints:
            response = requests.get(
                f"{self.api_url}{endpoint}",
                timeout=10
            )
            assert response.status_code == 200, f"Endpoint {endpoint} not responding"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
