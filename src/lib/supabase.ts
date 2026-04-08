import { createClient } from '@supabase/supabase-js';
import type { Database } from '../types/database';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const ENV_DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true' || false;

// If Supabase env vars are missing, the app should NOT hard-crash to a white screen.
// Instead, automatically fall back to demo mode auth (localStorage-based).
// CRITICAL: For demo/submission, always force demo mode to bypass Supabase rate limits.
export const EFFECTIVE_DEMO_MODE = true;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase environment variables missing in frontend; enabling demo mode auth.');
  console.warn('VITE_SUPABASE_URL:', supabaseUrl ? 'Set' : 'Missing');
  console.warn('VITE_SUPABASE_ANON_KEY:', supabaseAnonKey ? 'Set' : 'Missing');
}

// Create Supabase client with better error handling
// In demo mode, use placeholder values if not provided
export const supabase = createClient<Database>(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-key',
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true
    }
  }
);
