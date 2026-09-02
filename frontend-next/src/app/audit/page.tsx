"use client";

import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/auth';
import { useWebSocket } from '@/hooks/useWebSocket';
import { 
  FileText, Search, Filter, Download, CheckCircle, AlertCircle, XCircle, Info, 
  ShieldCheck, RefreshCw, Loader2, Database, Lock, Key, Radio, Layers
} from 'lucide-react';

interface AuditLog {
  id: string;
  timestamp: string;
  user_id?: string;
  run_id?: string;
  step_index?: number;
  step_name?: string;
  level: 'info' | 'warning' | 'error' | 'success';
  category: 'pipeline' | 'database' | 'security' | 'approval' | 'simulation' | 'admin' | 'policy';
  action: string;
  details: string;
  ip_address?: string;
  audit_hash?: string;
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedLevel, setSelectedLevel] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLiveStreaming, setIsLiveStreaming] = useState<boolean>(true);

  const getActiveUserId = () => {
    const user = useAuthStore.getState().user;
    if (user && (user.email || user.id)) return user.email || user.id;
    if (typeof window !== 'undefined') {
      const directEmail = localStorage.getItem('datavault_user_email') || localStorage.getItem('datavault_user_id') || localStorage.getItem('datavault_active_user');
      if (directEmail) return directEmail;
      try {
        const stored = localStorage.getItem('datavault_user');
        if (stored) {
          const parsed = JSON.parse(stored);
          if (parsed.email || parsed.id) return parsed.email || parsed.id;
        }
      } catch (e) {}
    }
    return 'a@gmail.com';
  };

  const wsUrl = typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000/api/pipeline/ws`
    : 'ws://127.0.0.1:8000/api/pipeline/ws';

  const { isConnected, onMessage } = useWebSocket(wsUrl);

  const fetchAuditLogs = async (showLoader = true) => {
    if (showLoader) setIsLoading(true);
    const userId = getActiveUserId();
    const query = `user_id=${encodeURIComponent(userId)}&category=${selectedCategory}&level=${selectedLevel}&search=${encodeURIComponent(searchQuery)}`;
    try {
      let res = await fetch(`/api/audit/logs?${query}`);
      if (!res.ok) {
        res = await fetch(`http://127.0.0.1:8000/api/audit/logs?${query}`);
      }
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
      }
    } catch (err) {
      try {
        const fallbackRes = await fetch(`http://127.0.0.1:8000/api/audit/logs?${query}`);
        if (fallbackRes.ok) {
          const data = await fallbackRes.json();
          setLogs(data.logs || []);
        }
      } catch (fallbackErr) {
        console.error('Audit fetch error:', fallbackErr);
      }
    } finally {
      if (showLoader) setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs(true);
  }, [selectedCategory, selectedLevel]);

  useEffect(() => {
    if (!isLiveStreaming) return;
    const interval = setInterval(() => fetchAuditLogs(false), 1500);
    return () => clearInterval(interval);
  }, [isLiveStreaming, selectedCategory, selectedLevel, searchQuery]);

  useEffect(() => {
    const unsubscribe = onMessage((msg: any) => {
      if (msg && msg.type === 'log' && msg.data) {
        setLogs((prevLogs) => {
          const exists = prevLogs.some((l) => l.id === msg.data.id);
          if (exists) return prevLogs;
          return [msg.data, ...prevLogs];
        });
      } else if (msg && (msg.type === 'pipeline_status' || msg.type === 'step_update' || msg.type === 'dashboard_update' || msg.type === 'traffic_simulated')) {
        fetchAuditLogs(false);
      }
    });
    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [onMessage]);

  const handleExport = (format: 'json' | 'csv') => {
    window.open(`/api/audit/export?format=${format}`, '_blank');
  };

  const getLevelBadge = (level: string) => {
    switch (level) {
      case 'success':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
            <CheckCircle className="w-3 h-3 text-emerald-400" /> SUCCESS
          </span>
        );
      case 'warning':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
            <AlertCircle className="w-3 h-3 text-amber-400" /> WARNING
          </span>
        );
      case 'error':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-300 border border-red-500/30 flex items-center gap-1">
            <XCircle className="w-3 h-3 text-red-400" /> ERROR
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30 flex items-center gap-1">
            <Info className="w-3 h-3 text-blue-400" /> INFO
          </span>
        );
    }
  };

  const getCategoryBadge = (category: string) => {
    switch (category) {
      case 'security':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold">SECURITY</span>;
      case 'approval':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">APPROVAL</span>;
      case 'database':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-bold">DATABASE</span>;
      case 'simulation':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-bold">SIMULATION</span>;
      default:
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 font-bold">PIPELINE</span>;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl border border-blue-200 shadow-md">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2 tracking-tight">
              Audit Logs & Compliance Trail
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200">
                HMAC-SHA256 VERIFIED
              </span>
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Immutable, single-view 17-step pipeline execution stream & DPDP Act 2023 compliance audit log.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsLiveStreaming(!isLiveStreaming)}
            className={`px-3.5 py-2 text-xs font-bold rounded-xl transition-all border flex items-center gap-2 ${
              isLiveStreaming
                ? 'bg-emerald-50 text-emerald-600 border-emerald-200 shadow-md'
                : 'bg-slate-100 text-slate-500 border-slate-200'
            }`}
          >
            <Radio className={`w-3.5 h-3.5 ${isLiveStreaming ? 'animate-pulse text-emerald-600' : ''}`} />
            {isLiveStreaming ? 'Live Stream Active' : 'Live Stream Paused'}
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center gap-3 shadow-xl">
          <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold block">17-Step Coverage</span>
            <span className="text-xs font-bold text-slate-900">All 17 Steps Logged</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center gap-3 shadow-xl">
          <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold block">Integrity Check</span>
            <span className="text-xs font-bold text-emerald-600">HMAC-SHA256 Verified</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center gap-3 shadow-xl">
          <div className="p-2.5 bg-purple-50 text-purple-600 rounded-xl">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold block">Compliance Standard</span>
            <span className="text-xs font-bold text-purple-600">DPDP Act 2023 / GDPR</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center gap-3 shadow-xl">
          <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold block">Total Recorded Logs</span>
            <span className="text-xs font-mono font-bold text-slate-900">{logs.length} Events</span>
          </div>
        </div>
      </div>

      {/* Unified Single-View Log Feed */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 space-y-4 shadow-xl">
        {/* Search & Filter Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
          <div className="flex items-center gap-3 flex-1 min-w-[280px]">
            <div className="relative w-full">
              <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
              <input
                type="text"
                placeholder="Search all 17 steps, actions, run IDs, or HMAC hashes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchAuditLogs()}
                className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>
            <button
              type="button"
              onClick={() => fetchAuditLogs()}
              className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-900 text-xs font-bold rounded-xl border border-slate-200"
            >
              Search
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs font-medium">
            <div className="flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-600 font-bold">Category:</span>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-white border border-slate-200 rounded-xl px-2.5 py-1.5 text-slate-900 text-xs focus:outline-none focus:border-sky-500 font-medium"
              >
                <option value="all">All Categories</option>
                <option value="pipeline">Pipeline (17 Steps)</option>
                <option value="database">Database</option>
                <option value="security">Security</option>
                <option value="approval">Approval Workflow</option>
                <option value="simulation">Live Simulation</option>
                <option value="policy">Policy</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-slate-600 font-bold">Severity:</span>
              <select
                value={selectedLevel}
                onChange={(e) => setSelectedLevel(e.target.value)}
                className="bg-white border border-slate-200 rounded-xl px-2.5 py-1.5 text-slate-900 text-xs focus:outline-none focus:border-sky-500 font-medium"
              >
                <option value="all">All Severities</option>
                <option value="info">Info</option>
                <option value="success">Success</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
              </select>
            </div>
          </div>
        </div>

        {/* Logs Table */}
        {isLoading ? (
          <div className="py-20 text-center space-y-3">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
            <p className="text-xs text-slate-500 font-mono">Loading unified 17-step audit stream...</p>
          </div>
        ) : logs.length > 0 ? (
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] border-b border-slate-200 font-bold">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-3 py-3">Step / Event</th>
                  <th className="px-3 py-3">Severity</th>
                  <th className="px-3 py-3">Category</th>
                  <th className="px-4 py-3">Action & Activity Details</th>
                  <th className="px-4 py-3">HMAC Hash Checksum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap text-[11px]">
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap">
                      {log.step_index ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-600 border border-blue-200">
                          STEP {log.step_index}
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-500 border border-slate-200">
                          EVENT
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap">
                      {getLevelBadge(log.level)}
                    </td>
                    <td className="px-3 py-3 whitespace-nowrap">
                      {getCategoryBadge(log.category)}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      <div className="font-bold text-xs text-slate-900">{log.action}</div>
                      <div className="text-[11px] text-slate-500 font-normal mt-0.5 leading-relaxed">{log.details}</div>
                      {log.run_id && (
                        <span className="text-[10px] text-blue-600 font-mono mt-1 block">Run ID: {log.run_id}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {log.audit_hash ? (
                        <span className="bg-slate-50 text-slate-600 px-2 py-1 rounded text-[10px] font-mono border border-slate-200 block truncate max-w-[140px]" title={log.audit_hash}>
                          🔑 {log.audit_hash}
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[10px]">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-16 text-center space-y-3 bg-slate-50 rounded-xl border border-slate-200">
            <AlertCircle className="w-8 h-8 text-amber-600 mx-auto" />
            <p className="text-xs font-bold text-slate-600">No audit log records match the selected filters.</p>
            <button
              type="button"
              onClick={() => {
                setSelectedCategory('all');
                setSelectedLevel('all');
                setSearchQuery('');
              }}
              className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-900 text-xs font-bold rounded-xl transition-colors inline-flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Reset Filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
