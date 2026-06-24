import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { api, FileResponse } from '../utils/api';
import { Project, SourceInput, GeneratedAsset } from '../types';
import { Button } from '../components/design/Button';
import { Badge } from '../components/design/Badge';
import { Card } from '../components/design/Card';
import { 
  ArrowLeft, Loader2, AlertTriangle, FileText, CheckCircle2,
  Star, Edit2, RotateCw, Download, Save, History, Folder, Settings, Shield, LogOut, Sparkles,
  Share2, ExternalLink, ShieldCheck, ShieldX, Clock, Link2, Hash, Eye, Video
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Transcript Diagnostics Panel
// ---------------------------------------------------------------------------
function TranscriptDiagnosticsPanel({ source, onUploadSuccess }: { source: SourceInput, onUploadSuccess?: () => void }) {
  const isYouTube = source.type === 'YOUTUBE';
  const { projectId } = useParams<{ projectId: string }>();
  const { showToast } = useToast();
  const [uploading, setUploading] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  if (!isYouTube) return null;

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !projectId) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['srt', 'vtt', 'txt'].includes(ext || '')) {
      showToast('Unsupported format. Please upload SRT, VTT, or TXT.', 'error');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post(`/api/orgs/${api.orgSlug}/projects/${projectId}/sources/${source.id}/upload_transcript/`, formData);
      showToast('Transcript uploaded successfully. Restarting processing...', 'success');
      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      console.error(err);
      showToast('Failed to upload transcript.', 'error');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const status = source.transcript_validation_status;
  const hasDiagnostics = !!status;
  const isPassed = status === 'PASS';
  const isFailed = status === 'FAIL';

  const statusColor = isPassed
    ? 'hsl(var(--success))'
    : isFailed
    ? 'hsl(var(--danger))'
    : 'hsl(var(--text-dim))';

  const statusBg = isPassed
    ? 'hsl(var(--success) / 0.08)'
    : isFailed
    ? 'hsl(var(--danger) / 0.08)'
    : 'hsl(var(--border-muted) / 0.2)';

  const formatLength = (n: number | null) =>
    n != null ? n.toLocaleString() + ' chars' : '—';

  const formatTimestamp = (ts: string | null) => {
    if (!ts) return '—';
    try {
      return new Date(ts).toLocaleString();
    } catch {
      return ts;
    }
  };

  return (
    <div style={{
      border: `1px solid ${isPassed ? 'hsl(var(--success) / 0.3)' : isFailed ? 'hsl(var(--danger) / 0.3)' : 'hsl(var(--border-muted))'}`,
      borderRadius: '12px',
      overflow: 'hidden',
      marginBottom: '1.5rem',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '1rem 1.5rem',
        background: statusBg,
        borderBottom: `1px solid ${isPassed ? 'hsl(var(--success) / 0.2)' : isFailed ? 'hsl(var(--danger) / 0.2)' : 'hsl(var(--border-muted))'}`,
      }}>
        {isPassed ? (
          <ShieldCheck size={20} color="hsl(var(--success))" />
        ) : isFailed ? (
          <ShieldX size={20} color="hsl(var(--danger))" />
        ) : (
          <ShieldCheck size={20} color="hsl(var(--text-dim))" />
        )}
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'hsl(var(--text-primary))' }}>
            Transcript Diagnostics
          </div>
          <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-dim))' }}>
            Validation results for YouTube transcript retrieval
          </div>
        </div>
        {hasDiagnostics && (
          <div style={{
            padding: '0.3rem 0.9rem',
            borderRadius: '20px',
            fontSize: '0.75rem',
            fontWeight: 800,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            background: isPassed ? 'hsl(var(--success) / 0.15)' : 'hsl(var(--danger) / 0.15)',
            color: statusColor,
            border: `1px solid ${statusColor}`,
          }}>
            {status}
          </div>
        )}
      </div>

      {/* Body */}
      <div style={{ padding: '1.5rem' }}>
        {!hasDiagnostics ? (
          <div style={{ color: 'hsl(var(--text-dim))', fontSize: '0.9rem', textAlign: 'center', padding: '1rem 0' }}>
            Diagnostics not yet available — ingestion may still be processing.
          </div>
        ) : (
          <>
            {/* Stat grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
              gap: '1rem',
              marginBottom: source.transcript_preview ? '1.5rem' : 0,
            }}>
              {[
                {
                  icon: <FileText size={15} />,
                  label: 'Source',
                  value: source.transcript_source ? source.transcript_source.toUpperCase() : '—',
                },
                {
                  icon: <Hash size={15} />,
                  label: 'Length',
                  value: formatLength(source.transcript_length ?? null),
                },
                {
                  icon: <Link2 size={15} />,
                  label: 'Retrieval Method',
                  value: source.transcript_retrieval_method || '—',
                },
                {
                  icon: <Clock size={15} />,
                  label: 'Retrieved At',
                  value: formatTimestamp(source.transcript_retrieved_at ?? null),
                },
              ].map(stat => (
                <div key={stat.label} style={{
                  background: 'hsl(var(--bg-main) / 0.4)',
                  border: '1px solid hsl(var(--border-muted) / 0.4)',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'hsl(var(--text-dim))', fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.4rem' }}>
                    {stat.icon} {stat.label}
                  </div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'hsl(var(--text-primary))', wordBreak: 'break-all' }}>
                    {stat.value}
                  </div>
                </div>
              ))}
            </div>

            {/* FAIL reason */}
            {isFailed && source.error_message && (
              <div style={{
                background: 'hsl(var(--danger) / 0.08)',
                border: '1px solid hsl(var(--danger) / 0.25)',
                borderRadius: '8px',
                padding: '0.75rem 1rem',
                marginBottom: source.transcript_preview ? '1rem' : 0,
                fontSize: '0.85rem',
                color: 'hsl(var(--danger))',
              }}>
                <strong>Error:</strong> {source.error_message}
                <div style={{ marginTop: '0.4rem', fontSize: '0.8rem', color: 'hsl(var(--danger) / 0.8)', fontWeight: 600 }}>
                  ⛔ Gemini generation was blocked — no AI assets were created from invalid data.
                </div>
                
                <div style={{ marginTop: '1.5rem', padding: '1.25rem', background: 'hsl(var(--card))', borderRadius: '8px', border: '1px solid hsl(var(--danger) / 0.3)' }}>
                  <h4 style={{ fontSize: '0.9rem', color: 'hsl(var(--text-primary))', marginBottom: '0.5rem' }}>Manual Fallback Available</h4>
                  <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.8rem', marginBottom: '1rem', lineHeight: 1.5 }}>
                    YouTube has blocked our automated retrieval. You can bypass this by uploading the video's transcript manually. 
                    We support <strong>.srt</strong>, <strong>.vtt</strong>, or plain <strong>.txt</strong> files.
                  </p>
                  
                  <input 
                    type="file" 
                    accept=".srt,.vtt,.txt" 
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                    id={`upload-transcript-${source.id}`}
                  />
                  <Button 
                    variant="primary" 
                    loading={uploading}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Upload Transcript (SRT, VTT, TXT)
                  </Button>
                </div>
              </div>
            )}

            {/* Preview */}
            {source.transcript_preview && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', fontWeight: 700, color: 'hsl(var(--text-dim))', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
                  <Eye size={13} /> Transcript Preview
                </div>
                <div style={{
                  background: 'hsl(var(--bg-main) / 0.6)',
                  border: '1px solid hsl(var(--border-muted) / 0.4)',
                  borderRadius: '8px',
                  padding: '1rem',
                  fontSize: '0.85rem',
                  lineHeight: 1.7,
                  color: 'hsl(var(--text-muted))',
                  fontFamily: 'var(--font-mono, monospace)',
                  maxHeight: '180px',
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap',
                }}>
                  {source.transcript_preview}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

type TabType = 'transcript' | 'moments' | 'assets' | 'analytics';

export default function ProjectDetails() {
  const { projectId } = useParams<{ projectId: string }>();
  const { user, logoutUser } = useAuth();
  const { showToast } = useToast();

  const [project, setProject] = useState<Project | null>(null);
  const [sources, setSources] = useState<SourceInput[]>([]);
  const [assets, setAssets] = useState<GeneratedAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Navigation Tabs
  const [activeTab, setActiveTab] = useState<TabType>('transcript');

  // Editing state
  const [editingAssetId, setEditingAssetId] = useState<number | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [savingAssetId, setSavingAssetId] = useState<number | null>(null);

  // Regeneration state
  const [regeneratingId, setRegeneratingId] = useState<number | null>(null);

  // Publishing state
  const [publishingAsset, setPublishingAsset] = useState<GeneratedAsset | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<'TWITTER' | 'YOUTUBE' | 'TIKTOK' | 'INSTAGRAM'>('TWITTER');
  const [isPublishing, setIsPublishing] = useState(false);

  const navigate = useNavigate();
  const orgSlug = api.orgSlug;
  const username = user?.username || 'Creator';

  useEffect(() => {
    loadProjectDetails();
    const interval = setInterval(() => {
      checkProjectStatus();
    }, 4000);

    return () => clearInterval(interval);
  }, [projectId]);

  const loadProjectDetails = async () => {
    if (!projectId) return;
    try {
      const proj = await api.get(`/api/orgs/${orgSlug}/projects/${projectId}/`) as Project;
      setProject(proj);

      const srcList = await api.get(`/api/orgs/${orgSlug}/projects/${projectId}/sources/`) as SourceInput[];
      setSources(srcList);

      const assetList = await api.get(`/api/orgs/${orgSlug}/projects/${projectId}/assets/`) as GeneratedAsset[];
      setAssets(assetList);
      
      setError('');
    } catch (err) {
      console.error(err);
      setError('Failed to load project details.');
    } finally {
      setLoading(false);
    }
  };

  const checkProjectStatus = async () => {
    if (!project || project.status === 'COMPLETED' || project.status === 'PARTIAL_SUCCESS' || !projectId) return;
    const activeSource = sources[0];
    if (activeSource && activeSource.status === 'FAILED') return;
    try {
      const proj = await api.get(`/api/orgs/${orgSlug}/projects/${projectId}/`) as Project;
      if (proj.status !== project.status) {
        setProject(proj);
        if (proj.status === 'COMPLETED' || proj.status === 'PARTIAL_SUCCESS') {
          const srcList = await api.get(`/api/orgs/${orgSlug}/projects/${projectId}/sources/`) as SourceInput[];
          setSources(srcList);
          const assetList = await api.get(`/api/orgs/${orgSlug}/projects/${projectId}/assets/`) as GeneratedAsset[];
          setAssets(assetList);
          if (proj.status === 'COMPLETED') {
            showToast('Your content is ready! Explore your generated assets.', 'success');
          }
        }
      }
    } catch (err) {
      console.error('Polling error:', err);
    }
  };

  const handleToggleFavorite = async (assetId: number) => {
    try {
      const res = await api.post(`/api/orgs/${orgSlug}/projects/${projectId}/assets/${assetId}/toggle_favorite/`) as { is_favorite: boolean };
      setAssets(assets.map(a => a.id === assetId ? { ...a, is_favorite: res.is_favorite } : a));
      showToast(res.is_favorite ? 'Added to favorites' : 'Removed from favorites', 'info');
    } catch (err) {
      console.error(err);
    }
  };

  const handleStartEdit = (asset: GeneratedAsset) => {
    setEditingAssetId(asset.id);
    setEditingContent(asset.content);
  };

  const handleSaveEdit = async (assetId: number) => {
    setSavingAssetId(assetId);
    try {
      const updated = await api.post(`/api/orgs/${orgSlug}/projects/${projectId}/assets/${assetId}/save_version/`, {
        content: editingContent
      }) as GeneratedAsset;
      setAssets(assets.map(a => a.id === assetId ? updated : a));
      setEditingAssetId(null);
      showToast('Asset changes saved & version tracked.', 'success');
    } catch (err) {
      console.error(err);
      showToast('Failed to save asset edits.', 'error');
    } finally {
      setSavingAssetId(null);
    }
  };

  const handleRegenerate = async (assetId: number) => {
    setRegeneratingId(assetId);
    try {
      const regenerated = await api.post(`/api/orgs/${orgSlug}/projects/${projectId}/assets/${assetId}/regenerate/`) as GeneratedAsset;
      setAssets(assets.map(a => a.id === assetId ? regenerated : a));
      if (editingAssetId === assetId) {
        setEditingContent(regenerated.content);
      }
      showToast('Asset content regenerated.', 'success');
    } catch (err) {
      console.error(err);
      showToast('AI Regeneration failed. Check provider rate limits.', 'error');
    } finally {
      setRegeneratingId(null);
    }
  };

  const handlePublishAsset = async () => {
    if (!publishingAsset || !projectId) return;
    setIsPublishing(true);
    try {
      const updatedAsset = await api.post(`/api/orgs/${orgSlug}/projects/${projectId}/assets/${publishingAsset.id}/publish/`, {
        platform: selectedPlatform
      }) as GeneratedAsset;
      
      setAssets(assets.map(a => a.id === publishingAsset.id ? updatedAsset : a));
      showToast(`Asset successfully published to ${selectedPlatform}!`, 'success');
      setPublishingAsset(null);
    } catch (err) {
      console.error(err);
      showToast('Publishing failed. Please verify API configuration.', 'error');
    } finally {
      setIsPublishing(false);
    }
  };

  const handleExport = async () => {
    try {
      const res = await api.get(`/api/orgs/${orgSlug}/projects/${projectId}/export_pack/`) as FileResponse;
      if (res.isFile) {
        const url = window.URL.createObjectURL(res.blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `viralops_export_${projectId}.txt`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        showToast('Export content pack downloaded!', 'success');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to download content pack.', 'error');
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

  if (error || !project) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'hsl(var(--bg-main))', gap: '1rem' }}>
        <AlertTriangle size={48} color="hsl(var(--danger))" />
        <h3>{error || 'Project not found.'}</h3>
        <Link to="/dashboard" className="button secondary" style={{ textDecoration: 'none' }}>
          <ArrowLeft size={16} /> Back to Dashboard
        </Link>
      </div>
    );
  }

  const activeSource = sources[0];

  return (
    <div className="flex-1 w-full flex flex-col relative z-10 max-h-[100dvh] overflow-y-auto overflow-x-hidden">
      {/* Ambient Top Glow */}
      <div className="absolute top-0 left-0 right-0 h-[500px] bg-gradient-to-b from-accent-primary/5 to-transparent pointer-events-none -z-10" />

      <div className="w-full max-w-7xl mx-auto px-6 lg:px-12 py-10">
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2.5rem' }}>
          <div>
            <Link to="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'hsl(var(--text-muted))', textDecoration: 'none', fontSize: '0.9rem', marginBottom: '0.75rem' }}>
              <ArrowLeft size={14} /> Back to Dashboard
            </Link>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>{project.name}</h1>
              <Badge status={project.status} />
            </div>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', marginTop: '0.25rem' }}>{project.description || 'Your workspace for repurposing ingested content.'}</p>
          </div>
          
          {(project.status === 'COMPLETED' || project.status === 'PARTIAL_SUCCESS') && (
            <div style={{ display: 'flex', gap: '1rem' }}>
              <Button onClick={() => navigate(`/projects/${projectId}/moments`)}>
                <Sparkles size={16} /> Open Moments Workspace
              </Button>
              <Button variant="secondary" onClick={handleExport}>
                <Download size={16} /> Export Content Pack
              </Button>
            </div>
          )}
        </header>

        {project.status === 'PARTIAL_SUCCESS' && (
          <div style={{ 
            background: 'hsl(var(--warning) / 0.15)', 
            border: '1px solid hsl(var(--warning) / 0.5)', 
            borderRadius: '0.5rem', 
            padding: '1rem 1.5rem', 
            marginBottom: '2rem', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '1rem' 
          }}>
            <AlertTriangle size={24} color="hsl(var(--warning))" style={{ flexShrink: 0 }} />
            <div>
              <h4 style={{ color: 'hsl(var(--warning))', marginBottom: '0.25rem', fontWeight: 600 }}>AI Enhancement Delayed</h4>
              <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem' }}>
                Core transcript processing completed successfully, but AI asset generation is temporarily delayed due to provider quota limits. We will automatically retry in the background.
              </p>
            </div>
          </div>
        )}

        {/* Top Source Preview */}
        {activeSource && project.status !== 'PROCESSING' && project.status !== 'FAILED' && (
          <Card className="mb-8 p-6 flex flex-col md:flex-row gap-6 items-start border-white/5 bg-white/[0.02]">
            <div className="flex-1 w-full">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-accent-primary/20 flex items-center justify-center border border-accent-primary/30">
                  <Video size={18} className="text-accent-primary" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white tracking-wide uppercase">Source Material</h3>
                  <p className="text-xs text-text-muted">{activeSource.type}</p>
                </div>
              </div>
              {activeSource.type === 'YOUTUBE' && activeSource.source_url && (
                <a href={activeSource.source_url} target="_blank" rel="noopener noreferrer" className="text-accent-cyan text-sm flex items-center gap-2 hover:underline">
                  <Link2 size={14} /> {activeSource.source_url}
                </a>
              )}
            </div>
            {activeSource.transcript_length && (
              <div className="flex flex-col items-end justify-center h-full border-l border-white/10 pl-6 shrink-0">
                <span className="text-2xl font-display font-bold text-white">{activeSource.transcript_length.toLocaleString()}</span>
                <span className="text-xs text-text-dim uppercase tracking-widest">Characters Extracted</span>
              </div>
            )}
          </Card>
        )}

        {project.status !== 'COMPLETED' && project.status !== 'PARTIAL_SUCCESS' && (!activeSource || activeSource.status !== 'FAILED') ? (
          <Card style={{ padding: '4rem 2rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyItems: 'center' }}>
            <Loader2 size={48} className="loading-spinner" style={{ marginBottom: '1.5rem' }} />
            <h3 style={{ fontSize: '1.3rem', marginBottom: '0.7rem' }}>Your Content is Being Processed</h3>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', maxWidth: '480px', lineHeight: 1.6, marginBottom: '2rem' }}>
              We're transcribing, analyzing, and extracting the best moments from your content. Our AI will generate hooks, captions, and short scripts shortly.
            </p>
            <div style={{ display: 'flex', gap: '2rem', fontSize: '0.85rem', color: 'hsl(var(--text-dim))' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'hsl(var(--success))' }}><CheckCircle2 size={16} /> Source Received</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'hsl(var(--accent-primary))' }} className="pulsate"><RotateCw size={16} className="spin" /> AI Working...</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>Assets Ready</div>
            </div>
          </Card>
        ) : activeSource && activeSource.status === 'FAILED' ? (
          <Card style={{ padding: '3rem', textAlign: 'center', borderColor: 'hsl(var(--danger) / 0.3)' }}>
            <AlertTriangle size={48} color="hsl(var(--danger))" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: 'hsl(var(--danger))' }}>Processing Failed</h3>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
              There was an issue processing your content: {activeSource?.error_message || 'An unexpected error occurred.'}
            </p>
            <Button onClick={() => navigate('/dashboard')}>Back to Dashboard</Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-[600px]">
            {/* LEFT PANEL: Source & Transcript */}
            <div className="flex flex-col gap-6">
              <h2 className="text-xl font-display font-bold text-white flex items-center gap-2">
                <FileText size={20} className="text-accent-primary" /> Source Content
              </h2>
              {activeSource && <TranscriptDiagnosticsPanel source={activeSource} onUploadSuccess={loadProjectDetails} />}

              <Card className="flex flex-col flex-1 max-h-[800px] overflow-hidden">
                <div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/[0.02]">
                  <h3 className="text-sm font-bold tracking-wider uppercase text-text-muted">Transcript</h3>
                </div>
                <div className="p-6 overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-text-muted font-mono">
                  {activeSource?.text_content || 'No text extracted.'}
                </div>
              </Card>
            </div>

            {/* CENTER PANEL: Viral Moments */}
            <div className="flex flex-col gap-6">
              <h2 className="text-xl font-display font-bold text-white flex items-center gap-2">
                <Sparkles size={20} className="text-accent-cyan" /> Viral Moments
              </h2>
              <Card className="flex-1 p-8 text-center flex flex-col items-center justify-center border-dashed border-white/20 bg-white/[0.01]">
                <Sparkles size={48} className="text-accent-cyan/30 mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">Moments Extraction</h3>
                <p className="text-sm text-text-muted max-w-xs">
                  Key moments from your content will be displayed here as they are detected.
                </p>
                <Button className="mt-6" variant="secondary" onClick={() => navigate(`/projects/${projectId}/moments`)}>
                  Open Moments Workspace
                </Button>
              </Card>
            </div>

            {/* RIGHT PANEL: Assets */}
            <div className="flex flex-col gap-6">
              <h2 className="text-xl font-display font-bold text-white flex items-center gap-2">
                <Star size={20} className="text-warning" /> Generated Assets
              </h2>
              
              <div className="flex flex-col gap-6 overflow-y-auto max-h-[800px] pr-2">
                {assets.length === 0 ? (
                  <Card className="p-8 text-center border-dashed border-white/20 bg-white/[0.01]">
                    <p className="text-text-muted">No assets generated yet.</p>
                  </Card>
                ) : (
                  ['TITLE', 'HOOK', 'CAPTION', 'SCRIPT', 'CTA', 'HASHTAG'].map(type => {
                    const typeAssets = assets.filter(a => a.type === type);
                    if (typeAssets.length === 0) return null;
                    
                    const typeTitles: Record<string, string> = {
                      'TITLE': 'Clickable Titles',
                      'HOOK': 'Video Hooks',
                      'CAPTION': 'Social Captions',
                      'SCRIPT': 'Short Scripts',
                      'CTA': 'Call to Actions',
                      'HASHTAG': 'Hashtags'
                    };
                    
                    return (
                      <div key={type} className="flex flex-col gap-4">
                        <h3 className="text-sm font-bold text-white border-b border-white/10 pb-2 tracking-wider uppercase">{typeTitles[type]}</h3>
                        <div className="flex flex-col gap-4">
                          {typeAssets.map(asset => (
                            <Card key={asset.id} className="p-5 flex flex-col gap-4 bg-white/[0.03] hover:bg-white/[0.05] transition-colors border-white/5">
                              <div className="flex justify-between items-center">
                                <span className="text-xs font-bold text-accent-primary uppercase tracking-widest bg-accent-primary/10 px-2 py-1 rounded">
                                  {asset.platform}
                                </span>
                                
                                <div className="flex items-center gap-1">
                                  <Button 
                                    variant="ghost"
                                    onClick={() => handleToggleFavorite(asset.id)}
                                    className="p-1 h-8 w-8"
                                  >
                                    <Star size={14} fill={asset.is_favorite ? 'hsl(var(--warning))' : 'none'} className={asset.is_favorite ? 'text-warning' : 'text-text-muted'} />
                                  </Button>
                                  <Button 
                                    variant="ghost"
                                    onClick={() => handleRegenerate(asset.id)}
                                    loading={regeneratingId === asset.id}
                                    className="p-1 h-8 w-8 text-text-muted"
                                  >
                                    <RotateCw size={14} className={regeneratingId === asset.id ? 'spin' : ''} />
                                  </Button>
                                  <Button 
                                    variant="ghost"
                                    onClick={() => setPublishingAsset(asset)}
                                    className="p-1 h-8 w-8 text-text-muted"
                                    title="Publish Asset"
                                  >
                                    <Share2 size={14} />
                                  </Button>
                                </div>
                              </div>

                              {editingAssetId === asset.id ? (
                                <div className="flex flex-col gap-3">
                                  <textarea
                                    value={editingContent}
                                    onChange={(e) => setEditingContent(e.target.value)}
                                    rows={asset.type === 'SCRIPT' || asset.type === 'CAPTION' ? 6 : 3}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary"
                                  />
                                  <div className="flex justify-end gap-2">
                                    <Button variant="ghost" onClick={() => setEditingAssetId(null)}>Cancel</Button>
                                    <Button onClick={() => handleSaveEdit(asset.id)} loading={savingAssetId === asset.id}>
                                      <Save size={14} className="mr-2" /> Save
                                    </Button>
                                  </div>
                                </div>
                              ) : (
                                <div>
                                  <div className="whitespace-pre-wrap text-sm leading-relaxed text-white/90">
                                    {asset.content}
                                  </div>
                                  <div className="flex justify-between items-center mt-4">
                                    <Button variant="ghost" onClick={() => handleStartEdit(asset)} className="text-xs text-text-muted h-8 px-2">
                                      <Edit2 size={12} className="mr-1.5" /> Edit
                                    </Button>
                                    
                                    {asset.versions && asset.versions.length > 0 && (
                                      <span className="text-xs text-text-dim flex items-center gap-1">
                                        <History size={12} /> {asset.versions.length} edits
                                      </span>
                                    )}
                                  </div>

                                  {asset.publish_records && asset.publish_records.length > 0 && (
                                    <div className="mt-4 pt-4 border-t border-dashed border-white/10">
                                      <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">Publication History</h4>
                                      <div className="flex flex-col gap-2">
                                        {asset.publish_records.map(rec => (
                                          <div key={rec.id} className="flex justify-between items-center text-xs bg-black/20 p-2 rounded-lg">
                                            <span className="flex items-center gap-2">
                                              <span className="font-bold text-white/80">{rec.platform}</span>
                                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                                                rec.status === 'SUCCESS' ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'
                                              }`}>
                                                {rec.status}
                                              </span>
                                            </span>
                                            {rec.status === 'SUCCESS' && rec.published_url && (
                                              <a href={rec.published_url} target="_blank" rel="noopener noreferrer" className="text-accent-primary hover:underline flex items-center gap-1">
                                                View Post <ExternalLink size={10} />
                                              </a>
                                            )}
                                            {rec.status === 'FAILED' && (
                                              <span className="text-danger truncate max-w-[120px]">{rec.error_message}</span>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </Card>
                          ))}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Social Publishing Modal */}
      {publishingAsset && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <Card style={{
            width: '100%',
            maxWidth: '500px',
            padding: '2.5rem',
            boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
            border: '1px solid hsl(var(--border-muted) / 0.3)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem',
            background: 'hsl(var(--card) / 0.9)'
          }}>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.25rem' }}>Publish Asset to Social</h3>
              <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.85rem' }}>Select the target destination to publish this asset.</p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'hsl(var(--text-muted))' }}>Select Platform</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                {[
                  { id: 'TWITTER', label: 'Twitter / X' },
                  { id: 'YOUTUBE', label: 'YouTube Shorts' },
                  { id: 'TIKTOK', label: 'TikTok' },
                  { id: 'INSTAGRAM', label: 'Instagram Reels' }
                ].map(plat => (
                  <Button
                    key={plat.id}
                    type="button"
                    variant={selectedPlatform === plat.id ? 'primary' : 'secondary'}
                    onClick={() => setSelectedPlatform(plat.id as any)}
                    style={{ fontSize: '0.85rem', padding: '0.5rem' }}
                  >
                    {plat.label}
                  </Button>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'hsl(var(--text-muted))' }}>Content Preview</label>
              <div style={{ 
                background: 'hsl(var(--bg-main) / 0.5)', 
                padding: '1rem', 
                borderRadius: '8px', 
                fontSize: '0.9rem', 
                maxHeight: '120px', 
                overflowY: 'auto',
                border: '1px solid hsl(var(--border-muted) / 0.5)',
                whiteSpace: 'pre-wrap'
              }}>
                {publishingAsset.content}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', borderTop: '1px solid hsl(var(--border-muted))', paddingTop: '1.25rem' }}>
              <Button variant="secondary" onClick={() => setPublishingAsset(null)} disabled={isPublishing}>Cancel</Button>
              <Button onClick={handlePublishAsset} loading={isPublishing}>
                Confirm & Publish
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
