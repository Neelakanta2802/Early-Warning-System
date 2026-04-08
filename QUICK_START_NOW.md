# 🚀 Quick Start - Start Both Servers Now!

## ✅ Status Check

### Backend: ✅ Configured
- ✅ `.env` file exists
- ✅ Supabase credentials loaded
- ✅ Ready to start!

### Frontend: ⚠️ Check Needed
- ⚠️ Verify `.env` file in project root
- ⚠️ Should have `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`

---

## 🎯 Start Both Servers

### Option 1: Two Terminal Windows (Recommended)

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

### Option 2: Use Batch Files

**Double-click these files:**
1. `START_BACKEND.bat` (starts backend)
2. `START_HERE.bat` (starts frontend)

---

## ✅ Verification

### 1. Check Backend (Port 8000)
Open browser: http://localhost:8000/api/health

**Expected Response:**
```json
{"status": "healthy"}
```

### 2. Check Frontend (Port 5173)
Open browser: http://localhost:5173

**Expected:** Landing page with "Early Warning System"

### 3. Check API Docs
Open browser: http://localhost:8000/docs

**Expected:** Interactive API documentation

---

## 🎉 You're Ready!

Once both servers are running:
- ✅ Frontend: http://localhost:5173
- ✅ Backend: http://localhost:8000
- ✅ API Docs: http://localhost:8000/docs

**Start the servers and you're good to go!** 🚀
