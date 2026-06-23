import React, { InputHTMLAttributes, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils/cn';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  containerClassName?: string;
}

export function Input({ label, error, containerClassName, id, className, required, ...props }: InputProps) {
  const inputId = id || `input-${Math.random().toString(36).substring(2, 9)}`;
  const [focused, setFocused] = useState(false);

  return (
    <div className={cn("flex flex-col gap-2 relative", containerClassName)}>
      <label 
        htmlFor={inputId} 
        className={cn(
          "text-sm font-semibold transition-colors",
          focused ? "text-accent-cyan" : "text-text-muted"
        )}
      >
        {label} {required && <span className="text-accent-primary">*</span>}
      </label>
      <div className="relative">
        <input 
          id={inputId} 
            className={cn(
              "w-full bg-white/[0.02] border border-white/[0.08] rounded-[6px] text-white px-4 py-3 font-sans outline-none transition-all duration-300 placeholder:text-text-dim",
              "focus:bg-white/[0.04] focus:border-accent-primary focus-visible:ring-1 focus-visible:ring-accent-primary",
              error && "border-danger focus:border-danger focus-visible:ring-danger bg-danger/5",
              className
            )}
          onFocus={(e) => {
            setFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setFocused(false);
            props.onBlur?.(e);
          }}
          required={required}
          {...props} 
        />
        
        {/* Removed expensive blur effect */}
      </div>
      <AnimatePresence>
        {error && (
          <motion.span 
            initial={{ opacity: 0, height: 0, y: -10 }}
            animate={{ opacity: 1, height: 'auto', y: 0 }}
            exit={{ opacity: 0, height: 0, y: -10 }}
            className="text-xs text-danger mt-1 font-medium"
          >
            {error}
          </motion.span>
        )}
      </AnimatePresence>
    </div>
  );
}
