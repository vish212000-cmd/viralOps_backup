import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

const LandingPage = lazy(() => import('./pages/LandingPage'));
const Login = lazy(() => import('./pages/Login'));
const Signup = lazy(() => import('./pages/Signup'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ProjectDetails = lazy(() => import('./pages/ProjectDetails'));
const Preferences = lazy(() => import('./pages/Preferences'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const Billing = lazy(() => import('./pages/Billing'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Policies = lazy(() => import('./pages/Policies'));
const GoogleCallback = lazy(() => import('./pages/GoogleCallback'));
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));
const AcceptInvite = lazy(() => import('./pages/AcceptInvite'));

import ErrorBoundary from './components/ErrorBoundary';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';

import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.VITE_SENTRY_ENV || 'production',
  release: import.meta.env.VITE_SENTRY_RELEASE,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration({ maskAllText: true, blockAllMedia: true }),
  ],
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});


interface PrivateRouteProps {
  children: React.ReactElement;
}

function PrivateRoute({ children }: PrivateRouteProps) {
  const token = localStorage.getItem('access_token');
  return token ? children : <Navigate to="/login" replace />;
}

const LoadingFallback = () => (
  <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'hsl(var(--bg-main))' }}>
    <Loader2 className="loading-spinner" size={40} />
  </div>
);

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <Router>
            <Suspense fallback={<LoadingFallback />}>
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
                
                {/* Email verification and password recovery routes */}
                <Route path="/verify-email" element={<VerifyEmail />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword />} />
                <Route path="/accept-invite" element={<AcceptInvite />} />
                
                {/* Social Login and Public Policy routes */}
                <Route path="/auth/google/callback" element={<GoogleCallback />} />
                <Route path="/terms" element={<Policies page="terms" />} />
                <Route path="/privacy" element={<Policies page="privacy" />} />
                <Route path="/refund" element={<Policies page="refund" />} />
                
                {/* Private workspaces routes */}
                <Route path="/dashboard" element={
                  <PrivateRoute>
                    <Dashboard />
                  </PrivateRoute>
                } />
                <Route path="/projects/:projectId" element={
                  <PrivateRoute>
                    <ProjectDetails />
                  </PrivateRoute>
                } />
                <Route path="/preferences" element={
                  <PrivateRoute>
                    <Preferences />
                  </PrivateRoute>
                } />
                <Route path="/billing" element={
                  <PrivateRoute>
                    <Billing />
                  </PrivateRoute>
                } />
                <Route path="/analytics" element={
                  <PrivateRoute>
                    <Analytics />
                  </PrivateRoute>
                } />
                <Route path="/admin" element={
                  <PrivateRoute>
                    <AdminDashboard />
                  </PrivateRoute>
                } />
              </Routes>
            </Suspense>
          </Router>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
