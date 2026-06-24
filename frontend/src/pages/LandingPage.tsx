import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Video, Type, BarChart2, ArrowRight, Zap, Target, Layers, Play, CheckCircle2 } from 'lucide-react';
import { Button } from '../components/design/Button';
import { Card } from '../components/design/Card';

export default function LandingPage() {
  const container: any = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const item: any = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="min-h-screen bg-bg-base flex flex-col font-sans overflow-x-hidden selection:bg-accent-primary/30">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-accent-primary rounded-lg flex items-center justify-center">
              <Sparkles size={18} className="text-white" />
            </div>
            <span className="text-xl font-display font-bold tracking-tight text-white">
              ViralOps
            </span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#features" className="text-sm font-medium text-text-muted hover:text-white transition-colors hidden md:block">Features</a>
            <a href="#pricing" className="text-sm font-medium text-text-muted hover:text-white transition-colors hidden md:block">Pricing</a>
            <Link to="/login" className="text-sm font-bold text-white hover:text-accent-primary transition-colors">Log in</Link>
            <Link to="/signup">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-1 pt-32 pb-20 px-6 relative">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-3xl h-[400px] bg-accent-primary/20 blur-[120px] pointer-events-none rounded-full" />
        
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-primary/10 border border-accent-primary/20 text-accent-primary text-xs font-bold tracking-wide uppercase mb-8">
            <Sparkles size={14} /> The AI Content Team for Creators
          </motion.div>
          
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }} className="text-5xl md:text-7xl font-display font-bold text-white tracking-tight leading-[1.1] mb-6">
            Turn one video into <br className="hidden md:block" /> a month of content.
          </motion.h1>
          
          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }} className="text-lg md:text-xl text-text-muted max-w-2xl mx-auto mb-10 leading-relaxed">
            Upload your podcast, YouTube video, or article. Our AI extracts the best moments, writes engaging hooks, and generates ready-to-post social assets in seconds.
          </motion.p>
          
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }} className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/signup">
              <Button size="lg" className="w-full sm:w-auto text-lg px-8 py-6" icon={<ArrowRight size={20} />}>
                Start Creating for Free
              </Button>
            </Link>
            <a href="#features">
              <Button variant="ghost" size="lg" className="w-full sm:w-auto text-lg px-8 py-6">
                See How It Works
              </Button>
            </a>
          </motion.div>
        </div>

        {/* Bento Grid Features */}
        <div id="features" className="max-w-6xl mx-auto mt-40">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-display font-bold text-white mb-4 tracking-tight">Everything you need to go viral.</h2>
            <p className="text-text-muted text-lg">Designed specifically for modern creators and personal brands.</p>
          </div>

          <motion.div 
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
            className="grid grid-cols-1 md:grid-cols-3 auto-rows-[320px] gap-6"
          >
            {/* Large Card */}
            <motion.div variants={item} className="md:col-span-2">
              <Card className="h-full p-8 flex flex-col justify-between bg-gradient-to-br from-white/[0.05] to-transparent border-white/10 overflow-hidden relative group">
                <div className="absolute top-0 right-0 w-64 h-64 bg-accent-cyan/10 blur-[60px] rounded-full translate-x-1/2 -translate-y-1/2 group-hover:bg-accent-cyan/20 transition-colors duration-500" />
                <div className="relative z-10">
                  <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center mb-6 border border-white/5">
                    <Video size={24} className="text-white" />
                  </div>
                  <h3 className="text-2xl font-display font-bold text-white mb-3">Accepts Any Format</h3>
                  <p className="text-text-muted text-lg max-w-md">
                    Paste a YouTube link, upload raw audio, or drop in a PDF script. We process it all and find the hidden gems.
                  </p>
                </div>
              </Card>
            </motion.div>

            {/* Small Card */}
            <motion.div variants={item}>
              <Card className="h-full p-8 flex flex-col justify-between bg-white/[0.02] border-white/5 hover:bg-white/[0.04] transition-colors">
                <div>
                  <div className="w-12 h-12 bg-accent-primary/20 rounded-xl flex items-center justify-center mb-6">
                    <Type size={24} className="text-accent-primary" />
                  </div>
                  <h3 className="text-xl font-display font-bold text-white mb-2">Platform-Specific</h3>
                  <p className="text-text-muted">
                    Outputs perfectly formatted for X, LinkedIn, TikTok, and Instagram Reels.
                  </p>
                </div>
              </Card>
            </motion.div>

            {/* Small Card */}
            <motion.div variants={item}>
              <Card className="h-full p-8 flex flex-col justify-between bg-white/[0.02] border-white/5 hover:bg-white/[0.04] transition-colors">
                <div>
                  <div className="w-12 h-12 bg-warning/20 rounded-xl flex items-center justify-center mb-6">
                    <Target size={24} className="text-warning" />
                  </div>
                  <h3 className="text-xl font-display font-bold text-white mb-2">Brand Kit</h3>
                  <p className="text-text-muted">
                    Teach the AI your exact tone of voice, audience, and preferred calls to action.
                  </p>
                </div>
              </Card>
            </motion.div>

            {/* Large Card */}
            <motion.div variants={item} className="md:col-span-2">
              <Card className="h-full p-8 flex flex-col justify-between bg-white/[0.02] border-white/5 relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-t from-accent-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative z-10 flex flex-col md:flex-row gap-8 items-center h-full">
                  <div className="flex-1">
                    <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center mb-6 border border-white/5">
                      <Zap size={24} className="text-white" />
                    </div>
                    <h3 className="text-2xl font-display font-bold text-white mb-3">Instant Assets</h3>
                    <p className="text-text-muted text-lg">
                      Stop staring at a blank page. Generate 10+ clickable titles, viral hooks, and engaging threads from one piece of content in minutes.
                    </p>
                  </div>
                </div>
              </Card>
            </motion.div>
          </motion.div>
        </div>

        {/* Pricing */}
        <div id="pricing" className="max-w-5xl mx-auto mt-40 mb-20">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-display font-bold text-white mb-4 tracking-tight">Simple, transparent pricing.</h2>
            <p className="text-text-muted text-lg">Start for free, upgrade when you need more power.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <Card className="p-10 bg-white/[0.02] border-white/5 flex flex-col">
              <h3 className="text-2xl font-display font-bold text-white mb-2">Starter</h3>
              <p className="text-text-muted mb-6">Perfect for trying out the platform.</p>
              <div className="text-5xl font-display font-bold text-white mb-8">$0 <span className="text-lg text-text-muted font-normal">/mo</span></div>
              
              <ul className="space-y-4 mb-10 flex-1">
                {[
                  '3 Projects per month',
                  'Text ingestion only',
                  'Standard social assets',
                  'Basic templates'
                ].map((feature, i) => (
                  <li key={i} className="flex items-center gap-3 text-text-muted">
                    <CheckCircle2 size={18} className="text-white/30" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Link to="/signup" className="w-full">
                <Button variant="secondary" className="w-full">Get Started</Button>
              </Link>
            </Card>

            <Card className="p-10 bg-gradient-to-b from-white/[0.08] to-white/[0.02] border-accent-primary/30 relative flex flex-col">
              <div className="absolute top-0 right-10 -translate-y-1/2 px-3 py-1 bg-accent-primary text-white text-xs font-bold uppercase tracking-wider rounded-full">
                Most Popular
              </div>
              <h3 className="text-2xl font-display font-bold text-white mb-2">Creator Pro</h3>
              <p className="text-text-muted mb-6">For serious creators and agencies.</p>
              <div className="text-5xl font-display font-bold text-white mb-8">$29 <span className="text-lg text-text-muted font-normal">/mo</span></div>
              
              <ul className="space-y-4 mb-10 flex-1">
                {[
                  'Unlimited Projects',
                  'Video & Audio uploads',
                  'YouTube link ingestion',
                  'Brand Kit integration',
                  'Priority support'
                ].map((feature, i) => (
                  <li key={i} className="flex items-center gap-3 text-text-muted">
                    <CheckCircle2 size={18} className="text-accent-primary" />
                    <span className="text-white">{feature}</span>
                  </li>
                ))}
              </ul>
              <Link to="/signup" className="w-full">
                <Button className="w-full">Upgrade to Pro</Button>
              </Link>
            </Card>
          </div>
        </div>
      </main>

      <footer className="py-8 border-t border-white/5 text-center text-sm text-text-dim">
        <p>&copy; {new Date().getFullYear()} ViralOps Inc. All rights reserved.</p>
      </footer>
    </div>
  );
}
