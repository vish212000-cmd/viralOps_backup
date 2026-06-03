import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../utils/api';
import { useToast } from '../context/ToastContext';
import { Loader2, ShieldAlert } from 'lucide-react';
import { Card } from '../components/design/Card';

export default function GoogleCallback() {
  const [searchParams] = useSearchParams();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    const oauthError = searchParams.get('error');

    if (oauthError) {
      setError(`Google OAuth failed: ${oauthError}`);
      showToast('Google login rejected.', 'error');
      return;
    }

    if (!code) {
      setError('OAuth authorization code not found in URL query parameters.');
      return;
    }

    exchangeCode(code);
  }, [searchParams]);

  const exchangeCode = async (code: string) => {
    try {
      const redirectUri = `${window.location.origin}/auth/google/callback`;
      const res = await api.post('/api/auth/google/', {
        code,
        redirect_uri: redirectUri
      }) as { access: string; refresh: string; user: { username: string; email: string } };

      // Set API client token and update local storage parameters
      api.setToken(res.access);
      localStorage.setItem('refresh_token', res.refresh);
      localStorage.setItem('username', res.user.username);

      showToast('Successfully signed in with Google!', 'success');
      
      // Redirect using location reload to force AuthProvider to re-initialize from storage
      window.location.href = '/dashboard';
    } catch (err: any) {
      console.error(err);
      setError(err?.data?.error || 'Failed to exchange authorization token with backend.');
      showToast('Google OAuth verification failed.', 'error');
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'hsl(var(--bg-main))', padding: '1rem' }}>
      <Card glow style={{ width: '100%', maxWidth: '420px', padding: '2.5rem', textAlign: 'center' }}>
        {error ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
            <ShieldAlert size={48} color="hsl(var(--danger))" />
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Authentication Error</h3>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem', lineHeight: 1.5 }}>{error}</p>
            <Button variant="secondary" onClick={() => navigate('/login')} style={{ marginTop: '1rem' }}>
              Back to Login
            </Button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem' }}>
            <Loader2 className="loading-spinner" size={40} />
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Verifying credentials...</h3>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem' }}>
              Exchanging secure tokens with Google accounts services.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}

// Inline button import fallback just in case
function Button({ children, onClick, variant, style }: any) {
  const isSec = variant === 'secondary';
  return (
    <button 
      onClick={onClick}
      style={{
        backgroundColor: isSec ? 'transparent' : 'hsl(var(--accent-primary))',
        color: '#fff',
        border: isSec ? '1px solid hsl(var(--border-muted))' : 'none',
        borderRadius: '8px',
        padding: '0.6rem 1.2rem',
        cursor: 'pointer',
        fontSize: '0.9rem',
        fontWeight: 600,
        ...style
      }}
    >
      {children}
    </button>
  );
}
