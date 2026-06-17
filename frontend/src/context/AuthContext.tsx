import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '../utils/api';

export interface UserProfile {
  username: string;
  email: string;
}

export interface Workspace {
  id: number;
  name: string;
  slug: string;
  created_at: string;
}

interface AuthContextType {
  user: UserProfile | null;
  orgs: Workspace[];
  currentOrg: Workspace | null;
  loading: boolean;
  loginInitiate: (username: string, pass: string) => Promise<void>;
  loginVerifyOTP: (username: string, otp: string) => Promise<void>;
  registerUser: (username: string, email: string, pass: string) => Promise<void>;
  logoutUser: () => void;
  selectOrg: (slug: string) => void;
  loadWorkspaces: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [orgs, setOrgs] = useState<Workspace[]>([]);
  const [currentOrg, setCurrentOrg] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initial check from localStorage
    const savedUser = localStorage.getItem('username');
    const savedToken = localStorage.getItem('access_token');
    
    if (savedUser && savedToken) {
      setUser({ username: savedUser, email: '' });
      // Fetch fresh org details
      fetchWorkspaces();
    } else {
      setLoading(false);
    }

    // Listener for auth token expirations
    const handleAuthExpired = () => {
      logoutUser();
    };
    window.addEventListener('auth-expired', handleAuthExpired);
    return () => window.removeEventListener('auth-expired', handleAuthExpired);
  }, []);

  const fetchWorkspaces = async () => {
    try {
      const workspaces = await api.get('/api/workspaces/') as Workspace[];
      setOrgs(workspaces);
      if (workspaces.length > 0) {
        const savedSlug = localStorage.getItem('current_org_slug') || workspaces[0].slug;
        const active = workspaces.find(w => w.slug === savedSlug) || workspaces[0];
        setCurrentOrg(active);
        api.setOrgSlug(active.slug);
      } else {
        setCurrentOrg(null);
        api.setOrgSlug(null);
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err);
    } finally {
      setLoading(false);
    }
  };

  const loginInitiate = async (username: string, pass: string) => {
    await api.post('/api/auth/login/', { username, password: pass });
  };

  const loginVerifyOTP = async (username: string, otp: string) => {
    const res = await api.post('/api/auth/login/verify/', { username, otp }) as { access: string; refresh: string; user: UserProfile };
    api.setToken(res.access);
    localStorage.setItem('refresh_token', res.refresh);
    localStorage.setItem('username', res.user.username);
    setUser(res.user);
    await fetchWorkspaces();
  };

  const registerUser = async (username: string, email: string, pass: string) => {
    await api.post('/api/auth/register/', { username, email, password: pass });
  };

  const logoutUser = () => {
    api.setToken(null);
    api.setOrgSlug(null);
    localStorage.clear();
    setUser(null);
    setOrgs([]);
    setCurrentOrg(null);
  };

  const selectOrg = (slug: string) => {
    const active = orgs.find(w => w.slug === slug);
    if (active) {
      setCurrentOrg(active);
      api.setOrgSlug(slug);
    }
  };

  const value: AuthContextType = {
    user,
    orgs,
    currentOrg,
    loading,
    loginInitiate,
    loginVerifyOTP,
    registerUser,
    logoutUser,
    selectOrg,
    loadWorkspaces: fetchWorkspaces
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
