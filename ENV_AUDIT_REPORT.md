# 🔍 Environment Variables Audit Report

## Executive Summary

This report audits all environment variables required and used in both the Frontend (FE) and Backend (BE) of the Early Warning System.

**Status**: ✅ **Mostly Complete** - Some discrepancies found between documentation and actual usage.

---

## 📋 Frontend Environment Variables

### Required Variables

| Variable | Status | Used In | Notes |
|----------|--------|---------|-------|
| `VITE_SUPABASE_URL` | ✅ **REQUIRED** | `src/lib/supabase.ts` | Required unless `VITE_DEMO_MODE=true` |
| `VITE_SUPABASE_ANON_KEY` | ✅ **REQUIRED** | `src/lib/supabase.ts` | Required unless `VITE_DEMO_MODE=true` |

### Optional Variables

| Variable | Status | Default | Used In | Notes |
|----------|--------|---------|---------|-------|
| `VITE_API_URL` | ⚠️ **OPTIONAL** | `http://localhost:8000` | `src/lib/api.ts` | Has default fallback |
| `VITE_DEMO_MODE` | ⚠️ **OPTIONAL** | `false` | `src/lib/supabase.ts`, `src/contexts/AuthContext.tsx` | Enables demo mode without Supabase |

### Frontend Code Analysis

**Files using environment variables:**
1. `src/lib/supabase.ts`:
   - `VITE_SUPABASE_URL` (required unless demo mode)
   - `VITE_SUPABASE_ANON_KEY` (required unless demo mode)
   - `VITE_DEMO_MODE` (optional)

2. `src/lib/api.ts`:
   - `VITE_API_URL` (optional, defaults to `http://localhost:8000`)

3. `src/contexts/AuthContext.tsx`:
   - `VITE_DEMO_MODE` (optional, used in multiple places)

### Frontend Minimum Requirements

**For Production (Non-Demo Mode):**
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

**For Demo Mode:**
```env
VITE_DEMO_MODE=true
# Supabase variables not required in demo mode
```

