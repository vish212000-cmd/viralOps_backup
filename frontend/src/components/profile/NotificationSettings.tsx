import React, { useState } from 'react';
import { Card } from '../design/Card';

export function NotificationSettings({ settings, onChange }: any) {
  // We mock the onChange to keep it simple, since we don't have the full API defined yet.
  
  const toggleSetting = (key: string) => {
    // In a real app we'd dispatch this to the backend
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-bold font-display mb-4">Notifications</h2>
      <p className="text-text-muted text-sm mb-6">Manage how we contact you.</p>
      
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl">
          <div>
            <h4 className="font-semibold text-sm">Processing Complete</h4>
            <p className="text-xs text-text-muted">Get notified when your videos are done processing.</p>
          </div>
          <div className="w-10 h-5 bg-accent-cyan rounded-full relative cursor-pointer" onClick={() => toggleSetting('processing')}>
              <div className="w-4 h-4 bg-bg-main rounded-full absolute right-1 top-0.5"></div>
          </div>
        </div>

        <div className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl">
          <div>
            <h4 className="font-semibold text-sm">Product Updates</h4>
            <p className="text-xs text-text-muted">Receive updates about new features and improvements.</p>
          </div>
          <div className="w-10 h-5 bg-white/10 rounded-full relative cursor-pointer" onClick={() => toggleSetting('updates')}>
              <div className="w-4 h-4 bg-text-muted rounded-full absolute left-1 top-0.5"></div>
          </div>
        </div>
      </div>
    </Card>
  );
}
