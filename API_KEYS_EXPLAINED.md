# API Keys Explained - Frontend vs Backend

## 🔑 Key Summary

### Frontend API Keys
- **Supabase Anon Key** (Public, Safe for Frontend)
- **No separate API key needed** for backend communication

### Backend API Keys
- **Supabase Service Role Key** (Private, Server-Side Only)
- **No separate API key needed** for frontend communication

---

## 📱 FRONTEND API KEYS

### 1. Supabase Anon Key (Required)
```env
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**What it is:**
- Public anonymous key from Supabase
- Safe to expose in frontend code
- Limited permissions (respects Row Level Security)

**What it's used for:**
- Direct database queries from frontend
- User authentication (login/signup)
- Reading data from Supabase tables
- Subject to Row Level Security (RLS) policies

**Where to get it:**
- Supabase Dashboard → Settings → API → **anon public** key

**Security:**
- ✅ Safe to expose in frontend
- ✅ Protected by RLS policies
- ✅ Limited permissions

---

### 2. Backend API URL (Optional)
```env
VITE_API_URL=http://localhost:8000
```

**What it is:**
- Just a URL, not an API key
- Defaults to `http://localhost:8000` if not set

**What it's used for:**
- Frontend knows where to find the backend API
- Used by `apiClient` in `src/lib/api.ts`

**Security:**
- ✅ Just a URL, no authentication needed
- ✅ Backend has CORS configured (allows frontend)

---

## 🔴 BACKEND API KEYS

### 1. Supabase Service Role Key (Required)
```env
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**What it is:**
- Private service role key from Supabase
- **MUST be kept secret** (server-side only)
- Full database permissions (bypasses RLS)

**What it's used for:**
- Backend database operations
- Creating/updating/deleting records
- Administrative operations
- ML model data access

**Where to get it:**
- Supabase Dashboard → Settings → API → **service_role** key

**Security:**
- ⚠️ **NEVER expose in frontend**
- ⚠️ **Keep it secret**
- ⚠️ Full permissions - use carefully

---

### 2. Supabase Anon Key (Required)
```env
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**What it is:**
- Same anon key as frontend uses
- Used for some backend operations

**Why backend needs it:**
- Some operations may use anon key
- Consistency with frontend

---

## 🔐 Authentication Flow

### Frontend → Supabase
```
Frontend (with anon key)
    ↓
Supabase Database
    ↓
RLS Policies Check
    ↓
Data Returned (if authorized)
```

### Backend → Supabase
```
Backend (with service_role key)
    ↓
Supabase Database
    ↓
Full Access (bypasses RLS)
    ↓
Data Returned
```

### Frontend → Backend
```
Frontend
    ↓
HTTP Request (no API key needed)
    ↓
Backend API (CORS allows frontend)
    ↓
Response Returned
```

**Note:** Frontend doesn't need an API key to call backend - CORS is configured to allow requests.

---

## 📋 Complete API Key List

### Frontend `.env`
```env
# Required
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...  # anon public key

# Optional
VITE_API_URL=http://localhost:8000  # Just a URL, not a key
```

### Backend `.env`
```env
# Required
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJ...  # service_role key (PRIVATE)
SUPABASE_ANON_KEY=eyJ...  # anon public key
```

---

## 🔍 Key Differences

| Aspect | Frontend Anon Key | Backend Service Key |
|--------|------------------|---------------------|
| **Type** | Public | Private |
| **Permissions** | Limited (RLS enforced) | Full (bypasses RLS) |
| **Exposure** | Safe in frontend code | Must be secret |
| **Use Case** | User-facing operations | Admin/ML operations |
| **Security** | Protected by RLS | Full access |

---

## 🚨 Security Best Practices

### ✅ DO:
- ✅ Use anon key in frontend
- ✅ Use service_role key only in backend
- ✅ Keep `.env` files in `.gitignore`
- ✅ Never commit keys to version control
- ✅ Use service_role key for admin operations only

### ❌ DON'T:
- ❌ Never use service_role key in frontend
- ❌ Never expose service_role key in client code
- ❌ Never commit `.env` files
- ❌ Never share service_role key publicly

---

## 🎯 Quick Reference

### Frontend Needs:
1. **VITE_SUPABASE_ANON_KEY** - Public anon key (safe for frontend)
2. **VITE_API_URL** - Just the backend URL (not a key)

### Backend Needs:
1. **SUPABASE_KEY** - Service role key (private, secret)
2. **SUPABASE_ANON_KEY** - Anon key (same as frontend)

### No Separate API Keys Needed:
- ❌ No API key for frontend → backend communication
- ❌ No API key for backend → frontend communication
- ❌ No external service API keys
- ✅ Just Supabase keys

---

## 📝 Example Configuration

### Frontend `.env` (project/.env)
```env
# Supabase (Public Keys - Safe for Frontend)
VITE_SUPABASE_URL=https://abcdefghijklmnop.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYxNjIzOTAyMiwiZXhwIjoxOTMxODE1MDIyfQ.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Backend URL (Not a Key - Just a URL)
VITE_API_URL=http://localhost:8000
```

### Backend `.env` (project/backend/.env)
```env
# Supabase (Private Service Key - Keep Secret!)
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjE2MjM5MDIyLCJleHAiOjE5MzE4MTUwMjJ9.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYxNjIzOTAyMiwiZXhwIjoxOTMxODE1MDIyfQ.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🔄 How They Work Together

```
┌─────────────┐
│   Frontend   │
│              │
│ Uses:        │
│ • anon key   │ ────┐
└─────────────┘     │
                    │
                    │ Both connect to
                    │
┌─────────────┐     │     ┌─────────────┐
│   Backend   │     │     │  Supabase   │
│             │     │     │             │
│ Uses:       │ ────┘     │  Database   │
│ • service   │           │             │
│   role key  │ ──────────┘             │
└─────────────┘                         │
                                        │
┌─────────────┐                         │
│   Frontend  │ ────────────────────────┘
│             │
│ → Backend   │ (No API key needed)
│   API       │ (Just HTTP requests)
└─────────────┘
```

---

## ✅ Summary

**Frontend API Keys:**
- ✅ `VITE_SUPABASE_ANON_KEY` - Public anon key (required)
- ✅ `VITE_API_URL` - Just a URL, not a key (optional)

**Backend API Keys:**
- ✅ `SUPABASE_KEY` - Service role key (required, private)
- ✅ `SUPABASE_ANON_KEY` - Anon key (required)

**No Separate API Keys:**
- ❌ No API key for frontend ↔ backend communication
- ❌ No external service API keys needed
- ✅ Communication is via HTTP (CORS configured)

---

**Bottom Line:** You only need Supabase keys - no separate API keys for frontend-backend communication!
