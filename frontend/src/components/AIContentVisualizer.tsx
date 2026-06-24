import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Circle, Loader2, Sparkles, FileText, Database, Wand2, PlayCircle } from 'lucide-react';
import { cn } from '../utils/cn';

interface ContentStage {
  id: string;
  label: string;
  icon: React.ElementType;
}

const STAGES: ContentStage[] = [
  { id: 'received', label: 'Source Received', icon: Database },
  { id: 'transcribing', label: 'Transcribing', icon: FileText },
  { id: 'cleaning', label: 'Cleaning Data', icon: Sparkles },
  { id: 'extracting', label: 'Extracting Hooks', icon: Wand2 },
  { id: 'scripts', label: 'Building Scripts', icon: FileText },
  { id: 'generating', label: 'Generating Assets', icon: PlayCircle },
  { id: 'ready', label: 'Ready', icon: CheckCircle2 }
];

export function AIContentVisualizer({ currentStageId = 'transcribing' }: { currentStageId?: string }) {
  const currentIndex = STAGES.findIndex(s => s.id === currentStageId);
  const activeIndex = currentIndex === -1 ? 0 : currentIndex;

  return (
    <div className="w-full relative py-12 px-6 flex flex-col items-center justify-center overflow-hidden">
      {/* Background Neural Net simulation - Removed expensive particles */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
        <div className="absolute top-1/2 left-0 w-full h-px bg-gradient-to-r from-transparent via-accent-cyan to-transparent shadow-[0_0_15px_rgba(34,211,238,0.8)]" />
      </div>

      <div className="relative z-10 w-full max-w-4xl flex justify-between items-center">
        {STAGES.map((stage, idx) => {
          const isCompleted = idx < activeIndex;
          const isActive = idx === activeIndex;
          const isPending = idx > activeIndex;
          const Icon = stage.icon;

          return (
            <div key={stage.id} className="relative flex flex-col items-center gap-4 flex-1">
              {/* Connecting Line (except first) */}
              {idx > 0 && (
                <div className="absolute top-6 left-[-50%] w-full h-[2px] -z-10">
                  <div className="w-full h-full bg-white/10" />
                  <motion.div 
                    initial={{ width: '0%' }}
                    animate={{ width: isCompleted || isActive ? '100%' : '0%' }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-accent-primary to-accent-cyan shadow-[0_0_10px_rgba(34,211,238,0.5)]"
                  />
                </div>
              )}

              {/* Stage Element */}
              <motion.div 
                layout
                initial={{ scale: 0.8, opacity: 0.5 }}
                animate={{ 
                  scale: isActive ? 1.2 : 1, 
                  opacity: isPending ? 0.4 : 1,
                }}
                transition={{ type: "spring", stiffness: 200, damping: 20 }}
                className={cn(
                  "relative w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-500 z-10",
                  isActive ? "bg-accent-primary shadow-[0_0_30px_rgba(139,92,246,0.6)] border border-white/20" : 
                  isCompleted ? "bg-bg-elevated border border-accent-cyan shadow-[0_0_15px_rgba(34,211,238,0.3)]" : 
                  "bg-white/5 border border-white/10"
                )}
              >
                {isActive && (
                  <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                    className="absolute -inset-[2px] rounded-2xl border border-dashed border-accent-cyan/50"
                  />
                )}
                
                {isCompleted ? (
                  <CheckCircle2 size={20} className="text-accent-cyan" />
                ) : isActive ? (
                  <Icon size={20} className="text-white animate-pulse" />
                ) : (
                  <Icon size={18} className="text-text-muted" />
                )}
              </motion.div>

              {/* Label */}
              <div className="absolute top-16 whitespace-nowrap text-center">
                <span className={cn(
                  "text-xs font-mono tracking-wider transition-colors duration-300",
                  isActive ? "text-accent-cyan font-bold" : 
                  isCompleted ? "text-text-primary" : 
                  "text-text-dim"
                )}>
                  {stage.label}
                </span>
                
                {isActive && (
                  <motion.div
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-1 flex items-center justify-center gap-1.5"
                  >
                    <Loader2 size={10} className="animate-spin text-accent-primary" />
                    <span className="text-[10px] text-accent-primary uppercase font-bold tracking-widest">Processing</span>
                  </motion.div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
