'use client';

import { CheckCircle2, Loader2, Circle, Clock } from 'lucide-react';
import { PipelineState } from '@/types';
import { formatElapsed } from './StepDetailPanel';

interface PipelineFooterProps {
  state: PipelineState | null;
}

export default function PipelineFooter({ state }: PipelineFooterProps) {
  const completed = (state as any)?.completedSteps ?? state?.steps.filter((s: any) => s.status === 'completed').length ?? 0;
  const total = state?.totalSteps ?? 17;
  const currentStep = state?.currentStep ?? 0;
  const pending = Math.max(0, total - completed - (state?.status === 'running' ? 1 : 0));
  const elapsed = state?.elapsedSeconds ?? 0;

  return (
    <footer className="flex items-center gap-8 px-6 py-3.5 border-t border-slate-200 bg-white flex-shrink-0">
      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mr-2">
        Pipeline Summary
      </span>

      <div className="flex items-center gap-2">
        <CheckCircle2 size={14} className="text-emerald-600" />
        <span className="text-xs text-slate-500">Completed:</span>
        <strong className="text-xs text-slate-900 font-bold">
          {completed} / {total}
        </strong>
      </div>

      <div className="w-px h-4 bg-slate-200" />

      <div className="flex items-center gap-2">
        {state?.status === 'running' ? (
          <Loader2 size={14} className="text-blue-600 animate-spin" />
        ) : (
          <Circle size={14} className="text-blue-600" />
        )}
        <span className="text-xs text-slate-500">In Progress:</span>
        <strong className="text-xs text-blue-600 font-bold">
          {state?.status === 'running' || state?.status === 'completed'
            ? `Step ${currentStep} of ${total}`
            : '—'}
        </strong>
      </div>

      <div className="w-px h-4 bg-slate-200" />

      <div className="flex items-center gap-2">
        <Circle size={14} className="text-slate-400" />
        <span className="text-xs text-slate-500">Pending:</span>
        <strong className="text-xs text-slate-900 font-bold">
          {pending} Steps Remaining
        </strong>
      </div>

      <div className="flex-1" />

      <div className="flex items-center gap-2">
        <Clock size={14} className="text-slate-400" />
        <span className="text-xs text-slate-500">Total Elapsed Time:</span>
        <strong className="text-xs text-slate-900 font-bold font-mono">
          {formatElapsed(elapsed)}
        </strong>
      </div>
    </footer>
  );
}
