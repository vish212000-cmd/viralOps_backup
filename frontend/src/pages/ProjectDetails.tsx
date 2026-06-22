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
  Share2, ExternalLink, ShieldCheck, ShieldX, Clock, Link2, Hash, Eye
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
      showToast('Transcript uploaded successfully. Restarting pipeline...', 'success');
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

type TabType = 'hooks' | 'titles' | 'captions' | 'scripts' | 'ctas' | 'hashtags' | 'source';

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
  const [activeTab, setActiveTab] = useState<TabType>('hooks');

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
            showToast('Ingestion pipeline completed successfully!', 'success');
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

  const tabFilters = {
    hooks: 'HOOK',
    titles: 'TITLE',
    captions: 'CAPTION',
    scripts: 'SCRIPT',
    ctas: 'CTA',
    hashtags: 'HASHTAG',
  };

  const activeAssets = assets.filter(a => a.type === (tabFilters as any)[activeTab]);
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
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', marginTop: '0.25rem' }}>{project.description || 'Repurposing workspace for ingested content.'}</p>
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

        {project.status !== 'COMPLETED' && project.status !== 'PARTIAL_SUCCESS' && (!activeSource || activeSource.status !== 'FAILED') ? (
          <Card style={{ padding: '4rem 2rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyItems: 'center' }}>
            <Loader2 size={48} className="loading-spinner" style={{ marginBottom: '1.5rem' }} />
            <h3 style={{ fontSize: '1.3rem', marginBottom: '0.7rem' }}>Content Ingestion Pipeline Active</h3>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', maxWidth: '480px', lineHeight: 1.6, marginBottom: '2rem' }}>
              We are transcribing, cleaning, and normalizing your text source. Then our AI orchestrator will extract hooks, captions, and platform short scripts.
            </p>
            <div style={{ display: 'flex', gap: '2rem', fontSize: '0.85rem', color: 'hsl(var(--text-dim))' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'hsl(var(--success))' }}><CheckCircle2 size={16} /> Source Received</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'hsl(var(--accent-primary))' }} className="pulsate"><RotateCw size={16} className="spin" /> Processing AI Pipeline</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>Assets Ready</div>
            </div>
          </Card>
        ) : activeSource && activeSource.status === 'FAILED' ? (
          <Card style={{ padding: '3rem', textAlign: 'center', borderColor: 'hsl(var(--danger) / 0.3)' }}>
            <AlertTriangle size={48} color="hsl(var(--danger))" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: 'hsl(var(--danger))' }}>Ingestion Pipeline Failed</h3>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
              Error Log: {activeSource?.error_message || 'Unexpected worker timeout during execution.'}
            </p>
            <Button onClick={() => navigate('/dashboard')}>Back to Projects</Button>
          </Card>
        ) : (
          <div>
            {/* Navigation Tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid hsl(var(--border-muted))', marginBottom: '2rem', overflowX: 'auto', gap: '1rem' }}>
              {[
                { id: 'hooks', label: 'Hooks Opener' },
                { id: 'titles', label: 'Clickable Titles' },
                { id: 'captions', label: 'Social Captions' },
                { id: 'scripts', label: 'Short Scripts' },
                { id: 'ctas', label: 'CTAs' },
                { id: 'hashtags', label: 'Hashtags' },
                { id: 'source', label: 'Source Material' },
              ].map(tab => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id as TabType)}
                  style={{ 
                    background: 'transparent',
                    border: 'none',
                    borderBottom: activeTab === tab.id ? '2px solid hsl(var(--accent-primary))' : '2px solid transparent',
                    borderRadius: 0,
                    padding: '0.75rem 0.5rem',
                    color: activeTab === tab.id ? 'hsl(var(--text-primary))' : 'hsl(var(--text-muted))',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    boxShadow: 'none',
                    transform: 'none',
                    cursor: 'pointer'
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab content panel */}
            <div style={{ minHeight: '400px' }}>
              {activeTab === 'source' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  {/* Transcript Diagnostics Panel — YouTube only */}
                  {/* Transcript Diagnostics Panel — YouTube only */}
                  {activeSource && <TranscriptDiagnosticsPanel source={activeSource} onUploadSuccess={loadProjectDetails} />}

                  {/* Source metadata */}
                  {activeSource?.type === 'YOUTUBE' && activeSource.source_url && (
                    <Card style={{ padding: '1.25rem 1.5rem' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'hsl(var(--text-dim))', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Video URL</div>
                        <a
                          href={activeSource.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'hsl(var(--accent-primary))', textDecoration: 'none', fontSize: '0.9rem', wordBreak: 'break-all' }}
                        >
                          {activeSource.source_url} <ExternalLink size={13} />
                        </a>
                      </div>
                    </Card>
                  )}

                  {/* Full content preview */}
                  <Card style={{ padding: '2rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid hsl(var(--border-muted))', paddingBottom: '0.75rem' }}>
                      <h3 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <FileText size={18} /> Ingested Normalized Content
                      </h3>
                      <span style={{ fontSize: '0.8rem', color: 'hsl(var(--text-dim))' }}>
                        Type: {activeSource?.type}
                      </span>
                    </div>
                    <div style={{ whiteSpace: 'pre-wrap', color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: 1.6, maxHeight: '500px', overflowY: 'auto', paddingRight: '1rem' }}>
                      {activeSource?.text_content || 'No text extracted.'}
                    </div>
                  </Card>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  {activeAssets.length === 0 ? (
                    <Card style={{ padding: '3rem', textAlign: 'center', color: 'hsl(var(--text-dim))' }}>
                      No assets found for this category.
                    </Card>
                  ) : (
                    activeAssets.map(asset => (
                      <Card key={asset.id} style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid hsl(var(--border-muted))', paddingBottom: '0.75rem' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'hsl(var(--accent-primary))', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            {asset.type} ({asset.platform})
                          </span>
                          
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <Button 
                              variant="secondary"
                              onClick={() => handleToggleFavorite(asset.id)}
                              style={{ padding: '0.4rem', border: 'none' }}
                            >
                              <Star size={16} fill={asset.is_favorite ? 'hsl(var(--warning))' : 'none'} color={asset.is_favorite ? 'hsl(var(--warning))' : 'currentColor'} />
                            </Button>
                            <Button 
                              variant="secondary"
                              onClick={() => handleRegenerate(asset.id)}
                              loading={regeneratingId === asset.id}
                              style={{ padding: '0.4rem', border: 'none' }}
                            >
                              <RotateCw size={16} className={regeneratingId === asset.id ? 'spin' : ''} />
                            </Button>
                            <Button 
                              variant="secondary"
                              onClick={() => setPublishingAsset(asset)}
                              style={{ padding: '0.4rem', border: 'none' }}
                              title="Publish Asset"
                            >
                              <Share2 size={16} />
                            </Button>
                          </div>
                        </div>

                        {editingAssetId === asset.id ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <textarea
                              value={editingContent}
                              onChange={(e) => setEditingContent(e.target.value)}
                              rows={asset.type === 'SCRIPT' || asset.type === 'CAPTION' ? 8 : 2}
                              style={{ fontSize: '0.95rem', lineHeight: 1.6 }}
                            />
                            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                              <Button variant="secondary" onClick={() => setEditingAssetId(null)}>Cancel</Button>
                              <Button onClick={() => handleSaveEdit(asset.id)} loading={savingAssetId === asset.id}>
                                <Save size={14} /> Save Change
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div>
                            <div style={{ whiteSpace: 'pre-wrap', fontSize: '1rem', lineHeight: 1.6, color: 'hsl(var(--text-primary))', background: 'hsl(var(--bg-main) / 0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid hsl(var(--border-muted) / 0.5)' }}>
                              {asset.content}
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
                              <Button variant="secondary" onClick={() => handleStartEdit(asset)} style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
                                <Edit2 size={12} /> Edit Asset
                              </Button>
                              
                              {asset.versions && asset.versions.length > 0 && (
                                <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-dim))', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                  <History size={12} /> {asset.versions.length} edits saved
                                </span>
                              )}
                            </div>

                            {asset.publish_records && asset.publish_records.length > 0 && (
                              <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px dashed hsl(var(--border-muted) / 0.5)' }}>
                                <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: 'hsl(var(--text-muted))', marginBottom: '0.5rem' }}>Publication History</h4>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                  {asset.publish_records.map(rec => (
                                    <div key={rec.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', background: 'hsl(var(--bg-main) / 0.5)', padding: '0.4rem 0.6rem', borderRadius: '6px' }}>
                                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                        <span style={{ fontWeight: 600 }}>{rec.platform}</span>
                                        <span style={{ 
                                          fontSize: '0.7rem', 
                                          padding: '0.1rem 0.4rem', 
                                          borderRadius: '4px',
                                          background: rec.status === 'SUCCESS' ? 'hsl(var(--success) / 0.15)' : 'hsl(var(--danger) / 0.15)',
                                          color: rec.status === 'SUCCESS' ? 'hsl(var(--success))' : 'hsl(var(--danger))'
                                        }}>
                                          {rec.status}
                                        </span>
                                      </span>
                                      {rec.status === 'SUCCESS' && rec.published_url && (
                                        <a href={rec.published_url} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem', color: 'hsl(var(--accent-primary))', textDecoration: 'none' }}>
                                          View Post <ExternalLink size={12} />
                                        </a>
                                      )}
                                      {rec.status === 'FAILED' && (
                                        <span style={{ color: 'hsl(var(--danger))', fontSize: '0.75rem' }}>{rec.error_message}</span>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                      </Card>
                    ))
                  )}
                </div>
              )}
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
