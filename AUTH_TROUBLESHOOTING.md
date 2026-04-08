# 🔐 Authentication Troubleshooting Guide

## Issue: "Failed to Fetch" Error

### Common Causes:

1. **Invalid Supabase Credentials**
   - Check `.env` file has correct values
   - Verify Supabase project is active
   - Ensure keys are not expired

2. **Network/CORS Issues**
   - Supabase URL not reachable
   - CORS not configured in Supabase
   - Firewall blocking requests

3. **Supabase Project Not Set Up**
   - Authentication not enabled
   - Database tables not created
   - RLS policies blocking access

---

## ✅ Fixes Applied

### 1. Better Error Messages
- More descriptive error messages
- Specific guidance for common issues
- Network error detection

### 2. Improved Error Handling
- Graceful failure handling
- Better logging
- User-friendly messages

### 3. Connection Validation
- Checks Supabase URL reachability
- Validates credentials on startup
- Clear error messages

---

## 🔧 Quick Fixes

### Fix 1: Verify Supabase Credentials

**Check `.env` file:**
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...  # Should start with eyJ
```

**Get from Supabase Dashboard:**
1. Go to: https://app.supabase.com
2. Select your project
3. Settings → API
4. Copy Project URL and anon public key

### Fix 2: Check Supabase Project Status

- Ensure project is active (not paused)
- Check if authentication is enabled
- Verify database tables exist

### Fix 3: Test Connection

**In browser console (F12):**
```javascript
// Check if Supabase client is created
console.log(import.meta.env.VITE_SUPABASE_URL);
console.log(import.meta.env.VITE_SUPABASE_ANON_KEY);
```

---

## 🧪 Testing Authentication

### Test 1: Check Environment Variables
```javascript
// In browser console
console.log('URL:', import.meta.env.VITE_SUPABASE_URL);
console.log('Key:', import.meta.env.VITE_SUPABASE_ANON_KEY?.substring(0, 20) + '...');
```

### Test 2: Test Supabase Connection
```javascript
// In browser console
import { supabase } from './lib/supabase';
supabase.auth.getSession().then(console.log).catch(console.error);
```

### Test 3: Check Network Tab
1. Open Developer Tools (F12)
2. Go to Network tab
3. Try to sign in
4. Look for failed requests to Supabase
5. Check error details

---

## 🎯 Common Solutions

### Solution 1: Restart Dev Server
After changing `.env` file:
```bash
# Stop frontend (Ctrl+C)
# Restart
npm run dev
```

### Solution 2: Clear Browser Cache
- Clear browser cache
- Hard refresh (Ctrl+Shift+R)
- Try incognito mode

### Solution 3: Check Supabase Dashboard
- Verify project is active
- Check authentication settings
- Verify RLS policies

---

## 📋 Error Messages Explained

| Error Message | Meaning | Solution |
|---------------|--------|----------|
| "Failed to fetch" | Network/connection issue | Check Supabase URL, internet connection |
| "Invalid login credentials" | Wrong email/password | Use correct credentials |
| "User already registered" | Email exists | Sign in instead of sign up |
| "Missing Supabase variables" | .env not configured | Add credentials to .env file |

---

## ✅ Verification Checklist

- [ ] `.env` file exists in project root
- [ ] `VITE_SUPABASE_URL` is set correctly
- [ ] `VITE_SUPABASE_ANON_KEY` is set correctly
- [ ] Supabase project is active
- [ ] Authentication is enabled in Supabase
- [ ] Database tables exist (profiles table)
- [ ] Frontend dev server restarted after .env changes
- [ ] Browser cache cleared

---

**After applying fixes, try signing in again!**
