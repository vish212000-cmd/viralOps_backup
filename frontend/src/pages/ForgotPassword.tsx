import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { Card } from '../components/design/Card';
import { Input } from '../components/design/Input';
import { Button } from '../components/design/Button';
import { useToast } from '../context/ToastContext';
import { Sparkles, ShieldAlert, KeyRound, CheckCircle } from 'lucide-react';

export default function ForgotPassword() {
  const [step, setStep] = useState<'EMAIL' | 'OTP'>('EMAIL');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [success, setSuccess] = useState(false);
  const { showToast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleRequestOTP = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post('/api/auth/password-reset/', { email });
      setStep('OTP');
      setCountdown(60);
      showToast('Password reset code sent!', 'success');
    } catch (err: any) {
      console.error(err);
      setError(err?.data?.error || 'Failed to send password reset code. Please try again.');
      showToast('Request failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post('/api/auth/password-reset-confirm/', { email, otp, password: newPassword });
      setSuccess(true);
      showToast('Password reset successfully!', 'success');
    } catch (err: any) {
      console.error(err);
      setError(err?.data?.error || 'Invalid code or failed to reset password.');
      showToast('Verification failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'hsl(var(--bg-main))', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
      <Card glow style={{ width: '100%', maxWidth: '420px', padding: '2.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '2.5rem' }}>
          <div style={{ background: 'linear-gradient(135deg, hsl(var(--accent-primary)), hsl(var(--accent-secondary)))', width: '48px', height: '48px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
            {success ? <CheckCircle size={24} color="#fff" /> : (step === 'EMAIL' ? <Sparkles size={24} color="#fff" /> : <KeyRound size={24} color="#fff" />)}
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'var(--font-display)' }}>
            {success ? 'Password Reset' : (step === 'EMAIL' ? 'Recover Password' : 'Reset Password')}
          </h2>
          <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem', marginTop: '0.25rem', textAlign: 'center' }}>
            {success 
              ? 'Your password has been changed successfully.' 
              : (step === 'EMAIL' ? 'Enter your email to receive a reset code' : `We've sent a 6-digit code to your email. Enter it below.`)}
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
            <Link to="/login" style={{ width: '100%', marginTop: '1rem' }}>
              <Button style={{ width: '100%', justifyContent: 'center' }}>Back to Sign In</Button>
            </Link>
          </div>
        ) : step === 'EMAIL' ? (
          <form onSubmit={handleRequestOTP} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Input 
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="name@example.com"
            />

            <Button type="submit" loading={loading} style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
              Send Reset Code
            </Button>
          </form>
        ) : (
          <form onSubmit={handleResetPassword} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Input 
              label="6-Digit Verification Code"
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              required
              placeholder="000000"
              maxLength={6}
              style={{ textAlign: 'center', letterSpacing: '0.25em', fontSize: '1.25rem' }}
            />
            
            <Input 
              label="New Password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />

            <Button type="submit" loading={loading} style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
              Reset Password
            </Button>

            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '0.5rem' }}>
              <button
                type="button"
                disabled={countdown > 0 || loading}
                onClick={() => handleRequestOTP()}
                style={{
                  background: 'none', border: 'none', 
                  color: countdown > 0 ? 'hsl(var(--text-dim))' : 'hsl(var(--accent-primary))', 
                  cursor: countdown > 0 ? 'not-allowed' : 'pointer',
                  fontSize: '0.85rem', fontWeight: 500, textDecoration: countdown > 0 ? 'none' : 'underline'
                }}
              >
                {countdown > 0 ? `Resend code in ${countdown}s` : 'Resend code'}
              </button>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1rem' }}>
              <button
                type="button"
                onClick={() => setStep('EMAIL')}
                style={{
                  background: 'none', border: 'none', 
                  color: 'hsl(var(--text-muted))', 
                  cursor: 'pointer',
                  fontSize: '0.8rem', textDecoration: 'underline'
                }}
              >
                Change Email
              </button>
            </div>
          </form>
        )}

        {!success && step === 'EMAIL' && (
          <p style={{ color: 'hsl(var(--text-dim))', fontSize: '0.85rem', textAlign: 'center', marginTop: '2rem' }}>
            Remembered your password? <Link to="/login" style={{ color: 'hsl(var(--accent-primary))', textDecoration: 'none', fontWeight: 600 }}>Sign in</Link>
          </p>
        )}
      </Card>
    </div>
  );
}