**Recommended (with backend connection):**
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
VITE_API_URL=http://localhost:8000
```

---

## 📋 Backend Environment Variables

### Required Variables

| Variable | Status | Used In | Notes |
|----------|--------|---------|-------|
| `SUPABASE_URL` | ✅ **REQUIRED** | `backend/config.py`, `backend/database.py` | No default, must be set |
| `SUPABASE_KEY` | ✅ **REQUIRED** | `backend/config.py`, `backend/database.py` | Service role key (NOT anon key) |
| `SUPABASE_ANON_KEY` | ⚠️ **DEFINED BUT NOT USED** | `backend/config.py` | Defined in config but not used in code |

### Optional Variables (Have Defaults)

| Variable | Status | Default | Used In | Notes |
|----------|--------|---------|---------|-------|
| `DATABASE_URL` | ⚠️ **OPTIONAL** | `""` (empty) | `backend/config.py` | Not currently used |
| `API_HOST` | ⚠️ **OPTIONAL** | `"0.0.0.0"` | `backend/main.py`, `backend/run.py` | Server host |
| `API_PORT` | ⚠️ **OPTIONAL** | `8000` | `backend/main.py`, `backend/run.py` | Server port |
| `API_RELOAD` | ⚠️ **OPTIONAL** | `true` | `backend/main.py`, `backend/run.py` | Auto-reload in dev |
| `MODEL_TYPE` | ⚠️ **OPTIONAL** | `"xgboost"` | `backend/config.py`, `backend/risk_engine.py` | ML model type |
| `MODEL_VERSION` | ⚠️ **OPTIONAL** | `"2.0"` | Multiple files | Model version |
| `RISK_THRESHOLD_LOW` | ⚠️ **OPTIONAL** | `30` | `backend/risk_engine.py` | Risk threshold |
| `RISK_THRESHOLD_MEDIUM` | ⚠️ **OPTIONAL** | `60` | `backend/risk_engine.py` | Risk threshold |
| `RISK_THRESHOLD_HIGH` | ⚠️ **OPTIONAL** | `80` | `backend/risk_engine.py` | Risk threshold |
| `ATTENDANCE_THRESHOLD_WARNING` | ⚠️ **OPTIONAL** | `75.0` | `backend/early_warning.py`, `backend/risk_engine.py` | Attendance % |
| `ATTENDANCE_THRESHOLD_CRITICAL` | ⚠️ **OPTIONAL** | `60.0` | `backend/early_warning.py`, `backend/risk_engine.py` | Attendance % |
| `GPA_THRESHOLD_WARNING` | ⚠️ **OPTIONAL** | `2.5` | `backend/early_warning.py`, `backend/risk_engine.py` | GPA threshold |
| `GPA_THRESHOLD_CRITICAL` | ⚠️ **OPTIONAL** | `2.0` | `backend/early_warning.py`, `backend/risk_engine.py` | GPA threshold |
| `MONITORING_INTERVAL_MINUTES` | ⚠️ **OPTIONAL** | `60` | `backend/monitoring.py` | Monitoring interval |
| `ALERT_COOLDOWN_HOURS` | ⚠️ **OPTIONAL** | `24` | `backend/early_warning.py` | Alert cooldown |
| `LOG_LEVEL` | ⚠️ **OPTIONAL** | `"INFO"` | `backend/main.py`, `backend/run.py` | Logging level |

### Backend Code Analysis

**Files using environment variables:**
1. `backend/config.py`: Defines all settings using Pydantic BaseSettings
2. `backend/database.py`: Uses `settings.supabase_url` and `settings.supabase_key`
3. `backend/main.py`: Uses server config and logging
4. `backend/risk_engine.py`: Uses model and threshold settings
5. `backend/early_warning.py`: Uses threshold settings
6. `backend/monitoring.py`: Uses monitoring interval

**⚠️ ISSUE FOUND**: `SUPABASE_ANON_KEY` is defined in `config.py` but **never actually used** in the backend code. The backend only uses `SUPABASE_KEY` (service role key).

### Backend Minimum Requirements

**For Production:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key-here
```

**Note**: `SUPABASE_ANON_KEY` is defined but not used. It can be removed from requirements or kept for future use.

---

## 🔍 Issues Found

### 1. ⚠️ Backend `SUPABASE_ANON_KEY` Not Used

**Issue**: The backend `config.py` defines `supabase_anon_key: str` as required, but this variable is **never used** in the actual backend code.

**Evidence**:
- `backend/database.py` only uses `settings.supabase_url` and `settings.supabase_key`
- No other backend files reference `supabase_anon_key`
- Documentation says it's required, but code doesn't use it

**Recommendation**:
- **Option A**: Remove `supabase_anon_key` from `config.py` (if not needed)
- **Option B**: Keep it but make it optional (if planning to use it later)
- **Option C**: Document that it's not currently used but kept for consistency

**Current Status**: Defined as required but unused.

### 2. ✅ Frontend Demo Mode Support

**Status**: Properly implemented
- `VITE_DEMO_MODE` allows frontend to work without Supabase credentials
- Gracefully handles missing Supabase variables when in demo mode

### 3. ✅ Frontend API URL Has Default

**Status**: Properly implemented
- `VITE_API_URL` defaults to `http://localhost:8000` if not set
- No breaking changes if variable is missing

---

## 📊 Comparison: Documentation vs. Actual Usage

### Frontend

| Variable | Documentation Says | Code Actually Uses | Match? |
|----------|-------------------|-------------------|--------|
| `VITE_SUPABASE_URL` | Required | Required (unless demo mode) | ✅ Yes |
| `VITE_SUPABASE_ANON_KEY` | Required | Required (unless demo mode) | ✅ Yes |
| `VITE_API_URL` | Optional | Optional (has default) | ✅ Yes |
| `VITE_DEMO_MODE` | Not documented | Used in code | ⚠️ Missing from docs |

