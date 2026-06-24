import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { Menu } from 'lucide-react';

export default function AppLayout() {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  return (
    <div className="app-shell">
      {/* Reserves sidebar space in the flexbox flow */}
      <div className="sidebar-placeholder" />
      
      {/* The actual sidebar */}
      <Sidebar isMobileOpen={isMobileOpen} onClose={() => setIsMobileOpen(false)} />
      
      {/* Mobile backdrop */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
          aria-hidden="true"
        />
      )}
      
      <main className="content-shell">
        {/* Mobile top header bar */}
        <div className="lg:hidden flex items-center justify-between bg-bg-surface/90 backdrop-blur-md border-b border-white/5 px-6 py-4 relative z-30">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsMobileOpen(true)}
              className="text-text-muted hover:text-white focus:outline-none cursor-pointer focus-visible:ring-2 focus-visible:ring-accent-cyan rounded"
              aria-label="Open navigation menu"
              aria-expanded={isMobileOpen}
            >
              <Menu size={24} />
            </button>
            <span className="font-display font-bold text-lg text-white">ViralOps</span>
          </div>
        </div>

        <Outlet />
      </main>
    </div>
  );
}
