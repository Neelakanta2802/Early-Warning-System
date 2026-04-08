# 🔗 Verifying Frontend-Backend Connection

## ✅ Connection Test

### Step 1: Verify Both Servers Running

**Backend:**
```bash
curl http://localhost:8000/api/health
```
**Expected:** `{"status": "healthy"}`

**Frontend:**
Open: http://localhost:5173
**Expected:** Landing page loads

---

### Step 2: Test API Connection from Frontend

1. **Open Browser Console** (F12)
2. **Navigate to Student Profile** page
3. **Check Network Tab**
4. **Look for requests to `localhost:8000`**

**Expected:**
- API calls to backend
- No CORS errors
- Successful responses

---

### Step 3: Test Backend API Directly

**Get Students:**
```bash
curl http://localhost:8000/api/students
```

**Get Model Info:**
```bash
curl http://localhost:8000/api/ml/model/info
```

---

## 🔍 Troubleshooting Connection

### Issue: CORS Errors

**Symptom:** Browser console shows CORS errors

**Solution:**
- Backend CORS is configured (allows all origins)
- Verify backend is running
- Check backend logs

### Issue: API Not Responding

**Symptom:** Frontend can't reach backend

**Solution:**
1. Verify backend is running: http://localhost:8000/api/health
2. Check `VITE_API_URL` in frontend `.env`
3. Should be: `VITE_API_URL=http://localhost:8000`

### Issue: 404 Errors

**Symptom:** API endpoints return 404

**Solution:**
- Verify backend started successfully
- Check backend logs for errors
- Ensure all routes are registered

---

## ✅ Success Indicators

### When Everything Works Together:

1. **Frontend loads** ✅
2. **Backend responds** ✅
3. **API calls succeed** ✅
4. **No CORS errors** ✅
5. **Data flows correctly** ✅

---

## 🧪 Quick Test

### Test in Browser:

1. Open http://localhost:5173
2. Open Developer Tools (F12)
3. Go to Network tab
4. Navigate to a student profile
5. Look for API calls to `localhost:8000`
6. Check if they succeed (200 status)

---

**Both servers working together means:**
- Frontend can call backend API
- Backend processes requests
- Data flows between them
- ML features available (if model trained)
