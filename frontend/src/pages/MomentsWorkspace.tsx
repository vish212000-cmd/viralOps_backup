import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { useToast } from '../context/ToastContext';
import { Moment, TranscriptSegment, GeneratedAsset, SourceInput } from '../types';
import { MomentCard } from '../components/MomentCard';
import { Card } from '../components/design/Card';
import { Button } from '../components/design/Button';
import { Loader2, ArrowLeft, Download, Play, Video, Sparkles, Filter, Link2 } from 'lucide-react';

export default function MomentsWorkspace() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const orgSlug = api.orgSlug;

  const [loading, setLoading] = useState(true);
  const [moments, setMoments] = useState<Moment[]>([]);
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [source, setSource] = useState<SourceInput | null>(null);
  
  const [selectedMomentId, setSelectedMomentId] = useState<number | null>(null);
  const [generatingAssets, setGeneratingAssets] = useState(false);

  useEffect(() => {
    loadWorkspace();
  }, [projectId]);

  const loadWorkspace = async () => {
    if (!projectId) return;
    try {
      const [srcList, momentsList, segList] = await Promise.all([
        api.get(`/api/orgs/${orgSlug}/projects/${projectId}/sources/`),
        api.get(`/api/orgs/${orgSlug}/projects/${projectId}/moments/`),
        api.get(`/api/orgs/${orgSlug}/projects/${projectId}/segments/`)
      ]);

      if (srcList && srcList.length > 0) setSource(srcList[0]);
      setMoments(momentsList);
      setSegments(segList);
      
      if (momentsList.length > 0) {
        setSelectedMomentId(momentsList[0].id);
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to load Moments Workspace.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFavorite = async (momentId: number) => {
    try {
      const res = await api.post(`/api/orgs/${orgSlug}/projects/${projectId}/moments/${momentId}/toggle-favorite/`) as { is_favorite: boolean };
      setMoments(moments.map(m => m.id === momentId ? { ...m, is_favorite: res.is_favorite } : m));
    } catch (err) {
      showToast('Failed to favorite moment', 'error');
    }
  };

  const handleGenerateAssets = async (momentId: number) => {
    setGeneratingAssets(true);
    try {
      const res = await api.post(`/api/orgs/${orgSlug}/projects/${projectId}/moments/${momentId}/generate-assets/`) as { assets: GeneratedAsset[] };
      // Refresh the moment to get the newly attached assets
      const momentsList = await api.get(`/api/orgs/${orgSlug}/projects/${projectId}/moments/`) as Moment[];
      setMoments(momentsList);
      showToast('Assets generated successfully for this moment!', 'success');
    } catch (err) {
      showToast('Failed to generate assets', 'error');
    } finally {
      setGeneratingAssets(false);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Loader2 className="loading-spinner" size={40} />
      </div>
    );
  }

  const selectedMoment = moments.find(m => m.id === selectedMomentId);
  const momentSegments = selectedMoment?.segments || [];
  const generatedAssets = selectedMoment?.generated_assets || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'hsl(var(--bg-main))' }}>
      {/* Header */}
      <header style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        padding: '1.25rem 2rem', 
        borderBottom: '1px solid hsl(var(--border-muted))',
        background: 'hsl(var(--card))',
        zIndex: 10
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <button 
            onClick={() => navigate(`/projects/${projectId}`)}
            style={{ background: 'none', border: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', color: 'hsl(var(--text-muted))', fontSize: '0.9rem', fontWeight: 600 }}
          >
            <ArrowLeft size={16} /> Back
          </button>
          <div style={{ width: '1px', height: '24px', background: 'hsl(var(--border-muted))' }} />
          <h1 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={20} color="hsl(var(--accent-primary))" />
            Viral Moment Discovery
          </h1>
        </div>
        
        {source && (
          <div style={{ fontSize: '0.85rem', color: 'hsl(var(--text-dim))', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Video size={16} /> {source.file_name || source.source_url || 'Unknown Source'}
          </div>
        )}
      </header>

      {/* Main Two-Pane Workspace */}
      <main style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        
        {/* Left Pane: Moments List */}
        <section style={{ 
          width: '400px', 
          borderRight: '1px solid hsl(var(--border-muted))', 
          display: 'flex', 
          flexDirection: 'column',
          background: 'hsl(var(--bg-main))'
        }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid hsl(var(--border-muted))', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Top Moments ({moments.length})</h2>
            <Button variant="secondary" style={{ padding: '0.4rem' }}>
              <Filter size={16} />
            </Button>
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {moments.map(moment => (
              <MomentCard 
                key={moment.id}
                moment={moment}
                isActive={selectedMomentId === moment.id}
                onClick={() => setSelectedMomentId(moment.id)}
                onToggleFavorite={handleToggleFavorite}
              />
            ))}
            {moments.length === 0 && (
              <div style={{ textAlign: 'center', color: 'hsl(var(--text-dim))', padding: '2rem', fontSize: '0.9rem' }}>
                No viral moments detected yet.
              </div>
            )}
          </div>
        </section>

        {/* Right Pane: Moment Detail & Transcript Highlight */}
        <section style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto', padding: '2rem' }}>
          {selectedMoment ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '900px', margin: '0 auto', width: '100%' }}>
              
              {/* Moment Detail Header */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 800, padding: '0.25rem 0.6rem', borderRadius: '4px', background: 'hsl(var(--accent-primary) / 0.15)', color: 'hsl(var(--accent-primary))' }}>
                    {selectedMoment.category}
                  </span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'hsl(var(--warning))', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Sparkles size={14} /> {selectedMoment.score} / 100 Viral Score
                  </span>
                </div>
                <h2 style={{ fontSize: '2rem', fontWeight: 800, margin: 0, color: 'hsl(var(--text-primary))', lineHeight: 1.2 }}>
                  {selectedMoment.title}
                </h2>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: 'hsl(var(--text-muted))', fontSize: '0.9rem', background: 'hsl(var(--card))', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid hsl(var(--border-muted))' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600 }}>
                    <Play size={14} color="hsl(var(--accent-primary))" /> 
                    Timestamp: {selectedMoment.start_time} - {selectedMoment.end_time}
                  </span>
                  {selectedMoment.video_clip_url && (
                    <a href={selectedMoment.video_clip_url} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'hsl(var(--text-primary))', textDecoration: 'none', marginLeft: 'auto', fontWeight: 600 }}>
                      <Link2 size={14} /> View Clip
                    </a>
                  )}
                </div>
              </div>

              {/* Action Bar */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.5rem', background: 'hsl(var(--card))', borderRadius: '12px', border: '1px solid hsl(var(--border-muted))' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 0.25rem 0' }}>Generate Content</h3>
                  <p style={{ margin: 0, fontSize: '0.85rem', color: 'hsl(var(--text-muted))' }}>Turn this exact moment into ready-to-publish social posts.</p>
                </div>
                <Button onClick={() => handleGenerateAssets(selectedMoment.id)} loading={generatingAssets}>
                  <Sparkles size={16} /> Generate Post Assets
                </Button>
              </div>

              {/* Generated Assets Display */}
              {generatedAssets.length > 0 && (
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Sparkles size={16} color="hsl(var(--accent-primary))" /> Generated Content
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                    {generatedAssets.map(asset => (
                      <Card key={asset.id} style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'hsl(var(--accent-primary))' }}>{asset.type}</div>
                        <div style={{ fontSize: '0.9rem', color: 'hsl(var(--text-primary))', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>{asset.content}</div>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Transcript Viewer / Highlights */}
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Moment Transcript</h3>
                <Card style={{ padding: '2rem', background: 'hsl(var(--card))' }}>
                  {momentSegments.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      {momentSegments.map((seg, i) => (
                        <div key={i} style={{ display: 'flex', gap: '1rem' }}>
                          <div style={{ minWidth: '60px', fontSize: '0.75rem', color: 'hsl(var(--text-dim))', fontWeight: 600, paddingTop: '0.2rem' }}>
                            {Math.floor(seg.start_time / 60)}:{(Math.floor(seg.start_time % 60)).toString().padStart(2, '0')}
                          </div>
                          <div style={{ flex: 1, fontSize: '1.05rem', lineHeight: 1.6, color: 'hsl(var(--text-primary))' }}>
                            {seg.text}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '1.05rem', lineHeight: 1.6, color: 'hsl(var(--text-primary))', whiteSpace: 'pre-wrap', fontStyle: 'italic' }}>
                      "{selectedMoment.excerpt}"
                    </div>
                  )}
                </Card>
              </div>

            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'hsl(var(--text-dim))', fontSize: '1.1rem' }}>
              Select a moment to view details
            </div>
          )}
        </section>

      </main>
    </div>
  );
}
