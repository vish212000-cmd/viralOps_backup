import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { api } from '../utils/api';
import { Project, SourceType } from '../types';
import { Button } from '../components/design/Button';
import { Input } from '../components/design/Input';
import { Badge } from '../components/design/Badge';
import { Card } from '../components/design/Card';
import Sidebar from '../components/Sidebar';
import { 
  Sparkles, Plus, Folder, Video, FileText, Link2, 
  Settings, LogOut, Loader2, AlertCircle, Shield
} from 'lucide-react';

export default function Dashboard() {
  const { user, orgs, currentOrg, loading: authLoading, logoutUser, selectOrg, loadWorkspaces } = useAuth();
  const { showToast } = useToast();
  
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState('');
  
  // New Org Form
  const [newOrgName, setNewOrgName] = useState('');
  const [creatingOrg, setCreatingOrg] = useState(false);

  // New Project Form
  const [showNewProj, setShowNewProj] = useState(false);
  const [projName, setProjName] = useState('');
  const [projDesc, setProjDesc] = useState('');
  
  // New Source Form
  const [sourceType, setSourceType] = useState<SourceType>('ARTICLE');
  const [sourceTitle, setSourceTitle] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [sourceText, setSourceText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Validation errors
  const [nameError, setNameError] = useState('');
  const [urlError, setUrlError] = useState('');
  const [textError, setTextError] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    if (!authLoading) {
      if (orgs.length > 0 && currentOrg) {
        loadProjects(currentOrg.slug);
      } else {
        setLoading(false);
      }
    }
  }, [authLoading, currentOrg, orgs]);

  const loadProjects = async (orgSlug: string) => {
    try {
      const projList = await api.get(`/api/orgs/${orgSlug}/projects/`) as Project[];
      setProjects(projList);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Failed to fetch projects.');
    } finally {
      setLoading(false);
    }
  };

  const handleOrgChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const slug = e.target.value;
    if (slug === 'CREATE_NEW') {
      setCreatingOrg(true);
      return;
    }
    selectOrg(slug);
    setLoading(true);
  };

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    setLoading(true);
    try {
      await api.post('/api/workspaces/', { name: newOrgName });
      await loadWorkspaces();
      setNewOrgName('');
      setCreatingOrg(false);
      showToast('New workspace created!', 'success');
    } catch (err) {
      console.error(err);
      setError('Failed to create workspace.');
      showToast('Failed to create workspace.', 'error');
      setLoading(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setNameError('');
    setUrlError('');
    setTextError('');

    let hasValError = false;
    if (projName.trim().length < 3) {
      setNameError('Project name must be at least 3 characters long.');
      hasValError = true;
    }

    if (sourceType === 'YOUTUBE') {
      const isYoutube = sourceUrl.includes('youtube.com') || sourceUrl.includes('youtu.be');
      if (!sourceUrl || !isYoutube) {
        setUrlError('A valid YouTube URL is required (must contain youtube.com or youtu.be).');
        hasValError = true;
      }
    }

    if (sourceType === 'ARTICLE' && !sourceText.trim()) {
      setTextError('Source content text body is required.');
      hasValError = true;
    }

    if (hasValError || !currentOrg) return;

    setSubmitting(true);
    try {
      const project = await api.post(`/api/orgs/${currentOrg.slug}/projects/`, {
        name: projName,
        description: projDesc
      }) as Project;

      const sourcePayload: Record<string, any> = {
        type: sourceType,
        title: sourceTitle,
      };

      if (sourceType === 'YOUTUBE') {
        sourcePayload.source_url = sourceUrl;
      } else if (sourceType === 'VIDEO' || sourceType === 'AUDIO') {
        sourcePayload.file_name = sourceUrl || 'uploaded_file.mp4';
        sourcePayload.file_size = 15242880; // 15MB Mock
      } else {
        sourcePayload.text_content = sourceText;
      }

      await api.post(`/api/orgs/${currentOrg.slug}/projects/${project.id}/sources/`, sourcePayload);

      setProjName('');
      setProjDesc('');
      setSourceTitle('');
      setSourceUrl('');
      setSourceText('');
      setShowNewProj(false);
      
      showToast('Ingestion pipeline triggered!', 'success');
      loadProjects(currentOrg.slug);
    } catch (err: any) {
      console.error(err);
      const errors = err?.data;
      if (errors?.file_size) {
        showToast(errors.file_size, 'error');
      } else {
        showToast('Failed to start ingestion.', 'error');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogout = () => {
    logoutUser();
    navigate('/');
  };

  if (authLoading || (loading && orgs.length > 0)) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'hsl(var(--bg-main))' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
          <Loader2 size={40} className="loading-spinner" />
          <span style={{ color: 'hsl(var(--text-muted))' }}>Loading workspace dashboard...</span>
        </div>
      </div>
    );
  }

  // Zero State Setup Workspace
  if (orgs.length === 0 || creatingOrg) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'hsl(var(--bg-main))', padding: '1rem' }}>
        <Card style={{ width: '100%', maxWidth: '480px', padding: '2.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <Sparkles size={24} color="hsl(var(--accent-primary))" />
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'var(--font-display)' }}>
              {creatingOrg ? 'Create New Workspace' : 'Setup Your Workspace'}
            </h2>
          </div>
          <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: 1.6, marginBottom: '2rem' }}>
            To start generating hooks, captions, and short scripts, you need an organization workspace. Give your workspace a name below.
          </p>
          <form onSubmit={handleCreateOrg} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Input 
              label="Workspace Name"
              type="text"
              value={newOrgName}
              onChange={(e) => setNewOrgName(e.target.value)}
              required
              placeholder="e.g. My Agency or Solo Brand"
            />
            <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
              <Button type="submit" style={{ flex: 1, justifyContent: 'center' }}>
                Create Workspace
              </Button>
              {creatingOrg && (
                <Button type="button" variant="secondary" onClick={() => setCreatingOrg(false)}>
                  Cancel
                </Button>
              )}
            </div>
          </form>
        </Card>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      <Sidebar />

      {/* Main Content */}
      <main className="main-content">
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>Workspace Dashboard</h1>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem' }}>Manage and repurpose content in {currentOrg?.name}</p>
          </div>
          <Button onClick={() => setShowNewProj(true)}>
            <Plus size={18} /> New Project
          </Button>
        </header>

        {error && (
          <div style={{ background: 'hsl(var(--danger) / 0.1)', border: '1px solid hsl(var(--danger) / 0.3)', padding: '1rem', borderRadius: '12px', color: 'hsl(var(--danger))', display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '2rem' }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* Stats Panel */}
        <Card style={{ padding: '1.5rem', marginBottom: '2.5rem', display: 'flex', gap: '3rem', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Total Projects</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800 }}>{projects.length}</div>
          </div>
          <div style={{ width: '1px', background: 'hsl(var(--border-muted))' }} />
          <div>
            <div style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>AI Credits Used</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800 }}>12 / 60 <span style={{ fontSize: '0.9rem', fontWeight: 500, color: 'hsl(var(--text-dim))' }}>generations</span></div>
          </div>
        </Card>

        {/* Projects list */}
        <section>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1.25rem' }}>Your Projects</h2>
          
          {projects.length === 0 ? (
            <Card style={{ padding: '4rem 2rem', textAlign: 'center' }}>
              <Folder size={48} style={{ color: 'hsl(var(--text-dim))', marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>No projects created yet</h3>
              <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                Get started by creating your first repurposing project.
              </p>
              <Button onClick={() => setShowNewProj(true)}>
                <Plus size={16} /> Create Project
              </Button>
            </Card>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem' }}>
              {projects.map(proj => (
                <Card key={proj.id} style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '180px' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                      <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>{proj.name}</h3>
                      <Badge status={proj.status} />
                    </div>
                    <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.9rem', lineHeight: 1.5, marginBottom: '1.5rem' }}>
                      {proj.description || 'No description provided.'}
                    </p>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid hsl(var(--border-muted))', paddingTop: '0.75rem' }}>
                    <span style={{ fontSize: '0.8rem', color: 'hsl(var(--text-dim))' }}>
                      Created: {new Date(proj.created_at).toLocaleDateString()}
                    </span>
                    <Link to={`/projects/${proj.id}`} className="button secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', textDecoration: 'none' }}>
                      Open Workspace
                    </Link>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </section>

        {/* Ingestion Modal Dialog */}
        {showNewProj && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0, 0, 0, 0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '1rem' }}>
            <Card style={{ width: '100%', maxWidth: '640px', padding: '2.5rem', maxHeight: '90vh', overflowY: 'auto' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '1.5rem' }}>Create New Repurposing Project</h2>
              
              <form onSubmit={handleCreateProject} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div style={{ display: 'flex', gap: '1rem', flexDirection: 'row' }}>
                  <div style={{ flex: 1 }}>
                    <Input 
                      label="Project Name"
                      type="text"
                      value={projName}
                      onChange={(e) => setProjName(e.target.value)}
                      error={nameError}
                      required
                      placeholder="e.g. Episode 23 Podcast Hook"
                    />
                  </div>
                  <div style={{ flex: 1 }}>
                    <Input 
                      label="Source Title"
                      type="text"
                      value={sourceTitle}
                      onChange={(e) => setSourceTitle(e.target.value)}
                      required
                      placeholder="e.g. AI Strategy Video"
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'hsl(var(--text-muted))' }}>Description (Optional)</label>
                  <textarea 
                    value={projDesc} 
                    onChange={(e) => setProjDesc(e.target.value)} 
                    placeholder="Describe this project context..."
                    rows={2}
                  />
                </div>

                <div style={{ borderTop: '1px solid hsl(var(--border-muted))', paddingTop: '1.25rem' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Content Ingestion Source</h3>
                  
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                    {[
                      { id: 'ARTICLE', label: 'Article/Text', icon: <FileText size={16} /> },
                      { id: 'YOUTUBE', label: 'YouTube URL', icon: <Link2 size={16} /> },
                      { id: 'VIDEO', label: 'Video Upload', icon: <Video size={16} /> },
                    ].map(type => (
                      <Button
                        key={type.id}
                        type="button"
                        variant={sourceType === type.id ? 'primary' : 'secondary'}
                        onClick={() => setSourceType(type.id as SourceType)}
                        style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                      >
                        {type.icon} {type.label}
                      </Button>
                    ))}
                  </div>

                  {sourceType === 'YOUTUBE' && (
                    <Input 
                      label="YouTube Link"
                      type="url"
                      value={sourceUrl}
                      onChange={(e) => setSourceUrl(e.target.value)}
                      error={urlError}
                      required
                      placeholder="https://www.youtube.com/watch?v=..."
                    />
                  )}

                  {sourceType === 'VIDEO' && (
                    <Input 
                      label="Simulate Video Upload (File Name)"
                      type="text"
                      value={sourceUrl}
                      onChange={(e) => setSourceUrl(e.target.value)}
                      required
                      placeholder="e.g. interview_recording_raw.mp4"
                    />
                  )}

                  {sourceType === 'ARTICLE' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'hsl(var(--text-muted))' }}>Content Text / Script / Blog Article</label>
                      <textarea 
                        value={sourceText} 
                        onChange={(e) => setSourceText(e.target.value)} 
                        required 
                        placeholder="Paste article text, blog post, transcript or raw script here..."
                        rows={6}
                        style={{ borderColor: textError ? 'hsl(var(--danger))' : undefined }}
                      />
                      {textError && <span style={{ fontSize: '0.75rem', color: 'hsl(var(--danger))' }}>{textError}</span>}
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                  <Button type="button" variant="secondary" onClick={() => setShowNewProj(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" loading={submitting}>
                    Start Ingestion Pipeline
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
