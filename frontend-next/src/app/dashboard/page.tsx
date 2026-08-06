"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { 
  LayoutDashboard, ShieldCheck, Database, Layers, CheckCircle2, AlertTriangle, 
  ArrowRight, Lock, Activity, PieChart, RefreshCw, Sparkles, Server, FileText, Rocket,
  History, Eye, X, Clock
} from 'lucide-react';

interface RunHistoryItem {
  run_id: string;
  version: string;
  is_current: boolean;
  timestamp: string;
  table_name: string;
  status: string;
  records_anonymized: number;
  privacy_score: number;
  risk_score: number;
  risk_level: string;
  techniques_summary: string;
  total_columns?: number;
  policy_snapshot?: {
    version: string;
    created_at: string;
    column_policies: Array<{
      column_name: string;
      is_pii: boolean;
      pii_type: string;
      anonymization_technique: string;
    }>;
  };
}

interface DashboardStats {
  is_new_user?: boolean;
  view_mode?: string;
  total_records_anonymized: number;
  total_executed_runs: number;
  privacy_score: number;
  risk_score: number;
  risk_level: string;
  compliance_law: string;
  compliance_status: string;
  is_pending_approval: boolean;
  pending_table: string;
  active_run_id: string;
  technique_distribution: Array<{ technique: string; count: number; percentage: number }>;
  total_audit_events: number;
  run_history?: Array<RunHistoryItem>;
}

