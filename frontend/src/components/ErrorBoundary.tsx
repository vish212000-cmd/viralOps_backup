import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an uncaught error:", error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/dashboard';
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'hsl(var(--bg-main))', padding: '1.5rem' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '500px', padding: '2.5rem', textAlign: 'center', borderColor: 'hsl(var(--danger) / 0.3)' }}>
            <div style={{ background: 'hsl(var(--danger) / 0.1)', width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem auto' }}>
              <AlertOctagon size={32} color="hsl(var(--danger))" />
            </div>
            
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.75rem', fontFamily: 'var(--font-display)' }}>
              Application Render Crash
            </h2>
            
            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.95rem', lineHeight: 1.6, marginBottom: '2rem' }}>
              A critical client-side rendering error occurred. The application state has been preserved in console logs.
            </p>

            <div style={{ background: 'hsl(var(--bg-main))', padding: '1rem', borderRadius: '8px', border: '1px solid hsl(var(--border-muted))', fontSize: '0.8rem', fontFamily: 'monospace', textAlign: 'left', overflowX: 'auto', marginBottom: '2rem', color: 'hsl(var(--danger))' }}>
              {this.state.error?.toString() || 'Unknown runtime render exception'}
            </div>

            <button onClick={this.handleReset} style={{ justifyContent: 'center', width: '100%' }}>
              <RotateCcw size={16} /> Reset Application Layout
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
