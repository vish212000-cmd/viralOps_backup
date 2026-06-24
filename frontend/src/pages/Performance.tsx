import React from 'react';
import { Helmet } from 'react-helmet-async';
import { BarChart2, Clock, Zap } from 'lucide-react';

export default function Performance() {
  return (
    <>
      <Helmet>
        <title>Performance | ViralOps</title>
      </Helmet>
      
      <div className="flex-1 flex flex-col min-h-0 bg-bg-base">
        <header className="px-8 py-6 border-b border-glass-border bg-bg-surface/50 backdrop-blur-md sticky top-0 z-10">
          <div className="max-w-7xl mx-auto">
            <h1 className="text-2xl font-display font-semibold text-white tracking-tight">Performance</h1>
            <p className="text-text-muted text-sm mt-1">Creator-focused analytics and ROI tracking.</p>
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-7xl mx-auto space-y-6">
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="glass-panel p-6 flex flex-col relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <Zap size={64} className="text-accent-primary" />
                </div>
                <h3 className="text-text-muted font-medium mb-2 relative z-10">Assets Created</h3>
                <div className="text-4xl font-display font-bold text-white relative z-10">1,248</div>
                <div className="text-sm text-success mt-2 relative z-10">+12% this month</div>
              </div>

              <div className="glass-panel p-6 flex flex-col relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <Clock size={64} className="text-accent-cyan" />
                </div>
                <h3 className="text-text-muted font-medium mb-2 relative z-10">Time Saved</h3>
                <div className="text-4xl font-display font-bold text-white relative z-10">156h</div>
                <div className="text-sm text-success mt-2 relative z-10">+8h this week</div>
              </div>

              <div className="glass-panel p-6 flex flex-col relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <BarChart2 size={64} className="text-accent-secondary" />
                </div>
                <h3 className="text-text-muted font-medium mb-2 relative z-10">Top Format</h3>
                <div className="text-4xl font-display font-bold text-white relative z-10">LinkedIn</div>
                <div className="text-sm text-text-muted mt-2 relative z-10">45% of total generated</div>
              </div>
            </div>

            <div className="glass-panel p-12 flex flex-col items-center justify-center text-center mt-8">
              <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 border border-glass-border">
                <BarChart2 size={32} className="text-text-muted" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">More insights coming soon</h2>
              <p className="text-text-muted max-w-md">
                We're building advanced analytics to track actual impressions and engagement of your generated content.
              </p>
            </div>
            
          </div>
        </main>
      </div>
    </>
  );
}
