"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { HardDrive, ShieldCheck, RefreshCw, Loader2, Table, Search, AlertCircle, Database, CheckCircle2, Lock, ArrowRight, ShieldAlert } from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function SandboxPage() {
  const router = useRouter();
  const { onMessage } = useWebSocket();
  const [selectedTable, setSelectedTable] = useState<string>('customers');
  const [configuredTargetTable, setConfiguredTargetTable] = useState<string>('customers');
  const [records, setRecords] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusState, setStatusState] = useState<'success' | 'not_connected' | 'step_pending' | 'table_mismatch' | 'error'>('success');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchSandboxRecords = async (table: string, isSilent = false) => {
    if (!isSilent) setIsLoading(true);
    setErrorMsg(null);
    setSelectedTable(table);
    try {
      const userId = (typeof window !== 'undefined' && localStorage.getItem('datavault_user_id')) || 'b@gmail.com';
      const endpoint = `/api/pipeline/destination-records?table=${encodeURIComponent(table)}&limit=30&user_id=${encodeURIComponent(userId)}`;
      let res = await fetch(`http://127.0.0.1:8000${endpoint}`);
      if (!res.ok) {
        res = await fetch(endpoint);
      }
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'success') {
          setRecords(data.records || []);
          setStatusState('success');
        } else if (data.status === 'not_connected') {
          setStatusState('not_connected');
          setErrorMsg(data.message || 'Source database not connected.');
          setRecords([]);
        } else if (data.status === 'step_pending') {
          setStatusState('step_pending');
          setErrorMsg(data.message || 'Destination records unavailable until Step 17 completion.');
          setRecords([]);
        } else if (data.status === 'table_mismatch') {
          setStatusState('table_mismatch');
          setErrorMsg(data.message || 'Target table mismatch.');
          setRecords([]);
        } else {
          setStatusState('error');
          setErrorMsg(data.message || 'Failed to fetch destination records.');
          setRecords([]);
        }
      } else {
        setStatusState('error');
        setErrorMsg('Network error while connecting to sandbox endpoint.');
        setRecords([]);
      }
    } catch (err) {
      console.error('Sandbox fetch error:', err);
      setStatusState('error');
      setErrorMsg('Unable to connect to backend server.');
      setRecords([]);
    } finally {
      if (!isSilent) setIsLoading(false);
    }
  };

  useEffect(() => {
    const initSandbox = async () => {
      try {
        let res = await fetch('/api/pipeline/status');
        if (!res.ok) {
          res = await fetch('http://127.0.0.1:8000/api/pipeline/status');
        }
        if (res.ok) {
          const data = await res.json();
          const target = data.state?.target_table || 'accounts';
          setConfiguredTargetTable(target);
          setSelectedTable(target);
          fetchSandboxRecords(target, false);
          return;
        }
      } catch (e) {
        console.error('Initial sandbox target table fetch error:', e);
      }
      setSelectedTable('accounts');
      fetchSandboxRecords('accounts', false);
    };
    initSandbox();

    const interval = setInterval(() => {
      fetchSandboxRecords(selectedTable, true);
    }, 1500);

    return () => clearInterval(interval);
  }, [selectedTable]);

  useEffect(() => {
    const unsubscribe = onMessage((msg: any) => {
      if (msg && (msg.type === 'traffic_simulated' || msg.type === 'dashboard_update' || msg.type === 'step_update')) {
        fetchSandboxRecords(selectedTable, true);
      }
    });
    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [onMessage, selectedTable]);

  const filteredRecords = records.filter((row) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return Object.values(row).some((val) => String(val ?? '').toLowerCase().includes(term));
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-500/10 text-emerald-400 rounded-xl flex items-center justify-center border border-emerald-500/20 shadow-md">
            <HardDrive className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              Sandbox Environment
              {statusState === 'success' && (
                <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  DESTINATION DB: neondb_anonymized
                </span>
              )}
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Isolated target database containing privacy-preserved records generated strictly by Pipeline Step 12 & Step 13 for the targeted table.
            </p>
          </div>
        </div>

        {statusState === 'success' && (
          <button
            type="button"
            onClick={() => fetchSandboxRecords(selectedTable)}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 border border-slate-700 shadow"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-emerald-400' : ''}`} />
            Refresh Sandbox
          </button>
        )}
      </div>

      {/* Render Main Content Based on Connection & Step Execution State */}
      {isLoading ? (
        <div className="py-24 text-center space-y-3 bg-slate-900 border border-slate-800 rounded-xl">
          <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400 font-mono">Checking destination database records...</p>
        </div>
      ) : statusState === 'not_connected' ? (
        <div className="py-20 text-center space-y-4 bg-slate-900 rounded-2xl border border-slate-800 p-8 max-w-xl mx-auto shadow-2xl my-8">
          <div className="w-14 h-14 bg-blue-500/10 text-blue-400 rounded-2xl flex items-center justify-center mx-auto border border-blue-500/20 shadow-inner">
            <Database className="w-7 h-7" />
          </div>
          <div className="space-y-1.5">
            <h3 className="text-lg font-bold text-white">No Source Database Connected</h3>
            <p className="text-xs text-slate-400 leading-relaxed max-w-md mx-auto">
              No database connected yet. Please configure your source database credentials at /database to view destination records.
            </p>
          </div>
          <button
            type="button"
            onClick={() => router.push('/database')}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl transition-all inline-flex items-center gap-2 shadow-lg shadow-blue-600/20 cursor-pointer"
          >
            <Database className="w-4 h-4" />
            Connect Database Now
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      ) : statusState === 'step_pending' ? (
        <div className="py-20 text-center space-y-4 bg-slate-900 rounded-2xl border border-amber-500/30 p-8 max-w-xl mx-auto shadow-2xl my-8">
          <div className="w-14 h-14 bg-amber-500/10 text-amber-400 rounded-2xl flex items-center justify-center mx-auto border border-amber-500/20 shadow-inner">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <div className="space-y-1.5">
            <h3 className="text-lg font-bold text-white">Pipeline Step 12 & 13 Pending</h3>
            <p className="text-xs text-slate-400 leading-relaxed max-w-md mx-auto">
              Anonymized destination records for target table <strong className="text-white font-mono">{configuredTargetTable || 'targeted table'}</strong> will be generated after executing Step 12 (Data Anonymization) & Step 13 (Destination Loading).
            </p>
          </div>
          <button
            type="button"
            onClick={() => router.push('/pipeline')}
            className="px-6 py-2.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl transition-all inline-flex items-center gap-2 shadow-lg shadow-amber-600/20 cursor-pointer"
          >
            <ShieldCheck className="w-4 h-4" />
            View Pipeline Execution
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <>
          {/* Metadata KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-3">
              <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-lg">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Target Database</span>
                <span className="text-xs font-mono font-bold text-emerald-400">neondb_anonymized</span>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-3">
              <div className="p-2.5 bg-purple-500/10 text-purple-400 rounded-lg">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Configured Target Table</span>
                <span className="text-xs font-mono font-bold text-purple-300 uppercase">{configuredTargetTable}</span>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-3">
              <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-lg">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Step 12 & 13 Execution</span>
                <span className="text-xs font-bold text-emerald-400">✓ Step 12 & 13 Complete</span>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-3">
              <div className="p-2.5 bg-amber-500/10 text-amber-400 rounded-lg">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Loaded Records</span>
                <span className="text-xs font-mono font-bold text-white">{records.length} Rows Rendered</span>
              </div>
            </div>
          </div>

          {/* Main Sandbox Data Workspace */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6 shadow-xl">
            {/* Controls Header: Targeted Table Badge & Search */}
            <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="px-3 py-1.5 text-xs font-mono font-bold rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 flex items-center gap-2">
                  <Table className="w-3.5 h-3.5" />
                  TARGETED TABLE: {configuredTargetTable.toUpperCase()}
                </span>
              </div>

              {/* Search Bar */}
              <div className="relative min-w-[240px]">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search anonymized rows..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>
            </div>

            {/* Table View */}
            {filteredRecords.length > 0 ? (
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                    <tr>
                      {Object.keys(filteredRecords[0]).map((col) => (
                        <th key={col} className="px-4 py-3 font-semibold text-slate-300">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/60">
                    {filteredRecords.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-slate-800/40 transition-colors">
                        {Object.entries(row).map(([k, val]: [string, any]) => {
                          const valStr = String(val ?? '');
                          const isMasked = valStr.includes('*') || valStr.includes('xxxx');
                          const isHash = valStr.length > 20 && !valStr.includes('@') && !valStr.includes(' ');
                          return (
                            <td key={k} className="px-4 py-2.5 text-slate-200 whitespace-nowrap">
                              {isMasked ? (
                                <span className="bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded border border-amber-500/30 text-[11px] font-bold">
                                  {valStr}
                                </span>
                              ) : isHash ? (
                                <span className="bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded border border-purple-500/30 text-[10px] font-bold truncate max-w-[150px] inline-block">
                                  {valStr}
                                </span>
                              ) : (
                                valStr
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-16 text-center space-y-3 bg-slate-950/50 rounded-lg border border-slate-800">
                <AlertCircle className="w-8 h-8 text-amber-400 mx-auto" />
                <p className="text-xs text-slate-300">
                  No anonymized records found in table <strong className="text-emerald-400 font-mono">{selectedTable}</strong>.
                </p>
                <p className="text-[11px] text-slate-500">
                  Run the 17-step pipeline on <strong className="text-blue-400">/pipeline</strong> to populate anonymized records into <code className="text-emerald-400 font-mono">neondb_anonymized</code>.
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
