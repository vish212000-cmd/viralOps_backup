import React from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, Video, FileText, BarChart, ArrowRight, Zap, Target, Layers } from 'lucide-react';

export default function LandingPage() {
  return (
    <div style={{ minHeight: '100vh', background: 'hsl(var(--bg-main))', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header className="glass-panel" style={{ margin: '1.5rem', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderRadius: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ background: 'linear-gradient(135deg, hsl(var(--accent-primary)), hsl(var(--accent-secondary)))', width: '36px', height: '36px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Sparkles size={20} color="#fff" />
          </div>
          <span style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'var(--font-display)', letterSpacing: '-0.03em' }}>
            Viral<span style={{ color: 'hsl(var(--accent-primary))' }}>Ops</span>
          </span>
        </div>
        <nav style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
          <a href="#features" style={{ color: 'hsl(var(--text-muted))', textDecoration: 'none', fontWeight: 500 }}>Features</a>
          <a href="#pricing" style={{ color: 'hsl(var(--text-muted))', textDecoration: 'none', fontWeight: 500 }}>Pricing</a>
          <Link to="/login" style={{ color: 'hsl(var(--text-primary))', textDecoration: 'none', fontWeight: 600 }}>Login</Link>
          <Link to="/signup" className="button" style={{ textDecoration: 'none', padding: '0.6rem 1.2rem' }}>
            Get Started <ArrowRight size={16} />
          </Link>
        </nav>
      </header>

      {/* Hero Section */}
      <main style={{ flex: 1, maxWidth: '1200px', margin: '0 auto', padding: '4rem 2rem', textAlign: 'center' }}>
        <div className="gradient-glow" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'hsl(var(--accent-primary) / 0.1)', border: '1px solid hsl(var(--accent-primary) / 0.3)', padding: '0.5rem 1rem', borderRadius: '99px', color: 'hsl(var(--accent-primary))', fontSize: '0.85rem', fontWeight: 600, marginBottom: '2rem' }}>
          <Zap size={14} /> AI-Powered Social Ingestion Engine
        </div>

        <h1 className="gradient-text" style={{ fontSize: '4.5rem', fontWeight: 800, lineHeight: 1.1, marginBottom: '1.5rem', fontFamily: 'var(--font-display)' }}>
          Turn Long-Form Content<br />Into Viral Assets
        </h1>
        
        <p style={{ color: 'hsl(var(--text-muted))', fontSize: '1.25rem', maxWidth: '700px', margin: '0 auto 3rem auto', lineHeight: 1.6 }}>
          Submit raw video, podcasts, transcripts, articles, or scripts. Extract high-performing hooks, clickable titles, social captions, CTA variants, hashtags, and short scripts optimized for Shorts, Reels, and TikTok.
        </p>

        <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center' }}>
          <Link to="/signup" className="button" style={{ fontSize: '1.1rem', padding: '0.9rem 2.2rem', textDecoration: 'none' }}>
            Start Repurposing Free
          </Link>
          <a href="#features" className="button secondary" style={{ fontSize: '1.1rem', padding: '0.9rem 2.2rem', textDecoration: 'none' }}>
            Explore Features
          </a>
        </div>

        {/* Bento Grid Features */}
        <section id="features" style={{ marginTop: '8rem', textAlign: 'left' }}>
          <h2 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '3rem', fontFamily: 'var(--font-display)', textAlign: 'center' }}>
            Engineered For Scale. Designed For Creators.
          </h2>
          
          <div className="bento-grid">
            <div className="glass-panel" style={{ padding: '2rem' }}>
              <Video style={{ color: 'hsl(var(--accent-primary))', marginBottom: '1rem' }} size={32} />
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Multi-Source Ingestion</h3>
              <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: 1.5 }}>
                Submit YouTube links, upload raw audio/video files, or paste transcripts, raw scripts, article PDFs, and blogs.
              </p>
            </div>

            <div className="glass-panel" style={{ padding: '2rem' }}>
              <Layers style={{ color: 'hsl(var(--accent-secondary))', marginBottom: '1rem' }} size={32} />
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Social Output Packs</h3>
              <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: 1.5 }}>
                Get custom bundles containing multiple hook variations, titles, captions, CTAs, tags, and formatted short scripts.
              </p>
            </div>

            <div className="glass-panel" style={{ padding: '2rem' }}>
              <Target style={{ color: 'hsl(var(--accent-indigo))', marginBottom: '1rem' }} size={32} />
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Workspace Preferences Memory</h3>
              <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: 1.5 }}>
                Store your brand's unique tone, preferred hooks, and style requirements. Every generation automatically aligns with your identity.
              </p>
            </div>

            <div className="glass-panel" style={{ padding: '2rem' }}>
              <BarChart style={{ color: 'hsl(var(--success))', marginBottom: '1rem' }} size={32} />
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Enterprise Operations</h3>
              <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: 1.5 }}>
                Monitor API usage, track failed jobs, inspect comprehensive audit logs, and easily run retries via our admin panel.
              </p>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" style={{ marginTop: '8rem', paddingBottom: '4rem' }}>
          <h2 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '1rem', fontFamily: 'var(--font-display)', textAlign: 'center' }}>
            Flexible Pricing for Growing Teams
          </h2>
          <p style={{ color: 'hsl(var(--text-muted))', textAlign: 'center', marginBottom: '4rem' }}>
            Scale up as your social presence grows.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2rem', maxWidth: '900px', margin: '0 auto' }}>
            <div className="glass-panel" style={{ padding: '3rem 2rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Creator Free</h3>
                <div style={{ fontSize: '2.5rem', fontWeight: 700, margin: '1.5rem 0' }}>$0 <span style={{ fontSize: '1rem', color: 'hsl(var(--text-muted))' }}>/ mo</span></div>
                <ul style={{ listStyle: 'none', color: 'hsl(var(--text-muted))', lineHeight: 2, marginBottom: '2rem', fontSize: '0.95rem' }}>
                  <li>✓ 3 Projects / month</li>
                  <li>✓ Text Ingestion only</li>
                  <li>✓ Standard Hook Generation</li>
                  <li>✓ 1 User Seat</li>
                </ul>
              </div>
              <Link to="/signup" className="button secondary" style={{ justifyContent: 'center', textDecoration: 'none' }}>Get Started</Link>
            </div>

            <div className="glass-panel" style={{ padding: '3rem 2rem', borderColor: 'hsl(var(--accent-primary) / 0.5)', position: 'relative', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{ position: 'absolute', top: '-12px', right: '24px', background: 'hsl(var(--accent-primary))', color: '#fff', padding: '0.25rem 0.75rem', borderRadius: '99px', fontSize: '0.75rem', fontWeight: 700 }}>MOST POPULAR</div>
              <div>
                <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Pro Plan</h3>
                <div style={{ fontSize: '2.5rem', fontWeight: 700, margin: '1.5rem 0' }}>$29 <span style={{ fontSize: '1rem', color: 'hsl(var(--text-muted))' }}>/ mo</span></div>
                <ul style={{ listStyle: 'none', color: 'hsl(var(--text-muted))', lineHeight: 2, marginBottom: '2rem', fontSize: '0.95rem' }}>
                  <li>✓ Unlimited Projects</li>
                  <li>✓ Video/Audio File Uploads</li>
                  <li>✓ YouTube Link Ingestion</li>
                  <li>✓ Tone & Brand Memory Layer</li>
                  <li>✓ Pro Asset Exports</li>
                </ul>
              </div>
              <Link to="/signup" className="button" style={{ justifyContent: 'center', textDecoration: 'none' }}>Upgrade to Pro</Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid hsl(var(--border-muted))', padding: '2rem', textAlign: 'center', color: 'hsl(var(--text-dim))', fontSize: '0.9rem' }}>
        &copy; {new Date().getFullYear()} ViralOps Inc. All rights reserved.
      </footer>
    </div>
  );
}
