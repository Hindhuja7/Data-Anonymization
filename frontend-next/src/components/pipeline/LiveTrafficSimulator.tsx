"use client";

import React, { useState, useEffect } from 'react';
import { Plus, Edit3, Trash2, Zap, Database, CheckCircle2, AlertCircle } from 'lucide-react';

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

  // Tab mode: 'insert' | 'update' | 'delete' | 'quick'
  const [subTab, setSubTab] = useState<'insert' | 'update' | 'delete' | 'quick'>('insert');
  
  // Schema & Records State
  const [pkCol, setPkCol] = useState<string>('id');
  const [schemaColumns, setSchemaColumns] = useState<ColumnSchema[]>([]);
  const [existingRecords, setExistingRecords] = useState<any[]>([]);
  const [selectedRecordId, setSelectedRecordId] = useState<string | number>('');
  
  // Form Data State
  const [insertFormData, setInsertFormData] = useState<Record<string, string>>({});
  const [updateFormData, setUpdateFormData] = useState<Record<string, string>>({});
  const [loadingSchema, setLoadingSchema] = useState<boolean>(false);
  const [loadingRecords, setLoadingRecords] = useState<boolean>(false);

  // Fetch current database configuration on mount
  useEffect(() => {
    const fetchUserConfig = async () => {
      setLoadingConfig(true);
      try {
        const res = await fetch('http://localhost:8000/api/database/config');
        if (res.ok) {
          const data = await res.json();
          if (data && data.target_table) {
            setActiveTable(data.target_table);
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

  // Fetch dynamic table schema whenever activeTable changes
  useEffect(() => {
    if (activeTable) {
      const fetchSchema = async () => {
        setLoadingSchema(true);
        try {
          const res = await fetch(`http://localhost:8000/api/pipeline/table-schema?table=${activeTable}`);
          if (res.ok) {
            const data = await res.json();
            if (data.status === 'success' && Array.isArray(data.columns)) {
              setSchemaColumns(data.columns);
              setPkCol(data.pk_col || 'id');
              const initialData: Record<string, string> = {};
              data.columns.forEach((col: ColumnSchema) => {
                initialData[col.name] = '';
              });
              setInsertFormData(initialData);
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
  }, [activeTable]);

  // Fetch existing records when switching to Update or Delete tabs
  const fetchRecords = async () => {
    if (!activeTable) return;
    setLoadingRecords(true);
    try {
      const res = await fetch(`http://localhost:8000/api/pipeline/table-records?table=${activeTable}&limit=20`);
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'success' && Array.isArray(data.records)) {
          setExistingRecords(data.records);
          if (data.records.length > 0) {
            const firstRec = data.records[0];
            const pkv = firstRec[pkCol] ?? firstRec.id ?? Object.values(firstRec)[0];
            setSelectedRecordId(pkv);
            populateUpdateForm(firstRec);
          }
        }
      }
    } catch (err) {
      console.warn('Could not fetch records for table:', activeTable, err);
    } finally {
      setLoadingRecords(false);
    }
  };

  useEffect(() => {
    if ((subTab === 'update' || subTab === 'delete') && activeTable) {
      fetchRecords();
    }
  }, [subTab, activeTable]);

  const populateUpdateForm = (record: any) => {
    if (!record) return;
    const initialData: Record<string, string> = {};
    schemaColumns.forEach((col) => {
      initialData[col.name] = record[col.name] !== undefined && record[col.name] !== null ? String(record[col.name]) : '';
    });
    setUpdateFormData(initialData);
  };

  const handleRecordSelect = (recordId: string | number) => {
    setSelectedRecordId(recordId);
    const rec = existingRecords.find(r => String(r[pkCol] ?? r.id ?? Object.values(r)[0]) === String(recordId));
    if (rec) {
      populateUpdateForm(rec);
    }
  };

  const handleSimulate = async (operation: 'INSERT' | 'UPDATE' | 'DELETE') => {
    if (!activeTable) {
      setLogMessage({
        type: 'error',
        text: 'No database configuration available. Please configure a database first.'
      });
      return;
    }

    setLoading(operation);
    setLogMessage(null);

    try {
      const payload: any = { operation, target_table: activeTable };

      if (subTab === 'insert') {
        payload.custom_data = insertFormData;
      } else if (subTab === 'update') {
        payload.custom_data = updateFormData;
        payload.record_id = selectedRecordId;
      } else if (subTab === 'delete') {
        payload.record_id = selectedRecordId;
      }

      const response = await fetch('http://localhost:8000/api/pipeline/simulate-traffic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          if (operation === 'INSERT') {
            setLogMessage({
              type: 'success',
              text: `➕ [INSERT SUCCESS] Created new record #${data.inserted_id || 'AUTO'} in '${activeTable}' table.`
            });
          } else if (operation === 'UPDATE') {
            setLogMessage({
              type: 'info',
              text: `✏️ [UPDATE SUCCESS] Updated record #${selectedRecordId || data.updated_id} in '${activeTable}' table.`
            });
          } else if (operation === 'DELETE') {
            setLogMessage({
              type: 'error',
              text: `🗑️ [DELETE SUCCESS] Removed record #${selectedRecordId || data.deleted_id} from '${activeTable}' table.`
            });
          }
          if (subTab === 'update' || subTab === 'delete') {
            fetchRecords();
          }
          if (onSimulationSuccess) onSimulationSuccess();
        } else {
          setLogMessage({
            type: 'error',
            text: `Simulation error: ${data.message || 'Server error occurred.'}`
          });
        }
      }
    } catch (err: any) {
      setLogMessage({
        type: 'error',
        text: `Network error: ${err.message || 'Could not connect to server.'}`
      });
    } finally {
      setLoading(null);
    }
  };

  if (loadingConfig) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl animate-pulse font-mono">
        <p className="text-xs text-slate-400">Loading target database schema...</p>
      </div>
    );
  }

  if (!activeTable) {
    return (
      <div className="bg-slate-900 border border-amber-900/40 rounded-xl p-5 shadow-xl font-mono">
        <div className="flex items-center gap-2 mb-2">
          <span className="w-3 h-3 rounded-full bg-amber-400"></span>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Live Traffic Simulator</h3>
        </div>
        <p className="text-xs text-amber-300">
          No database target table configured. Configure a database to enable live traffic simulation.
        </p>
      </div>
    );
  }

  const getSmartPlaceholder = (name: string, type: string) => {
    const n = name.toLowerCase();
    const t = type.toLowerCase();
    
    if (n.includes('email')) return 'e.g. rahul.s@example.com';
    if (n.includes('phone') || n.includes('mobile')) return 'e.g. 10 digits (9876543210)';
    if (n.includes('ssn')) return 'e.g. 9 digits (123-45-6789)';
    if (n.includes('aadhaar') || n.includes('aadhar')) return 'e.g. 12 digits (1234 5678 9012)';
    if (n.includes('pan')) return 'e.g. 10 chars (ABCDE1234F)';
    if (n.includes('credit') || n.includes('card')) return 'e.g. 16 digits (4532-1111-2222-3333)';
    if (n.includes('salary') || n.includes('amount') || n.includes('balance') || n.includes('price')) return 'e.g. Number (e.g. 75000)';
    if (n.includes('account_number') || n.includes('acc_num')) return 'e.g. 12 digits (123456789012)';
    if (n.includes('routing')) return 'e.g. 9 digits (021000021)';
    if (n.includes('address') || n.includes('location')) return 'e.g. MG Road, Bangalore';
    if (n.includes('name') || n.includes('first') || n.includes('last')) return 'e.g. Rahul Sharma';
    if (n.includes('date') || n.includes('dob')) return 'e.g. YYYY-MM-DD (1995-08-15)';
    if (n.includes('customer_id') || n.includes('user_id') || n.includes('dept') || n.includes('department_id') || n.includes('account_id')) return 'e.g. Integer ID (e.g. 101)';
    if (t.includes('int') || t.includes('number')) return 'e.g. Integer Number (e.g. 100)';
    if (t.includes('float') || t.includes('double') || t.includes('numeric') || t.includes('decimal')) return 'e.g. Decimal Number (e.g. 2500.50)';
    return `e.g. Enter ${name.replace('_', ' ')}...`;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl font-mono">
      {/* Header & Dedicated Sub-Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Live Traffic Simulator</h3>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Test continuous Change Data Capture (CDC) & Polling Worker on target table <strong className="text-cyan-300">{activeTable}</strong>
          </p>
        </div>

        {/* Dedicated Sub-Tabs for INSERT, UPDATE, DELETE & 1-CLICK */}
        <div className="bg-slate-950 p-1 rounded-lg border border-slate-800 flex items-center gap-1">
          <button
            type="button"
            onClick={() => setSubTab('insert')}
            className={`px-3 py-1.5 text-xs font-bold rounded transition-all flex items-center gap-1.5 ${
              subTab === 'insert'
                ? 'bg-emerald-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Plus size={13} />
            Insert
          </button>
          <button
            type="button"
            onClick={() => setSubTab('update')}
            className={`px-3 py-1.5 text-xs font-bold rounded transition-all flex items-center gap-1.5 ${
              subTab === 'update'
                ? 'bg-amber-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Edit3 size={13} />
            Update
          </button>
          <button
            type="button"
            onClick={() => setSubTab('delete')}
            className={`px-3 py-1.5 text-xs font-bold rounded transition-all flex items-center gap-1.5 ${
              subTab === 'delete'
                ? 'bg-rose-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Trash2 size={13} />
            Delete
          </button>
          <button
            type="button"
            onClick={() => setSubTab('quick')}
            className={`px-3 py-1.5 text-xs font-bold rounded transition-all flex items-center gap-1.5 ${
              subTab === 'quick'
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Zap size={13} />
            1-Click
          </button>
        </div>
      </div>

      {/* 1. DEDICATED INSERT TAB */}
      {subTab === 'insert' && (
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
              <Plus size={14} />
              Insert New Record into '{activeTable}'
            </h4>
            <span className="text-[10px] text-slate-500">Auto-discovered schema fields</span>
          </div>

          {loadingSchema ? (
            <div className="text-xs text-slate-400 py-4 text-center">Inspecting column schema...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {schemaColumns.map((col) => (
                <div key={col.name} className="space-y-1">
                  <label className="text-[11px] font-bold text-slate-300 flex items-center justify-between">
                    <span className="capitalize">{col.name.replace('_', ' ')}</span>
                    <span className="text-[9px] text-emerald-400/80 font-mono">[{col.type}]</span>
                  </label>
                  <input
                    type="text"
                    value={insertFormData[col.name] || ''}
                    onChange={(e) => setInsertFormData(prev => ({ ...prev, [col.name]: e.target.value }))}
                    placeholder={getSmartPlaceholder(col.name, col.type)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors font-mono"
                  />
                  <span className="text-[10px] text-slate-500 block font-mono">
                    Format: {getSmartPlaceholder(col.name, col.type)}
                  </span>
                </div>
              ))}
            </div>
          )}

          <div className="pt-2">
            <button
              onClick={() => handleSimulate('INSERT')}
              disabled={loading !== null}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs rounded-lg transition-colors flex items-center gap-2 shadow-lg shadow-emerald-600/20 disabled:opacity-50"
            >
              {loading === 'INSERT' ? (
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              ) : (
                <Plus size={14} />
              )}
              Submit INSERT Record
            </button>
          </div>
        </div>
      )}

      {/* 2. DEDICATED UPDATE TAB */}
      {subTab === 'update' && (
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
              <Edit3 size={14} />
              Update Existing Record in '{activeTable}'
            </h4>
            <span className="text-[10px] text-slate-500">Select record ID from database</span>
          </div>

          {/* Record Selector Dropdown */}
          <div className="space-y-1">
            <label className="text-[11px] font-bold text-slate-300 block">Select Record ID to Update</label>
            {loadingRecords ? (
              <div className="text-xs text-slate-400 py-1">Fetching target table records...</div>
            ) : existingRecords.length === 0 ? (
              <div className="text-xs text-amber-400 py-1">No existing records found in table '{activeTable}'. Insert a record first.</div>
            ) : (
              <select
                value={selectedRecordId}
                onChange={(e) => handleRecordSelect(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-amber-500 font-mono"
              >
                {existingRecords.map((rec, i) => {
                  const idVal = rec[pkCol] ?? rec.id ?? Object.values(rec)[0];
                  const labelVal = rec.email || rec.name || rec.full_name || rec.account_number || `Record #${idVal}`;
                  return (
                    <option key={i} value={idVal}>
                      Record #{idVal} — ({labelVal})
                    </option>
                  );
                })}
              </select>
            )}
          </div>

          {/* Dynamic Editable Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
            {schemaColumns.map((col) => (
              <div key={col.name} className="space-y-1">
                <label className="text-[11px] font-bold text-slate-300 flex items-center justify-between">
                  <span className="capitalize">{col.name.replace('_', ' ')}</span>
                  <span className="text-[9px] text-amber-400/80 font-mono">[{col.type}]</span>
                </label>
                <input
                  type="text"
                  value={updateFormData[col.name] || ''}
                  onChange={(e) => setUpdateFormData(prev => ({ ...prev, [col.name]: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-amber-500 transition-colors font-mono"
                />
              </div>
            ))}
          </div>

          <div className="pt-2">
            <button
              onClick={() => handleSimulate('UPDATE')}
              disabled={loading !== null || existingRecords.length === 0}
              className="px-5 py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-extrabold text-xs rounded-lg transition-colors flex items-center gap-2 shadow-lg shadow-amber-600/20 disabled:opacity-50"
            >
              {loading === 'UPDATE' ? (
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              ) : (
                <Edit3 size={14} />
              )}
              Submit UPDATE Record #{selectedRecordId}
            </button>
          </div>
        </div>
      )}

      {/* 3. DEDICATED DELETE TAB */}
      {subTab === 'delete' && (
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-2">
              <Trash2 size={14} />
              Safely Delete Record from '{activeTable}'
            </h4>
            <span className="text-[10px] text-slate-500">Tests Change Deletion Detection</span>
          </div>

          {/* Record Selector Dropdown for Delete */}
          <div className="space-y-1">
            <label className="text-[11px] font-bold text-slate-300 block">Select Record ID to Delete</label>
            {loadingRecords ? (
              <div className="text-xs text-slate-400 py-1">Fetching target table records...</div>
            ) : existingRecords.length === 0 ? (
              <div className="text-xs text-amber-400 py-1">No records available to delete in '{activeTable}'.</div>
            ) : (
              <select
                value={selectedRecordId}
                onChange={(e) => setSelectedRecordId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-rose-500 font-mono"
              >
                {existingRecords.map((rec, i) => {
                  const idVal = rec[pkCol] ?? rec.id ?? Object.values(rec)[0];
                  const labelVal = rec.email || rec.name || rec.full_name || rec.account_number || `Record #${idVal}`;
                  return (
                    <option key={i} value={idVal}>
                      Record #{idVal} — ({labelVal})
                    </option>
                  );
                })}
              </select>
            )}
          </div>

          <div className="pt-2">
            <button
              onClick={() => handleSimulate('DELETE')}
              disabled={loading !== null || existingRecords.length === 0}
              className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-extrabold text-xs rounded-lg transition-colors flex items-center gap-2 shadow-lg shadow-rose-600/20 disabled:opacity-50"
            >
              {loading === 'DELETE' ? (
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              ) : (
                <Trash2 size={14} />
              )}
              Confirm DELETE Record #{selectedRecordId}
            </button>
          </div>
        </div>
      )}

      {/* 4. 1-CLICK AUTO TAB */}
      {subTab === 'quick' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <button
            onClick={() => handleSimulate('INSERT')}
            disabled={loading !== null}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 rounded-lg font-bold text-xs transition-all disabled:opacity-50"
          >
            {loading === 'INSERT' ? (
              <span className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <Plus size={14} />
            )}
            Simulate 1-Click INSERT
          </button>

          <button
            onClick={() => handleSimulate('UPDATE')}
            disabled={loading !== null}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/40 rounded-lg font-bold text-xs transition-all disabled:opacity-50"
          >
            {loading === 'UPDATE' ? (
              <span className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <Edit3 size={14} />
            )}
            Simulate 1-Click UPDATE
          </button>

          <button
            onClick={() => handleSimulate('DELETE')}
            disabled={loading !== null}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 rounded-lg font-bold text-xs transition-all disabled:opacity-50"
          >
            {loading === 'DELETE' ? (
              <span className="w-4 h-4 border-2 border-rose-400 border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <Trash2 size={14} />
            )}
            Simulate 1-Click DELETE
          </button>
        </div>
      )}

      {/* Log Output Message */}
      {logMessage && (
        <div className={`mt-4 p-3 rounded-lg text-xs border flex items-center gap-2 ${
          logMessage.type === 'success' ? 'bg-emerald-950/60 border-emerald-800/60 text-emerald-300' :
          logMessage.type === 'info' ? 'bg-amber-950/60 border-amber-800/60 text-amber-300' :
          'bg-rose-950/60 border-rose-800/60 text-rose-300'
        }`}>
          {logMessage.type === 'success' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
          <span>{logMessage.text}</span>
        </div>
      )}
    </div>
  );
};
