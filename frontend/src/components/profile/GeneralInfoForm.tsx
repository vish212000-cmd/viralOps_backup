import React from 'react';
import { Card } from '../design/Card';
import { Input } from '../design/Input';
import { AvatarUpload } from './AvatarUpload';
import { useAutoSave } from '../../utils/autoSave';

export function GeneralInfoForm({ account, formData, onChange }: any) {
  const { debouncedSave, status } = useAutoSave('/api/profiles/me/');

  const handleChange = (section: string, field: string, value: string) => {
    onChange(section, field, value);
    
    // Auto-save logic
    const payload: any = {};
    if (section === 'user') {
      payload.user = { [field]: value };
    } else {
      payload.profile = { [field]: value };
    }
    debouncedSave(payload);
  };

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold font-display">General Info</h2>
        {status === 'saving' && <span className="text-xs text-text-muted animate-pulse">Saving...</span>}
        {status === 'saved' && <span className="text-xs text-accent-cyan">Saved</span>}
        {status === 'failed' && <span className="text-xs text-red-400">Failed to save</span>}
      </div>
      
      <div className="flex flex-col gap-6">
        <div className="mb-2">
          <AvatarUpload currentAvatarUrl={account?.profile?.avatar} username={account?.user?.username || 'U'} />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <Input 
            label="First Name" 
            value={formData?.user?.first_name || ''} 
            onChange={(e) => handleChange('user', 'first_name', e.target.value)}
          />
          <Input 
            label="Last Name" 
            value={formData?.user?.last_name || ''} 
            onChange={(e) => handleChange('user', 'last_name', e.target.value)}
          />
        </div>
        
        <Input label="Username" value={account?.user?.username || ''} disabled />
        <Input label="Email" value={account?.user?.email || ''} disabled />
        
        <div className="grid grid-cols-2 gap-4">
          <Input 
            label="Job Title" 
            value={formData?.profile?.job_title || ''} 
            onChange={(e) => handleChange('profile', 'job_title', e.target.value)}
          />
          <Input 
            label="Company" 
            value={formData?.profile?.company || ''} 
            onChange={(e) => handleChange('profile', 'company', e.target.value)}
          />
        </div>

        <Input 
          label="Bio" 
          as="textarea" 
          rows={3} 
          value={formData?.profile?.bio || ''} 
          onChange={(e) => handleChange('profile', 'bio', e.target.value)}
        />
      </div>
    </Card>
  );
}
