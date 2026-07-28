"use client";

import React, { useState, useEffect } from 'react';

interface LiveTrafficSimulatorProps {
  onSimulationSuccess?: () => void;
}

interface ColumnSchema {
  name: string;
  type: string;
}

export const LiveTrafficSimulator: React.FC<LiveTrafficSimulatorProps> = ({
  onSimulationSuccess
}) => {
  const [activeTable, setActiveTable] = useState<string | null>(null);
  const [loadingConfig, setLoadingConfig] = useState<boolean>(true);
  const [loading, setLoading] = useState<string | null>(null);
  const [logMessage, setLogMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  // Custom Form Entry State
  const [mode, setMode] = useState<'quick' | 'custom'>('quick');
  const [schemaColumns, setSchemaColumns] = useState<ColumnSchema[]>([]);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [loadingSchema, setLoadingSchema] = useState<boolean>(false);

  // Fetch current user database configuration on mount
  useEffect(() => {
    const fetchUserConfig = async () => {
      setLoadingConfig(true);
      try {
        const res = await fetch('/api/database/config');
        if (res.ok) {
          const contentType = res.headers.get('content-type') || '';
          if (contentType.includes('application/json')) {
            const data = await res.json();
            if (data && data.target_table) {
              setActiveTable(data.target_table);
            }
          }
        }
      } catch (err) {
        console.warn('Could not fetch user database config for simulator:', err);
      } finally {
        setLoadingConfig(false);
      }
    };
    fetchUserConfig();
  }, []);

  // Fetch schema columns when switching to custom mode
  useEffect(() => {
    if (mode === 'custom' && activeTable) {
      const fetchSchema = async () => {
        setLoadingSchema(true);
        try {
          const res = await fetch(`/api/pipeline/table-schema?table=${activeTable}`);
          if (res.ok) {
            const data = await res.json();
            if (data.status === 'success' && Array.isArray(data.columns)) {
              setSchemaColumns(data.columns);
              const initialData: Record<string, string> = {};
              data.columns.forEach((col: ColumnSchema) => {
                initialData[col.name] = '';
              });
              setFormData(initialData);
            }
          }
        } catch (err) {
          console.warn('Could not fetch schema for table:', activeTable, err);
        } finally {
          setLoadingSchema(false);
        }
      };
      fetchSchema();
    }
  }, [mode, activeTable]);

  const handleSimulate = async (operation: 'INSERT' | 'UPDATE' | 'DELETE', useCustomData: boolean = false) => {
    if (!activeTable) {
      setLogMessage({
        type: 'error',
        text: 'No database configuration available. Please configure a database before using Live Traffic Simulator.'
      });
      return;
    }

    setLoading(operation);
    setLogMessage(null);
    try {
      const payload: any = { operation, target_table: activeTable };
      if (useCustomData && mode === 'custom') {
        payload.custom_data = formData;
      }

      const response = await fetch('/api/pipeline/simulate-traffic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const contentType = response.headers.get('content-type') || '';
      let data: any = {};

      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const rawText = await response.text();
        setLogMessage({
          type: 'error',
          text: `Simulation failed: Server returned non-JSON response (HTTP ${response.status}).`
        });
        setLoading(null);
        return;
      }

      if (response.ok && data.status === 'success') {
        if (operation === 'INSERT') {
          setLogMessage({
            type: 'success',
            text: `➕ [INSERT SUCCESS] Created simulator record #${data.inserted_id} in '${activeTable}' table.`
          });
        } else if (operation === 'UPDATE') {
          setLogMessage({
            type: 'info',
            text: `✏️ [UPDATE SUCCESS] Modified field '${data.updated_field}' for record #${data.updated_id} in '${activeTable}' table.`
          });
        } else if (operation === 'DELETE') {
          setLogMessage({
            type: 'error',
            text: `🗑️ [DELETE SUCCESS] Safely removed simulator record #${data.deleted_id} from '${activeTable}' table.`
          });
        }
        if (onSimulationSuccess) onSimulationSuccess();
      } else {
        setLogMessage({
          type: 'error',
          text: `Simulation failed: ${data.message || 'Unknown server error.'}`
        });
      }
    } catch (err: any) {
      setLogMessage({
        type: 'error',
        text: `Simulation failed: ${err.message || 'Network error occurred.'}`
      });
    } finally {
      setLoading(null);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (loadingConfig) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur-md mb-6 animate-pulse">
        <p className="text-xs text-slate-400">Loading user database configuration...</p>
      </div>
    );
  }

  if (!activeTable) {
    return (
      <div className="bg-slate-900/80 border border-amber-900/40 rounded-xl p-5 shadow-xl backdrop-blur-md mb-6">
        <div className="flex items-center gap-2 mb-2">
          <span className="w-3 h-3 rounded-full bg-amber-400"></span>
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Live Traffic Simulator
          </h3>
        </div>
        <p className="text-xs text-amber-300/90 font-mono">
          No database configuration available. Configure a database before using Live Traffic Simulator.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur-md mb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse"></div>
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Live Traffic Simulator
          </h3>
        </div>

        <div className="flex items-center gap-3">
          {/* Mode Switch Tabs */}
          <div className="bg-slate-950 p-1 rounded-lg border border-slate-800 flex items-center gap-1">
            <button
              type="button"
              onClick={() => setMode('quick')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                mode === 'quick'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              ⚡ 1-Click Auto
            </button>
            <button
              type="button"
              onClick={() => setMode('custom')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                mode === 'custom'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              ✍️ Custom Input Form
            </button>
          </div>

          <span className="text-xs px-2.5 py-1 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/50 font-mono font-bold">
            Target Table: {activeTable}
          </span>
        </div>
      </div>

      <p className="text-xs text-slate-400 mb-4">
        Simulate real-time CRUD traffic (INSERT, UPDATE, DELETE) on the source database to test continuous 30-second change detection and automatic PII anonymization.
      </p>

      {/* QUICK MODE */}
      {mode === 'quick' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <button
            onClick={() => handleSimulate('INSERT')}
            disabled={loading !== null}
            className="flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 rounded-lg font-medium text-xs transition-all disabled:opacity-50"
          >
            {loading === 'INSERT' ? (
              <span className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <span>➕</span>
            )}
            Simulate INSERT
          </button>

          <button
            onClick={() => handleSimulate('UPDATE')}
            disabled={loading !== null}
            className="flex items-center justify-center gap-2 px-4 py-2.5 bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/40 rounded-lg font-medium text-xs transition-all disabled:opacity-50"
          >
            {loading === 'UPDATE' ? (
              <span className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <span>✏️</span>
            )}
            Simulate UPDATE
          </button>

          <button
            onClick={() => handleSimulate('DELETE')}
            disabled={loading !== null}
            className="flex items-center justify-center gap-2 px-4 py-2.5 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 rounded-lg font-medium text-xs transition-all disabled:opacity-50"
          >
            {loading === 'DELETE' ? (
              <span className="w-4 h-4 border-2 border-rose-400 border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <span>🗑️</span>
            )}
            Simulate DELETE
          </button>
        </div>
      )}

      {/* CUSTOM FORM MODE */}
      {mode === 'custom' && (
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Enter Custom Record Details for Table '{activeTable}'
            </h4>
            <span className="text-[10px] text-slate-500 font-mono">
              Fill in custom fields below or leave blank to auto-generate
            </span>
          </div>

          {loadingSchema ? (
            <div className="text-xs text-slate-400 py-4 text-center">Loading column schema...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {schemaColumns.map((col) => (
                <div key={col.name} className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-300 flex items-center justify-between">
                    <span className="capitalize">{col.name.replace('_', ' ')}</span>
                    <span className="text-[9px] font-mono text-slate-500">{col.type}</span>
                  </label>
                  <input
                    type="text"
                    value={formData[col.name] || ''}
                    onChange={(e) => handleInputChange(col.name, e.target.value)}
                    placeholder={`Enter ${col.name}...`}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors font-mono"
                  />
                </div>
              ))}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              onClick={() => handleSimulate('INSERT', true)}
              disabled={loading !== null}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs rounded-lg transition-colors flex items-center gap-2 shadow-md disabled:opacity-50"
            >
              {loading === 'INSERT' ? (
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              ) : (
                <span>➕</span>
              )}
              Submit Custom INSERT
            </button>

            <button
              onClick={() => handleSimulate('UPDATE', true)}
              disabled={loading !== null}
              className="px-5 py-2 bg-amber-600 hover:bg-amber-500 text-white font-medium text-xs rounded-lg transition-colors flex items-center gap-2 shadow-md disabled:opacity-50"
            >
              {loading === 'UPDATE' ? (
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              ) : (
                <span>✏️</span>
              )}
              Submit Custom UPDATE
            </button>

            <button
              onClick={() => handleSimulate('DELETE')}
              disabled={loading !== null}
              className="px-5 py-2 bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs rounded-lg transition-colors flex items-center gap-2 shadow-md disabled:opacity-50"
            >
              {loading === 'DELETE' ? (
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              ) : (
                <span>🗑️</span>
              )}
              Safely Delete Simulator Record
            </button>
          </div>
        </div>
      )}

      {logMessage && (
        <div className={`mt-4 p-3 rounded-lg text-xs font-mono border ${
          logMessage.type === 'success' ? 'bg-emerald-950/60 border-emerald-800/60 text-emerald-300' :
          logMessage.type === 'info' ? 'bg-amber-950/60 border-amber-800/60 text-amber-300' :
          'bg-rose-950/60 border-rose-800/60 text-rose-300'
        }`}>
          {logMessage.text}
        </div>
      )}
    </div>
  );
};
