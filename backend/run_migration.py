#!/usr/bin/env python3
"""
Run database migration to create all required tables.
This script executes the SQL migration directly via Supabase client.
"""
import sys
from pathlib import Path
from supabase import create_client
from config import settings

print("=" * 70)
print("DATABASE MIGRATION RUNNER")
print("=" * 70)
print()

# Read migration file
migration_file = Path(__file__).parent.parent / "supabase" / "migrations" / "20251225151810_create_ews_schema.sql"
if not migration_file.exists():
    # Try alternative location
    migration_file = Path(__file__).parent / "database_migrations.sql"
    if not migration_file.exists():
        print(f"[ERROR] Migration file not found!")
        print(f"   Looked for: {migration_file}")
        sys.exit(1)

print(f"Reading migration file: {migration_file}")
with open(migration_file, 'r', encoding='utf-8') as f:
    migration_sql = f.read()

print(f"Migration SQL length: {len(migration_sql)} characters")
print()

# Create Supabase client
print("Connecting to Supabase...")
try:
    client = create_client(settings.supabase_url, settings.supabase_key)
    print("[OK] Connected to Supabase")
except Exception as e:
    print(f"[ERROR] Failed to connect: {e}")
    sys.exit(1)

print()
print("=" * 70)
print("IMPORTANT: Supabase Python client doesn't support raw SQL execution")
print("=" * 70)
print()
print("You need to run the migration manually in Supabase Dashboard:")
print()
print("STEPS:")
print("1. Go to: https://app.supabase.com")
print("2. Select your project: mkrcbjmzefqzhsmuhbro")
print("3. Go to: SQL Editor (left sidebar)")
print("4. Click: 'New query'")
print("5. Copy and paste the SQL from:")
print(f"   {migration_file}")
print("6. Click: 'Run' (or press Ctrl+Enter)")
print()
print("ALTERNATIVE: Use Supabase CLI")
print("  supabase db push")
print()
print("=" * 70)
print()
print("Migration file location:")
print(f"  {migration_file}")
print()
print("Would you like to see the first 500 characters of the migration?")
print("(The full SQL is in the file above)")
