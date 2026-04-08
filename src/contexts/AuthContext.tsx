import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User } from '@supabase/supabase-js';
import { supabase, EFFECTIVE_DEMO_MODE } from '../lib/supabase';
import type { Database } from '../types/database';

type Profile = Database['public']['Tables']['profiles']['Row'];

interface AuthContextType {
  user: User | null;
  profile: Profile | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName: string, role: string, department?: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In demo mode, check localStorage for existing session
    if (EFFECTIVE_DEMO_MODE) {
      // Seed default demo user if none exist or if it needs updating
      const existingUsersStr = localStorage.getItem('demo_users');
      const users = existingUsersStr ? JSON.parse(existingUsersStr) : {};

      const defaultEmail = 'avulaneelakanta75@gmail.com';
      const defaultAdmin = {
        id: '00000000-0000-0000-0000-000000000000',
        email: defaultEmail,
        password: '22P11A0505',
        full_name: 'Avula Neelakanta',
        role: 'administrator',
        created_at: new Date().toISOString()
      };

      // Always ensure the default user exists and is up to date
      if (!users[defaultEmail] || users[defaultEmail].full_name !== defaultAdmin.full_name) {
        users[defaultEmail] = defaultAdmin;
        localStorage.setItem('demo_users', JSON.stringify(users));
        console.log('Seeded/Updated default demo user: ' + defaultEmail);

        // Force a session refresh for the new user if they were logged in as someone else
        localStorage.removeItem('demo_session');
      }

      // Check if there's a stored session
      let storedSession = localStorage.getItem('demo_session');

      // CRITICAL: For demo/submission, we used to auto-login.
      // Now we let the user see the login page for "basic protected auth".

      if (storedSession) {
        try {
          const session = JSON.parse(storedSession);
          const storedUsers = localStorage.getItem('demo_users');
          const users = storedUsers ? JSON.parse(storedUsers) : {};
          const userData = users[session.email];

          if (userData) {
            const demoUser = {
              id: userData.id,
              email: session.email,
              user_metadata: { full_name: userData.full_name }
            } as any;

            setUser(demoUser);
            setProfile({
              id: userData.id,
              email: session.email,
              full_name: userData.full_name,
              role: userData.role,
              department: userData.department,
              created_at: userData.created_at
            } as Profile);
          }
        } catch (err) {
          console.error('Error loading session:', err);
          localStorage.removeItem('demo_session');
        }
      }
      setLoading(false);
      return;
    }

