import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Input } from '../components/design/Input';
import { Button } from '../components/design/Button';
import { Card } from '../components/design/Card';
import { Sparkles, ShieldAlert } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { loginUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await loginUser(username, password);
      showToast('Successfully signed in!', 'success');
      navigate('/dashboard');
    } catch (err: any) {
      console.error(err);
      setError(err?.data?.detail || 'Invalid username or password. Please try again.');
      showToast('Authentication failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    const clientId = (window as any).VITE_GOOGLE_OAUTH_CLIENT_ID || '';
    const redirectUri = encodeURIComponent(`${window.location.origin}/auth/google/callback`);
    
    if (!clientId) {
      // Offline fallback: navigate straight to callback with mock token
      navigate(`/auth/google/callback?code=mock_google_code`);
    } else {
      window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=${clientId}&redirect_uri=${redirectUri}&scope=profile%20email`;
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'hsl(var(--bg-main))', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
      <Card glow style={{ width: '100%', maxWidth: '420px', padding: '2.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '2.5rem' }}>
          <div style={{ background: 'linear-gradient(135deg, hsl(var(--accent-primary)), hsl(var(--accent-secondary)))', width: '48px', height: '48px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
            <Sparkles size={24} color="#fff" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'var(--font-display)' }}>Welcome Back</h2>
          <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem', marginTop: '0.25rem' }}>Sign in to manage your workspaces</p>
        </div>

        {error && (
          <div style={{ background: 'hsl(var(--danger) / 0.1)', border: '1px solid hsl(var(--danger) / 0.3)', padding: '0.75rem 1rem', borderRadius: '8px', color: 'hsl(var(--danger))', display: 'flex', gap: '0.5rem', alignItems: 'flex-start', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
            <ShieldAlert size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <Input 
            label="Username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            placeholder="Enter your username"
          />

          <Input 
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '-0.75rem' }}>
            <Link to="/forgot-password" style={{ color: 'hsl(var(--accent-primary))', textDecoration: 'none', fontSize: '0.8rem', fontWeight: 500 }}>
              Forgot password?
            </Link>
          </div>

          <Button type="submit" loading={loading} style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
            Sign In
          </Button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', margin: '1.5rem 0', gap: '0.75rem' }}>
          <div style={{ flex: 1, height: '1px', background: 'hsl(var(--border-muted))' }} />
          <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-dim))', textTransform: 'uppercase' }}>or</span>
          <div style={{ flex: 1, height: '1px', background: 'hsl(var(--border-muted))' }} />
        </div>

        <Button type="button" variant="secondary" onClick={handleGoogleLogin} style={{ width: '100%', justifyContent: 'center' }}>
          <Sparkles size={16} /> Continue with Google
        </Button>

        <p style={{ color: 'hsl(var(--text-dim))', fontSize: '0.85rem', textAlign: 'center', marginTop: '2rem' }}>
          Don't have an account? <Link to="/signup" style={{ color: 'hsl(var(--accent-primary))', textDecoration: 'none', fontWeight: 600 }}>Sign up</Link>
        </p>
      </Card>
    </div>
  );
}
