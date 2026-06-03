import React, { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  containerStyle?: React.CSSProperties;
}

export function Input({ label, error, containerStyle, id, style, ...props }: InputProps) {
  const inputId = id || `input-${Math.random().toString(36).substring(2, 9)}`;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', ...containerStyle }}>
      <label htmlFor={inputId} style={{ fontSize: '0.85rem', fontWeight: 600, color: 'hsl(var(--text-muted))' }}>
        {label}
      </label>
      <input 
        id={inputId} 
        style={{ 
          borderColor: error ? 'hsl(var(--danger))' : undefined,
          ...style 
        }} 
        {...props} 
      />
      {error && (
        <span style={{ fontSize: '0.75rem', color: 'hsl(var(--danger))', marginTop: '0.1rem' }}>
          {error}
        </span>
      )}
    </div>
  );
}
