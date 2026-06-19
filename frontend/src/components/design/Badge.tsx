import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

interface BadgeProps {
  status: 'ACTIVE' | 'COMPLETED' | 'PENDING' | 'PROCESSING' | 'FAILED' | string;
  className?: string;
}

export function Badge({ status, className }: BadgeProps) {
  const normalized = status.toUpperCase();
  
  const variants: Record<string, string> = {
    active: 'bg-success/15 text-success border-success/30',
    pending: 'bg-warning/15 text-warning border-warning/30',
    failed: 'bg-danger/15 text-danger border-danger/30',
    neutral: 'bg-white/10 text-text-muted border-white/10'
  };

  let type = 'neutral';
  if (normalized === 'ACTIVE' || normalized === 'COMPLETED') type = 'active';
  if (normalized === 'PENDING' || normalized === 'PROCESSING') type = 'pending';
  if (normalized === 'FAILED') type = 'failed';

  return (
    <motion.span 
      layout
      className={cn(
        "inline-flex items-center px-2.5 py-1 text-[0.70rem] font-bold font-mono uppercase tracking-wider rounded-full border shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]", 
        variants[type],
        className
      )}
    >
      {/* If active, show a small pulsing dot */}
      {(type === 'active' || type === 'pending') && (
        <span className={cn(
          "w-1.5 h-1.5 rounded-full mr-1.5 animate-pulse",
          type === 'active' ? "bg-success" : "bg-warning"
        )} />
      )}
      {status}
    </motion.span>
  );
}
