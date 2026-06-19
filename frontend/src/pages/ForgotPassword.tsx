import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../utils/api';
import { Card } from '../components/design/Card';
import { Input } from '../components/design/Input';
import { Button } from '../components/design/Button';
import { useToast } from '../context/ToastContext';
import { Sparkles, ShieldAlert, KeyRound, CheckCircle, ArrowRight } from 'lucide-react';
import { cn } from '../utils/cn';

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
                  key={success ? 'SUCCESS' : step}
                  initial={{ opacity: 0, scale: 0.5, rotate: -90 }}
                  animate={{ opacity: 1, scale: 1, rotate: 0 }}
                  exit={{ opacity: 0, scale: 0.5, rotate: 90 }}
                  transition={{ duration: 0.3 }}
                >
                  {success ? <CheckCircle size={24} className="text-white" /> : (step === 'EMAIL' ? <Sparkles size={24} className="text-white" /> : <KeyRound size={24} className="text-white" />)}
                </motion.div>
              </AnimatePresence>
            </motion.div>
            
            <h2 className="text-2xl font-display font-bold tracking-tight text-white mb-2">
              {success ? 'Passkey Restored' : (step === 'EMAIL' ? 'Recover Passkey' : 'Reset Passkey')}
            </h2>
            <p className="text-sm text-text-muted">
              {success 
                ? 'Your access credentials have been securely updated.' 
                : (step === 'EMAIL' ? 'Enter your comm link to receive an authorization code.' : `We've sent a 6-digit code to your terminal. Enter it below.`)}
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
                  <span className="break-words">{error}</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence mode="wait">
            {success ? (
              <motion.div
                key="success"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center gap-4 text-center mt-6"
              >
                <Link to="/login" className="w-full">
                  <Button className="w-full justify-center">Return to Login</Button>
                </Link>
              </motion.div>
            ) : step === 'EMAIL' ? (
              <motion.div
                key="email"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <form onSubmit={handleRequestOTP} className="flex flex-col gap-5">
                  <Input 
                    label="Secure Comm Link (Email)"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="name@example.com"
                  />

                  <Button type="submit" loading={loading} className="w-full mt-2" icon={<ArrowRight size={16} />}>
                    Send Reset Code
                  </Button>
                </form>
              </motion.div>
            ) : (
              <motion.div
                key="otp"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <form onSubmit={handleResetPassword} className="flex flex-col gap-5">
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
                  
                  <Input 
                    label="New Passkey"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                  />

                  <Button type="submit" loading={loading} className="w-full mt-2">
                    Confirm Changes
                  </Button>

                  <div className="flex flex-col items-center gap-4 mt-4">
                    <button
                      type="button"
                      disabled={countdown > 0 || loading}
                      onClick={() => handleRequestOTP()}
                      className={cn(
                        "text-sm font-semibold transition-colors",
                        countdown > 0 ? "text-text-dim cursor-not-allowed" : "text-accent-cyan hover:text-accent-primary"
                      )}
                    >
                      {countdown > 0 ? `Resend code in ${countdown}s` : 'Request new code'}
                    </button>
                    
                    <button
                      type="button"
                      onClick={() => setStep('EMAIL')}
                      className="text-xs text-text-muted hover:text-white transition-colors"
                    >
                      Use a different email
                    </button>
                  </div>
                </form>
              </motion.div>
            )}
          </AnimatePresence>

          {!success && step === 'EMAIL' && (
            <p className="text-sm text-text-muted text-center mt-8">
              Remembered your passkey? <Link to="/login" className="text-white hover:text-accent-cyan font-semibold transition-colors">Establish Connection</Link>
            </p>
          )}
        </Card>
      </motion.div>
    </div>
  );
}
