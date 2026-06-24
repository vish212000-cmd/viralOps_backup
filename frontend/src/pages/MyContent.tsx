import React from 'react';
import { Helmet } from 'react-helmet-async';
import { Video, Filter, Download } from 'lucide-react';

export default function MyContent() {
  return (
    <>
      <Helmet>
        <title>My Content | ViralOps</title>
      </Helmet>
      
      <div className="flex-1 flex flex-col min-h-0 bg-bg-base">
        <header className="px-8 py-6 border-b border-glass-border bg-bg-surface/50 backdrop-blur-md sticky top-0 z-10">
          <div className="flex justify-between items-center max-w-7xl mx-auto">
            <div>
              <h1 className="text-2xl font-display font-semibold text-white tracking-tight">My Content</h1>
              <p className="text-text-muted text-sm mt-1">Manage and export your repurposed assets.</p>
            </div>
            
            <div className="flex gap-3">
              <button className="flex items-center gap-2 px-4 py-2 bg-bg-elevated border border-glass-border rounded-lg text-sm text-white hover:bg-white/5 transition-colors">
                <Filter size={16} />
                Filters
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-accent-primary hover:bg-accent-secondary text-white rounded-lg text-sm font-medium transition-colors">
                <Download size={16} />
                Export All
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-7xl mx-auto">
            <div className="glass-panel p-12 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-full bg-accent-primary/10 flex items-center justify-center mb-4">
                <Video size={32} className="text-accent-primary" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">No content yet</h2>
              <p className="text-text-muted max-w-md mb-6">
                You haven't repurposed any content yet. Upload your first video to start generating viral assets.
              </p>
              <button className="px-6 py-3 bg-white text-black font-semibold rounded-lg hover:bg-gray-100 transition-colors shadow-lg shadow-white/10">
                Upload Content
              </button>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
