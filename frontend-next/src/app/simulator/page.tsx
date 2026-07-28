"use client";

import React, { useState, useEffect } from 'react';
import { LiveTrafficSimulator } from '@/components/pipeline/LiveTrafficSimulator';
import { Activity, ShieldCheck, Database, RefreshCw, Zap } from 'lucide-react';

export default function SimulatorPage() {
  const [pollingStatus, setPollingStatus] = useState<string>('inactive');

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/pipeline/status');
        if (res.ok) {
          const contentType = res.headers.get('content-type') || '';
          if (contentType.includes('application/json')) {
            const data = await res.json();
            const state = data.state || {};
            setPollingStatus(state.polling_status || 'inactive');
          }
        }
      } catch (err) {
        console.warn('Could not fetch pipeline status for simulator page:', err);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const isListenerActive = pollingStatus === 'active';

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-blue-600/20 text-blue-400 rounded-xl border border-blue-500/30">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">Live Traffic Simulator</h1>
              <p className="text-xs text-slate-400">
                Continuous Data Change Detection & Real-Time Anonymization Test Suite
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isListenerActive ? (
            <span className="text-xs px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5 font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              Live Sync Listener Active
            </span>
          ) : (
            <span className="text-xs px-3 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1.5 font-mono">
              <span className="w-2 h-2 rounded-full bg-slate-500"></span>
              {pollingStatus === 'waiting' ? 'Waiting for Pipeline Completion' : 'Live Sync Listener Inactive'}
            </span>
          )}
        </div>
      </div>

      {/* Live Traffic Simulator UI - Uses Authoritative Config */}
      <LiveTrafficSimulator />

      {/* How It Works Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-cyan-400" />
          How Continuous Sync Works in Real Enterprises
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs text-slate-300">
          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
            <div className="font-semibold text-cyan-300 flex items-center gap-1.5">
              <Database className="w-4 h-4 text-cyan-400" /> 1. Source DB Change (CRUD)
            </div>
            <p className="text-slate-400 leading-relaxed">
              Applications insert new records, update existing entries, or remove records in the production database table.
            </p>
          </div>
          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
            <div className="font-semibold text-amber-300 flex items-center gap-1.5">
              <RefreshCw className="w-4 h-4 text-amber-400" /> 2. 30s Change Detection
            </div>
            <p className="text-slate-400 leading-relaxed">
              DataVault AI Polling Worker detects incremental row modifications without locking tables or degrading production performance.
            </p>
          </div>
          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
            <div className="font-semibold text-emerald-300 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" /> 3. Policy Anonymization
            </div>
            <p className="text-slate-400 leading-relaxed">
              PII fields are transformed using your Step 7 Approved Policy rules (Tokenization, Masking, Hashing) and synced safely to the destination DB.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
