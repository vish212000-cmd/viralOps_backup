import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Input } from '../components/design/Input';
import { Button } from '../components/design/Button';
import { Card } from '../components/design/Card';
import { Sparkles, ShieldAlert, KeyRound } from 'lucide-react';

export default function Login() {
  const [step, setStep] = useState<'CREDENTIALS' | 'OTP'>('CREDENTIALS');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);
  
  const { loginInitiate, loginVerifyOTP } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await loginInitiate(username, password);
      showToast('Verification code sent to your email!', 'success');
      setStep('OTP');
      setCountdown(60);
    } catch (err: any) {
      console.error(err);
      setError(err?.data?.detail || 'Invalid username or password. Please try again.');
      showToast('Authentication failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setError('');
    setLoading(true);
    try {
      await loginInitiate(username, password);
      showToast('A new verification code has been sent!', 'success');
      setCountdown(60);
    } catch (err: any) {
      setError(err?.data?.detail || 'Failed to resend OTP. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleOTPSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await loginVerifyOTP(username, otp);
      showToast('Successfully signed in!', 'success');
      navigate('/dashboard');
    } catch (err: any) {
      console.error(err);
      setError(err?.data?.detail || 'Invalid verification code. Please try again.');
      showToast('Verification failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    const clientId = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID || '';
    const redirectUri = encodeURIComponent(`${window.location.origin}/auth/google/callback`);
    
    if (!clientId) {
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
            {step === 'CREDENTIALS' ? <Sparkles size={24} color="#fff" /> : <KeyRound size={24} color="#fff" />}
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'var(--font-display)' }}>
            {step === 'CREDENTIALS' ? 'Welcome Back' : 'Verify Login'}
          </h2>
          <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem', marginTop: '0.25rem', textAlign: 'center' }}>
            {step === 'CREDENTIALS' 
              ? 'Sign in to manage your workspaces' 
              : `We've sent a 6-digit code to your email. Enter it below.`}
          </p>
        </div>

        {error && (
          <div style={{ background: 'hsl(var(--danger) / 0.1)', border: '1px solid hsl(var(--danger) / 0.3)', padding: '0.75rem 1rem', borderRadius: '8px', color: 'hsl(var(--danger))', display: 'flex', gap: '0.5rem', alignItems: 'flex-start', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
            <ShieldAlert size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{error}</span>
          </div>
        )}

        {step === 'CREDENTIALS' ? (
          <>
            <form onSubmit={handleCredentialsSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
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
          </>
        ) : (
          <form onSubmit={handleOTPSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
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

            <Button type="submit" loading={loading} style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
              Verify & Sign In
            </Button>

            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '0.5rem' }}>
              <button
                type="button"
                disabled={countdown > 0 || loading}
                onClick={handleResendOTP}
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
                onClick={() => setStep('CREDENTIALS')}
                style={{
                  background: 'none', border: 'none', 
                  color: 'hsl(var(--text-muted))', 
                  cursor: 'pointer',
                  fontSize: '0.8rem', textDecoration: 'underline'
                }}
              >
                Back to Login
              </button>
            </div>
          </form>
        )}

        {step === 'CREDENTIALS' && (
          <p style={{ color: 'hsl(var(--text-dim))', fontSize: '0.85rem', textAlign: 'center', marginTop: '2rem' }}>
            Don't have an account? <Link to="/signup" style={{ color: 'hsl(var(--accent-primary))', textDecoration: 'none', fontWeight: 600 }}>Sign up</Link>
          </p>
        )}
      </Card>
    </div>
  );
}
