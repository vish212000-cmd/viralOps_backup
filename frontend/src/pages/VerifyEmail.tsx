import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../utils/api';
import { Card } from '../components/design/Card';
import { Button } from '../components/design/Button';
import { useToast } from '../context/ToastContext';
import { CheckCircle, ShieldAlert, Loader2, Sparkles } from 'lucide-react';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const [statusState, setStatusState] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const { showToast } = useToast();
  const navigate = useNavigate();

  const token = searchParams.get('token');

  useEffect(() => {
    if (!token) {
      setStatusState('error');
      setMessage('Verification token is missing. Please click the link in your email again.');
      return;
    }

    const verifyToken = async () => {
      try {
        const res = await api.post('/api/auth/verify-email/', { token });
        setStatusState('success');
        setMessage(res.message || 'Your email has been verified successfully!');
        showToast('Email verified successfully!', 'success');
      } catch (err: any) {
        console.error(err);
        setStatusState('error');
        setMessage(err?.data?.error || 'Failed to verify email. The link may have expired or is invalid.');
        showToast('Verification failed.', 'error');
      }
    };

    verifyToken();
  }, [token]);

  return (
    <div style={{ minHeight: '100vh', background: 'hsl(var(--bg-main))', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
      <Card glow style={{ width: '100%', maxWidth: '440px', padding: '2.5rem', textAlign: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '2rem' }}>
          <div style={{ background: 'linear-gradient(135deg, hsl(var(--accent-primary)), hsl(var(--accent-secondary)))', width: '48px', height: '48px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
            <Sparkles size={24} color="#fff" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'var(--font-display)' }}>Email Verification</h2>
        </div>

        {statusState === 'loading' && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', margin: '2rem 0' }}>
            <Loader2 className="loading-spinner" size={40} color="hsl(var(--accent-primary))" />
            <p style={{ color: 'hsl(var(--text-muted))' }}>Verifying your email address, please wait...</p>
          </div>
        )}

        {statusState === 'success' && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem', margin: '2rem 0' }}>
            <div style={{ background: 'hsl(var(--success) / 0.1)', color: 'hsl(var(--success))', width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CheckCircle size={36} />
            </div>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: '1.5' }}>{message}</p>
            <Button onClick={() => navigate('/login')} style={{ width: '100%', justifyContent: 'center', marginTop: '1rem' }}>
              Sign In to Account
            </Button>
          </div>
        )}

        {statusState === 'error' && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem', margin: '2rem 0' }}>
            <div style={{ background: 'hsl(var(--danger) / 0.1)', color: 'hsl(var(--danger))', width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldAlert size={36} />
            </div>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: '1.5' }}>{message}</p>
            
            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1rem' }}>
              <Button onClick={() => navigate('/login')} variant="secondary" style={{ width: '100%', justifyContent: 'center' }}>
                Back to Sign In
              </Button>
            </div>
          </div>
        )}

        <p style={{ color: 'hsl(var(--text-dim))', fontSize: '0.85rem', marginTop: '1.5rem' }}>
          Need help? <Link to="/support" style={{ color: 'hsl(var(--accent-primary))', textDecoration: 'none' }}>Contact support</Link>
        </p>
      </Card>
    </div>
  );
}
