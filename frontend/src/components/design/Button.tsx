import React, { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
  icon?: ReactNode;
}

export function Button({ 
  children, 
  variant = 'primary', 
  loading = false, 
  icon, 
  disabled, 
  style,
  ...props 
}: ButtonProps) {
  const classNames = `button ${variant !== 'primary' ? variant : ''}`;

  return (
    <button 
      disabled={disabled || loading} 
      className={classNames}
      style={{ ...style }}
      {...props}
    >
      {loading ? (
        <span className="loading-spinner" style={{ width: '14px', height: '14px', borderTopColor: '#fff' }} />
      ) : (
        icon
      )}
      {children}
    </button>
  );
}
