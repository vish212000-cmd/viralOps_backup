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
const Dashboard = lazyImportWithRecovery(() => import('./pages/Dashboard'), 'Dashboard'); // This acts as Overview
const ProjectDetails = lazyImportWithRecovery(() => import('./pages/ProjectDetails'), 'ProjectDetails');
const MomentsWorkspace = lazyImportWithRecovery(() => import('./pages/MomentsWorkspace'), 'MomentsWorkspace');
const BrandKit = lazyImportWithRecovery(() => import('./pages/BrandKit'), 'BrandKit');
const Performance = lazyImportWithRecovery(() => import('./pages/Performance'), 'Performance');
const Settings = lazyImportWithRecovery(() => import('./pages/Settings'), 'Settings');
const Profile = lazyImportWithRecovery(() => import('./pages/Profile'), 'Profile'); 
const Billing = lazyImportWithRecovery(() => import('./pages/Billing'), 'Billing');
const MyContent = lazyImportWithRecovery(() => import('./pages/MyContent'), 'MyContent'); 
const AdminDashboard = lazyImportWithRecovery(() => import('./pages/AdminDashboard'), 'AdminDashboard');
const Policies = lazyImportWithRecovery(() => import('./pages/Policies'), 'Policies');
const GoogleCallback = lazyImportWithRecovery(() => import('./pages/GoogleCallback'), 'GoogleCallback');
const VerifyEmail = lazyImportWithRecovery(() => import('./pages/VerifyEmail'), 'VerifyEmail');
const ForgotPassword = lazyImportWithRecovery(() => import('./pages/ForgotPassword'), 'ForgotPassword');
const ResetPassword = lazyImportWithRecovery(() => import('./pages/ResetPassword'), 'ResetPassword');
const AcceptInvite = lazyImportWithRecovery(() => import('./pages/AcceptInvite'), 'AcceptInvite');

import ErrorBoundary from './components/ErrorBoundary';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import AppLayout from './components/AppLayout';

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

import { HelmetProvider } from 'react-helmet-async';

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <HelmetProvider>
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
                <Route element={
                  <PrivateRoute>
                    <AppLayout />
                  </PrivateRoute>
                }>
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/content" element={<MyContent />} />
                  <Route path="/brand-kit" element={<BrandKit />} />
                  <Route path="/performance" element={<Performance />} />
                  <Route path="/billing" element={<Billing />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/profile" element={<Profile />} />
                  <Route path="/admin" element={<AdminDashboard />} />
                  <Route path="/projects/:projectId" element={<ProjectDetails />} />
                  <Route path="/projects/:projectId/moments" element={<MomentsWorkspace />} />
                </Route>
              </Routes>
            </Suspense>
          </Router>
          </HelmetProvider>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
