import React from 'react';
import { Card } from '../design/Card';
import { Input } from '../design/Input';
import { useAutoSave } from '../../utils/autoSave';

export function PreferencesForm({ formData, onChange }: any) {
  const { debouncedSave, status } = useAutoSave('/api/profiles/me/');

  const handleChange = (field: string, value: string) => {
    onChange('preferences', field, value);
    debouncedSave({ preferences: { [field]: value } });
  };

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold font-display">AI Preferences</h2>
        {status === 'saving' && <span className="text-xs text-text-muted animate-pulse">Saving...</span>}
        {status === 'saved' && <span className="text-xs text-accent-cyan">Saved</span>}
        {status === 'failed' && <span className="text-xs text-red-400">Failed to save</span>}
      </div>
      <p className="text-sm text-text-muted mb-6">Configure how the AI generates content for you.</p>

      <div className="flex flex-col gap-4">
          <Input 
            label="Default AI Provider" 
            placeholder="e.g. OpenAI, Anthropic, Gemini"
            value={formData?.preferences?.default_ai_provider || ''} 
            onChange={(e) => handleChange('default_ai_provider', e.target.value)}
          />

          <Input 
            label="Creativity Level" 
            placeholder="e.g. Balanced, High, Conservative"
            value={formData?.preferences?.creativity_level || ''} 
            onChange={(e) => handleChange('creativity_level', e.target.value)}
          />
      </div>
    </Card>
  );
}
