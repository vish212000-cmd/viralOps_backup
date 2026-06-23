import React, { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
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
      setError('Authorization token is missing. Please request a new link.');
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
      showToast('Password reset successfully!', 'success');
    } catch (err: any) {
      console.error(err);
      setError(err?.data?.error || 'Failed to update password. The link may have expired or is invalid.');
      showToast('Reset failed.', 'error');
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
              className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center mb-6 shadow-lg shadow-accent-primary/20"
            >
              <Sparkles size={24} className="text-white" />
            </motion.div>
            
            <h2 className="text-2xl font-display font-bold tracking-tight text-white mb-2">Set a New Password</h2>
            <p className="text-sm text-text-muted">
              Choose a strong new password for your account.
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

          {success ? (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center gap-6 text-center mt-6"
            >
              <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center border border-success/30 shadow-[0_0_20px_rgba(34,197,94,0.3)]">
                <CheckCircle size={32} className="text-success" />
              </div>
              <p className="text-sm text-text-muted">
                Your password has been updated. You can now sign in with your new credentials.
              </p>
              <Button onClick={() => navigate('/login')} className="w-full mt-4 justify-center">
                Sign In
              </Button>
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              <Input 
                label="New Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Minimum 8 characters"
              />

              <Input 
                label="Confirm New Password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                placeholder="Repeat new password"
              />

              <Button type="submit" loading={loading} className="w-full mt-2">
                Update Password
              </Button>
            </form>
          )}
        </Card>
      </motion.div>
    </div>
  );
}
