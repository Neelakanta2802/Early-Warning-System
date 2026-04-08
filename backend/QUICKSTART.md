# Quick Start Guide

Get the Early Warning System backend running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Supabase account (or PostgreSQL database)
- Internet connection (for package installation)

## Step 1: Setup Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your Supabase credentials
# Required:
# - SUPABASE_URL
# - SUPABASE_KEY
# - SUPABASE_ANON_KEY
```

Edit `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

API_HOST=0.0.0.0
API_PORT=8000
```

## Step 3: Database Setup

1. Ensure your Supabase database has the base schema (from `../project/supabase/migrations/`)
2. (Optional) Apply additional migrations from `database_migrations.sql` if needed

## Step 4: Run Server

```bash
# Option 1: Using the run script
python run.py

# Option 2: Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Option 3: Using Python directly
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Monitoring engine started
```

## Step 5: Test the API

### Option 1: Using Swagger UI (Recommended)

Open in browser:
```
http://localhost:8000/docs
```

This provides interactive API documentation where you can test all endpoints.

### Option 2: Using cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Get students
curl http://localhost:8000/api/students

# Get analytics overview
curl http://localhost:8000/api/analytics/overview
```

### Option 3: Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Get students
response = requests.get(f"{BASE_URL}/students")
students = response.json()
print(f"Found {len(students)} students")
```

## Step 6: Evaluate a Student (Optional)

If you have student data in the database:

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Get first student
students = requests.get(f"{BASE_URL}/students").json()
if students:
    student_id = students[0]['id']
    
    # Evaluate student
    result = requests.post(f"{BASE_URL}/students/{student_id}/evaluate")
    print(result.json())
```

## Verify Everything Works

1. ✅ Server starts without errors
2. ✅ Health check returns `{"status": "healthy"}`
3. ✅ Monitoring engine starts (check logs)
4. ✅ API documentation accessible at `/docs`
5. ✅ Can query students endpoint

## Troubleshooting

### Port Already in Use

```bash
# Change port in .env
API_PORT=8001
```

Or kill the process using port 8000:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill
```

### Database Connection Error

- Verify Supabase credentials in `.env`
- Check internet connection
- Verify database is accessible
- Check RLS policies if using Supabase

### Module Not Found

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Import Errors

Ensure virtual environment is activated:
```bash
# Check if activated (should show (venv))
which python  # macOS/Linux
where python  # Windows
```

## Next Steps

1. **Add Student Data**: Import student data via Supabase dashboard or API
2. **Configure Thresholds**: Adjust risk thresholds in `.env`
3. **Test Monitoring**: Let the monitoring engine run and check logs
4. **Integrate Frontend**: Connect frontend to backend API
5. **Customize Models**: Train ML models with your data (optional)

## Development Mode

For development with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

This will automatically reload on code changes.

## Production Mode

For production:
1. Set `API_RELOAD=false` in `.env`
2. Use a production WSGI server (e.g., Gunicorn)
3. Configure proper logging
4. Set up reverse proxy (Nginx)
5. Enable HTTPS

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Support

- Check logs for error messages
- Review `README.md` for detailed documentation
- Check `API_REFERENCE.md` for API details
- Verify configuration in `.env`

## Common Commands

```bash
# Start server
python run.py

# Run with debug logging
LOG_LEVEL=DEBUG python run.py

# Check Python version
python --version  # Should be 3.8+

# List installed packages
pip list

# Update dependencies
pip install -r requirements.txt --upgrade
```

That's it! Your backend should now be running. 🚀
