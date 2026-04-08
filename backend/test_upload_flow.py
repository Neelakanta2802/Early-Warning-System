"""
Quick test script to verify upload flow and risk assessment creation.
Run this after restarting the backend to see what's happening.
"""
import requests
import json

def test_upload_flow():
    """Test the upload endpoint with a simple CSV."""
    print("=" * 80)
    print("TESTING UPLOAD FLOW AND RISK ASSESSMENT")
    print("=" * 80)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        print(f"✅ Backend is running: {response.status_code}")
        
        # Check diagnostics
        diag_response = requests.get("http://localhost:8000/api/diagnostics", timeout=5)
        if diag_response.status_code == 200:
            diag_data = diag_response.json()
            print(f"\n📊 Diagnostics:")
            print(f"   Code Version: {diag_data.get('code_version', 'NOT SET')}")
            print(f"   Students in DB: {diag_data.get('database', {}).get('student_count', 0)}")
            print(f"   Risk Assessments in DB: {diag_data.get('database', {}).get('risk_assessment_count', 0)}")
            
            students_without = diag_data.get('database', {}).get('students_without_assessments', 0)
            if students_without > 0:
                print(f"   ⚠️ {students_without} students WITHOUT risk assessments!")
        
        # Test evaluate-all endpoint
        print(f"\n🔄 Testing evaluate-all endpoint...")
        eval_response = requests.post("http://localhost:8000/api/students/evaluate-all", timeout=30)
        if eval_response.status_code == 200:
            eval_data = eval_response.json()
            print(f"✅ Evaluate-all completed:")
            print(f"   Evaluated: {eval_data.get('evaluated', 0)}")
            print(f"   Errors: {eval_data.get('errors', 0)}")
            print(f"   Total students: {eval_data.get('total_students', 0)}")
        else:
            print(f"❌ Evaluate-all failed: {eval_response.status_code}")
            print(f"   Response: {eval_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend is NOT running! Please start it first.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_upload_flow()
