import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Input } from '../components/design/Input';
import { Button } from '../components/design/Button';
import { Card } from '../components/design/Card';
import { Sparkles, ShieldAlert, ArrowRight } from 'lucide-react';

export default function Signup() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { registerUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await registerUser(username, email, password);
      showToast('Account created! Please check your email to verify your account before logging in.', 'success');
      navigate('/login');
    } catch (err: any) {
      console.error(err);
      const errors = err?.data;
      if (errors) {
        const messages = Object.entries(errors).map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(', ') : val}`);
        setError(messages.join(' | ') || 'Failed to register account.');
      } else {
        setError('Something went wrong during signup. Please try again.');
      }
      showToast('Registration failed.', 'error');
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
              className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center mb-6 shadow-lg shadow-accent-primary/20"
            >
              <Sparkles size={24} className="text-white" />
            </motion.div>
            
            <h2 className="text-2xl font-display font-bold tracking-tight text-white mb-2">
              Create Account
            </h2>
            <p className="text-sm text-text-muted">
              Start creating viral short-form content with AI.
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

          <form onSubmit={handleSignup} className="flex flex-col gap-5">
            <Input 
              label="Username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="e.g. maverick"
            />

            <Input 
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@domain.com"
            />

            <Input 
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Minimum 8 characters"
            />

            <Button type="submit" loading={loading} className="w-full mt-2" icon={<ArrowRight size={16} />}>
              Create Account
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

          <p className="text-sm text-text-muted text-center mt-8">
            Already have an account? <Link to="/login" className="text-white hover:text-accent-cyan font-semibold transition-colors">Sign In</Link>
          </p>
        </Card>
      </motion.div>
    </div>
  );
}
