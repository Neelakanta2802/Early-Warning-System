#!/usr/bin/env python3
"""
Test runner script for all Early Warning System tests.
Run all test suites and generate a comprehensive report.
"""
import sys
import pytest
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Run all tests with detailed reporting."""
    print("=" * 80)
    print("🧪 Early Warning System - Comprehensive Test Suite")
    print("=" * 80)
    print()
    
    # Test files
    test_files = [
        "tests/test_file_upload.py",
        "tests/test_file_processing.py",
        "tests/test_ml_models.py",
        "tests/test_ui_display.py",
        "tests/test_integration.py"
    ]
    
    # Check if API is running
    try:
        import requests
        api_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        health_response = requests.get(f"{api_url}/api/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Backend API is running")
        else:
            print("⚠️  Backend API health check failed")
    except Exception as e:
        print(f"⚠️  Cannot connect to backend API: {e}")
        print("   Some tests may fail. Ensure backend is running.")
        print()
    
    print("Running test suites...")
    print()
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        "-v",  # Verbose
        "--tb=short",  # Short traceback format
        "--color=yes",  # Color output
        *test_files
    ])
    
    print()
    print("=" * 80)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Some tests failed (exit code: {exit_code})")
    print("=" * 80)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
