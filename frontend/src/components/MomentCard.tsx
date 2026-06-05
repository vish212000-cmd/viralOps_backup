import React from 'react';
import { Moment } from '../types';
import { Card } from './design/Card';
import { Button } from './design/Button';
import { Play, Sparkles, Star, ChevronRight } from 'lucide-react';

interface MomentCardProps {
  moment: Moment;
  isActive: boolean;
  onClick: () => void;
  onToggleFavorite: (id: number) => void;
}

export function MomentCard({ moment, isActive, onClick, onToggleFavorite }: MomentCardProps) {
  const formatTime = (timeStr: string) => {
    // Basic formatting assuming MM:SS or HH:MM:SS string
    return timeStr || '00:00';
  };

  const scoreColor = moment.score >= 85 ? 'hsl(var(--success))' : 
                     moment.score >= 70 ? 'hsl(var(--warning))' : 'hsl(var(--text-muted))';

  return (
    <Card 
      onClick={onClick}
      style={{ 
        padding: '1.25rem',
        cursor: 'pointer',
        border: isActive ? '2px solid hsl(var(--accent-primary))' : '1px solid hsl(var(--border-muted))',
        background: isActive ? 'hsl(var(--bg-main) / 0.8)' : 'hsl(var(--card))',
        transition: 'all 0.2s ease',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        boxShadow: isActive ? '0 0 0 2px hsl(var(--accent-primary) / 0.2)' : 'none'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ 
            fontSize: '0.75rem', 
            fontWeight: 800, 
            padding: '0.2rem 0.5rem', 
            borderRadius: '4px',
            background: 'hsl(var(--accent-primary) / 0.15)',
            color: 'hsl(var(--accent-primary))'
          }}>
            {moment.category}
          </div>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.25rem', 
            fontSize: '0.75rem', 
            fontWeight: 700, 
            color: scoreColor 
          }}>
            <Sparkles size={12} /> {moment.score} Viral Score
          </div>
        </div>
        
        <button 
          onClick={(e) => { e.stopPropagation(); onToggleFavorite(moment.id); }}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
        >
          <Star size={16} fill={moment.is_favorite ? 'hsl(var(--warning))' : 'none'} color={moment.is_favorite ? 'hsl(var(--warning))' : 'hsl(var(--text-muted))'} />
        </button>
      </div>

      <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'hsl(var(--text-primary))', lineHeight: 1.4, margin: 0 }}>
        {moment.title}
      </h4>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'hsl(var(--text-dim))' }}>
        <Play size={12} /> {formatTime(moment.start_time)} - {formatTime(moment.end_time)}
      </div>

      <p style={{ 
        fontSize: '0.85rem', 
        color: 'hsl(var(--text-muted))', 
        lineHeight: 1.5,
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
        margin: 0
      }}>
        "{moment.excerpt}"
      </p>

      {isActive && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'hsl(var(--accent-primary))', display: 'flex', alignItems: 'center' }}>
            View Details <ChevronRight size={14} />
          </span>
        </div>
      )}
    </Card>
  );
}