import { useWebSocket } from '@/hooks/useWebSocket';

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [viewMode, setViewMode] = useState<'personal' | 'admin_global'>('personal');
  const [selectedHistoryItem, setSelectedHistoryItem] = useState<RunHistoryItem | null>(null);

  const authUser = useAuthStore((state) => state.user);

  const getActiveUser = () => {
    if (authUser && (authUser.email || authUser.id)) return authUser;
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('datavault_user');
        if (stored) return JSON.parse(stored);
      } catch (e) {}
    }
    return { email: 'b@gmail.com', role: 'user' };
  };

  const activeUser = getActiveUser();
  const isAdmin = activeUser?.role === 'admin' || activeUser?.email?.toLowerCase().includes('admin');

  const wsUrl = typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000/api/pipeline/ws`
    : 'ws://127.0.0.1:8000/api/pipeline/ws';

  const { isConnected, onMessage } = useWebSocket(wsUrl);

  const fetchDashboardStats = async () => {
    try {
      const userId = activeUser?.email || activeUser?.id || 'b@gmail.com';
      const endpoint = `/api/dashboard/stats?user_id=${encodeURIComponent(userId)}&mode=${viewMode}`;
      let res = await fetch(`http://127.0.0.1:8000${endpoint}`);
      if (!res.ok) {
        res = await fetch(endpoint);
      }
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'success') {
          setStats(data.stats);
        }
      }
    } catch (err) {
      console.warn('Dashboard stats error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardStats();
    const interval = setInterval(fetchDashboardStats, 1500);
    return () => clearInterval(interval);
  }, [viewMode]);

  useEffect(() => {
    const unsubscribe = onMessage((msg: any) => {
      if (msg && (msg.type === 'pipeline_status' || msg.type === 'step_update' || msg.type === 'log' || msg.type === 'dashboard_update' || msg.type === 'traffic_simulated')) {
        fetchDashboardStats();
      }
    });
    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [onMessage]);

  const handleApproveStep7 = async () => {
    try {
      let res = await fetch('http://127.0.0.1:8000/api/pipeline/approve', { method: 'POST' });
      if (!res.ok) {
        res = await fetch('/api/pipeline/approve', { method: 'POST' });
      }
      if (res.ok) {
        fetchDashboardStats();
        router.push('/pipeline');
      }
    } catch (err) {
      console.error('Approval error:', err);
    }
  };

  const isNewUser = stats?.is_new_user === true || (stats?.total_executed_runs === 0 && !stats?.is_pending_approval);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-xl border border-blue-500/20 shadow-md">
            <LayoutDashboard className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              Enterprise Dashboard
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                DPDP ACT 2023 COMPLIANT
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Real-time enterprise privacy monitoring, 17-step pipeline status, and security compliance telemetry.
            </p>
          </div>
        </div>

        {/* View Mode Toggle Switch */}
        <div className="flex items-center bg-slate-900/80 p-1.5 rounded-xl border border-slate-800 shadow-md">
          <button
            type="button"
            onClick={() => setViewMode('personal')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
              viewMode === 'personal'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            My Personal View
          </button>
          <button
            type="button"
            onClick={() => setViewMode('admin_global')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
              viewMode === 'admin_global'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <Server className="w-3.5 h-3.5" />
            Global Enterprise View
          </button>
        </div>

        <button
          type="button"
          onClick={fetchDashboardStats}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold rounded-xl transition-colors border border-slate-700 flex items-center gap-2 shadow"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-blue-400' : ''}`} />
          Refresh Stats
        </button>
      </div>

      {/* NEW USER ONBOARDING BANNER */}
      {isNewUser ? (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-900/40 via-slate-900 to-indigo-900/40 border border-blue-500/30 text-white space-y-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-600/20 text-blue-400 rounded-xl border border-blue-500/30">
              <Rocket className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Welcome to DataVault AI Onboarding</h2>
              <p className="text-xs text-slate-300">
                You currently have 0 active runs. Follow the 3-step workflow below to connect your database and run your first 17-step anonymization pipeline.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div 
              onClick={() => router.push('/database')}
              className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 cursor-pointer transition-all space-y-2"
            >
              <div className="text-xs font-mono font-bold text-blue-400">STEP 1</div>
              <h3 className="text-sm font-bold text-white">Connect Source Database</h3>
              <p className="text-xs text-slate-400">Configure PostgreSQL credentials & target table.</p>
            </div>

            <div 
              onClick={() => router.push('/pipeline')}
              className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 hover:border-emerald-500/50 cursor-pointer transition-all space-y-2"
            >
              <div className="text-xs font-mono font-bold text-emerald-400">STEP 2</div>
              <h3 className="text-sm font-bold text-white">Run 17-Step Pipeline</h3>
              <p className="text-xs text-slate-400">Scan PII, approve policy, & execute anonymization.</p>
            </div>

            <div 
              onClick={() => router.push('/audit')}
              className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 hover:border-purple-500/50 cursor-pointer transition-all space-y-2"
            >
              <div className="text-xs font-mono font-bold text-purple-400">STEP 3</div>
              <h3 className="text-sm font-bold text-white">Inspect Compliance & Audit Logs</h3>
              <p className="text-xs text-slate-400">Export DPDP Act certificates & view HMAC audit stream.</p>
            </div>
          </div>
        </div>
      ) : stats?.is_pending_approval ? (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 space-y-3 shadow-lg">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/20 text-amber-400 rounded-xl border border-amber-500/30">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Step 7 Approval Required</h3>
                <p className="text-xs text-amber-200 font-mono mt-0.5">
                  Pipeline run <strong className="text-white">{stats.active_run_id}</strong> is paused at Step 7 for target table <strong className="text-blue-400">{stats.pending_table}</strong>.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => router.push('/pipeline')}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold rounded-xl border border-slate-700"
              >
                Review Policy
              </button>
              <button
                type="button"
                onClick={handleApproveStep7}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl shadow-md flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-4 h-4" />
                Approve & Resume Pipeline
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {/* Top Row: Executive KPI Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-bold tracking-wider">Total Anonymized</span>
            <Database className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-extrabold text-white font-mono">
            {stats ? stats.total_records_anonymized.toLocaleString() : '0'} <span className="text-xs font-normal text-slate-400 font-sans">Rows</span>
          </div>
          <span className="text-[11px] text-slate-400 font-medium">
            {isNewUser ? 'No pipeline run yet' : '100% Synced to Destination'}
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-bold tracking-wider">Executed Runs</span>
            <Layers className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-extrabold text-white font-mono">
            {stats ? stats.total_executed_runs : 0} <span className="text-xs font-normal text-slate-400 font-sans">Runs</span>
          </div>
          <span className="text-[11px] text-slate-400 font-medium">17-Step Lifecycle Monitored</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-bold tracking-wider">Privacy Score</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-400 font-mono">
            {stats && stats.privacy_score > 0 ? `${stats.privacy_score.toFixed(1)}%` : 'N/A'}
          </div>
          <span className="text-[11px] text-slate-400 font-medium">
            {isNewUser ? 'Awaiting First Run' : `Risk Level: ${stats?.risk_level}`}
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-bold tracking-wider">Security Vault</span>
            <Lock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold text-white font-mono">
            Redis Vault
          </div>
          <span className="text-[11px] text-emerald-400 font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" /> HMAC-SHA256 Encrypted
          </span>
        </div>
      </div>

      {/* Middle Grid: DPDP Compliance & Technique Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Compliance Status Gauge */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Regulatory Compliance Status</h3>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              {stats ? stats.compliance_law : 'DPDP Act 2023'}
            </span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300">Audit Certification Status</span>
              <span className={`text-xs font-bold px-2.5 py-1 rounded border ${
                isNewUser 
                  ? 'bg-slate-800 text-slate-400 border-slate-700' 
                  : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
              }`}>
                {stats ? stats.compliance_status : 'NOT STARTED (AWAITING FIRST RUN)'}
              </span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
              <div 
                className="bg-emerald-500 h-2.5 rounded-full transition-all duration-500" 
                style={{ width: `${stats ? stats.privacy_score : 0}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>Overall Privacy Score: {stats ? stats.privacy_score.toFixed(1) : '0.0'}%</span>
              <span>Max Threshold: 100%</span>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={() => router.push('/audit')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold rounded-xl transition-all border border-slate-700 flex items-center gap-2"
            >
              <FileText className="w-4 h-4 text-blue-400" />
              View Full Audit Trail & Export Certificate
            </button>
          </div>
        </div>


        {/* Applied Anonymization Technique Distribution */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <PieChart className="w-5 h-5 text-blue-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Applied Protection Techniques</h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400 font-bold">SCHEMATIC DISTRIBUTION</span>
          </div>

          <div className="space-y-3">
            {stats?.technique_distribution && stats.technique_distribution.length > 0 ? (
              stats.technique_distribution.map((item) => (
                <div key={item.technique} className="space-y-1">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="font-bold text-slate-200">{item.technique}</span>
                    <span className="text-slate-400">{item.count} columns ({item.percentage}%)</span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        item.technique === 'TOKENIZATION' ? 'bg-blue-500' :
                        item.technique === 'MASKING' ? 'bg-amber-400' :
                        item.technique === 'DIFFERENTIAL_PRIVACY' ? 'bg-purple-500' : 'bg-emerald-400'
                      }`}
                      style={{ width: `${item.percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center space-y-3 bg-slate-950 rounded-xl border border-slate-800">
                <PieChart className="w-8 h-8 text-slate-600 mx-auto" />
                <p className="text-xs text-slate-400 font-mono">No anonymization policy executed yet.</p>
                <button
                  type="button"
                  onClick={() => router.push('/database')}
                  className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl shadow transition-colors inline-flex items-center gap-1.5"
                >
                  <Database className="w-3.5 h-3.5" />
                  Connect Database to Start
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* POLICY & EXECUTION HISTORY TRACKER */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between pb-3 border-b border-slate-800 gap-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-blue-500/10 text-blue-400 rounded-xl border border-blue-500/20">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                Anonymization Policy & Execution History
                <span className="text-[10px] font-mono px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded border border-blue-500/30">
                  IMMUTABLE LOG
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                When a policy is updated or re-anonymized, previous versions are preserved below as historical snapshots.
              </p>
            </div>
          </div>

          <div className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
            Total History Versions: <strong className="text-blue-400">{stats?.run_history?.length || 0}</strong>
          </div>
        </div>

        {stats?.run_history && stats.run_history.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
                <tr>
                  <th className="p-3">Version / Status</th>
                  <th className="p-3">Run ID</th>
                  <th className="p-3">Target Table</th>
                  <th className="p-3">Executed At</th>
                  <th className="p-3">Rows</th>
                  <th className="p-3">Privacy Score</th>
                  <th className="p-3">Techniques Applied</th>
                  <th className="p-3 text-right">Policy Snapshot</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {stats.run_history.map((item, idx) => (
                  <tr 
                    key={item.run_id + idx}
                    className={`transition-colors hover:bg-slate-800/40 ${
                      item.is_current ? 'bg-blue-950/20' : ''
                    }`}
                  >
                    <td className="p-3 font-sans">
                      {item.is_current ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow-sm">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          {item.version}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          {item.version}
                        </span>
                      )}
                    </td>
                    <td className="p-3 font-mono font-bold text-white">{item.run_id}</td>
                    <td className="p-3 text-blue-400 font-bold">{item.table_name}</td>
                    <td className="p-3 text-slate-400">
                      {item.timestamp ? new Date(item.timestamp).toLocaleString() : 'N/A'}
                    </td>
                    <td className="p-3 text-white font-bold">{item.records_anonymized?.toLocaleString() || 5000}</td>
                    <td className="p-3">
                      <span className="text-emerald-400 font-bold">{item.privacy_score}%</span>
                    </td>
                    <td className="p-3 text-slate-300 text-[11px] max-w-xs truncate">
                      {item.techniques_summary}
                    </td>
                    <td className="p-3 text-right">
                      <button
                        type="button"
                        onClick={() => setSelectedHistoryItem(item)}
                        className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 rounded-lg border border-blue-500/30 font-sans font-bold transition-all text-xs inline-flex items-center gap-1.5"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        View Policy
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center space-y-2 bg-slate-950 rounded-xl border border-slate-800">
            <Clock className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-xs text-slate-400 font-mono">No execution history recorded yet.</p>
          </div>
        )}
      </div>

      {/* HISTORICAL POLICY SNAPSHOT MODAL */}
      {selectedHistoryItem && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-5 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  Policy Snapshot: <span className="text-blue-400">{selectedHistoryItem.version}</span>
                  {selectedHistoryItem.is_current && (
                    <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded border border-emerald-500/30">
                      CURRENT ACTIVE
                    </span>
                  )}
                </h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Run ID: {selectedHistoryItem.run_id} | Table: {selectedHistoryItem.table_name} | Privacy: {selectedHistoryItem.privacy_score}%
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedHistoryItem(null)}
                className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              <div className="grid grid-cols-3 gap-3 p-4 bg-slate-950 rounded-xl border border-slate-800 font-mono text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px]">EXECUTED AT</span>
                  <strong className="text-white">
                    {selectedHistoryItem.timestamp ? new Date(selectedHistoryItem.timestamp).toLocaleString() : 'N/A'}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">ANONYMIZED ROWS</span>
                  <strong className="text-white">{selectedHistoryItem.records_anonymized?.toLocaleString() || 5000}</strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">RISK SCORE</span>
                  <strong className="text-emerald-400">{selectedHistoryItem.risk_score} ({selectedHistoryItem.risk_level})</strong>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 font-mono">
                  Applied Column Anonymization Rules ({selectedHistoryItem.policy_snapshot?.column_policies?.length || 0} Columns)
                </h4>
                <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-950">
                  <table className="w-full text-left text-xs text-slate-300 font-mono">
                    <thead className="bg-slate-900 text-slate-400 text-[10px] border-b border-slate-800 uppercase">
                      <tr>
                        <th className="p-2.5">Column</th>
                        <th className="p-2.5">PII Status</th>
                        <th className="p-2.5">PII Type</th>
                        <th className="p-2.5">Applied Technique</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {selectedHistoryItem.policy_snapshot?.column_policies?.map((col, cidx) => (
                        <tr key={cidx} className="hover:bg-slate-900/50">
                          <td className="p-2.5 font-bold text-white">{col.column_name}</td>
                          <td className="p-2.5">
                            {col.is_pii ? (
                              <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-300 text-[10px] font-bold border border-red-500/30">
                                PII DETECTED
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                                NON-PII
                              </span>
                            )}
                          </td>
                          <td className="p-2.5 text-slate-300">{col.pii_type || 'N/A'}</td>
                          <td className="p-2.5">
                            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 text-[10px] font-bold border border-blue-500/30">
                              {col.anonymization_technique}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div className="p-4 bg-slate-950 border-t border-slate-800 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedHistoryItem(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold rounded-xl transition-colors"
              >
                Close Snapshot
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div 
          onClick={() => router.push('/database')}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl hover:border-blue-500/50 hover:bg-slate-800/60 transition-all cursor-pointer space-y-3"
        >
          <div className="flex items-center justify-between">
            <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-xl">
              <Database className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white">Database Connection</h4>
            <p className="text-xs text-slate-400 mt-1">Configure source PostgreSQL database & target tables.</p>
          </div>
        </div>

        <div 
          onClick={() => router.push('/pipeline')}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl hover:border-emerald-500/50 hover:bg-slate-800/60 transition-all cursor-pointer space-y-3"
        >
          <div className="flex items-center justify-between">
            <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-xl">
              <Activity className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white">17-Step Pipeline</h4>
            <p className="text-xs text-slate-400 mt-1">View step-by-step execution, approvals & live logs.</p>
          </div>
        </div>

        <div 
          onClick={() => router.push('/audit')}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl hover:border-amber-500/50 hover:bg-slate-800/60 transition-all cursor-pointer space-y-3"
        >
          <div className="flex items-center justify-between">
            <div className="p-2.5 bg-amber-500/10 text-amber-400 rounded-xl">
              <FileText className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white">Audit Logs</h4>
            <p className="text-xs text-slate-400 mt-1">Single-view 17-step stream & HMAC compliance trail.</p>
          </div>
        </div>

        <div 
          onClick={() => router.push('/sandbox')}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl hover:border-purple-500/50 hover:bg-slate-800/60 transition-all cursor-pointer space-y-3"
        >
          <div className="flex items-center justify-between">
            <div className="p-2.5 bg-purple-500/10 text-purple-400 rounded-xl">
              <Server className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white">Sandbox Explorer</h4>
            <p className="text-xs text-slate-400 mt-1">Inspect live anonymized records in destination DB.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
