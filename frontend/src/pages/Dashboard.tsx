import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { api } from '../utils/api';
import { Project, SourceType } from '../types';
import { Button } from '../components/design/Button';
import { Input } from '../components/design/Input';
import { Badge } from '../components/design/Badge';
import { Card } from '../components/design/Card';
import { 
  Sparkles, Plus, Folder, Video, FileText, Link2, 
  Settings, LogOut, Loader2, AlertCircle, Shield, Activity, HardDrive, Cpu, X, Database
} from 'lucide-react';
import { cn } from '../utils/cn';

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
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Validation errors
  const [nameError, setNameError] = useState('');
  const [urlError, setUrlError] = useState('');
  const [textError, setTextError] = useState('');
  const [fileError, setFileError] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    if (!authLoading) {
      if (orgs.length > 0 && currentOrg) {
        loadProjects(currentOrg.slug);
      } else if (orgs.length === 0 && !creatingOrg && user) {
        // Auto-create workspace for creator workflow
        autoCreateWorkspace();
      } else {
        setLoading(false);
      }
    }
  }, [authLoading, currentOrg, orgs]);

  const autoCreateWorkspace = async () => {
    setCreatingOrg(true);
    try {
      await api.post('/api/workspaces/', { name: 'Personal Workspace' });
      await loadWorkspaces();
      showToast('Workspace ready!', 'success');
    } catch (err) {
      console.error(err);
      setError('Failed to setup workspace.');
    } finally {
      setCreatingOrg(false);
      setLoading(false);
    }
  };

  const loadProjects = async (orgSlug: string) => {
    try {
      const projList = await api.get(`/api/orgs/${orgSlug}/projects/`) as Project[];
      setProjects(projList);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Failed to load projects.');
    } finally {
      setLoading(false);
    }
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
      showToast('Workspace created!', 'success');
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
      setNameError('Project identity must be at least 3 characters.');
      hasValError = true;
    }

    if (sourceType === 'YOUTUBE') {
      const isYoutube = sourceUrl.includes('youtube.com') || sourceUrl.includes('youtu.be');
      if (!sourceUrl || !isYoutube) {
        setUrlError('Please enter a valid YouTube URL.');
        hasValError = true;
      }
    }

    if (sourceType === 'ARTICLE' && !sourceText.trim()) {
      setTextError('Please enter some text to analyze.');
      hasValError = true;
    }

    if (['VIDEO', 'AUDIO', 'PDF'].includes(sourceType)) {
      if (!selectedFile) {
        setFileError('Please attach a media file to upload.');
        hasValError = true;
      } else if (selectedFile.size > 52428800) {
        setFileError('File exceeds the 50MB size limit.');
        hasValError = true;
      }
    }

    if (hasValError || !currentOrg) return;

    setSubmitting(true);
    try {
      const project = await api.post(`/api/orgs/${currentOrg.slug}/projects/`, {
        name: projName,
        description: projDesc
      }) as Project;

      const formData = new FormData();
      formData.append('type', sourceType);
      formData.append('title', sourceTitle);

      if (sourceType === 'YOUTUBE') {
        formData.append('source_url', sourceUrl);
      } else if (['VIDEO', 'AUDIO', 'PDF'].includes(sourceType)) {
        if (selectedFile) {
          formData.append('file', selectedFile);
          formData.append('file_name', selectedFile.name);
          formData.append('file_size', selectedFile.size.toString());
        }
      } else {
        formData.append('text_content', sourceText);
      }

      await api.post(`/api/orgs/${currentOrg.slug}/projects/${project.id}/sources/`, formData);

      setProjName('');
      setProjDesc('');
      setSourceTitle('');
      setSourceUrl('');
      setSourceText('');
      setSelectedFile(null);
      setShowNewProj(false);
      
      showToast('Project created! AI is generating your assets.', 'success');
      loadProjects(currentOrg.slug);
    } catch (err: any) {
      console.error(err);
      const errors = err?.data;
      if (errors?.file_size) {
        showToast(errors.file_size, 'error');
      } else if (errors?.file) {
        showToast(errors.file[0] || errors.file, 'error');
      } else {
        showToast('Failed to create project.', 'error');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 200, damping: 20 } }
  };

  if (authLoading || loading || creatingOrg) {
    return (
      <div className="min-h-[100dvh] flex items-center justify-center relative overflow-hidden bg-bg-base">
        <div className="flex flex-col items-center gap-6 relative z-10">
          <Loader2 size={32} className="text-accent-primary animate-spin" />
          <p className="text-text-muted text-sm font-medium">Setting up your studio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 w-full flex flex-col relative z-10 max-h-[100dvh] overflow-y-auto overflow-x-hidden">
      <div className="w-full max-w-7xl mx-auto px-6 lg:px-12 py-10">
          <header className="mb-12">
            <div>
              <motion.h1 initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="text-4xl md:text-5xl font-display font-bold text-white tracking-tight">
                Welcome back, {user?.username}
              </motion.h1>
              <motion.p initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="text-text-muted mt-2 text-lg">
                Let's create some content today.
              </motion.p>
            </div>
          </header>

          <AnimatePresence>
            {error && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mb-8 overflow-hidden">
                <div className="bg-danger/10 border border-danger/30 p-4 rounded-2xl text-danger flex items-center gap-3">
                  <AlertCircle size={20} />
                  <span className="font-medium text-sm">{error}</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Hero Action Section */}
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12"
          >
            <motion.div variants={itemVariants} className="md:col-span-2">
              <Card glow className="p-8 h-full flex flex-col justify-center items-center text-center border-dashed border-white/20 hover:border-accent-primary/50 transition-colors cursor-pointer bg-white/[0.02]" onClick={() => { setSourceType('VIDEO'); setShowNewProj(true); }}>
                <div className="w-16 h-16 rounded-full bg-accent-primary/20 flex items-center justify-center mb-6">
                  <Video size={28} className="text-accent-primary" />
                </div>
                <h2 className="text-2xl font-display font-bold text-white mb-2">Create New Content</h2>
                <p className="text-text-muted mb-6 max-w-md mx-auto">Upload a video, paste a YouTube link, or import a podcast to generate ready-to-post social assets.</p>
                <div className="flex flex-wrap items-center justify-center gap-4">
                  <Button onClick={(e) => { e.stopPropagation(); setSourceType('VIDEO'); setShowNewProj(true); }} icon={<Video size={18} />}>Upload Video</Button>
                  <Button variant="ghost" onClick={(e) => { e.stopPropagation(); setSourceType('YOUTUBE'); setShowNewProj(true); }} icon={<Link2 size={18} />}>Paste YouTube URL</Button>
                </div>
              </Card>
            </motion.div>

            <motion.div variants={itemVariants} className="flex flex-col gap-6">
              {/* Usage Section */}
              <Card className="p-6 flex-1 flex flex-col justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-text-muted mb-4 uppercase tracking-wider">AI Credits</h3>
                  <div className="text-4xl font-display font-bold text-white mb-2">12 <span className="text-lg text-text-dim font-normal">/ 60</span></div>
                  <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-accent-primary w-[20%] rounded-full" />
                  </div>
                </div>
              </Card>
              <Card className="p-6 flex-1 flex flex-col justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-text-muted mb-1 uppercase tracking-wider">Current Plan</h3>
                  <div className="text-xl font-display font-bold text-white mb-2">Creator <span className="text-xs text-success ml-2 px-2 py-1 bg-success/10 rounded-full">Active</span></div>
                  <div className="text-sm text-text-muted mt-2">142 assets generated this month</div>
                </div>
              </Card>
            </motion.div>
          </motion.div>

          {/* Recent Content */}
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, type: "spring", stiffness: 200, damping: 20 }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-display font-bold text-white">Recent Content</h2>
            </div>
            
            {projects.length === 0 ? (
              <Card className="p-12 flex flex-col items-center justify-center text-center bg-white/[0.02]">
                <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10 mb-4">
                  <FileText size={24} className="text-text-dim" />
                </div>
                <h3 className="text-lg font-display font-bold text-white mb-2">No content yet</h3>
                <p className="text-sm text-text-muted max-w-md">
                  Your generated assets will appear here.
                </p>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                <AnimatePresence>
                  {projects.map(proj => (
                    <motion.div
                      key={proj.id}
                      layout
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      whileHover={{ y: -4 }}
                      transition={{ type: "spring", stiffness: 300, damping: 25 }}
                    >
                      <Card className="h-full min-h-[220px] flex flex-col p-6 group transition-all hover:bg-bg-surface hover:border-white/20 hover:shadow-[0_10px_40px_-10px_rgba(139,92,246,0.15)]">
                        <div className="flex-1">
                          <div className="flex justify-between items-start gap-4 mb-4">
                            <h3 className="text-lg font-bold text-white leading-tight line-clamp-2 font-display group-hover:text-accent-cyan transition-colors">
                              {proj.name}
                            </h3>
                            <Badge status={proj.status} className="shrink-0" />
                          </div>
                          <p className="text-sm text-text-muted line-clamp-3 leading-relaxed">
                            {proj.description || 'No description provided for this project.'}
                          </p>
                        </div>
                        
                        <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Activity size={12} className="text-text-dim" />
                            <span className="text-[10px] font-mono tracking-wider text-text-dim uppercase">
                              {new Date(proj.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          
                          <Link to={`/projects/${proj.id}`}>
                            <Button variant="ghost" className="px-4 py-2 text-xs hover:bg-accent-primary/10 hover:text-accent-primary">
                              Open Project
                            </Button>
                          </Link>
                        </div>
                      </Card>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </motion.section>
        </div>
      
      {/* Ingestion Immersive Overlay */}
      <AnimatePresence>
        {showNewProj && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6"
          >
            <div className="absolute inset-0 bg-bg-base/90 backdrop-blur-md" onClick={() => setShowNewProj(false)} />
            
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: "spring", stiffness: 300, damping: 25 }}
              className="relative w-full max-w-[720px] max-h-[90dvh] flex flex-col"
            >
              <Card glow className="w-full h-full flex flex-col bg-bg-surface/95 border-white/10 shadow-[0_0_80px_rgba(0,0,0,0.8)] overflow-hidden min-h-0">
                <div className="flex items-center justify-between p-6 sm:p-8 border-b border-white/5 bg-white/[0.02] shrink-0">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-accent-cyan/10 flex items-center justify-center border border-accent-cyan/20">
                      <Cpu size={20} className="text-accent-cyan" />
                    </div>
                    <div>
                      <h2 className="text-xl font-display font-bold text-white">Create New Project</h2>
                      <p className="text-xs text-text-muted uppercase tracking-widest mt-1">Upload your content to get started</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => setShowNewProj(false)}
                    aria-label="Close modal"
                    className="w-8 h-8 flex items-center justify-center rounded-full bg-white/5 text-text-muted hover:bg-white/10 hover:text-white transition-colors focus-visible:outline-accent-cyan"
                  >
                    <X size={18} />
                  </button>
                </div>
                
                <div className="p-6 sm:p-8 overflow-y-auto custom-scrollbar flex-1 min-h-0">
                  <form id="ingestion-form" onSubmit={handleCreateProject} className="flex flex-col gap-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <Input 
                        label="Project Name"
                        type="text"
                        value={projName}
                        onChange={(e) => setProjName(e.target.value)}
                        error={nameError}
                        required
                        placeholder="e.g. ALPHA-HOOKS-01"
                        className="font-mono"
                      />
                      <Input 
                        label="Content Title"
                        type="text"
                        value={sourceTitle}
                        onChange={(e) => setSourceTitle(e.target.value)}
                        required
                        placeholder="e.g. Masterclass V1"
                      />
                    </div>

                    <div className="flex flex-col gap-2">
                      <label className="text-sm font-semibold text-text-muted">Description <span className="text-xs font-normal text-text-dim">(Optional)</span></label>
                      <textarea 
                        value={projDesc} 
                        onChange={(e) => setProjDesc(e.target.value)} 
                        placeholder="Describe the content, tone, or audience for better AI results..."
                        rows={3}
                        className="w-full bg-white/5 border border-white/10 rounded-xl text-white px-4 py-3 font-sans outline-none transition-all placeholder:text-text-dim focus:bg-white/10 focus:border-accent-cyan/50 resize-none"
                      />
                    </div>

                    <div className="pt-6 border-t border-white/5 mt-2">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-bold text-white uppercase tracking-widest font-mono">Content Type</h3>
                      </div>
                      
                      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
                        {[
                          { id: 'ARTICLE', label: 'Raw Text', icon: FileText },
                          { id: 'YOUTUBE', label: 'Stream', icon: Link2 },
                          { id: 'VIDEO', label: 'Video', icon: Video },
                          { id: 'AUDIO', label: 'Audio', icon: Video }, // reusing icon for brevity or use Mic if available, using Video based on original
                          { id: 'PDF', label: 'Document', icon: FileText },
                        ].map(type => {
                          const Icon = type.icon;
                          const isActive = sourceType === type.id;
                          return (
                            <button
                              key={type.id}
                              type="button"
                              onClick={() => {
                                setSourceType(type.id as SourceType);
                                setSelectedFile(null);
                                setFileError('');
                              }}
                              className={cn(
                                "flex flex-col items-center justify-center gap-2 p-4 rounded-xl border transition-all duration-200",
                                isActive 
                                  ? "bg-accent-primary/10 border-accent-primary text-accent-primary shadow-[inset_0_0_20px_rgba(139,92,246,0.1)]" 
                                  : "bg-white/5 border-white/10 text-text-muted hover:bg-white/10 hover:text-white hover:border-white/20"
                              )}
                            >
                              <Icon size={20} className={isActive ? "text-accent-primary" : ""} />
                              <span className="text-xs font-bold">{type.label}</span>
                            </button>
                          );
                        })}
                      </div>

                      <AnimatePresence mode="wait">
                        {sourceType === 'YOUTUBE' && (
                          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                            <Input 
                              label="YouTube URL"
                              type="url"
                              value={sourceUrl}
                              onChange={(e) => setSourceUrl(e.target.value)}
                              error={urlError}
                              required
                              placeholder="https://www.youtube.com/watch?v=..."
                              className="font-mono text-sm"
                            />
                          </motion.div>
                        )}

                        {['VIDEO', 'AUDIO', 'PDF'].includes(sourceType) && (
                          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                            <div className="flex flex-col gap-2">
                              <label className="text-sm font-semibold text-text-muted">
                                File Upload <span className="text-xs font-normal text-accent-cyan">(Max 50MB)</span>
                              </label>
                              <div className="relative group">
                                <input 
                                  type="file"
                                  accept={sourceType === 'VIDEO' ? 'video/*' : sourceType === 'AUDIO' ? 'audio/*' : '.pdf'}
                                  onChange={(e) => {
                                    const f = e.target.files?.[0] || null;
                                    setSelectedFile(f);
                                    setFileError('');
                                  }}
                                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                                  required
                                />
                                <div className={cn(
                                  "w-full flex items-center justify-center p-8 border-2 border-dashed rounded-xl transition-colors",
                                  fileError ? "border-danger/50 bg-danger/5" : "border-white/10 bg-white/[0.02] group-hover:bg-white/5 group-hover:border-accent-cyan/50"
                                )}>
                                  <div className="flex flex-col items-center gap-2 text-center pointer-events-none">
                                    <HardDrive size={24} className={selectedFile ? "text-accent-cyan" : "text-text-dim"} />
                                    {selectedFile ? (
                                      <>
                                        <span className="text-sm font-medium text-white">{selectedFile.name}</span>
                                        <span className="text-xs text-accent-cyan font-mono">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</span>
                                      </>
                                    ) : (
                                      <>
                                        <span className="text-sm font-medium text-white">Click or drag file here</span>
                                        <span className="text-xs text-text-dim">Supported formats depend on selection</span>
                                      </>
                                    )}
                                  </div>
                                </div>
                              </div>
                              {fileError && <span className="text-xs text-danger font-medium mt-1">{fileError}</span>}
                            </div>
                          </motion.div>
                        )}

                        {sourceType === 'ARTICLE' && (
                          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                            <div className="flex flex-col gap-2">
                              <label className="text-sm font-semibold text-text-muted">Your Text Content</label>
                              <textarea 
                                value={sourceText} 
                                onChange={(e) => setSourceText(e.target.value)} 
                                required 
                                placeholder="Paste article text, blog post, transcript or raw script here..."
                                rows={6}
                                className={cn(
                                  "w-full bg-white/5 border border-white/10 rounded-xl text-white px-4 py-3 font-mono text-sm outline-none transition-all placeholder:text-text-dim focus:bg-white/10 focus:border-accent-cyan/50 resize-none",
                                  textError && "border-danger focus:border-danger bg-danger/5"
                                )}
                              />
                              {textError && <span className="text-xs text-danger font-medium mt-1">{textError}</span>}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </form>
                </div>
                
                <div className="p-6 border-t border-white/5 bg-white/[0.02] flex items-center justify-end gap-4 shrink-0">
                  <Button type="button" variant="ghost" onClick={() => setShowNewProj(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" form="ingestion-form" loading={submitting} icon={<PlayCircle size={16} />}>
                    Create Project
                  </Button>
                </div>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Quick helper for missing icon (used in the button above)
function PlayCircle({ size, className }: { size?: number, className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size || 24} height={size || 24} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="12" r="10"></circle>
      <polygon points="10 8 16 12 10 16 10 8"></polygon>
    </svg>
  );
}
