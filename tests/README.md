# Early Warning System - Test Suite

Comprehensive test suite for the Early Warning System covering file upload, processing, ML models, and UI display.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── test_file_upload.py         # File upload tests (CSV, Excel, JSON)
├── test_file_processing.py     # Data processing and validation tests
├── test_ml_models.py           # ML model training and prediction tests
├── test_ui_display.py          # UI display and API endpoint tests
├── test_integration.py         # End-to-end integration tests
├── run_all_tests.py            # Test runner script
└── README.md                   # This file
```

## Prerequisites

1. **Backend Server Running**
   ```bash
   cd project/backend
   python run.py
   # Or
   uvicorn main:app --reload
   ```

2. **Environment Variables**
   - Ensure `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`
   - `API_BASE_URL` (optional, defaults to `http://localhost:8000`)

3. **Python Dependencies**
   ```bash
   pip install pytest pytest-cov requests pandas openpyxl
   ```

## Running Tests

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Specific Test Suite
```bash
# File upload tests
pytest tests/test_file_upload.py -v

# File processing tests
pytest tests/test_file_processing.py -v

# ML model tests
pytest tests/test_ml_models.py -v

# UI display tests
pytest tests/test_ui_display.py -v

# Integration tests
pytest tests/test_integration.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=project/backend --cov-report=html
```

### Run Specific Test
```bash
pytest tests/test_file_upload.py::TestFileUpload::test_csv_upload_success -v
```

## Test Categories

### 1. File Upload Tests (`test_file_upload.py`)
- ✅ CSV file upload
- ✅ Excel file upload
- ✅ JSON file upload
- ✅ Empty file handling
- ✅ Invalid format handling
- ✅ Large file upload
- ✅ Unicode content handling
- ✅ Upload with form fields
- ✅ Response structure validation

### 2. File Processing Tests (`test_file_processing.py`)
- ✅ Data processing module imports
- ✅ Feature engineering with various data combinations
- ✅ Data cleaning and normalization
- ✅ GPA calculation
- ✅ Attendance trend calculation
- ✅ Behavioral feature detection
- ✅ Database operation structure
- ✅ Data structure validation

### 3. ML Model Tests (`test_ml_models.py`)
- ✅ Risk engine initialization
- ✅ Feature extraction
- ✅ Rule-based prediction
- ✅ ML prediction (when trained)
- ✅ Risk level classification
- ✅ High/low risk detection
- ✅ Risk factors and explanations
- ✅ Scaler fitted check
- ✅ Training pipeline structure

### 4. UI Display Tests (`test_ui_display.py`)
- ✅ Students API endpoints
- ✅ Dashboard API endpoints
- ✅ Alerts API endpoints
- ✅ Interventions API endpoints
- ✅ Student profile endpoints
- ✅ Data consistency across endpoints
- ✅ Filter and pagination support

### 5. Integration Tests (`test_integration.py`)
- ✅ Complete upload-to-display workflow
- ✅ JSON upload workflow
- ✅ Risk assessment generation flow
- ✅ Dashboard data after upload
- ✅ Multiple upload consistency
- ✅ Error handling in workflows
- ✅ ML training workflows
- ✅ System health checks

## Test Data

Test data is generated programmatically in fixtures (see `conftest.py`). Sample test files include:
- CSV with student data
- Excel files with academic records
- JSON with complete student profiles

## Configuration

### Environment Variables
```bash
# Optional: Override API URL
export API_BASE_URL=http://localhost:8000
```

### Pytest Configuration
Create `pytest.ini` in project root:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## Troubleshooting

### Backend Not Running
```
⚠️ Cannot connect to backend API
```
**Solution:** Start the backend server before running tests.

### Database Connection Errors
```
❌ Database client not initialized
```
**Solution:** Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY` (service role key).

### Import Errors
```
ModuleNotFoundError: No module named 'risk_engine'
```
**Solution:** Ensure you're running tests from project root, and backend is in Python path.

### Timeout Errors
Some tests may timeout if:
- Backend is slow to respond
- Large file processing takes time

**Solution:** Increase timeout values in test files or check backend performance.

## Writing New Tests

1. **Add to appropriate test file** or create new one following naming convention `test_*.py`
2. **Use fixtures** from `conftest.py` for common test data
3. **Follow naming conventions:**
   - Test classes: `Test*`
   - Test methods: `test_*`
4. **Add docstrings** explaining what the test verifies
5. **Handle both success and error cases**

Example:
```python
def test_new_feature(self, api_base_url):
    """Test that new feature works correctly."""
    response = requests.get(f"{api_base_url}/api/new-endpoint")
    assert response.status_code == 200
```

## CI/CD Integration

To run tests in CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --tb=short
```

## Test Coverage Goals

- File Upload: 90%+
- File Processing: 85%+
- ML Models: 80%+
- UI Display: 85%+
- Integration: 75%+

## Notes

- Tests are designed to work with or without a running database
- Some tests may fail if Supabase credentials aren't configured (expected)
- Integration tests require backend to be running
- ML training tests may take longer (60-120 seconds)

## Support

For issues or questions about tests:
1. Check test output for specific error messages
2. Verify backend is running and accessible
3. Check environment variables are set correctly
4. Review backend logs for detailed error information
