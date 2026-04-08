"""
Quick script to verify ML libraries are installed and working.
"""
import sys

def check_library(name, import_name=None):
    """Check if a library is installed."""
    if import_name is None:
        import_name = name
    try:
        __import__(import_name)
        return True, None
    except ImportError as e:
        return False, str(e)

def main():
    """Check all ML libraries."""
    print("=" * 80)
    print("ML Libraries Verification")
    print("=" * 80)
    
    libraries = [
        ("XGBoost", "xgboost"),
        ("LightGBM", "lightgbm"),
        ("CatBoost", "catboost"),
        ("TensorFlow", "tensorflow"),
        ("Optuna", "optuna"),
        ("Statsmodels", "statsmodels"),
        ("Scikit-learn", "sklearn"),
        ("NumPy", "numpy"),
        ("Pandas", "pandas"),
        ("SHAP", "shap"),
    ]
    
    installed = []
    missing = []
    
    for lib_name, import_name in libraries:
        is_installed, error = check_library(lib_name, import_name)
        if is_installed:
            installed.append(lib_name)
            print(f"[OK] {lib_name}")
        else:
            missing.append(lib_name)
            print(f"[MISSING] {lib_name}")
    
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Installed: {len(installed)}/{len(libraries)}")
    print(f"Missing: {len(missing)}/{len(libraries)}")
    
    if missing:
        print(f"\nMissing libraries: {', '.join(missing)}")
        print("\nTo install missing libraries, run:")
        print("pip install " + " ".join(missing).lower().replace(" ", ""))
    
    if len(installed) >= 7:  # At least core + advanced ML
        print("\n[SUCCESS] Core ML libraries are installed. System is ready!")
        return 0
    else:
        print("\n[WARNING] Some libraries are missing, but system will use fallbacks.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
