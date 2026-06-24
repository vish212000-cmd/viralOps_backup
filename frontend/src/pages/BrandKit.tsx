import React, { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Palette, Save, Loader2 } from 'lucide-react';
import { api } from '../utils/api';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/design/Button';
import { Card } from '../components/design/Card';

interface BrandKitData {
  brand_name: string;
  audience: string;
  voice_style: string;
  standard_cta: string;
}

export default function BrandKit() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [data, setData] = useState<BrandKitData>({
    brand_name: '',
    audience: '',
    voice_style: '',
    standard_cta: ''
  });

  const orgSlug = api.orgSlug;

  useEffect(() => {
    if (orgSlug) {
      loadBrandKit();
    }
  }, [orgSlug]);

  const loadBrandKit = async () => {
    try {
      const res = await api.get(`/api/orgs/${orgSlug}/brand_kit/`) as BrandKitData;
      setData({
        brand_name: res.brand_name || '',
        audience: res.audience || '',
        voice_style: res.voice_style || '',
        standard_cta: res.standard_cta || ''
      });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await api.put(`/api/orgs/${orgSlug}/brand_kit/`, data) as BrandKitData;
      setData(res);
      showToast('Brand Kit saved successfully!', 'success');
    } catch (err) {
      console.error(err);
      showToast('Failed to save Brand Kit.', 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-bg-base">
        <Loader2 size={32} className="text-accent-primary animate-spin" />
      </div>
    );
  }

  return (
    <>
      <Helmet>
        <title>Brand Kit | ViralOps</title>
      </Helmet>
      
      <div className="flex-1 flex flex-col min-h-0 bg-bg-base">
        <header className="px-8 py-6 border-b border-glass-border bg-bg-surface/50 backdrop-blur-md sticky top-0 z-10">
          <div className="flex justify-between items-center max-w-4xl mx-auto">
            <div>
              <h1 className="text-2xl font-display font-semibold text-white tracking-tight flex items-center gap-2">
                <Palette className="text-accent-primary" /> Brand Kit
              </h1>
              <p className="text-text-muted text-sm mt-1">Define your brand voice to personalize your generated assets.</p>
            </div>
            
            <Button onClick={handleSave} loading={saving} icon={<Save size={16} />}>
              Save Changes
            </Button>
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-4xl mx-auto space-y-6">
            <Card className="p-8 bg-white/[0.02]">
              <h2 className="text-lg font-semibold text-white mb-6 tracking-wide">Brand Identity</h2>
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-bold text-text-muted mb-2 uppercase tracking-wider">Brand Name</label>
                  <input 
                    type="text" 
                    value={data.brand_name}
                    onChange={e => setData({...data, brand_name: e.target.value})}
                    className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary transition-all" 
                    placeholder="e.g. ViralOps" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-text-muted mb-2 uppercase tracking-wider">Target Audience</label>
                  <input 
                    type="text" 
                    value={data.audience}
                    onChange={e => setData({...data, audience: e.target.value})}
                    className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary transition-all" 
                    placeholder="e.g. Founders, Creators, Marketers" 
                  />
                </div>
              </div>
            </Card>

            <Card className="p-8 bg-white/[0.02]">
              <h2 className="text-lg font-semibold text-white mb-6 tracking-wide">Voice & Tone</h2>
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-bold text-text-muted mb-2 uppercase tracking-wider">Writing Style</label>
                  <textarea 
                    value={data.voice_style}
                    onChange={e => setData({...data, voice_style: e.target.value})}
                    className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary transition-all min-h-[120px]" 
                    placeholder="Describe how your brand sounds (e.g., Professional but approachable, witty, concise)..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-text-muted mb-2 uppercase tracking-wider">Standard CTA</label>
                  <input 
                    type="text" 
                    value={data.standard_cta}
                    onChange={e => setData({...data, standard_cta: e.target.value})}
                    className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary transition-all" 
                    placeholder="e.g. Subscribe to my newsletter for more tips!" 
                  />
                </div>
              </div>
            </Card>
          </div>
        </main>
      </div>
    </>
  );
}
