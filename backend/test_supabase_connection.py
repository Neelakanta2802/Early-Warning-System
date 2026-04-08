#!/usr/bin/env python3
"""
Test Supabase connection and credentials with actual database operations.
"""
import sys
from supabase import create_client, Client
from config import settings
import json
import base64

print("=" * 70)
print("SUPABASE CREDENTIALS VERIFICATION TEST")
print("=" * 70)
print()

# Check if credentials are loaded
print("1. CHECKING CREDENTIALS IN CONFIG")
print("-" * 70)
print(f"SUPABASE_URL: {settings.supabase_url}")
print(f"SUPABASE_KEY length: {len(settings.supabase_key)}")
print(f"SUPABASE_KEY starts with: {settings.supabase_key[:30]}...")
print()

# Verify key format
print("2. VERIFYING KEY FORMAT")
print("-" * 70)
try:
    # Decode JWT to check role
    parts = settings.supabase_key.split('.')
    if len(parts) >= 2:
        payload = parts[1]
        # Add padding
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        key_data = json.loads(decoded)
        role = key_data.get('role', 'unknown')
        ref = key_data.get('ref', 'unknown')
        print(f"Key Role: {role}")
        print(f"Project Ref: {ref}")
        if role == 'service_role':
            print("[OK] Key is a SERVICE ROLE key (correct for backend)")
        else:
            print(f"[ERROR] Key role is '{role}' (should be 'service_role')")
            print("   This key will NOT bypass RLS policies!")
    else:
        print("[ERROR] Key doesn't appear to be a valid JWT token")
except Exception as e:
    print(f"[WARN] Could not decode key: {e}")
print()

# Test connection
print("3. TESTING SUPABASE CONNECTION")
print("-" * 70)
try:
    client: Client = create_client(settings.supabase_url, settings.supabase_key)
    print("[OK] Supabase client created successfully")
except Exception as e:
    print(f"[ERROR] Failed to create Supabase client: {e}")
    sys.exit(1)
print()

# Test database access - Check if students table exists
print("4. TESTING DATABASE ACCESS")
print("-" * 70)
try:
    # Try to query students table
    response = client.table('students').select('id').limit(1).execute()
    print("[OK] Successfully queried 'students' table")
    print(f"   Found {len(response.data)} existing students")
except Exception as e:
    error_str = str(e)
    print(f"[ERROR] Failed to query 'students' table: {error_str}")
    
    if 'PGRST205' in error_str or 'not found' in error_str.lower():
        print()
        print("[WARN] ISSUE: 'students' table not found in schema cache")
        print("   This usually means:")
        print("   1. The table doesn't exist in your Supabase database")
        print("   2. The table exists but RLS is blocking access")
        print("   3. The schema hasn't been migrated")
        print()
        print("   SOLUTION: Run the database migration:")
        print("   - Check: project/supabase/migrations/")
        print("   - Or create the table manually in Supabase Dashboard")
    elif 'permission' in error_str.lower() or 'policy' in error_str.lower() or 'row level security' in error_str.lower():
        print()
        print("[WARN] ISSUE: Row Level Security (RLS) blocking access")
        print("   Even with service_role key, RLS might be blocking")
        print("   SOLUTION: Check RLS policies in Supabase Dashboard")
    elif 'JWT' in error_str or 'token' in error_str.lower() or 'unauthorized' in error_str.lower():
        print()
        print("[WARN] ISSUE: Authentication failed")
        print("   The SUPABASE_KEY might be invalid or expired")
        print("   SOLUTION: Get a new service_role key from Supabase Dashboard")
    else:
        print(f"   Full error: {error_str}")
print()

# Test INSERT operation
print("5. TESTING INSERT OPERATION (Dry Run)")
print("-" * 70)
import uuid as uuid_lib

test_student = {
    'id': str(uuid_lib.uuid4()),
    'student_id': 'TEST001',
    'full_name': 'Test Student',
    'email': 'test@example.com',
    'department': 'Test',
    'program': 'Test',
    'year_level': 1,
    'semester': 'Fall 2024',
    'enrollment_date': '2024-01-01',
    'status': 'active'
}

try:
    # Try to insert (this will fail if table doesn't exist or RLS blocks it)
    response = client.table('students').insert(test_student).execute()
    print("[OK] Successfully inserted test student")
    print(f"   Student ID: {response.data[0].get('id') if response.data else 'N/A'}")
    
    # Clean up - delete the test student
    test_id = test_student['id']
    try:
        client.table('students').delete().eq('id', test_id).execute()
        print("[OK] Test student cleaned up")
    except:
        print("[WARN] Could not clean up test student (may need manual deletion)")
        
except Exception as e:
    error_str = str(e)
    print(f"[ERROR] Failed to insert test student: {error_str}")
    
    if 'PGRST205' in error_str or 'not found' in error_str.lower():
        print()
        print("[ERROR] CRITICAL: 'students' table does not exist!")
        print("   You need to create the database schema first.")
        print()
        print("   STEPS TO FIX:")
        print("   1. Go to Supabase Dashboard → SQL Editor")
        print("   2. Run the migration from: project/supabase/migrations/")
        print("   3. Or use the SQL from: project/backend/database_migrations.sql")
    elif 'duplicate key' in error_str.lower() or 'unique constraint' in error_str.lower():
        print("[WARN] Test student already exists (this is OK, means table works)")
    elif 'permission' in error_str.lower() or 'policy' in error_str.lower():
        print()
        print("[ERROR] CRITICAL: RLS policies are blocking INSERT operations")
        print("   Even with service_role key, inserts are being blocked")
        print()
        print("   STEPS TO FIX:")
        print("   1. Go to Supabase Dashboard → Authentication → Policies")
        print("   2. Check RLS policies for 'students' table")
        print("   3. Ensure service_role can bypass RLS (it should by default)")
        print("   4. Or disable RLS for 'students' table temporarily for testing")
    else:
        print(f"   Full error details: {error_str}")
print()

# Check other required tables
print("6. CHECKING OTHER REQUIRED TABLES")
print("-" * 70)
required_tables = ['academic_records', 'attendance_records', 'risk_assessments', 'alerts', 'interventions']
for table in required_tables:
    try:
        response = client.table(table).select('id').limit(1).execute()
        print(f"[OK] Table '{table}' exists and is accessible")
    except Exception as e:
        error_str = str(e)
        if 'PGRST205' in error_str or 'not found' in error_str.lower():
            print(f"[ERROR] Table '{table}' does NOT exist")
        else:
            print(f"[WARN] Table '{table}' error: {error_str[:50]}...")
print()

# Final summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)

print()
print("RECOMMENDATIONS:")
print("1. Verify SUPABASE_KEY is the service_role key (not anon key)")
print("2. Check that database tables exist (run migrations)")
print("3. Verify RLS policies allow service_role operations")
print("4. Check Supabase Dashboard for any errors")
print()
print("Note: Review the test results above for specific issues.")
print()
print("=" * 70)
