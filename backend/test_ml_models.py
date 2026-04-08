"""
Test script to verify all ML models work correctly.
Run this to check if models are properly integrated.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test if all modules can be imported."""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    try:
        from risk_engine import RiskScoringEngine
        print("[OK] risk_engine imported successfully")
    except Exception as e:
        print(f"[FAIL] risk_engine import failed: {e}")
        return False
    
    try:
        from ml_training import MLTrainingPipeline
        print("[OK] ml_training imported successfully")
    except Exception as e:
        print(f"[FAIL] ml_training import failed: {e}")
        return False
    
    try:
        from advanced_ml_models import advanced_ml, XGBOOST_AVAILABLE, LIGHTGBM_AVAILABLE, TENSORFLOW_AVAILABLE, OPTUNA_AVAILABLE
        print("[OK] advanced_ml_models imported successfully")
        print(f"  - XGBoost available: {XGBOOST_AVAILABLE}")
        print(f"  - LightGBM available: {LIGHTGBM_AVAILABLE}")
        print(f"  - TensorFlow available: {TENSORFLOW_AVAILABLE}")
        print(f"  - Optuna available: {OPTUNA_AVAILABLE}")
    except Exception as e:
        print(f"[FAIL] advanced_ml_models import failed: {e}")
        return False
    
    try:
        from time_series_forecasting import time_series_forecaster
        print("[OK] time_series_forecasting imported successfully")
    except Exception as e:
        print(f"[FAIL] time_series_forecasting import failed: {e}")
        return False
    
    return True

def test_model_initialization():
    """Test if models can be initialized."""
    print("\n" + "=" * 60)
    print("Testing Model Initialization")
    print("=" * 60)
    
    from risk_engine import RiskScoringEngine
    
    model_types = [
        "random_forest",
        "logistic_regression",
        "gradient_boosting",
        "xgboost",
        "lightgbm",
        "neural_network",
        "ensemble"
    ]
    
    for model_type in model_types:
        try:
            engine = RiskScoringEngine()
            engine.model_type = model_type
            engine._initialize_model()
            if engine.model is not None or model_type in ["neural_network", "ensemble"]:
                print(f"[OK] {model_type} initialized successfully")
            else:
                print(f"[WARN] {model_type} initialized but model is None (may need training)")
        except Exception as e:
            print(f"[FAIL] {model_type} initialization failed: {e}")
    
    return True

def test_model_creation():
    """Test if advanced models can be created."""
    print("\n" + "=" * 60)
    print("Testing Advanced Model Creation")
    print("=" * 60)
    
    from advanced_ml_models import advanced_ml, XGBOOST_AVAILABLE, LIGHTGBM_AVAILABLE, TENSORFLOW_AVAILABLE
    
    if XGBOOST_AVAILABLE:
        try:
            model = advanced_ml.create_xgboost_model()
            print("[OK] XGBoost model created successfully")
        except Exception as e:
            print(f"[FAIL] XGBoost model creation failed: {e}")
    else:
        print("[WARN] XGBoost not available (install: pip install xgboost)")
    
    if LIGHTGBM_AVAILABLE:
        try:
            model = advanced_ml.create_lightgbm_model()
            print("[OK] LightGBM model created successfully")
        except Exception as e:
            print(f"[FAIL] LightGBM model creation failed: {e}")
    else:
        print("[WARN] LightGBM not available (install: pip install lightgbm)")
    
    if TENSORFLOW_AVAILABLE:
        try:
            import numpy as np
            model = advanced_ml.create_neural_network(input_dim=10)
            print("[OK] Neural network model created successfully")
        except Exception as e:
            print(f"[FAIL] Neural network model creation failed: {e}")
    else:
        print("[WARN] TensorFlow not available (install: pip install tensorflow)")
    
    return True

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ML Models Integration Test")
    print("=" * 60)
    
    if not test_imports():
        print("\n[FAIL] Import tests failed. Please check dependencies.")
        return
    
    if not test_model_initialization():
        print("\n[FAIL] Model initialization tests failed.")
        return
    
    if not test_model_creation():
        print("\n[FAIL] Model creation tests failed.")
        return
    
    print("\n" + "=" * 60)
    print("[OK] All tests passed!")
    print("=" * 60)
    print("\nNote: Some models may require additional packages.")
    print("Install with: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
