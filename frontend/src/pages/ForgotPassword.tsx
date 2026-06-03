import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../utils/api';
import { Card } from '../components/design/Card';
import { Input } from '../components/design/Input';
import { Button } from '../components/design/Button';
import { useToast } from '../context/ToastContext';
import { Sparkles, ShieldAlert, CheckCircle } from 'lucide-react';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const { showToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post('/api/auth/password-reset/', { email });
      setSuccess(true);
      showToast('Password reset link sent!', 'success');
    } catch (err: any) {
      console.error(err);
      setError(err?.data?.error || 'Failed to send password reset link. Please try again.');
      showToast('Request failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'hsl(var(--bg-main))', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
      <Card glow style={{ width: '100%', maxWidth: '420px', padding: '2.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '2.5rem' }}>
          <div style={{ background: 'linear-gradient(135deg, hsl(var(--accent-primary)), hsl(var(--accent-secondary)))', width: '48px', height: '48px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
            <Sparkles size={24} color="#fff" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'var(--font-display)' }}>Recover Password</h2>
          <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem', marginTop: '0.25rem', textAlign: 'center' }}>
            Enter your email to receive a password reset link
          </p>
        </div>

        {error && (
          <div style={{ background: 'hsl(var(--danger) / 0.1)', border: '1px solid hsl(var(--danger) / 0.3)', padding: '0.75rem 1rem', borderRadius: '8px', color: 'hsl(var(--danger))', display: 'flex', gap: '0.5rem', alignItems: 'flex-start', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
            <ShieldAlert size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{error}</span>
          </div>
        )}

        {success ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', textAlign: 'center', margin: '1.5rem 0' }}>
            <div style={{ background: 'hsl(var(--success) / 0.1)', color: 'hsl(var(--success))', width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CheckCircle size={24} />
            </div>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem', lineHeight: '1.5' }}>
              If an account is registered with this email, we have sent instructions to reset your password. Please check your inbox.
            </p>
            <Link to="/login" style={{ width: '100%', marginTop: '1rem' }}>
              <Button style={{ width: '100%', justifyContent: 'center' }}>Back to Sign In</Button>
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Input 
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="name@example.com"
            />

            <Button type="submit" loading={loading} style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
              Send Reset Link
            </Button>
          </form>
        )}

        {!success && (
          <p style={{ color: 'hsl(var(--text-dim))', fontSize: '0.85rem', textAlign: 'center', marginTop: '2rem' }}>
            Remembered your password? <Link to="/login" style={{ color: 'hsl(var(--accent-primary))', textDecoration: 'none', fontWeight: 600 }}>Sign in</Link>
          </p>
        )}
      </Card>
    </div>
  );
}
