# 🚀 Running Frontend and Backend Together

## ✅ YES! You Can Run Both Simultaneously!

Both servers can run at the same time on different ports:
- **Frontend**: Port 5173
- **Backend**: Port 8000

They don't conflict because they use different ports!

---

## 📋 How to Run Both

### Method 1: Two Separate Terminal Windows (Recommended)

**Terminal 1 - Backend:**
```bash
cd "c:\Users\91807\Downloads\AT risk student\project\backend"
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd "c:\Users\91807\Downloads\AT risk student\project"
npm run dev
```

**Expected Output:**

**Backend Terminal:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Frontend Terminal:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

---

### Method 2: Use Batch Files

**Windows:**
1. Double-click `START_BACKEND.bat` (opens backend in new window)
2. Double-click `START_HERE.bat` (opens frontend in new window)

Both will run in separate windows!

---

### Method 3: Background Processes

**PowerShell:**
```powershell
# Start backend in background
Start-Process python -ArgumentList "backend/run.py" -WindowStyle Normal

# Start frontend in background  
Start-Process npm -ArgumentList "run", "dev" -WindowStyle Normal
```

---

## ✅ Verification

### Check Both Are Running:

**Backend:**
- Open: http://localhost:8000/api/health
- Should see: `{"status": "healthy"}`

**Frontend:**
- Open: http://localhost:5173
- Should see: Landing page

**Both:**
- ✅ Frontend can call backend API
- ✅ No port conflicts
- ✅ Working together!

---

## 🎯 What Happens When Both Run

### Frontend (Port 5173):
- Serves React application
- Makes API calls to backend
- Displays UI to users

### Backend (Port 8000):
- Handles API requests from frontend
- Processes ML calculations
- Queries Supabase database
- Returns data to frontend

### Together:
- ✅ Frontend displays data
- ✅ Backend provides ML features
- ✅ Full application functionality
- ✅ Everything works!

---

## 🔍 Quick Status Check

### Check if Ports Are in Use:

**Windows:**
```bash
netstat -ano | findstr ":5173 :8000"
```

**If ports are in use:**
- Frontend: Port 5173 ✅
- Backend: Port 8000 ✅

---

## ⚠️ Troubleshooting

### Issue: Port Already in Use

**Error:** "Port 8000 already in use"

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Error:** "Port 5173 already in use"

**Solution:**
```bash
# Find process using port 5173
netstat -ano | findstr :5173

# Kill the process
taskkill /PID <PID> /F
```

---

## 📊 Running Status

| Server | Port | Command | Status Check |
|--------|------|---------|--------------|
| Frontend | 5173 | `npm run dev` | http://localhost:5173 |
| Backend | 8000 | `python backend/run.py` | http://localhost:8000/api/health |

---

## ✅ Summary

**YES! You can run both together:**

1. ✅ **Different ports** - No conflicts
2. ✅ **Independent processes** - Can start/stop separately
3. ✅ **Work together** - Frontend calls backend API
4. ✅ **Full functionality** - All features available

**Just run both commands in separate terminals!** 🚀

---

## 🎯 Quick Start

**Right Now:**

1. **Open Terminal 1:**
   ```bash
   cd backend
   python run.py
   ```

2. **Open Terminal 2:**
   ```bash
   npm run dev
   ```

3. **Open Browser:**
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000/api/health

**That's it! Both are running together!** ✅
