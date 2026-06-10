import React, { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  style?: React.CSSProperties;
  className?: string;
  glow?: boolean;
  onClick?: React.MouseEventHandler<HTMLDivElement>;
}

export function Card({ children, style, className = '', glow = false, onClick }: CardProps) {
  const classNames = `glass-panel ${glow ? 'gradient-glow' : ''} ${className}`.trim();

  return (
    <div className={classNames} style={{ ...style }} onClick={onClick}>
      {children}
    </div>
  );
}
