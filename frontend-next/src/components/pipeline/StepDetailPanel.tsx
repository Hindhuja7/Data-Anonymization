'use client';

import { useEffect, useState, useMemo } from 'react';
import { TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';
import { PipelineState } from '@/types';
import { getStepMeta } from '@/lib/pipelineSteps';
import StepIllustration from './StepIllustration';
import LiveActivityChart from './LiveActivityChart';

interface StepDetailPanelProps {
  state: PipelineState | null;
  selectedStep: number;
  onOpenApproval?: () => void;
}

function formatElapsed(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function formatNumber(n: number): string {
  return n.toLocaleString();
}

export default function StepDetailPanel({ state, selectedStep }: StepDetailPanelProps) {
  const stepId = selectedStep || state?.currentStep || 1;
  const meta = getStepMeta(stepId);
  const step = state?.steps.find((s: any) => s.id === stepId);
  const isActive = stepId === state?.currentStep;

  const [pollCountdown, setPollCountdown] = useState(30);

  useEffect(() => {
    if (!isActive || state?.status !== 'running') return;
    setPollCountdown(30);
    const interval = setInterval(() => {
      setPollCountdown((prev) => (prev <= 1 ? 30 : prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [isActive, state?.status, stepId]);

  const progress = useMemo(() => {
    if (isActive && state?.progress) return state.progress;
    if (step?.status === 'completed') return 100;
    return 0;
  }, [isActive, state?.progress, step?.status]);

  const metrics = useMemo(() => {
    const batches = state?.batchesLoaded ?? 0;
    const records = state?.recordsProcessed ?? 0;
    const batchSize = state?.batchSize ?? 1000;

    return [
      { label: 'Batches Loaded', value: formatNumber(batches), trend: '+16%', trendUp: true },
      { label: 'Records Processed', value: formatNumber(records), trend: '+12%', trendUp: true },
      { label: 'Last Batch Size', value: `${formatNumber(batchSize)} Rows`, trend: null, trendUp: false },
      {
        label: 'Next Poll In',
        value: `00:00:${String(pollCountdown).padStart(2, '0')}`,
        trend: null,
        trendUp: false,
        isTimer: true,
      },
    ];
  }, [state, pollCountdown]);

  return (
    <div className="glass-card rounded-2xl p-6 h-full flex flex-col overflow-hidden glow-blue">
      {/* Header row with illustration */}
      <div className="flex gap-6 mb-5 flex-shrink-0">
        <div className="flex-1">
          <div className="text-[10px] font-bold text-[#4F7CFF] uppercase tracking-wider mb-2">
            STEP {stepId} OF 17
          </div>
          <h2 className="text-xl font-extrabold tracking-tight text-white mb-2 leading-snug">
            {meta.name}
          </h2>
          <p className="text-sm text-[#8C96B5] leading-relaxed">{meta.description}</p>
        </div>
        <div className="flex-shrink-0 w-[180px] h-[120px]">
          <StepIllustration stepId={stepId} />
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-4 flex-shrink-0">
        <div className="flex justify-between text-xs font-bold mb-2">
          <span className="text-[#8C96B5] uppercase tracking-wider">Progress</span>
          <strong className="text-[#4F7CFF]">{progress}%</strong>
        </div>
        <div className="h-2.5 bg-white/6 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-[#4F7CFF] to-[#38bdf8] rounded-full shadow-[0_0_12px_rgba(79,124,255,0.5)]"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-4 gap-3 mb-4 flex-shrink-0">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="bg-[#050816]/50 border border-white/6 rounded-xl p-3 hover-lift"
          >
            <div className="text-[9px] text-[#8C96B5] uppercase tracking-wider mb-1 font-semibold">
              {metric.label}
            </div>
            <div className={`text-base font-extrabold ${metric.isTimer ? 'text-[#4F7CFF] font-mono' : 'text-white'}`}>
              {metric.value}
            </div>
            {metric.trend && (
              <div className="flex items-center gap-1 mt-1">
                <TrendingUp size={10} className="text-[#33D17A]" />
                <span className="text-[10px] text-[#33D17A] font-semibold">{metric.trend}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Details layout */}
      <div className="grid grid-cols-3 gap-4 flex-grow min-h-0">
        {/* Step Details */}
        <div className="bg-[#050816]/40 border border-white/6 rounded-xl p-4 overflow-y-auto custom-scrollbar">
          <h3 className="text-[10px] font-bold text-[#8C96B5] uppercase tracking-wider mb-3">
            Step Details
          </h3>
          <div className="space-y-2.5">
            {meta.details.map((detail) => {
              const Icon = detail.icon;
              return (
                <div key={detail.label} className="flex items-center gap-2.5">
                  <div className="w-6 h-6 rounded-md bg-[#4F7CFF]/10 flex items-center justify-center flex-shrink-0">
                    <Icon size={12} className="text-[#4F7CFF]" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-[9px] text-[#8C96B5]">{detail.label}</div>
                    <div className="text-[11px] font-semibold text-white truncate">{detail.value}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* How It Works */}
        <div className="bg-[#050816]/40 border border-white/6 rounded-xl p-4 overflow-y-auto custom-scrollbar">
          <h3 className="text-[10px] font-bold text-[#8C96B5] uppercase tracking-wider mb-3">
            How It Works
          </h3>
          <div className="relative">
            <div className="absolute left-[11px] top-2 bottom-2 w-px border-l border-dashed border-white/10" />
            <div className="space-y-3">
              {meta.howItWorks.map((item, index) => {
                const Icon = item.icon;
                return (
                  <div key={index} className="flex items-center gap-2.5 relative">
                    <div className="w-6 h-6 rounded-full bg-[#0D1324] border border-white/10 flex items-center justify-center flex-shrink-0 z-10">
                      <Icon size={11} className="text-[#8C96B5]" />
                    </div>
                    <span className="text-[11px] text-[#8C96B5] leading-tight">{item.label}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Live Activity */}
        <div className="bg-[#050816]/40 border border-white/6 rounded-xl p-4 flex flex-col overflow-hidden">
          <h3 className="text-[10px] font-bold text-[#8C96B5] uppercase tracking-wider mb-3 flex-shrink-0">
            Live Activity
          </h3>
          <div className="flex-grow min-h-[80px]">
            <LiveActivityChart isActive={isActive && state?.status === 'running'} />
          </div>
          <p className="text-[10px] text-[#4F7CFF]/70 mt-2 flex-shrink-0">
            {isActive && state?.status === 'running'
              ? 'Polling every 30 seconds...'
              : step?.status === 'completed'
              ? 'Step completed'
              : 'Waiting to start...'}
          </p>
        </div>
      </div>
    </div>
  );
}

export { formatElapsed };
