# 🚀 Starting Both Servers - Complete Guide

## ✅ Environment Variables Setup Complete!

Now let's start both frontend and backend servers.

---

## 📋 Step-by-Step Startup

### Step 1: Start Backend Server

**Option A: Using Command Line**
```bash
cd backend
python run.py
```

**Option B: Using Batch File**
```bash
START_BACKEND.bat
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify Backend:**
- Open: http://localhost:8000/api/health
- Should see: `{"status": "healthy"}`
- API Docs: http://localhost:8000/docs

---

### Step 2: Start Frontend Server

**Option A: Using Command Line**
```bash
npm run dev
```

**Option B: Using Batch File**
```bash
START_HERE.bat
```

**Expected Output:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Verify Frontend:**
- Open: http://localhost:5173
- Should see: Landing page with "Early Warning System"

---

## 🔄 Starting Both Servers

### Method 1: Two Separate Terminals

**Terminal 1 (Backend):**
```bash
cd backend
python run.py
```

**Terminal 2 (Frontend):**
```bash
npm run dev
```

### Method 2: Background Processes

**Windows PowerShell:**
```powershell
# Start backend in background
Start-Process python -ArgumentList "backend/run.py" -WindowStyle Normal

# Start frontend in background
Start-Process npm -ArgumentList "run", "dev" -WindowStyle Normal
```

---

## ✅ Verification Checklist

### Backend Verification:
- [ ] Backend starts without errors
- [ ] Health check works: http://localhost:8000/api/health
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] No Supabase connection errors

### Frontend Verification:
- [ ] Frontend starts without errors
- [ ] Landing page loads: http://localhost:5173
- [ ] No environment variable errors
- [ ] Can navigate to login page

### Connection Verification:
- [ ] Frontend can connect to backend API
- [ ] No CORS errors in browser console
- [ ] API calls work (check Network tab)

---

## 🧪 Quick Test

### Test 1: Backend Health
```bash
curl http://localhost:8000/api/health
```
**Expected:** `{"status": "healthy"}`

### Test 2: Frontend Loads
Open browser: http://localhost:5173
**Expected:** Landing page appears

### Test 3: API Connection
1. Open browser console (F12)
2. Navigate to a student profile
3. Check Network tab for API calls
4. Should see requests to `localhost:8000`

---

## 🐛 Troubleshooting

### Backend Won't Start

**Error: "Missing Supabase environment variables"**
- ✅ Check `.env` file exists in `backend/` folder
- ✅ Verify all 3 Supabase variables are set
- ✅ No typos in variable names

**Error: "Port 8000 already in use"**
```bash
# Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Frontend Won't Start

**Error: "Missing Supabase environment variables"**
- ✅ Check `.env` file exists in project root
- ✅ Verify `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set
- ✅ Restart dev server after changing `.env`

**Error: "Port 5173 already in use"**
```bash
# Find and kill process on port 5173
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

### Connection Issues

**CORS Errors:**
- ✅ Backend CORS is configured (allows all origins)
- ✅ Backend is running on port 8000
- ✅ Frontend is calling correct URL

**API Not Responding:**
- ✅ Backend is running
- ✅ Check backend logs for errors
- ✅ Verify Supabase connection in backend

---

## 📊 Expected Status

### When Everything Works:

```
┌─────────────────────────────────────┐
│  Backend (Port 8000)                │
│  ✅ Running                          │
│  ✅ Connected to Supabase            │
│  ✅ API endpoints active             │
└─────────────────────────────────────┘
              ↕ HTTP
┌─────────────────────────────────────┐
│  Frontend (Port 5173)               │
│  ✅ Running                          │
│  ✅ Connected to Supabase            │
│  ✅ Connected to Backend API         │
└─────────────────────────────────────┘
```

---

## 🎯 Next Steps After Starting

1. **Test Frontend:**
   - Open http://localhost:5173
   - Create an account or login
   - Explore the dashboard

2. **Test Backend:**
   - Open http://localhost:8000/docs
   - Try the health endpoint
   - Explore API documentation

3. **Test Integration:**
   - View a student profile
   - Check browser console for API calls
   - Verify ML features work (if model trained)

4. **Optional: Train ML Model:**
   - Add some student data
   - Call: `POST /api/ml/train`
   - Improves accuracy

---

## 🎉 Success Indicators

### ✅ Everything Working:
- ✅ Both servers running
- ✅ No errors in console
- ✅ Frontend loads correctly
- ✅ Backend API responds
- ✅ Can login/create account
- ✅ Dashboard shows data
- ✅ No connection errors

---

**Ready to start? Run the commands above!** 🚀
