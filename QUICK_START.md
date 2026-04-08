# Quick Start Guide - See the Application Running

## Step 1: Start the Frontend (Works Immediately)

The frontend can run even without the backend - it will connect directly to Supabase.

```bash
cd project
npm run dev
```

This will start the frontend on `http://localhost:5173`

## Step 2: Start the Backend (Requires .env file)

### Option A: With Supabase Credentials

1. Create `.env` file in `backend/` folder:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

2. Start backend:
```bash
cd backend
python run.py
```

Backend will run on `http://localhost:8000`

### Option B: Demo Mode (Without Real Database)

The frontend will work with mock data if Supabase is not configured.

## What You'll See

### Frontend (http://localhost:5173)
- Landing page with "Get Started" button
- Login/Signup page
- Dashboard with student statistics
- Student list with risk assessments
- Individual student profiles
- Alerts page
- Interventions page
- Risk analysis charts
- Planning & analytics

### Backend API (http://localhost:8000)
- Health check: `http://localhost:8000/api/health`
- API docs: `http://localhost:8000/docs`
- Students endpoint: `http://localhost:8000/api/students`

## Troubleshooting

### Frontend won't start
- Make sure you're in the `project` directory
- Run `npm install` first if needed

### Backend won't start
- Check `.env` file exists in `backend/` folder
- Verify Supabase credentials are correct
- Check Python version: `python --version` (needs 3.8+)

### No data showing
- This is normal if database is empty
- You can add test data through the UI or directly in Supabase
