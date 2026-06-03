import React, { createContext, useContext, useState, ReactNode } from 'react';
import { X, CheckCircle, Info, AlertTriangle, AlertOctagon } from 'lucide-react';

export type ToastType = 'success' | 'info' | 'warning' | 'error';

export interface ToastMessage {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = (message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast: ToastMessage = { id, message, type };
    setToasts(prev => [...prev, newToast]);

    // Auto dismiss after 4 seconds
    setTimeout(() => {
      dismissToast(id);
    }, 4000);
  };

  const dismissToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const icons = {
    success: <CheckCircle size={16} color="hsl(var(--success))" />,
    info: <Info size={16} color="hsl(var(--accent-secondary))" />,
    warning: <AlertTriangle size={16} color="hsl(var(--warning))" />,
    error: <AlertOctagon size={16} color="hsl(var(--danger))" />,
  };

  const borderColors = {
    success: 'hsl(var(--success) / 0.3)',
    info: 'hsl(var(--accent-secondary) / 0.3)',
    warning: 'hsl(var(--warning) / 0.3)',
    error: 'hsl(var(--danger) / 0.3)',
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      
      {/* Toasts Portal Container */}
      <div style={{
        position: 'fixed',
        top: '1.5rem',
        right: '1.5rem',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        maxWidth: '380px',
        width: '100%',
        pointerEvents: 'none'
      }}>
        {toasts.map(toast => (
          <div 
            key={toast.id}
            className="glass-panel" 
            style={{
              padding: '1rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              borderColor: borderColors[toast.type],
              pointerEvents: 'auto',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
              animation: 'toast-slide-in 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
              borderRadius: '12px',
            }}
          >
            <div style={{ flexShrink: 0, marginTop: '2px' }}>
              {icons[toast.type]}
            </div>
            <div style={{ flexGrow: 1, fontSize: '0.85rem', color: 'hsl(var(--text-primary))', lineHeight: 1.4 }}>
              {toast.message}
            </div>
            <button 
              onClick={() => dismissToast(toast.id)}
              style={{
                background: 'transparent',
                border: 'none',
                padding: '2px',
                cursor: 'pointer',
                color: 'hsl(var(--text-dim))',
                flexShrink: 0,
                boxShadow: 'none',
                transform: 'none'
              }}
              onMouseOver={(e) => (e.currentTarget.style.color = 'hsl(var(--text-primary))')}
              onMouseOut={(e) => (e.currentTarget.style.color = 'hsl(var(--text-dim))')}
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
      
      <style>{`
        @keyframes toast-slide-in {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
