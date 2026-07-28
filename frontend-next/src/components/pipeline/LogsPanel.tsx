'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { PipelineLog } from '@/types';

interface LogsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  logs: PipelineLog[];
}

export default function LogsPanel({ isOpen, onClose, logs }: LogsPanelProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-[480px] bg-[#0D1324]/95 backdrop-blur-xl border-l border-white/6 z-50 flex flex-col shadow-2xl"
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/6">
              <div>
                <h3 className="text-sm font-bold text-white">Pipeline Logs</h3>
                <p className="text-[10px] text-[#8C96B5]">{logs.length} entries</p>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-white/5 text-[#8C96B5] hover:text-white transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-1">
              {logs.length === 0 ? (
                <div className="text-center text-[#8C96B5] py-12">
                  No logs yet. Start the pipeline to see real-time logs.
                </div>
              ) : (
                logs.map((log) => (
                  <div
                    key={log.id}
                    className={`flex items-start gap-2 py-0.5 ${
                      log.level === 'error'
                        ? 'text-red-400'
                        : log.level === 'warning'
                        ? 'text-amber-400'
                        : log.level === 'success'
                        ? 'text-emerald-400'
                        : 'text-slate-300'
                    }`}
                  >
                    <span className="text-[#8C96B5] flex-shrink-0">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="text-[#4F7CFF] flex-shrink-0">[Step {log.step}]</span>
                    <span className="break-all">{log.message}</span>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
