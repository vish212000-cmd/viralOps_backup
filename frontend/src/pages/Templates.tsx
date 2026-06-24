import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { api } from '../utils/api';
import { MemoryRecord } from '../types';
import { Button } from '../components/design/Button';
import { Card } from '../components/design/Card';
import { Loader2, Save, Palette, Type, Hash, Shield, Plus, MoreHorizontal } from 'lucide-react';

export default function Templates() {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Brand Preference Settings
  const [tone, setTone] = useState('');
  const [styleGuide, setStyleGuide] = useState('');
  const [hooksPref, setHooksPref] = useState('');

  const orgSlug = api.orgSlug;

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
      showToast('Could not retrieve brand templates.', 'error');
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

      showToast('Brand Kit updated successfully!', 'success');
    } catch (err) {
      console.error(err);
      showToast('Failed to update brand kit.', 'error');
    } finally {
      setSaving(false);
    }
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
        <header className="mb-10 flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-display font-bold tracking-tight text-white mb-2">Templates & Brand Kits</h1>
            <p className="text-text-muted text-sm max-w-2xl">
              Manage your brand identity, tone of voice, and custom templates. Our AI applies these rules to ensure all generated content sounds exactly like you.
            </p>
          </div>
          <Button variant="primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Plus size={16} /> New Brand Kit
          </Button>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Brand Kits Sidebar (Mock for now to show intention) */}
          <div className="lg:col-span-3 flex flex-col gap-3">
            <h3 className="text-xs font-bold text-text-dim uppercase tracking-wider mb-2">Your Brand Kits</h3>
            
            <button className="flex items-center justify-between w-full p-3 rounded-lg bg-white/5 border border-white/10 text-left transition-colors hover:bg-white/10">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-accent-primary/20 border border-accent-primary/30 flex items-center justify-center">
                  <Palette size={14} className="text-accent-primary" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-white">Default Kit</div>
                  <div className="text-xs text-text-dim">Active Workspace</div>
                </div>
              </div>
              <MoreHorizontal size={16} className="text-text-dim" />
            </button>

            <button className="flex items-center justify-between w-full p-3 rounded-lg border border-dashed border-white/10 text-left transition-colors hover:bg-white/5 opacity-50">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full border border-white/20 flex items-center justify-center">
                  <Plus size={14} className="text-white" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-white">Add Client Kit</div>
                  <div className="text-xs text-text-dim">Pro Plan Feature</div>
                </div>
              </div>
            </button>
          </div>

          {/* Active Brand Kit Editor */}
          <div className="lg:col-span-9">
            <form onSubmit={handleSavePreferences} className="flex flex-col gap-6">
              <Card className="p-8 border-white/5 bg-white/[0.02]">
                <div className="flex items-center gap-3 mb-6 border-b border-white/10 pb-4">
                  <Type size={20} className="text-accent-cyan" />
                  <h2 className="text-xl font-bold text-white">Brand Voice Profile</h2>
                </div>
                
                <div className="flex flex-col gap-6">
                  <div className="flex flex-col gap-2">
                    <label className="text-sm font-semibold text-white">Primary Tone</label>
                    <textarea
                      value={tone}
                      onChange={(e) => setTone(e.target.value)}
                      placeholder="e.g. Analytical, authoritative, but accessible. Uses active voice and avoids jargon."
                      rows={3}
                      className="bg-bg-elevated border border-white/10 rounded-lg p-3 text-sm text-white focus:border-accent-primary/50 focus:outline-none transition-colors"
                    />
                    <span className="text-xs text-text-dim">How the AI should sound when writing for this brand kit.</span>
                  </div>

                  <div className="flex flex-col gap-2">
                    <label className="text-sm font-semibold text-white">Formatting Rules</label>
                    <textarea
                      value={styleGuide}
                      onChange={(e) => setStyleGuide(e.target.value)}
                      placeholder="e.g. One sentence per line. No emojis on LinkedIn. Always capitalize tool names."
                      rows={3}
                      className="bg-bg-elevated border border-white/10 rounded-lg p-3 text-sm text-white focus:border-accent-primary/50 focus:outline-none transition-colors"
                    />
                    <span className="text-xs text-text-dim">Dictates text structure, line breaks, and stylistic constraints.</span>
                  </div>

                  <div className="flex flex-col gap-2">
                    <label className="text-sm font-semibold text-white">Custom Hook Formulas</label>
                    <textarea
                      value={hooksPref}
                      onChange={(e) => setHooksPref(e.target.value)}
                      placeholder="e.g. How I [achieved result] in [timeframe] without [common pain point]."
                      rows={3}
                      className="bg-bg-elevated border border-white/10 rounded-lg p-3 text-sm text-white focus:border-accent-primary/50 focus:outline-none transition-colors"
                    />
                    <span className="text-xs text-text-dim">Specific structures the AI should prioritize for the first 3 seconds/lines.</span>
                  </div>
                </div>
              </Card>

              <div className="flex justify-end gap-4 mt-2">
                <Button type="button" variant="ghost">Discard Changes</Button>
                <Button type="submit" variant="primary" loading={saving}>
                  <Save size={16} className="mr-2" /> Save Brand Kit
                </Button>
              </div>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
}
