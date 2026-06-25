import React from 'react';
import { Card } from '../design/Card';
import { Input } from '../design/Input';
import { useAutoSave } from '../../utils/autoSave';

export function CreatorProfileForm({ formData, onChange }: any) {
  const { debouncedSave, status } = useAutoSave('/api/profiles/me/');

  const handleChange = (field: string, value: string) => {
    onChange('creator_profile', field, value);
    debouncedSave({ creator_profile: { [field]: value } });
  };

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold font-display">Creator Profile</h2>
        {status === 'saving' && <span className="text-xs text-text-muted animate-pulse">Saving...</span>}
        {status === 'saved' && <span className="text-xs text-accent-cyan">Saved</span>}
        {status === 'failed' && <span className="text-xs text-red-400">Failed to save</span>}
      </div>
      <p className="text-sm text-text-muted mb-6">Tell us about your content creation style to personalize AI suggestions.</p>
      
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <Input 
            label="Niche" 
            placeholder="e.g. Finance, Tech, Lifestyle"
            value={formData?.creator_profile?.niche || ''} 
            onChange={(e) => handleChange('niche', e.target.value)}
          />
          <Input 
            label="Primary Platform" 
            placeholder="e.g. YouTube, TikTok, LinkedIn"
            value={formData?.creator_profile?.primary_platform || ''} 
            onChange={(e) => handleChange('primary_platform', e.target.value)}
          />
        </div>

        <Input 
          label="Audience Size" 
          placeholder="e.g. 10k-50k followers"
          value={formData?.creator_profile?.audience_size || ''} 
          onChange={(e) => handleChange('audience_size', e.target.value)}
        />

        <Input 
          label="Preferred Tone" 
          placeholder="e.g. Professional, Casual, Humorous"
          value={formData?.creator_profile?.preferred_tone || ''} 
          onChange={(e) => handleChange('preferred_tone', e.target.value)}
        />
      </div>
    </Card>
  );
}
