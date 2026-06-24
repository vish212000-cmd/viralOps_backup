'use client';
import React, { ButtonHTMLAttributes, ReactNode, MouseEvent } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { cn } from '../../utils/cn';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  loading?: boolean;
  icon?: ReactNode;
}

export function Button({ 
  children, 
  variant = 'primary', 
  loading = false, 
  icon, 
  disabled, 
  className,
  ...props 
}: ButtonProps) {
  // Magnetic hover physics
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  
  const mouseXSpring = useSpring(x, { stiffness: 150, damping: 15, mass: 0.1 });
  const mouseYSpring = useSpring(y, { stiffness: 150, damping: 15, mass: 0.1 });

  const handleMouseMove = (e: MouseEvent<HTMLButtonElement>) => {
    if (disabled || loading) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Max magnetic pull distance is 20% of width/height
    x.set((mouseX - width / 2) * 0.2);
    y.set((mouseY - height / 2) * 0.2);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  const baseStyles = "relative inline-flex items-center justify-center gap-2 px-6 py-2.5 font-sans text-sm font-medium transition-colors outline-none disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden rounded-[6px]";
  
  const variants = {
    primary: "bg-accent-primary text-white hover:bg-accent-primary/90 shadow-[inset_0_1px_0_rgba(255,255,255,0.2)]",
    secondary: "bg-white/5 text-white hover:bg-white/10 border border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]",
    danger: "bg-danger text-white hover:bg-danger/90",
    ghost: "bg-transparent text-text-muted hover:text-white hover:bg-white/5"
  };

  return (
    <motion.button 
      style={{ x: mouseXSpring, y: mouseYSpring }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      whileTap={{ scale: 0.98, y: 1 }}
      disabled={disabled || loading} 
      className={cn(baseStyles, variants[variant], className)}
      {...props}
    >
      {loading ? (
        <span className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin" />
      ) : (
        icon
      )}
      <span className="relative z-10">{children}</span>
      
      {/* Glossy top highlight for primary button */}
      {variant === 'primary' && !disabled && (
        <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-white/40 to-transparent opacity-50" />
      )}
    </motion.button>
  );
}
