import React, { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  style?: React.CSSProperties;
  className?: string;
  glow?: boolean;
}

export function Card({ children, style, className = '', glow = false }: CardProps) {
  const classNames = `glass-panel ${glow ? 'gradient-glow' : ''} ${className}`.trim();

  return (
    <div className={classNames} style={{ ...style }}>
      {children}
    </div>
  );
}
