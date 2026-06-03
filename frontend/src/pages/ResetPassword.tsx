import React, { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../utils/api';
import { Card } from '../components/design/Card';
import { Input } from '../components/design/Input';
import { Button } from '../components/design/Button';
import { useToast } from '../context/ToastContext';
import { Sparkles, ShieldAlert, CheckCircle } from 'lucide-react';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const { showToast } = useToast();
  const navigate = useNavigate();

  const token = searchParams.get('token');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!token) {
      setError('Password reset token is missing. Please request a new link.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);

    try {
      await api.post('/api/auth/password-reset-confirm/', { token, password });
      setSuccess(true);
      showToast('Password reset successful!', 'success');
    } catch (err: any) {
      console.error(err);
      setError(err?.data?.error || 'Failed to reset password. The link may have expired or is invalid.');
      showToast('Reset failed.', 'error');
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
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'var(--font-display)' }}>Reset Password</h2>
          <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem', marginTop: '0.25rem', textAlign: 'center' }}>
            Choose a secure new password for your account
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
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem' }}>
              Your password has been successfully reset. You can now log in with your new credentials.
            </p>
            <Button onClick={() => navigate('/login')} style={{ width: '100%', marginTop: '1rem', justifyContent: 'center' }}>
              Sign In
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Input 
              label="New Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Create secure password"
            />

            <Input 
              label="Confirm New Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              placeholder="Confirm new password"
            />

            <Button type="submit" loading={loading} style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
              Save Password
            </Button>
          </form>
        )}
      </Card>
    </div>
  );
}
