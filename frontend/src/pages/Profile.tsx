import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { 
  User, Shield, Bell, Palette, Globe,
  Loader2
} from 'lucide-react';
import { Card } from '../components/design/Card';
import { Button } from '../components/design/Button';
import { api } from '../utils/api';

import { GeneralInfoForm } from '../components/profile/GeneralInfoForm';
import { CreatorProfileForm } from '../components/profile/CreatorProfileForm';
import { PreferencesForm } from '../components/profile/PreferencesForm';
import { NotificationSettings } from '../components/profile/NotificationSettings';
import { SecurityCenter } from '../components/profile/SecurityCenter';

export default function Profile() {
  const [activeTab, setActiveTab] = useState('general');
  const [formData, setFormData] = useState<any>({});

  const { data: account, isLoading: loading } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const res = await api.get('/api/profiles/me/');
      setFormData(res.data);
      return res.data;
    }
  });

  const handleChange = (section: string, field: string, value: string) => {
    setFormData((prev: any) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const tabs = [
    { id: 'general', label: 'General Info', icon: User },
    { id: 'creator', label: 'Creator Profile', icon: Globe },
    { id: 'preferences', label: 'AI Preferences', icon: Palette },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security & Tokens', icon: Shield },
  ];

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center h-screen bg-bg-main text-white">
        <Loader2 className="animate-spin text-accent-cyan" size={40} />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto h-screen relative bg-bg-main text-white">
      {/* Header */}
      <header className="sticky top-0 z-30 flex items-center justify-between px-8 py-6 bg-bg-main/80 backdrop-blur-md border-b border-white/5">
        <div>
          <h1 className="text-2xl font-bold font-display tracking-tight text-white">Account Center</h1>
          <p className="text-sm text-text-muted mt-1">Manage your personal settings, preferences, and security.</p>
        </div>
      </header>

      <div className="p-8 max-w-7xl mx-auto flex flex-col lg:flex-row gap-8">
        
        {/* Left Column: Navigation Sidebar (25%) */}
        <div className="w-full lg:w-1/4 flex flex-col gap-2">
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium text-sm text-left
                  ${isActive 
                    ? 'bg-accent-primary/10 text-accent-cyan border border-accent-primary/20' 
                    : 'text-text-muted hover:bg-white/5 hover:text-white'
                  }`}
              >
                <Icon size={18} className={isActive ? 'text-accent-cyan' : 'text-text-muted'} />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Center Column: Main Content (50%) */}
        <div className="w-full lg:w-2/4">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col gap-6"
            >
              {activeTab === 'general' && (
                <GeneralInfoForm account={account} formData={formData} onChange={handleChange} />
              )}

              {activeTab === 'creator' && (
                <CreatorProfileForm formData={formData} onChange={handleChange} />
              )}

              {activeTab === 'preferences' && (
                <PreferencesForm formData={formData} onChange={handleChange} />
              )}

              {activeTab === 'notifications' && (
                <NotificationSettings />
              )}

              {activeTab === 'security' && (
                <SecurityCenter />
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Right Column: Context & Meta (25%) */}
        <div className="w-full lg:w-1/4 flex flex-col gap-6">
          <Card className="p-5">
            <h3 className="font-semibold text-sm text-text-dim mb-4 uppercase tracking-wider">Account Completion</h3>
            <div className="flex items-center gap-3 mb-2">
              <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-accent-cyan w-[40%]" />
              </div>
              <span className="text-sm font-medium text-accent-cyan">40%</span>
            </div>
            <p className="text-xs text-text-muted">Complete your creator profile to unlock personalized AI suggestions.</p>
          </Card>

          <Card className="p-5">
            <h3 className="font-semibold text-sm text-text-dim mb-4 uppercase tracking-wider">Connected Accounts</h3>
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Globe size={16} className="text-text-muted" />
                  <span className="text-sm font-medium">Google</span>
                </div>
                <Button variant="ghost" size="sm" className="text-xs h-6 px-2 text-accent-cyan hover:bg-accent-cyan/10">Connected</Button>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Globe size={16} className="text-text-muted" />
                  <span className="text-sm font-medium">YouTube</span>
                </div>
                <Button variant="secondary" size="sm" className="text-xs h-6 px-2">Connect</Button>
              </div>
            </div>
          </Card>
          
          <div className="text-xs text-text-dim text-center px-4">
             Joined ViralOps on {new Date(account?.user?.date_joined || Date.now()).toLocaleDateString()}
          </div>
        </div>

      </div>
    </div>
  );
}