    // Check for existing session
    supabase.auth.getSession()
      .then(({ data: { session }, error }) => {
        if (error) {
          console.error('Error getting session:', error);
          setLoading(false);
          return;
        }
        setUser(session?.user ?? null);
        if (session?.user) {
          loadProfile(session.user.id);
        } else {
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error('Failed to get session:', err);
        setLoading(false);
      });

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      (async () => {
        setUser(session?.user ?? null);
        if (session?.user) {
          await loadProfile(session.user.id);
        } else {
          setProfile(null);
          setLoading(false);
        }
      })();
    });

    return () => subscription.unsubscribe();
  }, []);

  async function loadProfile(userId: string) {
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .maybeSingle();

      if (error) throw error;
      setProfile(data);
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setLoading(false);
    }
  }

  async function signIn(email: string, password: string) {
    try {
      if (EFFECTIVE_DEMO_MODE) {
        // Simple local storage-based auth
        const storedUsers = localStorage.getItem('demo_users');
        const users = storedUsers ? JSON.parse(storedUsers) : {};

        // Check if user exists
        if (!users[email]) {
          throw new Error('No account found with this email. Please sign up first.');
        }

        // Check if password matches
        if (users[email].password !== password) {
          throw new Error('Invalid password. Please try again.');
        }

        // User found and password matches - sign them in
        const userData = users[email];
        const demoUser = {
          id: userData.id,
          email: email,
          user_metadata: { full_name: userData.full_name }
        } as any;

        setUser(demoUser);
        setProfile({
          id: userData.id,
          email: email,
          full_name: userData.full_name,
          role: userData.role,
          department: userData.department,
          created_at: userData.created_at
        } as Profile);

        // Save session to localStorage
        localStorage.setItem('demo_session', JSON.stringify({ email: email }));

        setLoading(false);
        return;
      }

      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        // Better error messages
        if (error.message.includes('Invalid login credentials')) {
          throw new Error('Invalid email or password. Please try again.');
        } else if (error.message.includes('Email not confirmed')) {
          throw new Error('Please check your email and confirm your account.');
        } else if (error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
          throw new Error('Unable to connect to authentication service. Please check your internet connection and Supabase configuration.');
        }
        throw new Error(error.message || 'Sign in failed. Please try again.');
      }

      if (!data.user) {
        throw new Error('Sign in failed. Please try again.');
      }
    } catch (err) {
      console.error('Sign in error:', err);
      throw err;
    }
  }

  async function signUp(email: string, password: string, fullName: string, role: string, department?: string) {
    try {
      if (EFFECTIVE_DEMO_MODE) {
        // Simple local storage-based auth
        const storedUsers = localStorage.getItem('demo_users');
        const users = storedUsers ? JSON.parse(storedUsers) : {};

        // Check if user already exists
        if (users[email]) {
          // If the user already exists in demo mode, we'll just sign them in (give access) 
          // instead of throwing an error, to satisfy the user's requirement.
          if (users[email].password === password) {
            console.log('Demo Sign-Up: User already exists, checking password and giving access...');
          } else {
            throw new Error('This email is already registered with a different password.');
          }
        }

        // Create new user
        const userId = 'demo-user-' + Date.now();
        const userData = {
          id: userId,
          email: email,
          password: password, // Store password for signin verification
          full_name: fullName,
          role: role,
          department: department || null,
          created_at: new Date().toISOString()
        };

        // Save to localStorage
        users[email] = userData;
        localStorage.setItem('demo_users', JSON.stringify(users));

        // Sign them in automatically
        const demoUser = {
          id: userId,
          email: email,
          user_metadata: { full_name: fullName }
        } as any;

        setUser(demoUser);
        setProfile({
          id: userId,
          email: email,
          full_name: fullName,
          role: role as 'faculty' | 'administrator' | 'counselor',
          department: department || null,
          created_at: userData.created_at
        } as Profile);

        // Save session to localStorage
        localStorage.setItem('demo_session', JSON.stringify({ email: email }));

        setLoading(false);
        return;
      }

      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      });

      if (error) {
        // Better error messages
        if (error.message.includes('User already registered')) {
          throw new Error('This email is already registered. Please sign in instead.');
        } else if (error.message.includes('Password')) {
          throw new Error('Password must be at least 6 characters long.');
        } else if (error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
          throw new Error('Unable to connect to authentication service. Please check your internet connection and Supabase configuration. You can enable demo mode by setting VITE_DEMO_MODE=true in .env');
        }
        throw new Error(error.message || 'Sign up failed. Please try again.');
      }

      if (!data.user) {
        throw new Error('User creation failed. Please try again.');
      }

      // Create profile
      const { error: profileError } = await supabase
        .from('profiles')
        .insert({
          id: data.user.id,
          email,
          full_name: fullName,
          role: role as 'faculty' | 'administrator' | 'counselor',
          department: department || null,
        } as any);

      if (profileError) {
        console.error('Profile creation error:', profileError);
        // Don't fail signup if profile creation fails - user is still created
        // They can update profile later
      }
    } catch (err) {
      console.error('Sign up error:', err);
      throw err;
    }
  }

  async function signOut() {
    if (EFFECTIVE_DEMO_MODE) {
      // Clear session from localStorage
      localStorage.removeItem('demo_session');
      setUser(null);
      setProfile(null);
      return;
    }

    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  }

  return (
    <AuthContext.Provider value={{ user, profile, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
