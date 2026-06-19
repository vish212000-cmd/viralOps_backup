import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../utils/api';
import { Card } from '../components/design/Card';
import { Button } from '../components/design/Button';
import { useToast } from '../context/ToastContext';
import { CheckCircle, ShieldAlert, Sparkles } from 'lucide-react';

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
      setMessage('Authorization token is missing. Please initiate a new connection sequence.');
      return;
    }

    const verifyToken = async () => {
      try {
        const res = await api.post('/api/auth/verify-email/', { token });
        setStatusState('success');
        setMessage(res.message || 'Comm link successfully verified and secured.');
        showToast('Connection secured!', 'success');
      } catch (err: any) {
        console.error(err);
        setStatusState('error');
        setMessage(err?.data?.error || 'Verification failed. The token may be corrupted or expired.');
        showToast('Verification failed.', 'error');
      }
    };

    verifyToken();
  }, [token]);

  return (
    <div className="min-h-[100dvh] relative flex items-center justify-center p-4 overflow-hidden">
      {/* Aurora Background Elements Removed for Performance */}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-[420px] relative z-10"
      >
        <Card glow className="p-10 text-center">
          <div className="flex flex-col items-center mb-6 text-center">
            <motion.div 
              className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center mb-6 shadow-lg shadow-accent-primary/20"
            >
              <Sparkles size={24} className="text-white" />
            </motion.div>
            
            <h2 className="text-2xl font-display font-bold tracking-tight text-white mb-2">Secure Link Verification</h2>
          </div>

          <AnimatePresence mode="wait">
            {statusState === 'loading' && (
              <motion.div
                key="loading"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex flex-col items-center gap-6 my-8"
              >
                <div className="relative w-16 h-16 flex items-center justify-center">
                  <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-0 rounded-full border border-dashed border-accent-cyan/50"
                  />
                  <div className="w-8 h-8 rounded-full bg-accent-cyan/20 animate-pulse" />
                </div>
                <p className="text-sm font-mono text-accent-cyan tracking-widest uppercase">Analyzing token protocol...</p>
              </motion.div>
            )}

            {statusState === 'success' && (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center gap-6 my-8"
              >
                <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center border border-success/30 shadow-[0_0_20px_rgba(34,197,94,0.3)]">
                  <CheckCircle size={32} className="text-success" />
                </div>
                <p className="text-sm text-text-muted">{message}</p>
                <Button onClick={() => navigate('/login')} className="w-full mt-4 justify-center">
                  Establish Connection
                </Button>
              </motion.div>
            )}

            {statusState === 'error' && (
              <motion.div
                key="error"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center gap-6 my-8"
              >
                <div className="w-16 h-16 rounded-full bg-danger/20 flex items-center justify-center border border-danger/30 shadow-[0_0_20px_rgba(239,68,68,0.3)]">
                  <ShieldAlert size={32} className="text-danger" />
                </div>
                <p className="text-sm text-text-muted">{message}</p>
                
                <Button onClick={() => navigate('/login')} variant="secondary" className="w-full mt-4 justify-center">
                  Abort & Return
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      </motion.div>
    </div>
  );
}
