#!/usr/bin/env python3
"""
Test real student insert with the exact same code the backend uses.
"""
import sys
from database import db
from config import settings
import uuid
from datetime import datetime

print("=" * 70)
print("REAL STUDENT INSERT TEST")
print("=" * 70)
print()

# Check database connection
if db.client is None:
    print("[ERROR] Database client is None!")
    print("   This means Supabase connection failed during initialization")
    sys.exit(1)

print("[OK] Database client is initialized")
print()

# Test student data (same structure as backend uses)
test_student = {
    'id': str(uuid.uuid4()),
    'student_id': 'TEST001',
    'full_name': 'Test Student',
    'email': 'test@example.com',
    'department': 'Test',
    'program': 'Test',
    'year_level': 1,
    'semester': 'Fall 2024',
    'enrollment_date': datetime.utcnow().date().isoformat(),
    'status': 'active'
}

print("Attempting to create student with data:")
print(f"  student_id: {test_student['student_id']}")
print(f"  full_name: {test_student['full_name']}")
print(f"  email: {test_student['email']}")
print()

# Try to create student using the exact same method as backend
print("Calling db.create_student()...")
result = db.create_student(test_student)

if result:
    print("[OK] Student created successfully!")
    print(f"   Created student ID: {result.get('id')}")
    print(f"   Student ID (roll): {result.get('student_id')}")
    print()
    
    # Try to fetch it back
    print("Verifying student exists...")
    fetched = db.get_student_by_roll_number('TEST001')
    if fetched:
        print("[OK] Student can be fetched back")
        print(f"   Fetched student: {fetched.get('full_name')}")
    else:
        print("[WARN] Student was created but cannot be fetched back")
    
    # Clean up
    print()
    print("Cleaning up test student...")
    try:
        db.client.table('students').delete().eq('id', result.get('id')).execute()
        print("[OK] Test student deleted")
    except Exception as e:
        print(f"[WARN] Could not delete test student: {e}")
else:
    print("[ERROR] Student creation returned None!")
    print()
    print("This means db.create_student() failed silently.")
    print("Check the backend logs for detailed error messages.")
    print()
    print("Possible causes:")
    print("1. RLS policies blocking insert")
    print("2. Missing required fields")
    print("3. Database constraint violations")
    print("4. Service role key not bypassing RLS")
    sys.exit(1)

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
