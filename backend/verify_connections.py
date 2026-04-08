#!/usr/bin/env python3
"""
Connection verification script for Early Warning System.
Verifies all connections: Database, ML models, Frontend-Backend.
"""
import sys
import os
from typing import Dict, Any, List

def check_database() -> Dict[str, Any]:
    """Verify database connection."""
    try:
        from database import db
        students = db.get_students(limit=1)
        return {
            'status': 'success',
            'message': 'Database connection successful',
            'test_query': f'Found {len(students)} student(s)'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Database connection failed: {str(e)}'
        }

def check_ml_components() -> Dict[str, Any]:
    """Verify ML components are loaded."""
    results = {}
    
    # Check risk engine
    try:
        from risk_engine import risk_engine
        results['risk_engine'] = {
            'status': 'success',
            'model_type': risk_engine.model_type,
            'is_trained': risk_engine.is_trained
        }
    except Exception as e:
        results['risk_engine'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # Check data processor
    try:
        from data_processing import processor
        results['data_processor'] = {
            'status': 'success',
            'message': 'Data processor initialized'
        }
    except Exception as e:
        results['data_processor'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # Check training pipeline
    try:
        from ml_training import training_pipeline
        results['training_pipeline'] = {
            'status': 'success',
            'message': 'Training pipeline initialized'
        }
    except Exception as e:
        results['training_pipeline'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # Check model explainability
    try:
        from model_explainability import model_explainer
        results['model_explainer'] = {
            'status': 'success',
            'shap_available': hasattr(model_explainer, 'explainer') and model_explainer.explainer is not None
        }
    except Exception as e:
        results['model_explainer'] = {
            'status': 'error',
            'message': str(e)
        }
    
    return results

def check_api_endpoints() -> Dict[str, Any]:
    """Verify API can start."""
    try:
        from main import app
        routes = [route.path for route in app.routes]
        return {
            'status': 'success',
            'message': f'API initialized with {len(routes)} routes',
            'sample_routes': routes[:5]
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'API initialization failed: {str(e)}'
        }

def check_monitoring() -> Dict[str, Any]:
    """Verify monitoring engine."""
    try:
        from monitoring import monitoring_engine
        return {
            'status': 'success',
            'is_running': monitoring_engine.is_running,
            'message': 'Monitoring engine initialized'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Monitoring engine failed: {str(e)}'
        }

def check_model_files() -> Dict[str, Any]:
    """Check if model files exist."""
    import os
    models_dir = "models"
    model_path = f"{models_dir}/risk_model_1.0.pkl"
    
    return {
        'models_dir_exists': os.path.exists(models_dir),
        'model_file_exists': os.path.exists(model_path),
        'message': 'Model file check completed'
    }

def main():
    """Run all connection checks."""
    print("=" * 60)
    print("Early Warning System - Connection Verification")
    print("=" * 60)
    print()
    
    checks = {
        'Database': check_database(),
        'ML Components': check_ml_components(),
        'API Endpoints': check_api_endpoints(),
        'Monitoring': check_monitoring(),
        'Model Files': check_model_files()
    }
    
    all_passed = True
    
    for check_name, result in checks.items():
        print(f"[*] {check_name}:")
        if isinstance(result, dict):
            if result.get('status') == 'error':
                print(f"  [X] {result.get('message', 'Unknown error')}")
                all_passed = False
            else:
                print(f"  [OK] {result.get('message', 'OK')}")
                if 'test_query' in result:
                    print(f"       {result['test_query']}")
        elif isinstance(result, dict):
            for component, status in result.items():
                if status.get('status') == 'error':
                    print(f"  [X] {component}: {status.get('message', 'Unknown error')}")
                    all_passed = False
                else:
                    print(f"  [OK] {component}: {status.get('message', 'OK')}")
        print()
    
    print("=" * 60)
    if all_passed:
        print("[SUCCESS] All checks passed! System is ready.")
    else:
        print("[WARNING] Some checks failed. Please review errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
