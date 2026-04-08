#!/usr/bin/env python3
"""
Test the actual upload endpoint with a real CSV file to see what's happening.
"""
import sys
import requests
import json
from pathlib import Path

# Test file path
test_file = Path(__file__).parent.parent / "mock_students_data.csv"

if not test_file.exists():
    print(f"[ERROR] Test file not found: {test_file}")
    print("   Using a simple test instead...")
    # Create a simple test CSV
    test_csv = "student_id,full_name,email,department\nTEST001,Test Student,test@example.com,Test"
    test_file = Path(__file__).parent / "test_upload.csv"
    test_file.write_text(test_csv)

print("=" * 70)
print("TESTING UPLOAD ENDPOINT")
print("=" * 70)
print()

print(f"Test file: {test_file}")
print(f"File exists: {test_file.exists()}")
print()

# Read file content
with open(test_file, 'rb') as f:
    file_content = f.read()

print(f"File size: {len(file_content)} bytes")
print()

# Make request to upload endpoint
url = "http://localhost:8000/api/upload"
print(f"Uploading to: {url}")
print()

files = {
    'file': (test_file.name, file_content, 'text/csv')
}

try:
    response = requests.post(url, files=files, timeout=30)
    print(f"Response status: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        print("Response JSON:")
        print(json.dumps(result, indent=2))
        print()
        
        print("=" * 70)
        print("ANALYSIS")
        print("=" * 70)
        print()
        
        students_created = result.get('students_created', 0)
        rows_processed = result.get('rows_processed', 0)
        students_processed = result.get('students_processed', 0)
        errors = result.get('errors', [])
        
        print(f"students_created: {students_created}")
        print(f"rows_processed: {rows_processed}")
        print(f"students_processed: {students_processed}")
        print(f"errors count: {len(errors)}")
        print()
        
        if students_created == 0 and (rows_processed > 0 or students_processed > 0):
            print("[WARN] This will trigger the 'No Students Created' warning!")
            print()
            print("Possible causes:")
            print("1. All rows failed validation (missing roll_number or name)")
            print("2. All students already exist (duplicate student_id)")
            print("3. db.create_student() returning None for all rows")
            print("4. RLS policies blocking inserts (even with service_role)")
            print()
        
        if errors:
            print("ERRORS:")
            for i, error in enumerate(errors[:10], 1):  # Show first 10 errors
                print(f"  {i}. {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
            print()
    else:
        print(f"[ERROR] Upload failed with status {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to backend at http://localhost:8000")
    print("   Make sure the backend server is running!")
except Exception as e:
    print(f"[ERROR] Request failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
