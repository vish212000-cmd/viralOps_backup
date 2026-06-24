import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { api } from '../utils/api';
import { ProcessingJob, AuditLog as LogItem } from '../types';
import { Button } from '../components/design/Button';
import { Badge } from '../components/design/Badge';
import { Card } from '../components/design/Card';
import { 
  Sparkles, Loader2, RefreshCw, AlertOctagon, ShieldAlert, CheckCircle, 
  Clock, Activity, Shield, Folder, Settings, LogOut, Users, Layers, DollarSign
} from 'lucide-react';

interface SummaryStats {
  total_users: number;
  total_organizations: number;
  total_projects: number;
  projects_created_today: number;
  projects_processing: number;
  projects_completed: number;
  projects_failed: number;
  total_jobs: number;
  failed_jobs: number;
  average_processing_time: number;
  usage_transcription_minutes: number;
  usage_ai_generations: number;
  total_sources: number;
  transcript_success_rate: number;
  moment_detection_success_rate: number;
  asset_generation_success_rate: number;
  youtube_success_rate: number;
  pdf_success_rate: number;
  nvidia_api_errors: number;
  youtube_transcript_errors: number;
  total_moments: number;
  total_assets: number;
  queue_depth: number;
  stuck_projects: number;
  celery_failures: number;
  redis_failures: number;
}

interface AdminAnalyticsSummary {
  active_workspaces: number;
  total_revenue: number;
  job_status_counts: {
    PENDING: number;
    RUNNING: number;
    COMPLETED: number;
    FAILED: number;
  };
  plan_breakdown: Record<string, number>;
}

interface AdminSystemHealth {
  status: string;
  services: {
    database: string;
    cache_redis: string;
  };
  queue: {
    active_jobs_count: number;
    failed_jobs_last_7_days: number;
  };
  timestamp: string;
}

