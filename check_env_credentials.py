#!/usr/bin/env python3
"""
Check if frontend and backend environment credentials match.
"""
import os
from pathlib import Path

# Get project root
project_root = Path(__file__).parent
fe_env = project_root / ".env"
be_env = project_root / "backend" / ".env"

print("=" * 60)
print("ENVIRONMENT CREDENTIALS CHECK")
print("=" * 60)
print()

# Check if files exist
fe_exists = fe_env.exists()
be_exists = be_env.exists()

print(f"Frontend .env exists: {fe_exists}")
print(f"Backend .env exists: {be_exists}")
print()

if not fe_exists:
    print("[ERROR] Frontend .env file not found!")
if not be_exists:
    print("[ERROR] Backend .env file not found!")

if not fe_exists or not be_exists:
    exit(1)

# Read frontend env
fe_vars = {}
with open(fe_env, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            fe_vars[key.strip()] = value.strip()

# Read backend env
be_vars = {}
with open(be_env, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            be_vars[key.strip()] = value.strip()

print("FRONTEND VARIABLES:")
print("-" * 60)
fe_url = fe_vars.get('VITE_SUPABASE_URL', 'NOT SET')
fe_anon = fe_vars.get('VITE_SUPABASE_ANON_KEY', 'NOT SET')
fe_api = fe_vars.get('VITE_API_URL', 'NOT SET (defaults to http://localhost:8000)')

print(f"  VITE_SUPABASE_URL: {fe_url[:50]}..." if len(fe_url) > 50 else f"  VITE_SUPABASE_URL: {fe_url}")
print(f"  VITE_SUPABASE_ANON_KEY: {fe_anon[:30]}..." if len(fe_anon) > 30 and fe_anon != 'NOT SET' else f"  VITE_SUPABASE_ANON_KEY: {fe_anon}")
print(f"  VITE_API_URL: {fe_api}")
print()

print("BACKEND VARIABLES:")
print("-" * 60)
be_url = be_vars.get('SUPABASE_URL', 'NOT SET')
be_key = be_vars.get('SUPABASE_KEY', 'NOT SET')
be_anon = be_vars.get('SUPABASE_ANON_KEY', 'NOT SET (optional)')

print(f"  SUPABASE_URL: {be_url[:50]}..." if len(be_url) > 50 else f"  SUPABASE_URL: {be_url}")
print(f"  SUPABASE_KEY: {be_key[:30]}..." if len(be_key) > 30 and be_key != 'NOT SET' else f"  SUPABASE_KEY: {be_key}")
print(f"  SUPABASE_ANON_KEY: {be_anon[:30]}..." if len(be_anon) > 30 and be_anon != 'NOT SET' and be_anon != 'NOT SET (optional)' else f"  SUPABASE_ANON_KEY: {be_anon}")
print()

print("COMPARISON:")
print("-" * 60)

# Compare URLs
if fe_url != 'NOT SET' and be_url != 'NOT SET':
    if fe_url == be_url:
        print("[OK] SUPABASE_URL: MATCH")
        print(f"   Both point to: {fe_url[:50]}...")
    else:
        print("[ERROR] SUPABASE_URL: DO NOT MATCH")
        print(f"   Frontend: {fe_url[:50]}...")
        print(f"   Backend:  {be_url[:50]}...")
else:
    print("[WARN] SUPABASE_URL: One or both not set")
    if fe_url == 'NOT SET':
        print("   Frontend: NOT SET")
    if be_url == 'NOT SET':
        print("   Backend: NOT SET")

print()

# Compare Anon Keys
if fe_anon != 'NOT SET' and be_anon != 'NOT SET' and be_anon != 'NOT SET (optional)':
    if fe_anon == be_anon:
        print("[OK] SUPABASE_ANON_KEY: MATCH")
        print(f"   Both use the same anon key (first 20 chars): {fe_anon[:20]}...")
    else:
        print("[ERROR] SUPABASE_ANON_KEY: DO NOT MATCH")
        print(f"   Frontend: {fe_anon[:20]}...")
        print(f"   Backend:  {be_anon[:20]}...")
else:
    print("[WARN] SUPABASE_ANON_KEY: Status")
    if fe_anon == 'NOT SET':
        print("   Frontend: NOT SET")
    if be_anon == 'NOT SET' or be_anon == 'NOT SET (optional)':
        print("   Backend: NOT SET (optional, not used in code)")

print()

# Check service role key
if be_key != 'NOT SET':
    # Check if it's a service role key (should contain 'service_role' in the JWT payload)
    try:
        import base64
        import json
        parts = be_key.split('.')
        if len(parts) >= 2:
            # Decode the payload (second part)
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            role = data.get('role', 'unknown')
            if role == 'service_role':
                print("[OK] SUPABASE_KEY: Valid service role key detected")
            else:
                print(f"[WARN] SUPABASE_KEY: Key role is '{role}' (should be 'service_role')")
        else:
            print("[WARN] SUPABASE_KEY: Format doesn't look like a JWT token")
    except Exception as e:
        print(f"[WARN] SUPABASE_KEY: Could not verify format ({str(e)})")
else:
    print("[ERROR] SUPABASE_KEY: NOT SET (required for backend)")

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)

issues = []
if fe_url == 'NOT SET':
    issues.append("Frontend SUPABASE_URL not set")
if be_url == 'NOT SET':
    issues.append("Backend SUPABASE_URL not set")
if fe_url != 'NOT SET' and be_url != 'NOT SET' and fe_url != be_url:
    issues.append("Frontend and Backend SUPABASE_URL do not match")
if fe_anon == 'NOT SET':
    issues.append("Frontend SUPABASE_ANON_KEY not set")
if be_key == 'NOT SET':
    issues.append("Backend SUPABASE_KEY (service role) not set")

if issues:
    print("[ERROR] ISSUES FOUND:")
    for issue in issues:
        print(f"   - {issue}")
    print()
    print("[WARN] These issues may cause connection problems!")
else:
    print("[OK] All credentials are properly configured!")
    if fe_url == be_url:
        print("[OK] Frontend and Backend are using the same Supabase project")
    print()

print("=" * 60)
