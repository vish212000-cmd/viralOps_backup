import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

// Dynamic Import Recovery for Vite Chunk Loading Failures
const lazyImportWithRecovery = (importPromise: () => Promise<any>, chunkName: string) => {
  return lazy(async () => {
    try {
      return await importPromise();
    } catch (error: any) {
      const isChunkLoadError = error?.message?.includes('Failed to fetch dynamically imported module') || 
                               error?.message?.includes('ChunkLoadError');
      
      if (isChunkLoadError) {
        const reloadCountKey = `chunk_reload_${chunkName}`;
        const hasReloaded = sessionStorage.getItem(reloadCountKey);
        
        if (!hasReloaded) {
          sessionStorage.setItem(reloadCountKey, 'true');
          console.error(`Chunk load failed for ${chunkName}. Triggering page reload to fetch latest index.html...`, error);
          window.location.reload();
          // Return a never-resolving promise so React Suspense keeps showing the fallback while reloading
          return new Promise(() => {}); 
        } else {
          console.error(`Chunk load failed for ${chunkName} after reload attempt. Possible network issue.`, error);
          if (typeof window !== 'undefined' && (window as any).Sentry) {
             (window as any).Sentry.captureException(error, { tags: { issue: 'chunk_load_infinite_loop' } });
          }
        }
      }
      throw error;
    }
  });
};

const LandingPage = lazyImportWithRecovery(() => import('./pages/LandingPage'), 'LandingPage');
const Login = lazyImportWithRecovery(() => import('./pages/Login'), 'Login');
const Signup = lazyImportWithRecovery(() => import('./pages/Signup'), 'Signup');
const Dashboard = lazyImportWithRecovery(() => import('./pages/Dashboard'), 'Dashboard');
const ProjectDetails = lazyImportWithRecovery(() => import('./pages/ProjectDetails'), 'ProjectDetails');
const MomentsWorkspace = lazyImportWithRecovery(() => import('./pages/MomentsWorkspace'), 'MomentsWorkspace');
const Preferences = lazyImportWithRecovery(() => import('./pages/Preferences'), 'Preferences');
const AdminDashboard = lazyImportWithRecovery(() => import('./pages/AdminDashboard'), 'AdminDashboard');
const Billing = lazyImportWithRecovery(() => import('./pages/Billing'), 'Billing');
const Analytics = lazyImportWithRecovery(() => import('./pages/Analytics'), 'Analytics');
const Policies = lazyImportWithRecovery(() => import('./pages/Policies'), 'Policies');
const GoogleCallback = lazyImportWithRecovery(() => import('./pages/GoogleCallback'), 'GoogleCallback');
const VerifyEmail = lazyImportWithRecovery(() => import('./pages/VerifyEmail'), 'VerifyEmail');
const ForgotPassword = lazyImportWithRecovery(() => import('./pages/ForgotPassword'), 'ForgotPassword');
const ResetPassword = lazyImportWithRecovery(() => import('./pages/ResetPassword'), 'ResetPassword');
const AcceptInvite = lazyImportWithRecovery(() => import('./pages/AcceptInvite'), 'AcceptInvite');

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
                <Route path="/projects/:projectId/moments" element={
                  <PrivateRoute>
                    <MomentsWorkspace />
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
