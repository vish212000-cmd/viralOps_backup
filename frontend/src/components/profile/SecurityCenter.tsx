import React from 'react';
import { Card } from '../design/Card';
import { Button } from '../design/Button';
import { APIKeyManager } from './APIKeyManager';
import { SessionManager } from './SessionManager';

export function SecurityCenter() {
  return (
    <Card className="p-6">
      <h2 className="text-xl font-bold font-display mb-4">Security & API Tokens</h2>
      <div className="flex flex-col gap-8">
        
        {/* Password Section */}
        <div>
          <div className="flex justify-between items-center pb-4 border-b border-white/5 mb-4">
            <div>
              <h3 className="font-semibold text-white">Password</h3>
              <p className="text-sm text-text-muted mt-1">Change your password and manage security.</p>
            </div>
            <Button variant="secondary" size="sm">Change Password</Button>
          </div>
        </div>
        
        {/* 2FA Section */}
        <div>
          <div className="flex justify-between items-center pb-4 border-b border-white/5 mb-4">
            <div>
              <h3 className="font-semibold text-white flex items-center gap-2">
                Two-Factor Authentication (2FA)
                <span className="text-[10px] bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Inactive</span>
              </h3>
              <p className="text-sm text-text-muted mt-1">Add an extra layer of security to your account.</p>
            </div>
            <Button variant="primary" size="sm">Enable 2FA</Button>
          </div>
        </div>

        <APIKeyManager />

        <SessionManager />

      </div>
    </Card>
  );
}
