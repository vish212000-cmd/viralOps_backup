import React, { ReactNode } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '../../utils/cn';

interface CardProps extends HTMLMotionProps<"div"> {
  children: ReactNode;
  glow?: boolean;
}

export function Card({ children, className, glow = false, ...props }: CardProps) {
  return (
    <motion.div
      layout
      className={cn(
        "relative rounded-xl bg-bg-surface border border-white/[0.08] shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] shadow-2xl overflow-hidden",
        glow && "aurora-glow",
        className
      )}
      {...props}
    >
      {/* Optional ambient inner gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none" />
      <div className="relative z-10">
        {children}
      </div>
    </motion.div>
  );
}
