import React from 'react';

interface BadgeProps {
  status: 'ACTIVE' | 'COMPLETED' | 'PENDING' | 'PROCESSING' | 'FAILED' | string;
  style?: React.CSSProperties;
}

export function Badge({ status, style }: BadgeProps) {
  const normalized = status.toUpperCase();
  
  let type = 'neutral';
  if (normalized === 'ACTIVE' || normalized === 'COMPLETED') type = 'active';
  if (normalized === 'PENDING' || normalized === 'PROCESSING') type = 'pending';
  if (normalized === 'FAILED') type = 'failed';

  return (
    <span 
      className={`badge badge-${type}`} 
      style={{ ...style }}
    >
      {status}
    </span>
  );
}
