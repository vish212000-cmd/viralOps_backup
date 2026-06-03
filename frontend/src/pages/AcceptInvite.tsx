import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../utils/api';
import { Card } from '../components/design/Card';
import { Button } from '../components/design/Button';
import { useToast } from '../context/ToastContext';
import { CheckCircle, ShieldAlert, Loader2, Sparkles } from 'lucide-react';

export default function AcceptInvite() {
  const [searchParams] = useSearchParams();
  const [statusState, setStatusState] = useState<'loading' | 'unauthenticated' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const { showToast } = useToast();
  const navigate = useNavigate();

  const token = searchParams.get('token');

  useEffect(() => {
    if (!token) {
      setStatusState('error');
      setMessage('Invitation token is missing. Please check your invitation link again.');
      return;
    }

    const checkAndAccept = async () => {
      const accessToken = localStorage.getItem('access_token');
      if (!accessToken) {
        setStatusState('unauthenticated');
        setMessage('You must be logged in to accept this workspace invitation.');
        return;
      }

      try {
        const res = await api.post('/api/workspaces/accept-invite/', { token });
        setStatusState('success');
        setMessage(res.message || 'Invitation accepted successfully!');
        showToast('Joined workspace successfully!', 'success');
        
        // Update local workspaces list
        if (res.organization && res.organization.slug) {
          localStorage.setItem('current_org_slug', res.organization.slug);
        }
        
        setTimeout(() => {
          navigate('/dashboard');
        }, 2000);
      } catch (err: any) {
        console.error(err);
        if (err.status === 401) {
          setStatusState('unauthenticated');
          setMessage('You must be logged in to accept this workspace invitation.');
        } else {
          setStatusState('error');
          setMessage(err?.data?.error || 'Failed to accept invitation. The link may be expired, invalid, or sent to a different email address.');
          showToast('Failed to accept invitation.', 'error');
        }
      }
    };

    checkAndAccept();
  }, [token]);

  const handleLoginRedirect = () => {
    navigate(`/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`);
  };

  const handleSignupRedirect = () => {
    navigate(`/signup?next=${encodeURIComponent(window.location.pathname + window.location.search)}`);
  };

  return (
    <div style={{ minHeight: '100vh', background: 'hsl(var(--bg-main))', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
      <Card glow style={{ width: '100%', maxWidth: '440px', padding: '2.5rem', textAlign: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '2rem' }}>
          <div style={{ background: 'linear-gradient(135deg, hsl(var(--accent-primary)), hsl(var(--accent-secondary)))', width: '48px', height: '48px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
            <Sparkles size={24} color="#fff" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'var(--font-display)' }}>Workspace Invitation</h2>
        </div>

        {statusState === 'loading' && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', margin: '2rem 0' }}>
            <Loader2 className="loading-spinner" size={40} color="hsl(var(--accent-primary))" />
            <p style={{ color: 'hsl(var(--text-muted))' }}>Accepting invitation, please wait...</p>
          </div>
        )}

        {statusState === 'success' && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem', margin: '2rem 0' }}>
            <div style={{ background: 'hsl(var(--success) / 0.1)', color: 'hsl(var(--success))', width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CheckCircle size={36} />
            </div>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: '1.5' }}>{message}</p>
            <p style={{ color: 'hsl(var(--text-dim))', fontSize: '0.85rem' }}>Redirecting you to the dashboard...</p>
          </div>
        )}

        {statusState === 'unauthenticated' && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem', margin: '1.5rem 0' }}>
            <div style={{ background: 'hsl(var(--warning) / 0.1)', color: 'hsl(var(--warning))', width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldAlert size={36} />
            </div>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: '1.5' }}>{message}</p>
            
            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1rem' }}>
              <Button onClick={handleLoginRedirect} style={{ width: '100%', justifyContent: 'center' }}>
                Sign In
              </Button>
              <Button onClick={handleSignupRedirect} variant="secondary" style={{ width: '100%', justifyContent: 'center' }}>
                Create Account
              </Button>
            </div>
          </div>
        )}

        {statusState === 'error' && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem', margin: '2rem 0' }}>
            <div style={{ background: 'hsl(var(--danger) / 0.1)', color: 'hsl(var(--danger))', width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldAlert size={36} />
            </div>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: '1.5' }}>{message}</p>
            
            <Button onClick={() => navigate('/login')} style={{ width: '100%', justifyContent: 'center', marginTop: '1rem' }}>
              Back to Sign In
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
