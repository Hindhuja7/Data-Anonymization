'use client';

import { useMemo } from 'react';
import { Check } from 'lucide-react';
import { motion } from 'framer-motion';
import { PipelineStep } from '@/types';
// import { getStepMeta } from '@/lib/pipelineSteps'; // TODO: Create pipelineSteps utility

// Temporary stub for getStepMeta
const getStepMeta = (stepId: number) => ({
  icon: Check,
  title: `Step ${stepId}`,
  name: `Step ${stepId}`,
  description: `Step ${stepId} description`,
  details: [],
  howItWorks: []
});

interface PipelineFlowProps {
  steps: PipelineStep[];
  currentStep: number;
  onStepClick?: (stepId: number) => void;
  selectedStep?: number;
}

// Coordinates function matching the exact S-Curve alternating path layout
const getCoordinates = (id: number) => {
  // Alternate horizontal position: Left (85px) and Right (285px)
  let x = 85;
  if (id === 2 || id === 4 || id === 6 || id === 8 || id === 10 || id === 13 || id === 15 || id === 17) {
    x = 285;
  }
  // Y coordinate spreads vertically with generous spacing (85px per step)
  const y = (id - 1) * 85 + 45;
  return { x, y };
};

export default function PipelineFlow({
  steps,
  currentStep,
  onStepClick,
  selectedStep,
}: PipelineFlowProps) {
  const activeStep = selectedStep ?? currentStep;

  // Generate winding SVG connector path linking step circles
  const connectorPath = useMemo(() => {
    let path = "";
    for (let id = 1; id <= 17; id++) {
      const { x, y } = getCoordinates(id);
      if (id === 1) {
        path += `M ${x} ${y}`;
      } else {
        const prev = getCoordinates(id - 1);
        const cy = (prev.y + y) / 2;
        path += ` C ${prev.x} ${cy}, ${x} ${cy}, ${x} ${y}`;
      }
    }
    return path;
  }, []);

  const totalHeight = 17 * 85 + 20;

  return (
    <div className="relative w-full h-full overflow-y-auto overflow-x-hidden p-6 bg-[#040816]/40 backdrop-blur-sm">
      
      {/* SVG Connecting pipeline line in the background */}
      <svg
        className="absolute top-0 left-0 pointer-events-none z-1"
        width="100%"
        height={totalHeight}
      >
        <path
          d={connectorPath}
          fill="none"
          stroke="rgba(255, 255, 255, 0.05)"
          strokeWidth={3}
          strokeDasharray="4 4"
        />
        {/* Animated glowing progress line segment */}
        <path
          d={connectorPath}
          fill="none"
          stroke="rgba(79, 124, 255, 0.15)"
          strokeWidth={3}
          strokeDasharray="4 4"
          className="flow-line"
        />
      </svg>

      <div className="relative w-full" style={{ height: totalHeight }}>
        {steps.map((step) => {
          const { x, y } = getCoordinates(step.id);
          const meta = getStepMeta(step.id);
          const Icon = meta.icon;
          
          const isCompleted = step.id < currentStep;
          const isActive = step.id === activeStep;
          const isPending = step.id > currentStep;
          const isLeft = x === 85;

          return (
            <motion.div
              key={step.id}
              className={`absolute -translate-x-1/2 -translate-y-1/2 z-10 cursor-pointer ${
                isLeft ? 'left-[22%]' : 'left-[74%]'
              } ${isActive ? 'opacity-100 scale-102' : isCompleted ? 'opacity-80' : 'opacity-35'}`}
              style={{ top: `${y}px` }}
              onClick={() => onStepClick?.(step.id)}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className={`flex items-center gap-3.5 ${isLeft ? 'flex-row' : 'flex-row-reverse'}`}>
                
                {/* Circle step badge */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border transition-all flex-shrink-0 ${
                  isActive 
                    ? 'border-blue-500 bg-blue-50 text-blue-600 shadow-[0_0_15px_rgba(59,130,246,0.4)] animate-pulse' 
                    : isCompleted 
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-600' 
                      : 'border-slate-200 bg-white text-slate-500'
                }`}>
                  {step.id}
                </div>

                {/* Step Card */}
                <div className={`w-[210px] bg-white border rounded-xl px-3.5 py-2.5 flex items-center justify-between transition-all ${
                  isActive 
                    ? 'border-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.25)]' 
                    : 'border-slate-200 hover:border-slate-300'
                }`}>
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Icon size={14} className={isActive ? 'text-blue-600' : isCompleted ? 'text-emerald-600' : 'text-slate-400'} />
                    <span className={`text-[11px] font-semibold truncate ${isActive ? 'text-slate-900 font-bold' : 'text-slate-600'}`}>
                      {meta.name}
                    </span>
                  </div>
                  {isCompleted && (
                    <span className="w-4 h-4 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center text-[9px] font-bold flex-shrink-0">✓</span>
                  )}
                </div>

              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