export default function AdminDashboard() {
  const { user, logoutUser } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<SummaryStats | null>(null);
  const [analytics, setAnalytics] = useState<AdminAnalyticsSummary | null>(null);
  const [health, setHealth] = useState<AdminSystemHealth | null>(null);
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [error, setError] = useState('');
  const [retryingJobId, setRetryingJobId] = useState<number | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setLoading(true);
    setError('');
    try {
      const stats = await api.get('/api/adminops/summary/') as SummaryStats;
      setSummary(stats);

      const analyticsSummary = await api.get('/api/analytics/admin/summary/') as AdminAnalyticsSummary;
      setAnalytics(analyticsSummary);

      const healthRes = await api.get('/api/analytics/admin/system-health/') as AdminSystemHealth;
      setHealth(healthRes);

      const jobQueue = await api.get('/api/adminops/jobs/') as ProcessingJob[];
      setJobs(jobQueue);

      const auditLogs = await api.get('/api/adminops/logs/') as LogItem[];
      setLogs(auditLogs);
    } catch (err) {
      console.error(err);
      setError('You must have Super Admin permissions to access the operations panel.');
    } finally {
      setLoading(false);
    }
  };

  const handleRetryJob = async (jobId: number) => {
    setRetryingJobId(jobId);
    try {
      await api.post(`/api/adminops/jobs/${jobId}/retry/`);
      showToast('Rescheduled job!', 'success');
      loadAdminData();
    } catch (err) {
      console.error(err);
      showToast('Failed to reschedule job.', 'error');
    } finally {
      setRetryingJobId(null);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'hsl(var(--bg-main))' }}>
        <Loader2 className="loading-spinner" size={40} />
      </div>
    );
  }

  if (error || !summary || !analytics || !health) {
    return (
      <div className="flex-1 w-full flex flex-col relative z-10 max-h-[100dvh] overflow-y-auto overflow-x-hidden">
        {/* Ambient Top Glow */}
        <div className="absolute top-0 left-0 right-0 h-[500px] bg-gradient-to-b from-accent-primary/5 to-transparent pointer-events-none -z-10" />

        <div className="w-full max-w-7xl mx-auto px-6 lg:px-12 py-10 flex flex-col justify-center items-center" style={{ minHeight: '60vh' }}>
          <ShieldAlert size={48} color="hsl(var(--danger))" style={{ marginBottom: '1.5rem' }} />
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.5rem' }}>Access Denied</h2>
          <p style={{ color: 'hsl(var(--text-muted))', maxWidth: '420px', textAlign: 'center', lineHeight: 1.6, marginBottom: '2rem' }}>
            The operational dashboard is reserved for Super Admins. Please contact your workspace administrator to upgrade your access role.
          </p>
          <Link to="/dashboard" className="button" style={{ textDecoration: 'none' }}>
            Return to Projects Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 w-full flex flex-col relative z-10 max-h-[100dvh] overflow-y-auto overflow-x-hidden">
      {/* Ambient Top Glow */}
      <div className="absolute top-0 left-0 right-0 h-[500px] bg-gradient-to-b from-accent-primary/5 to-transparent pointer-events-none -z-10" />

      <div className="w-full max-w-7xl mx-auto px-6 lg:px-12 py-10">
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>Super Admin Operations</h1>
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', marginTop: '0.25rem' }}>
              Inspect background queues, track business revenue parameters, and trace security audit trials.
            </p>
          </div>
          <Button onClick={loadAdminData} variant="secondary" style={{ padding: '0.5rem 1rem' }}>
            <RefreshCw size={14} /> Refresh Panel
          </Button>
        </header>

        {/* Aggregate Stats */}
        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
          {[
            { label: 'Total Users', val: summary.total_users, icon: <Users size={20} color="hsl(var(--accent-primary))" /> },
            { label: 'Active Workspaces', val: analytics.active_workspaces, icon: <Layers size={20} color="hsl(var(--accent-secondary))" /> },
            { label: 'Payments Revenue', val: `₹${parseInt(analytics.total_revenue as any)}`, icon: <DollarSign size={20} color="hsl(var(--success))" /> },
            { label: 'Active Queue Jobs', val: health.queue.active_jobs_count, icon: <Activity size={20} color="hsl(var(--accent-indigo))" /> },
            { label: 'Failed Jobs (7d)', val: health.queue.failed_jobs_last_7_days, icon: <AlertOctagon size={20} color="hsl(var(--danger))" /> },
          ].map((stat, i) => (
            <Card key={i} style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ background: 'hsl(var(--bg-main))', padding: '0.6rem', borderRadius: '8px', border: '1px solid hsl(var(--border-muted))' }}>{stat.icon}</div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>{stat.label}</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{stat.val}</div>
              </div>
            </Card>
          ))}
        </section>

        {/* Production Health Stats */}
        <section style={{ marginBottom: '2.5rem' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={20} color="hsl(var(--accent-primary))" /> Production Health
          </h2>
          <div className="bento-grid">
            <Card style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Folder size={16} /> Projects Status
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>Created Today</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{summary.projects_created_today}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>Processing</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'hsl(var(--accent-indigo))' }}>{summary.projects_processing}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>Completed</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'hsl(var(--success))' }}>{summary.projects_completed}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>Failed</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'hsl(var(--danger))' }}>{summary.projects_failed}</div>
                </div>
              </div>
            </Card>
            
            <Card style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} /> Content Success Rates
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>Transcript Extracted</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{summary.transcript_success_rate}%</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>Moment Detection</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{summary.moment_detection_success_rate}%</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>Asset Generation</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{summary.asset_generation_success_rate}%</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>Avg Process Time</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{summary.average_processing_time}s</div>
                </div>
              </div>
            </Card>

            <Card style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'hsl(var(--danger))' }}>
                <AlertOctagon size={16} /> Critical Errors & Health
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.85rem', color: 'hsl(var(--text-muted))' }}>NVIDIA API Errors</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: summary.nvidia_api_errors > 0 ? 'hsl(var(--danger))' : 'hsl(var(--text-primary))' }}>{summary.nvidia_api_errors}</div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.85rem', color: 'hsl(var(--text-muted))' }}>YouTube Transcript Errors</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: summary.youtube_transcript_errors > 0 ? 'hsl(var(--danger))' : 'hsl(var(--text-primary))' }}>{summary.youtube_transcript_errors}</div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.85rem', color: 'hsl(var(--text-muted))' }}>Redis Failures</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: summary.redis_failures > 0 ? 'hsl(var(--danger))' : 'hsl(var(--text-primary))' }}>{summary.redis_failures}</div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.85rem', color: 'hsl(var(--text-muted))' }}>Celery Failures</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: summary.celery_failures > 0 ? 'hsl(var(--danger))' : 'hsl(var(--text-primary))' }}>{summary.celery_failures}</div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.85rem', color: 'hsl(var(--text-muted))' }}>Stuck Projects (&gt;15m)</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: summary.stuck_projects > 0 ? 'hsl(var(--danger))' : 'hsl(var(--text-primary))' }}>{summary.stuck_projects}</div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.85rem', color: 'hsl(var(--text-muted))' }}>Queue Depth</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: summary.queue_depth > 10 ? 'hsl(var(--warning))' : 'hsl(var(--text-primary))' }}>{summary.queue_depth}</div>
                </div>
              </div>
            </Card>
          </div>
        </section>

        {/* Health status & DB status */}
        <section className="bento-grid" style={{ marginBottom: '2.5rem' }}>
          <Card style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={16} color="hsl(var(--accent-primary))" />
              Connection & Service Status
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.9rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Database Connectivity:</span>
                <span style={{ 
                  color: health.services.database === 'UP' ? 'hsl(var(--success))' : 'hsl(var(--danger))', 
                  fontWeight: 700, 
                  display: 'inline-flex', 
                  alignItems: 'center', 
                  gap: '0.2rem' 
                }}>
                  <CheckCircle size={14} /> {health.services.database === 'UP' ? 'Operational' : 'Disconnected'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Redis / Cache Core:</span>
                <span style={{ 
                  color: health.services.cache_redis === 'UP' ? 'hsl(var(--success))' : 'hsl(var(--danger))', 
                  fontWeight: 700, 
                  display: 'inline-flex', 
                  alignItems: 'center', 
                  gap: '0.2rem' 
                }}>
                  <CheckCircle size={14} /> {health.services.cache_redis === 'UP' ? 'Operational' : 'Unavailable'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Global System Status:</span>
                <span style={{ 
                  color: health.status === 'HEALTHY' ? 'hsl(var(--success))' : 'hsl(var(--warning))',
                  fontWeight: 700 
                }}>
                  {health.status}
                </span>
              </div>
            </div>
          </Card>

          <Card style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Layers size={16} color="hsl(var(--accent-secondary))" />
              Subscription Plans Breakdown
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
              {Object.entries(analytics.plan_breakdown).map(([planName, count]) => (
                <div key={planName} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{planName}:</span>
                  <span style={{ fontWeight: 700 }}>{count} workspaces</span>
                </div>
              ))}
            </div>
          </Card>
        </section>

        {/* Job Queue trace */}
        <section style={{ marginBottom: '2.5rem' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Clock size={20} /> Background Processing Trace (Last 50 Jobs)
          </h2>
          <Card style={{ padding: 0, overflowX: 'auto', borderRadius: '12px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid hsl(var(--border-muted))', color: 'hsl(var(--text-muted))' }}>
                  <th style={{ padding: '1rem' }}>Job ID</th>
                  <th style={{ padding: '1rem' }}>Project ID</th>
                  <th style={{ padding: '1rem' }}>Status</th>
                  <th style={{ padding: '1rem' }}>Log / Error Trace</th>
                  <th style={{ padding: '1rem' }}>Created At</th>
                  <th style={{ padding: '1rem' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ padding: '2rem', textAlign: 'center', color: 'hsl(var(--text-dim))' }}>No queue jobs registered.</td>
                  </tr>
                ) : (
                  jobs.map(job => (
                    <tr key={job.id} style={{ borderBottom: '1px solid hsl(var(--border-muted) / 0.5)' }}>
                      <td style={{ padding: '1rem', fontFamily: 'monospace' }}>#{job.id}</td>
                      <td style={{ padding: '1rem' }}>Project #{job.project}</td>
                      <td style={{ padding: '1rem' }}>
                        <span className={`badge badge-${job.status.toLowerCase()}`}>
                          {job.status}
                        </span>
                      </td>
                      <td style={{ padding: '1rem', color: 'hsl(var(--text-dim))', maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {job.error_log || '-'}
                      </td>
                      <td style={{ padding: '1rem' }}>{new Date(job.created_at).toLocaleString()}</td>
                      <td style={{ padding: '1rem' }}>
                        {job.status === 'FAILED' && (
                          <Button 
                            variant="secondary" 
                            onClick={() => handleRetryJob(job.id)}
                            loading={retryingJobId === job.id}
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                          >
                            Retry
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </Card>
        </section>

        {/* Audit Log Panel */}
        <section>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Shield size={20} /> System Audit Trail Actions
          </h2>
          <Card style={{ padding: '1.5rem', maxHeight: '400px', overflowY: 'auto' }}>
            {logs.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'hsl(var(--text-dim))', padding: '2rem' }}>No audit trails recorded.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {logs.map(log => (
                  <div key={log.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.5rem 0', borderBottom: '1px solid hsl(var(--border-muted) / 0.3)' }}>
                    <div>
                      <span style={{ color: 'hsl(var(--accent-secondary))', fontWeight: 600 }}>{log.username || 'System'}</span>{' '}
                      <span style={{ color: 'hsl(var(--text-primary))' }}>{log.action}</span>{' '}
                      <span style={{ color: 'hsl(var(--text-dim))' }}>({JSON.stringify(log.details)})</span>
                    </div>
                    <div style={{ color: 'hsl(var(--text-dim))' }}>
                      {new Date(log.created_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </section>

      </div>
    </div>
  );
}
