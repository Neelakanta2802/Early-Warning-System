# Environment Variables Guide

## 📁 File Locations

### Frontend `.env`
**Location**: `project/.env` (root of project folder)

### Backend `.env`
**Location**: `project/backend/.env` (inside backend folder)

---

## 🔵 FRONTEND `.env` File

### Required Variables

```env
# Supabase Configuration (REQUIRED - unless using demo mode)
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

**Note**: If `VITE_DEMO_MODE=true`, Supabase variables are not required.

### Optional Variables

```env
# Backend API URL (OPTIONAL - has default)
VITE_API_URL=http://localhost:8000

# Demo Mode (OPTIONAL - allows running without Supabase)
VITE_DEMO_MODE=false
```

**Note**: If `VITE_API_URL` is not set, it defaults to `http://localhost:8000`

---

## 🔴 BACKEND `.env` File

### Required Variables (Must Set)

```env
# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key-here
```

**Note**: `SUPABASE_ANON_KEY` is defined in config but not currently used in backend code. It's optional.

### Optional Variables (Have Defaults)

```env
# Supabase Anon Key (Optional - defined but not used in code)
SUPABASE_ANON_KEY=your-anon-key-here

# Database (Optional)
DATABASE_URL=postgresql://user:password@host:port/database

# API Server (Optional - defaults shown)
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# ML Model (Optional - defaults shown)
MODEL_TYPE=random_forest
MODEL_VERSION=1.0

# Risk Thresholds (Optional - defaults shown)
RISK_THRESHOLD_LOW=30
RISK_THRESHOLD_MEDIUM=60
RISK_THRESHOLD_HIGH=80

# Attendance Thresholds (Optional - defaults shown)
ATTENDANCE_THRESHOLD_WARNING=75.0
ATTENDANCE_THRESHOLD_CRITICAL=60.0

# GPA Thresholds (Optional - defaults shown)
GPA_THRESHOLD_WARNING=2.5
GPA_THRESHOLD_CRITICAL=2.0

# Monitoring (Optional - defaults shown)
MONITORING_INTERVAL_MINUTES=60
ALERT_COOLDOWN_HOURS=24

# Logging (Optional - defaults shown)
LOG_LEVEL=INFO
```

---

## 🔑 How to Get Supabase Credentials

### Step 1: Go to Supabase Dashboard
1. Visit: https://app.supabase.com
2. Select your project (or create a new one)

### Step 2: Get API Keys
1. Go to: **Settings** → **API**
2. You'll see:
   - **Project URL** → Use for `SUPABASE_URL` / `VITE_SUPABASE_URL`
   - **anon public** key → Use for `SUPABASE_ANON_KEY` / `VITE_SUPABASE_ANON_KEY`
   - **service_role** key → Use for `SUPABASE_KEY` (backend only)

### Step 3: Copy to `.env` Files

**Frontend `.env`**:
```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Backend `.env`**:
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # service_role key
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # anon key
```

---

## 📋 Quick Setup Checklist

### Frontend Setup
- [ ] Create `.env` file in `project/` folder
- [ ] Add `VITE_SUPABASE_URL`
- [ ] Add `VITE_SUPABASE_ANON_KEY`
- [ ] (Optional) Add `VITE_API_URL` if backend runs on different port
- [ ] Restart frontend dev server

### Backend Setup
- [ ] Create `.env` file in `project/backend/` folder
- [ ] Add `SUPABASE_URL`
- [ ] Add `SUPABASE_KEY` (service role key)
- [ ] (Optional) Add `SUPABASE_ANON_KEY` (defined but not used)
- [ ] (Optional) Customize other variables if needed
- [ ] Restart backend server

---

## 🎯 Minimum Required Setup

### For Frontend to Work:
```env
# project/.env
VITE_SUPABASE_URL=your-url
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### For Backend to Work:
```env
# project/backend/.env
SUPABASE_URL=your-url
SUPABASE_KEY=your-service-role-key
# SUPABASE_ANON_KEY is optional (defined but not used)
```

---

## ⚠️ Important Notes

### 1. Variable Naming
- **Frontend**: All variables MUST start with `VITE_` (Vite requirement)
- **Backend**: No prefix needed (uses Pydantic settings)

### 2. Security
- **Never commit `.env` files** to version control
- `.env` files are in `.gitignore`
- `SUPABASE_KEY` (service role) is sensitive - keep it secret
- `VITE_SUPABASE_ANON_KEY` is public (safe for frontend)

### 3. Restart Required
- After changing `.env` files, **restart the server**
- Frontend: Stop and restart `npm run dev`
- Backend: Stop and restart `python run.py`

### 4. Case Sensitivity
- Backend variables are **case-insensitive** (Pydantic handles this)
- Frontend variables are **case-sensitive** (must match exactly)

---

## 📝 Example `.env` Files

### Frontend `.env` (project/.env)
```env
VITE_SUPABASE_URL=https://abcdefghijklmnop.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYxNjIzOTAyMiwiZXhwIjoxOTMxODE1MDIyfQ.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VITE_API_URL=http://localhost:8000
# VITE_DEMO_MODE=false  # Optional: set to 'true' to run without Supabase
```

### Backend `.env` (project/backend/.env)
```env
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjE2MjM5MDIyLCJleHAiOjE5MzE4MTUwMjJ9.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# SUPABASE_ANON_KEY=eyJ...  # Optional: defined but not currently used
```

---

## 🔍 Verification

### Check Frontend Variables
```bash
# In browser console (F12)
console.log(import.meta.env.VITE_SUPABASE_URL)
console.log(import.meta.env.VITE_API_URL)
```

### Check Backend Variables
```python
# In Python
from config import settings
print(settings.supabase_url)
print(settings.api_port)
```

---

## 🚨 Common Issues

### Issue: "Missing Supabase environment variables"
**Solution**: Make sure `.env` file exists and has correct variable names

### Issue: Backend won't start
**Solution**: Check that all 3 required Supabase variables are set

### Issue: Frontend can't connect to backend
**Solution**: Check `VITE_API_URL` matches backend port (default: 8000)

### Issue: Variables not loading
**Solution**: Restart the server after changing `.env` file

---

## 📚 Summary

| Variable | Frontend | Backend | Required | Default |
|----------|----------|---------|----------|---------|
| Supabase URL | `VITE_SUPABASE_URL` | `SUPABASE_URL` | ✅ Yes* | - |
| Anon Key | `VITE_SUPABASE_ANON_KEY` | `SUPABASE_ANON_KEY` | ✅ Yes* / ⚠️ Optional | - |
| Service Key | - | `SUPABASE_KEY` | ✅ Yes (BE only) | - |
| API URL | `VITE_API_URL` | - | ❌ No | `http://localhost:8000` |
| Demo Mode | `VITE_DEMO_MODE` | - | ❌ No | `false` |

*Required unless `VITE_DEMO_MODE=true` (frontend only)
| API Port | - | `API_PORT` | ❌ No | `8000` |
| Model Type | - | `MODEL_TYPE` | ❌ No | `random_forest` |
| Risk Thresholds | - | `RISK_THRESHOLD_*` | ❌ No | 30/60/80 |
| Log Level | - | `LOG_LEVEL` | ❌ No | `INFO` |

---

**Quick Start**: Copy `.env.example` files to `.env` and fill in your Supabase credentials!
