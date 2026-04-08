# 🔗 Frontend-Backend Connection via Environment Variables

## ✅ Current Setup (Already Configured!)

### Good News: **They're Already Connected!**

The frontend and backend are connected through environment variables, and it's already set up correctly.

---

## 📋 Environment Variable Configuration

### Frontend `.env` (project/.env)

**Required for Connection:**
```env
VITE_API_URL=http://localhost:8000
```

**What it does:**
- Tells frontend where to find the backend API
- Used by `apiClient` in `src/lib/api.ts`
- Defaults to `http://localhost:8000` if not set

**Current Status:**
- ✅ Already configured in your `.env` file
- ✅ Frontend knows where backend is

---

### Backend `.env` (project/backend/.env)

**No Frontend-Specific Variables Needed!**

Backend doesn't need to know about frontend because:
- ✅ CORS is configured to allow all origins
- ✅ Backend just responds to HTTP requests
- ✅ No frontend URL configuration needed

**Backend only needs:**
```env
SUPABASE_URL=...
SUPABASE_KEY=...
SUPABASE_ANON_KEY=...
```

---

## 🔍 How the Connection Works

### Current Flow:

```
┌─────────────────────────────────────┐
│  Frontend .env                     │
│  VITE_API_URL=http://localhost:8000│
└──────────────┬──────────────────────┘
               │
               │ Used by apiClient
               ▼
┌─────────────────────────────────────┐
│  src/lib/api.ts                     │
│  const API_BASE_URL =               │
│    import.meta.env.VITE_API_URL ||  │
│    'http://localhost:8000'          │
└──────────────┬──────────────────────┘
               │
               │ HTTP Requests
               ▼
┌─────────────────────────────────────┐
│  Backend (Port 8000)                │
│  CORS: allow_origins=["*"]          │
│  (No env config needed)             │
└─────────────────────────────────────┘
```

---

## ✅ What's Already Configured

### 1. Frontend API URL ✅
- **Location**: `project/.env`
- **Variable**: `VITE_API_URL=http://localhost:8000`
- **Status**: ✅ Configured
- **Used by**: `src/lib/api.ts`

### 2. Backend CORS ✅
- **Location**: `backend/main.py`
- **Configuration**: Allows all origins
- **Status**: ✅ Configured
- **No env needed**: Hardcoded in code

---

## 🎯 Do You Need Additional Env Variables?

### ❌ NO - Everything is Already Set!

**Frontend → Backend:**
- ✅ `VITE_API_URL` already set
- ✅ No additional config needed

**Backend → Frontend:**
- ✅ CORS already configured
- ✅ No env variables needed

**Backend → Supabase:**
- ✅ Already configured in backend `.env`
- ✅ `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_ANON_KEY`

---

## 🔧 Optional: Production Configuration

### If Deploying to Production:

**Frontend `.env.production`:**
```env
VITE_API_URL=https://your-backend-api.com
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

**Backend `.env.production`:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key
SUPABASE_ANON_KEY=your-anon-key
API_HOST=0.0.0.0
API_PORT=8000
```

**Backend CORS (for production):**
Update `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Dev
        "https://your-frontend-domain.com"  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Current Connection Status

| Component | Env Variable | Status | Required |
|-----------|-------------|--------|----------|
| Frontend → Backend | `VITE_API_URL` | ✅ Set | ✅ Yes |
| Backend → Frontend | CORS config | ✅ Set | ✅ Yes (in code) |
| Backend → Supabase | `SUPABASE_*` | ✅ Set | ✅ Yes |

---

## 🧪 Verify Connection

### Check Frontend Env:
```bash
# In browser console (F12)
console.log(import.meta.env.VITE_API_URL)
```
**Expected:** `http://localhost:8000`

### Check Backend CORS:
Open: http://localhost:8000/docs
**Expected:** API docs load (CORS working)

### Test Connection:
1. Open: http://localhost:5173
2. Open DevTools → Network tab
3. Navigate to student profile
4. Look for requests to `localhost:8000`
5. **If you see 200 status → Connected! ✅**

---

## ✅ Summary

### Current Setup:
- ✅ **Frontend `.env`**: Has `VITE_API_URL` → Backend connection configured
- ✅ **Backend CORS**: Configured in code → Frontend connection allowed
- ✅ **No additional env variables needed**

### They're Already Connected Through:
1. **Frontend env**: `VITE_API_URL` tells frontend where backend is
2. **Backend CORS**: Allows frontend to make requests
3. **HTTP REST API**: Standard connection method

---

## 🎯 Answer to Your Question

**"Should we connect frontend and backend through envs?"**

**Answer: ✅ YES - And it's already done!**

- ✅ Frontend uses `VITE_API_URL` env variable (already set)
- ✅ Backend uses CORS configuration (already set in code)
- ✅ **No additional configuration needed!**

**They're already connected and working together!** 🎉

---

## 🚀 Next Steps

1. **Verify Connection:**
   - Check `VITE_API_URL` in frontend `.env`
   - Should be: `http://localhost:8000`

2. **Test:**
   - Open http://localhost:5173
   - Check Network tab for API calls
   - Verify they go to `localhost:8000`

3. **That's it!** No additional env setup needed.

---

**Your frontend and backend are already connected through environment variables!** ✅
