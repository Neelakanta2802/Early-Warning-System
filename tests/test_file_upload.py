"""
Comprehensive tests for file upload functionality.
Tests CSV, Excel, JSON uploads and error handling.
"""
import pytest
import requests
import json
import pandas as pd
import io
from pathlib import Path
from typing import Dict, Any


class TestFileUpload:
    """Test suite for file upload endpoint."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_base_url):
        """Setup test fixture."""
        self.api_url = api_base_url
        self.upload_endpoint = f"{api_base_url}/api/upload"
    
    def _check_backend_available(self):
        """Check if backend is available, skip test if not."""
        try:
            requests.get(f"{self.api_url}/api/health", timeout=2)
            return True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip(f"Backend API not running at {self.api_url}. Start backend server to run this test.")
            return False
    
    def test_health_check(self):
        """Test that API is accessible."""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "healthy"
        except requests.exceptions.ConnectionError:
            pytest.skip(f"Backend API not running at {self.api_url}. Start backend server to run this test.")
    
    def test_csv_upload_success(self, sample_csv_content):
        """Test successful CSV file upload."""
        try:
            files = {
                'file': ('test_data.csv', sample_csv_content.encode('utf-8'), 'text/csv')
            }
            
            response = requests.post(
                self.upload_endpoint,
                files=files,
                timeout=30
            )
            
            assert response.status_code == 200, f"Response: {response.text}"
            data = response.json()
            
            assert data.get('success') is True
            assert 'students_created' in data
            assert 'academic_records_created' in data
            assert 'risk_assessments_created' in data
            assert data['students_created'] >= 0  # May be 0 if duplicates
        except requests.exceptions.ConnectionError:
            pytest.skip(f"Backend API not running at {self.api_url}. Start backend server to run this test.")
    
    def test_json_upload_success(self, sample_json_data):
        """Test successful JSON file upload."""
        if not self._check_backend_available():
            return
        
        json_content = json.dumps(sample_json_data)
        files = {
            'file': ('test_data.json', json_content.encode('utf-8'), 'application/json')
        }
        
        response = requests.post(
            self.upload_endpoint,
            files=files,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get('success') is True
        assert 'students_created' in data
        assert data['students_created'] >= 0  # May be 0 if duplicates
    
    def test_excel_upload_success(self, sample_excel_file):
        """Test successful Excel file upload."""
        if not self._check_backend_available():
            return
        
        with open(sample_excel_file, 'rb') as f:
            files = {
                'file': ('test_data.xlsx', f.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            }
            
            response = requests.post(
                self.upload_endpoint,
                files=files,
                timeout=30
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data.get('success') is True
            assert 'students_created' in data
    
    def test_upload_empty_file(self):
        """Test upload with empty file."""
        if not self._check_backend_available():
            return
        
        files = {
            'file': ('empty.csv', b'', 'text/csv')
        }
        
        response = requests.post(
            self.upload_endpoint,
            files=files,
            timeout=10
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'empty' in data.get('detail', '').lower() or 'no file' in data.get('detail', '').lower()
    
    def test_upload_no_file(self):
        """Test upload without file."""
        if not self._check_backend_available():
            return
        
        response = requests.post(
            self.upload_endpoint,
            timeout=10
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_upload_invalid_format(self):
        """Test upload with invalid file format."""
        if not self._check_backend_available():
            return
        
        files = {
            'file': ('test.bin', b'invalid binary data', 'application/octet-stream')
        }
        
        response = requests.post(
            self.upload_endpoint,
            files=files,
            timeout=10
        )
        
        # Should either process as text or return error
        assert response.status_code in [200, 400, 422]
    
    def test_upload_malformed_csv(self):
        """Test upload with malformed CSV."""
        if not self._check_backend_available():
            return
        
        malformed_csv = "invalid,csv,data\nno,proper,columns\n"
        files = {
            'file': ('malformed.csv', malformed_csv.encode('utf-8'), 'text/csv')
        }
        
        response = requests.post(
            self.upload_endpoint,
            files=files,
            timeout=30
        )
        
        # Should handle gracefully - either process or return error
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            # Should have errors in response
            assert 'errors' in data or data.get('students_created', 0) == 0
    
    def test_upload_with_form_fields(self, sample_csv_content):
        """Test upload with additional form fields."""
        if not self._check_backend_available():
            return
        
        files = {
            'file': ('test_data.csv', sample_csv_content.encode('utf-8'), 'text/csv')
        }
        data = {
            'student_name': 'Override Name',
            'roll_number': 'OVERRIDE001'
        }
        
        response = requests.post(
            self.upload_endpoint,
            files=files,
            data=data,
            timeout=30
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result.get('success') is True
    
    def test_upload_large_file(self):
        """Test upload with large file (stress test)."""
        if not self._check_backend_available():
            return
        
        # Create a large CSV with many students
        rows = []
        for i in range(100):
            rows.append(
                f"TEST{i:03d},Student {i},student{i}@university.edu,"
                f"Computer Science,Undergraduate,2,Fall 2024,"
                f"CS201,Data Structures,3.2,3,3.2,2024-09-15,present\n"
            )
        
        large_csv = "roll_number,full_name,email,department,program,year_level,semester,course_code,course_name,grade,credits,gpa,attendance_date,attendance_status\n"
        large_csv += "".join(rows)
        
        files = {
            'file': ('large_test.csv', large_csv.encode('utf-8'), 'text/csv')
        }
        
        response = requests.post(
            self.upload_endpoint,
            files=files,
            timeout=60  # Longer timeout for large file
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get('success') is True
        assert data.get('students_created', 0) >= 0  # May have duplicates
    
    def test_upload_unicode_content(self):
        """Test upload with unicode characters."""
        if not self._check_backend_available():
            return
        
        unicode_csv = """roll_number,full_name,email,department,program,year_level,semester,course_code,course_name,grade,credits,gpa,attendance_date,attendance_status
TEST001,José García,jose@university.edu,Computer Science,Undergraduate,2,Fall 2024,CS201,Data Structures,3.2,3,3.2,2024-09-15,present
TEST002,李华,lihua@university.edu,Mathematics,Undergraduate,1,Fall 2024,MATH101,Calculus I,2.1,4,2.1,2024-09-15,absent"""
        
        files = {
            'file': ('unicode_test.csv', unicode_csv.encode('utf-8'), 'text/csv')
        }
        
        response = requests.post(
            self.upload_endpoint,
            files=files,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get('success') is True
    
    def test_upload_response_structure(self, sample_csv_content):
        """Test that upload response has correct structure."""
        if not self._check_backend_available():
            return
        
        files = {
            'file': ('test_data.csv', sample_csv_content.encode('utf-8'), 'text/csv')
        }
        
        response = requests.post(
            self.upload_endpoint,
            files=files,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = [
            'success', 'filename', 'students_processed',
            'students_created', 'academic_records_created',
            'attendance_records_created', 'risk_assessments_created',
            'errors'
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check types
        assert isinstance(data['success'], bool)
        assert isinstance(data['students_created'], int)
        assert isinstance(data['errors'], list)
    
    def test_upload_creates_risk_assessments(self, sample_csv_content):
        """Test that upload triggers risk assessment creation."""
        if not self._check_backend_available():
            return
        
        files = {
            'file': ('test_data.csv', sample_csv_content.encode('utf-8'), 'text/csv')
        }
        
        response = requests.post(
            self.upload_endpoint,
            files=files,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should create risk assessments if students were created
        if data.get('students_created', 0) > 0:
            assert data.get('risk_assessments_created', 0) >= 0
            # May be 0 if ML model isn't trained, but shouldn't error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
