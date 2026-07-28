'use client';

import { List, Pause, Play } from 'lucide-react';
import Button from '@/components/ui/Button';

interface PipelineHeaderProps {
  isRunning: boolean;
  isPaused: boolean;
  onViewLogs: () => void;
  onPause: () => void;
  onStart: () => void;
  isStarting: boolean;
}

export default function PipelineHeader({
  isRunning,
  isPaused,
  onViewLogs,
  onPause,
  onStart,
  isStarting,
}: PipelineHeaderProps) {
  return (
    <header className="flex items-center justify-between px-6 py-5 border-b border-white/6 flex-shrink-0">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-white">
          Data Anonymization Pipeline
        </h1>
        <p className="text-sm text-[#8C96B5] mt-1">
          17 Steps &bull; Real-time Anonymization Workflow
        </p>
      </div>

      <div className="flex items-center gap-3">
        {!isRunning && !isPaused && (
          <button
            onClick={onStart}
            disabled={isStarting}
            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <Play size={14} />
            Start Pipeline
          </button>
        )}
        <button
          onClick={onViewLogs}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors border border-slate-700"
        >
          <List size={14} />
          View Logs
        </button>
        {isRunning && (
          <button
            onClick={onPause}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors border border-slate-700"
          >
            <Pause size={14} />
            Pause Pipeline
          </button>
        )}
      </div>
    </header>
  );
}