### Backend

| Variable | Documentation Says | Code Actually Uses | Match? |
|----------|-------------------|-------------------|--------|
| `SUPABASE_URL` | Required | Required | ✅ Yes |
| `SUPABASE_KEY` | Required | Required | ✅ Yes |
| `SUPABASE_ANON_KEY` | Required | **NOT USED** | ❌ **MISMATCH** |
| `DATABASE_URL` | Optional | Optional (not used) | ✅ Yes |
| All other vars | Optional | Optional (have defaults) | ✅ Yes |

---

## ✅ Recommended Environment Files

### Frontend `.env` (project/.env)

```env
# Required (unless using demo mode)
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here

# Optional (has default)
VITE_API_URL=http://localhost:8000

# Optional (for demo mode without Supabase)
# VITE_DEMO_MODE=true
```

### Backend `.env` (project/backend/.env)

```env
# Required
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key-here

# Optional (defined but not used - can be removed or kept for future)
# SUPABASE_ANON_KEY=your-anon-key-here

# Optional (has defaults)
# API_HOST=0.0.0.0
# API_PORT=8000
# API_RELOAD=true
# MODEL_TYPE=xgboost
# MODEL_VERSION=2.0
# RISK_THRESHOLD_LOW=30
# RISK_THRESHOLD_MEDIUM=60
# RISK_THRESHOLD_HIGH=80
# ATTENDANCE_THRESHOLD_WARNING=75.0
# ATTENDANCE_THRESHOLD_CRITICAL=60.0
# GPA_THRESHOLD_WARNING=2.5
# GPA_THRESHOLD_CRITICAL=2.0
# MONITORING_INTERVAL_MINUTES=60
# ALERT_COOLDOWN_HOURS=24
# LOG_LEVEL=INFO
```

---

## 🎯 Summary

### ✅ What's Correct

1. **Frontend**: All required variables are properly used
2. **Backend**: Core required variables (`SUPABASE_URL`, `SUPABASE_KEY`) are correctly used
3. **Optional variables**: All have sensible defaults
4. **Frontend demo mode**: Properly implemented

### ⚠️ What Needs Attention

1. **Backend `SUPABASE_ANON_KEY`**: 
   - Defined as required in `config.py`
   - Never actually used in code
   - Documentation says it's required
   - **Action needed**: Either remove it or document that it's unused

2. **Frontend `VITE_DEMO_MODE`**:
   - Used in code but not documented in `ENV_VARIABLES_GUIDE.md`
   - **Action needed**: Add to documentation

### 📝 Recommendations

1. **Update `backend/config.py`**:
   - Make `supabase_anon_key` optional: `supabase_anon_key: str = ""`
   - Or remove it if not needed

2. **Update `ENV_VARIABLES_GUIDE.md`**:
   - Document `VITE_DEMO_MODE` for frontend
   - Clarify that `SUPABASE_ANON_KEY` is optional/unused in backend

3. **Create `.env.example` files**:
   - `project/.env.example` for frontend
   - `project/backend/.env.example` for backend

---

## ✅ Verification Checklist

### Frontend
- [x] `VITE_SUPABASE_URL` - Required and used
- [x] `VITE_SUPABASE_ANON_KEY` - Required and used
- [x] `VITE_API_URL` - Optional with default
- [x] `VITE_DEMO_MODE` - Optional, used but not documented

### Backend
- [x] `SUPABASE_URL` - Required and used
- [x] `SUPABASE_KEY` - Required and used
- [ ] `SUPABASE_ANON_KEY` - Defined but **NOT USED** ⚠️
- [x] All optional variables have defaults

---

## 🚀 Next Steps

1. **Fix `SUPABASE_ANON_KEY` issue** in backend config
2. **Update documentation** to reflect actual usage
3. **Create `.env.example` files** for easy setup
4. **Test** with minimal required variables only

---

**Report Generated**: Environment variables audit complete
**Status**: ✅ Mostly correct, minor issues found
