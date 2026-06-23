import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { api } from '../utils/api';
import { Card } from '../components/design/Card';
import { Badge } from '../components/design/Badge';
import { Button } from '../components/design/Button';
import { 
  BarChart3, Sparkles, Folder, CheckCircle, Clock, 
  Activity, RefreshCw, Cpu, Loader2
} from 'lucide-react';

interface WorkspaceSummary {
  plan_name: string;
  generations_count: number;
  projects_count: number;
  sources_count: number;
  assets_count: number;
  limits: {
    limit_projects: number;
    limit_generations: number;
  };
  jobs_success_rate: number;
  avg_processing_time: number;
}

interface WorkspaceTrends {
  dates: string[];
  generations: number[];
  projects: number[];
}

export default function Analytics() {
  const { currentOrg } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [summary, setSummary] = useState<WorkspaceSummary | null>(null);
  const [trends, setTrends] = useState<WorkspaceTrends | null>(null);

  useEffect(() => {
    if (currentOrg) {
      loadAnalyticsData();
    }
  }, [currentOrg]);

  const loadAnalyticsData = async () => {
    try {
      const summaryRes = await api.get(`/api/analytics/orgs/${currentOrg?.slug}/workspace/summary/`) as WorkspaceSummary;
      const trendsRes = await api.get(`/api/analytics/orgs/${currentOrg?.slug}/workspace/trends/`) as WorkspaceTrends;
      
      setSummary(summaryRes);
      setTrends(trendsRes);
    } catch (err) {
      console.error(err);
      showToast('Failed to load analytics summaries.', 'error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadAnalyticsData();
  };

  // Helper function to build premium SVG Path coordinates for Trends
  const renderSVGPath = (data: number[], width: number, height: number) => {
    if (!data || data.length === 0) return '';
    const maxVal = Math.max(...data, 5); // default base height scale
    const points = data.map((val, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - (val / maxVal) * (height - 20); // 20px padding at top
      return { x, y };
    });

    // Generate smooth bezier curve path
    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const curr = points[i];
      const next = points[i + 1];
      const cpX1 = curr.x + (next.x - curr.x) / 2;
      const cpY1 = curr.y;
      const cpX2 = curr.x + (next.x - curr.x) / 2;
      const cpY2 = next.y;
      d += ` C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${next.x} ${next.y}`;
    }
    
    // Closed path for gradient fill
    const fillD = `${d} L ${points[points.length - 1].x} ${height} L ${points[0].x} ${height} Z`;
    
    return { lineD: d, fillD, points };
  };

  if (loading) {
    return (
      <div className="flex-1 w-full flex flex-col relative z-10 max-h-[100dvh] overflow-y-auto overflow-x-hidden">
        {/* Ambient Top Glow */}
        <div className="absolute top-0 left-0 right-0 h-[500px] bg-gradient-to-b from-accent-primary/5 to-transparent pointer-events-none -z-10" />

        <div className="w-full max-w-7xl mx-auto px-6 lg:px-12 py-10 flex items-center justify-center" style={{ minHeight: '60vh' }}>
          <Loader2 className="loading-spinner" size={40} />
        </div>
      </div>
    );
  }

  const svgWidth = 600;
  const svgHeight = 220;
  const genPaths = trends ? renderSVGPath(trends.generations, svgWidth, svgHeight) : null;
  const projPaths = trends ? renderSVGPath(trends.projects, svgWidth, svgHeight) : null;

  return (
    <div className="flex-1 w-full flex flex-col relative z-10 max-h-[100dvh] overflow-y-auto overflow-x-hidden">
      {/* Ambient Top Glow */}
      <div className="absolute top-0 left-0 right-0 h-[500px] bg-gradient-to-b from-accent-primary/5 to-transparent pointer-events-none -z-10" />

      <div className="w-full max-w-7xl mx-auto px-6 lg:px-12 py-10">
        <header className="mb-10 flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-display font-bold tracking-tight text-white mb-2">Content Performance</h1>
            <p className="text-text-muted text-sm max-w-2xl">
              Track your content output, time saved, and estimated reach across all platforms.
            </p>
          </div>
          <Button variant="secondary" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw size={16} className={refreshing ? 'loading-spinner' : ''} />
            Refresh
          </Button>
        </header>

        {/* Dashboard Cards Grid */}
        <section className="bento-grid" style={{ marginBottom: '2.5rem' }}>
          {/* Card 1: Assets Generated */}
          <Card style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', fontWeight: 700 }}>Assets Generated</span>
              <Sparkles size={18} color="hsl(var(--accent-primary))" />
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800 }}>{summary?.assets_count || summary?.generations_count || 0}</div>
            <div style={{ color: 'hsl(var(--text-dim))', fontSize: '0.8rem', marginTop: 'auto' }}>
              Across {summary?.projects_count || 0} projects
            </div>
          </Card>

          {/* Card 2: Estimated Time Saved */}
          <Card style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', fontWeight: 700 }}>Hours Saved</span>
              <Clock size={18} color="hsl(var(--accent-cyan))" />
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800 }}>
              {Math.round(((summary?.assets_count || summary?.generations_count || 0) * 45) / 60)} <span className="text-sm text-text-dim font-normal">hrs</span>
            </div>
            <div style={{ color: 'hsl(var(--text-dim))', fontSize: '0.8rem', marginTop: 'auto' }}>
              Based on 45m per asset creation
            </div>
          </Card>

          {/* Card 3: Publishing Rate */}
          <Card style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', fontWeight: 700 }}>Content Velocity</span>
              <Activity size={18} color="hsl(var(--success))" />
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800 }}>High</div>
            <div style={{ color: 'hsl(var(--text-dim))', fontSize: '0.8rem', marginTop: 'auto' }}>
              Consistency score
            </div>
          </Card>

          {/* Card 4: Plan Status */}
          <Card style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', fontWeight: 700 }}>Current Plan</span>
              <Cpu size={18} color="hsl(var(--accent-secondary))" />
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800 }}>{summary?.plan_name}</div>
            <div style={{ color: 'hsl(var(--text-dim))', fontSize: '0.8rem', marginTop: 'auto' }}>
              Limit: {summary?.limits?.limit_generations === 999999 ? 'Unlimited' : `${summary?.limits?.limit_generations || 0} / mo`}
            </div>
          </Card>
        </section>

        {/* 30-Day Trend Chart using Premium Native SVG */}
        <section style={{ marginBottom: '2.5rem' }}>
          <Card style={{ padding: '2.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={20} color="hsl(var(--accent-primary))" />
              AI generation & project creation trends (Last 30 Days)
            </h2>

            {trends && trends.dates && Array.isArray(trends.dates) && trends.dates.length > 0 ? (
              <div>
                {/* SVG Chart Wrapper */}
                <div style={{ width: '100%', overflowX: 'auto', marginBottom: '1.5rem' }}>
                  <svg 
                    viewBox={`0 0 ${svgWidth} ${svgHeight}`} 
                    style={{ width: '100%', minWidth: '600px', height: 'auto', overflow: 'visible' }}
                  >
                    <defs>
                      <linearGradient id="genGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--accent-primary))" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="hsl(var(--accent-primary))" stopOpacity="0.0" />
                      </linearGradient>
                      <linearGradient id="projGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--accent-secondary))" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="hsl(var(--accent-secondary))" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>
                    
                    {/* Grid lines */}
                    <line x1="0" y1={svgHeight} x2={svgWidth} y2={svgHeight} stroke="hsl(var(--border-muted))" strokeWidth="1" />
                    <line x1="0" y1={svgHeight / 2} x2={svgWidth} y2={svgHeight / 2} stroke="hsl(var(--border-muted) / 0.4)" strokeWidth="1" strokeDasharray="4 4" />
                    <line x1="0" y1="20" x2={svgWidth} y2="20" stroke="hsl(var(--border-muted) / 0.4)" strokeWidth="1" strokeDasharray="4 4" />

                    {/* Area Gradients */}
                    {genPaths && (
                      <path d={genPaths.fillD} fill="url(#genGrad)" />
                    )}
                    {projPaths && (
                      <path d={projPaths.fillD} fill="url(#projGrad)" />
                    )}

                    {/* Line paths */}
                    {genPaths && (
                      <path d={genPaths.lineD} fill="none" stroke="hsl(var(--accent-primary))" strokeWidth="3.5" strokeLinecap="round" />
                    )}
                    {projPaths && (
                      <path d={projPaths.lineD} fill="none" stroke="hsl(var(--accent-secondary))" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="2" />
                    )}

                    {/* Data Points Glow */}
                    {genPaths && genPaths.points.map((p, idx) => (
                      (idx === 0 || idx === genPaths.points.length - 1 || idx % 4 === 0) && (
                        <g key={`gp-${idx}`}>
                          <circle cx={p.x} cy={p.y} r="5" fill="hsl(var(--bg-main))" stroke="hsl(var(--accent-primary))" strokeWidth="3" />
                        </g>
                      )
                    ))}
                  </svg>
                </div>

                {/* Legend & Labels */}
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'hsl(var(--text-muted))', padding: '0 0.5rem' }}>
                  <span>{trends.dates[0]}</span>
                  <span>{trends.dates[Math.floor(trends.dates.length / 2)]}</span>
                  <span>{trends.dates[trends.dates.length - 1]}</span>
                </div>

                <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center', marginTop: '1.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '4px', background: 'hsl(var(--accent-primary))' }} />
                    <span style={{ fontWeight: 600 }}>AI Content Generations (Usage)</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '4px', background: 'hsl(var(--accent-secondary))', border: '1.5px dashed hsl(var(--accent-secondary))' }} />
                    <span style={{ fontWeight: 600 }}>Projects Created</span>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', color: 'hsl(var(--text-dim))', padding: '3rem 0' }}>
                Insufficient usage trends data to plot graphs.
              </div>
            )}
          </Card>
        </section>

        {/* Insights & Actions */}
        <section className="bento-grid">
          <Card style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BarChart3 size={18} color="hsl(var(--accent-primary))" />
              Content Impact Insights
            </h3>
            <ul style={{ paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem', color: 'hsl(var(--text-muted))' }}>
              <li>
                You have generated <strong>{summary?.assets_count || summary?.generations_count || 0} unique content assets</strong> this month.
              </li>
              <li>
                Your workflow has saved you an estimated <strong>{Math.round(((summary?.assets_count || summary?.generations_count || 0) * 45) / 60)} hours</strong> of writing and editing time.
              </li>
              <li>
                You are utilizing <strong>{summary?.projects_count}</strong> of your {summary?.limits?.limit_projects === 999999 ? 'unlimited' : (summary?.limits?.limit_projects || 0)} allocated projects.
              </li>
            </ul>
          </Card>
        </section>
      </div>
    </div>
  );
}
