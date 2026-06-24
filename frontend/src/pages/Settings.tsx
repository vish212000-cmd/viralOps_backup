import React from 'react';
import { Helmet } from 'react-helmet-async';
import { Settings as SettingsIcon } from 'lucide-react';

export default function Settings() {
  return (
    <>
      <Helmet>
        <title>Settings | ViralOps</title>
      </Helmet>
      
      <div className="flex-1 flex flex-col min-h-0 bg-bg-base">
        <header className="px-8 py-6 border-b border-glass-border bg-bg-surface/50 backdrop-blur-md sticky top-0 z-10">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-2xl font-display font-semibold text-white tracking-tight">Settings</h1>
            <p className="text-text-muted text-sm mt-1">Manage your account and workspace preferences.</p>
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="glass-panel p-12 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 border border-glass-border">
                <SettingsIcon size={32} className="text-text-muted" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">Account Settings</h2>
              <p className="text-text-muted max-w-md">
                Your account settings and profile configuration options will be available here soon.
              </p>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
