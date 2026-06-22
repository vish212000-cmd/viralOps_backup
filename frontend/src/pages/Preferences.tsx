import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { api } from '../utils/api';
import { MemoryRecord } from '../types';
import { Button } from '../components/design/Button';
import { Card } from '../components/design/Card';
import { Sparkles, Save, Loader2, Folder, Settings, Shield, LogOut } from 'lucide-react';

export default function Preferences() {
  const { user, logoutUser } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Brand Preference Settings
  const [tone, setTone] = useState('');
  const [styleGuide, setStyleGuide] = useState('');
  const [hooksPref, setHooksPref] = useState('');

  const navigate = useNavigate();
  const orgSlug = api.orgSlug;
  const username = user?.username || 'Creator';

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    setLoading(true);
    try {
      const records = await api.get(`/api/orgs/${orgSlug}/memory/`) as MemoryRecord[];
      
      records.forEach(rec => {
        if (rec.key === 'BRAND_TONE') setTone(rec.value?.tone || '');
        if (rec.key === 'STYLE_GUIDE') setStyleGuide(rec.value?.guide || '');
        if (rec.key === 'PREFERRED_HOOKS') setHooksPref(rec.value?.hooks || '');
      });
    } catch (err) {
      console.error(err);
      showToast('Could not retrieve brand voice settings.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      await api.post(`/api/orgs/${orgSlug}/memory/`, {
        key: 'BRAND_TONE',
        value: { tone }
      });
      await api.post(`/api/orgs/${orgSlug}/memory/`, {
        key: 'STYLE_GUIDE',
        value: { guide: styleGuide }
      });
      await api.post(`/api/orgs/${orgSlug}/memory/`, {
        key: 'PREFERRED_HOOKS',
        value: { hooks: hooksPref }
      });

      showToast('Brand voice parameters saved!', 'success');
    } catch (err) {
      console.error(err);
      showToast('Failed to update brand voice memory.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    logoutUser();
    navigate('/');
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'hsl(var(--bg-main))' }}>
        <Loader2 className="loading-spinner" size={40} />
      </div>
    );
  }

  return (
    <div className="flex-1 w-full flex flex-col relative z-10 max-h-[100dvh] overflow-y-auto overflow-x-hidden">
      {/* Ambient Top Glow */}
      <div className="absolute top-0 left-0 right-0 h-[500px] bg-gradient-to-b from-accent-primary/5 to-transparent pointer-events-none -z-10" />

      <div className="w-full max-w-7xl mx-auto px-6 lg:px-12 py-10">
        <header style={{ marginBottom: '2.5rem' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>Brand Voice Preferences</h1>
          <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', marginTop: '0.25rem' }}>
            Configure style rules and memory retrieval blocks for your workspace. Future generations will inherit these settings.
          </p>
        </header>

        <form onSubmit={handleSavePreferences} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '800px' }}>
          <Card style={{ padding: '2.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 600 }}>Brand Tone & Voice Profile</label>
              <textarea
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                placeholder="e.g. Sarcastic tech builder, punchy, energetic, no fluff. Uses active verbs."
                rows={3}
              />
              <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-dim))' }}>Describes how the AI should talk when writing hooks, captions, and scripts.</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 600 }}>Formatting & Style Guide</label>
              <textarea
                value={styleGuide}
                onChange={(e) => setStyleGuide(e.target.value)}
                placeholder="e.g. Split text into one sentence per line. Limit emoji usage to max 2 per video. Start key terms with capitalized headers."
                rows={3}
              />
              <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-dim))' }}>Dictates text structure, constraints, line breaks, and emoji controls.</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 600 }}>Preferred Hook Formats</label>
              <textarea
                value={hooksPref}
                onChange={(e) => setHooksPref(e.target.value)}
                placeholder="e.g. How to [action] without [pain] | If you are not doing [action], you are losing [benefit]"
                rows={3}
              />
              <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-dim))' }}>Optional hook structures or formulas you want the AI writer to mimic.</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid hsl(var(--border-muted))', paddingTop: '1.5rem', marginTop: '1rem' }}>
              <Button type="submit" loading={saving}>
                <Save size={16} /> Save Brand Parameters
              </Button>
            </div>
          </Card>
        </form>
      </div>
    </div>
  );
}
