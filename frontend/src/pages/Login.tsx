import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Input } from '../components/design/Input';
import { Button } from '../components/design/Button';
import { Card } from '../components/design/Card';
import { Sparkles, ShieldAlert, KeyRound, ArrowRight } from 'lucide-react';
import { cn } from '../utils/cn';

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
    return undefined;
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
    <div className="min-h-[100dvh] relative flex items-center justify-center p-4 overflow-hidden">
      {/* Aurora Background Elements Removed for Performance */}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-[420px] relative z-10"
      >
        <Card glow className="p-10">
          <div className="flex flex-col items-center mb-10 text-center">
            <motion.div 
              layoutId="auth-icon"
              className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center mb-6 shadow-lg shadow-accent-primary/20"
            >
              <AnimatePresence mode="wait">
                <motion.div
                  key={step}
                  initial={{ opacity: 0, scale: 0.5, rotate: -90 }}
                  animate={{ opacity: 1, scale: 1, rotate: 0 }}
                  exit={{ opacity: 0, scale: 0.5, rotate: 90 }}
                  transition={{ duration: 0.3 }}
                >
                  {step === 'CREDENTIALS' ? <Sparkles size={24} className="text-white" /> : <KeyRound size={24} className="text-white" />}
                </motion.div>
              </AnimatePresence>
            </motion.div>
            
            <h2 className="text-2xl font-display font-bold tracking-tight text-white mb-2">
              {step === 'CREDENTIALS' ? 'Welcome Back' : 'Security Check'}
            </h2>
            <p className="text-sm text-text-muted">
              {step === 'CREDENTIALS' 
                ? 'Sign in to continue to your ViralOps workspace.' 
                : 'Enter the 6-digit code we sent to your email address.'}
            </p>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden mb-6"
              >
                <div className="bg-danger/10 border border-danger/30 p-3 rounded-xl text-danger flex gap-3 text-sm font-medium items-center">
                  <ShieldAlert size={16} className="shrink-0" />
                  <span>{error}</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence mode="wait">
            {step === 'CREDENTIALS' ? (
              <motion.div
                key="credentials"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <form onSubmit={handleCredentialsSubmit} className="flex flex-col gap-5">
                  <Input 
                    label="Username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    placeholder="Enter username"
                  />

                  <div className="flex flex-col gap-1">
                    <Input 
                      label="Password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    <div className="flex justify-end mt-1">
                      <Link to="/forgot-password" className="text-xs font-semibold text-accent-cyan hover:text-accent-primary transition-colors">
                        Forgot Password?
                      </Link>
                    </div>
                  </div>

                  <Button type="submit" loading={loading} className="w-full mt-2" icon={<ArrowRight size={16} />}>
                    Sign In
                  </Button>
                </form>

                <div className="flex items-center my-8 gap-4">
                  <div className="flex-1 h-px bg-white/10" />
                  <span className="text-xs uppercase tracking-widest text-text-dim font-bold">Or</span>
                  <div className="flex-1 h-px bg-white/10" />
                </div>

                <Button type="button" variant="secondary" onClick={handleGoogleLogin} className="w-full">
                  <Sparkles size={16} /> Continue with Google
                </Button>
              </motion.div>
            ) : (
              <motion.div
                key="otp"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <form onSubmit={handleOTPSubmit} className="flex flex-col gap-5">
                  <Input 
                    label="6-Digit Authorization Code"
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    required
                    placeholder="000000"
                    maxLength={6}
                    className="text-center tracking-[0.5em] text-2xl font-mono py-4"
                  />

                  <Button type="submit" loading={loading} className="w-full mt-2">
                    Verify & Connect
                  </Button>

                  <div className="flex flex-col items-center gap-4 mt-4">
                    <button
                      type="button"
                      disabled={countdown > 0 || loading}
                      onClick={handleResendOTP}
                      className={cn(
                        "text-sm font-semibold transition-colors",
                        countdown > 0 ? "text-text-dim cursor-not-allowed" : "text-accent-cyan hover:text-accent-primary"
                      )}
                    >
                      {countdown > 0 ? `Resend code in ${countdown}s` : 'Request new code'}
                    </button>
                    
                    <button
                      type="button"
                      onClick={() => setStep('CREDENTIALS')}
                      className="text-xs text-text-muted hover:text-white transition-colors"
                    >
                      Back to Sign In
                    </button>
                  </div>
                </form>
              </motion.div>
            )}
          </AnimatePresence>

          {step === 'CREDENTIALS' && (
            <p className="text-sm text-text-muted text-center mt-8">
              Don't have an account? <Link to="/signup" className="text-white hover:text-accent-cyan font-semibold transition-colors">Create Account</Link>
            </p>
          )}
        </Card>
      </motion.div>
    </div>
  );
}
