'use client';

import { useState, useEffect } from 'react';
import { ShieldCheck, X, Check, Loader2, Database, Eye, EyeOff } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ApprovalModal({ isOpen, onClose }: ApprovalModalProps) {
  const [columns, setColumns] = useState<any[]>([]);
  const [samples, setSamples] = useState<Record<string, any[]>>({});
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'policy' | 'samples'>('policy');
  const [showAnonymized, setShowAnonymized] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      
      // Fetch Policy Configuration
      const fetchPolicy = fetch('/api/pipeline/policy')
        .then((res) => res.json())
        .then((data) => {
          if (data && data.column_policies) {
            setColumns(data.column_policies);
          }
        })
        .catch((e) => console.error("Error loading policy:", e));

      // Fetch Sample Data
      const fetchSamples = fetch('/api/pipeline/samples')
        .then((res) => res.json())
        .then((data) => {
          setSamples(data);
          const tables = Object.keys(data);
          if (tables.length > 0) {
            setSelectedTable(tables[0]);
          }
        })
        .catch((e) => console.error("Error loading samples:", e));

      Promise.all([fetchPolicy, fetchSamples]).finally(() => setIsLoading(false));
    }
  }, [isOpen]);

  const handleTechniqueChange = (index: number, technique: string) => {
    const updated = [...columns];
    updated[index] = { ...updated[index], anonymization_technique: technique };
    setColumns(updated);
  };

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      // 1. Save modified policies to backend
      await fetch('/api/pipeline/policy/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ column_policies: columns }),
      });

      // 2. Signal execution resumption
      await fetch('/api/pipeline/approve', { method: 'POST' });

      // 3. Close sign-off modal
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper function to anonymize preview data on the fly based on current selected techniques
  const getAnonymizedValue = (columnName: string, tableName: string, rawValue: any) => {
    if (rawValue === null || rawValue === undefined) return rawValue;
    
    // Find matching column configuration rule
    const rule = columns.find(
      (col) => col.table_name.toLowerCase() === tableName.toLowerCase() && 
               col.column_name.toLowerCase() === columnName.toLowerCase()
    );
    
    if (!rule || rule.anonymization_technique === 'NO_CHANGE') {
      return rawValue;
    }
    
    const tech = rule.anonymization_technique;
    const strVal = String(rawValue);
    
    if (tech === 'MASK_EMAIL') {
      const parts = strVal.split('@');
      if (parts.length === 2) {
        const name = parts[0];
        const domain = parts[1];
        if (name.length > 2) {
          return `${name.substring(0, 2)}***@${domain}`;
        }
        return `***@${domain}`;
      }
      return '***';
    }
    
    if (tech === 'HASH_HMAC') {
      // Returns a mock SHA-256 hash representation
      return 'e3b0c44298fc1c149afbf4c8996f...';
    }
    
    if (tech === 'PERTURBATION') {
      const num = Number(rawValue);
      if (!isNaN(num)) {
        // Return a stable perturbed number representing noise (+/- 10%)
        const hash = columnName.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        const percent = ((hash % 20) - 10) / 100; // stable -10% to +10%
        return Math.round(num * (1 + percent));
      }
      return rawValue;
    }
    
    if (tech === 'TOKENIZATION') {
      return `[TOK_${strVal.substring(0, 3).toUpperCase()}_948]`;
    }
    
    if (tech === 'REDACTION') {
      return '[REDACTED]';
    }
    
    return rawValue;
  };

  const sampleRows = samples[selectedTable] || [];
  const sampleHeaders = sampleRows.length > 0 ? Object.keys(sampleRows[0]) : [];

  const liveRiskScore = columns.length > 0 ? (() => {
    let totalMaxRisk = columns.length * 30;
    let currentRisk = 0;
    columns.forEach((col) => {
      const tech = col.anonymization_technique;
      if (tech === 'NO_CHANGE') {
        currentRisk += 30;
      } else if (tech === 'PERTURBATION') {
        currentRisk += 8;
      } else if (tech === 'MASK_EMAIL') {
        currentRisk += 4;
      } else if (tech === 'HASH_HMAC') {
        currentRisk += 3;
      } else if (tech === 'TOKENIZATION') {
        currentRisk += 2;
      } else if (tech === 'REDACTION') {
        currentRisk += 1;
      } else {
        currentRisk += 5;
      }
    });
    const score = Math.round((currentRisk / totalMaxRisk) * 100);
    return Math.min(Math.max(score, 8), 95);
  })() : 78;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-hidden">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-slate-900/50 backdrop-blur-md"
          />

          {/* Modal Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3 }}
            className="relative w-full max-w-4xl bg-white border border-slate-200 rounded-2xl shadow-[0_0_50px_rgba(79,124,255,0.15)] flex flex-col max-h-[85vh] overflow-hidden z-10"
          >
            {/* Header */}
            <div className="p-6 border-b border-slate-200 flex justify-between items-center bg-slate-50 flex-shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center border border-amber-500/20">
                  <ShieldCheck size={22} className="animate-pulse" />
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-extrabold text-slate-900 tracking-tight">Compliance & Policy Sign-off</h2>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase border tracking-wider flex items-center gap-1 ${
                      liveRiskScore > 70
                        ? 'bg-red-50 text-red-600 border-red-200'
                        : liveRiskScore > 30
                        ? 'bg-amber-50 text-amber-600 border-amber-200'
                        : 'bg-emerald-50 text-emerald-600 border-emerald-200'
                    }`}>
                      Live Privacy Risk: {liveRiskScore} / 100
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">Review detected PII columns and customize anonymization rules</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-900 flex items-center justify-center transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            {/* Tab Controls */}
            {!isLoading && (
              <div className="px-6 pt-4 flex gap-2 border-b border-slate-200 bg-slate-50 flex-shrink-0">
                <button
                  onClick={() => setActiveTab('policy')}
                  className={`px-4 py-2 text-xs font-bold transition-all border-b-2 -mb-[2px] ${
                    activeTab === 'policy'
                      ? 'border-blue-500 text-blue-600 font-extrabold'
                      : 'border-transparent text-slate-500 hover:text-slate-900'
                  }`}
                >
                  Anonymization Policies
                </button>
                <button
                  onClick={() => setActiveTab('samples')}
                  className={`px-4 py-2 text-xs font-bold transition-all border-b-2 -mb-[2px] ${
                    activeTab === 'samples'
                      ? 'border-blue-500 text-blue-600 font-extrabold'
                      : 'border-transparent text-slate-500 hover:text-slate-900'
                  }`}
                >
                  Privacy Safe Row Samples (Step 4)
                </button>
              </div>
            )}

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto p-6 min-h-0 bg-slate-50">
              {isLoading ? (
                <div className="flex h-48 w-full items-center justify-center text-slate-500 gap-2">
                  <Loader2 className="animate-spin text-blue-600" size={20} />
                  <span className="text-sm font-semibold">Loading active configuration and sample rows...</span>
                </div>
              ) : activeTab === 'policy' ? (
                /* Policies Tab */
                columns.length === 0 ? (
                  <div className="text-center py-12 text-slate-500 text-sm">
                    No columns configured in the anonymization policy.
                  </div>
                ) : (
                  <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-slate-50 text-slate-500 border-b border-slate-200 font-bold uppercase tracking-wider text-[10px]">
                          <th className="p-3.5 pl-4">Target Table</th>
                          <th className="p-3.5">Column Reference</th>
                          <th className="p-3.5">PII Category</th>
                          <th className="p-3.5 pr-4 text-right">Anonymization Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 text-slate-600">
                        {columns.map((col, index) => (
                          <tr key={index} className="hover:bg-slate-50 transition-colors">
                            <td className="p-3.5 pl-4 font-bold text-slate-900">{col.table_name}</td>
                            <td className="p-3.5 font-mono text-blue-600">{col.column_name}</td>
                            <td className="p-3.5">
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-600 border border-blue-200 uppercase">
                                {col.pii_type}
                              </span>
                            </td>
                            <td className="p-3.5 pr-4 text-right">
                              <select
                                value={col.anonymization_technique}
                                onChange={(e) => handleTechniqueChange(index, e.target.value)}
                                className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-xs text-slate-900 focus:outline-none focus:border-blue-500 cursor-pointer hover:border-slate-300 transition-all font-semibold font-mono"
                              >
                                <option value="NO_CHANGE">NO_CHANGE</option>
                                <option value="MASK_EMAIL">MASK_EMAIL</option>
                                <option value="HASH_HMAC">HASH_HMAC</option>
                                <option value="PERTURBATION">PERTURBATION</option>
                                <option value="TOKENIZATION">TOKENIZATION</option>
                                <option value="REDACTION">REDACTION</option>
                              </select>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )
              ) : (
                /* Samples Tab */
                Object.keys(samples).length === 0 ? (
                  <div className="text-center py-12 text-slate-500 text-sm">
                    No database samples available.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Controls Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50 border border-slate-200 rounded-xl p-3.5">
                      <div className="flex items-center gap-3">
                        <Database size={16} className="text-blue-600" />
                        <span className="text-xs text-slate-600 font-semibold">Select Table Sample:</span>
                        <select
                          value={selectedTable}
                          onChange={(e) => setSelectedTable(e.target.value)}
                          className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:border-blue-500 cursor-pointer font-bold transition-all hover:border-slate-300"
                        >
                          {Object.keys(samples).map((tbl) => (
                            <option key={tbl} value={tbl}>
                              {tbl} ({samples[tbl].length} rows)
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Live Toggle Switch */}
                      <button
                        onClick={() => setShowAnonymized(!showAnonymized)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-bold transition-all ${
                          showAnonymized 
                            ? 'bg-emerald-50 border-emerald-200 text-emerald-600 shadow-sm' 
                            : 'bg-slate-100 border-slate-200 text-slate-500 hover:text-slate-900'
                        }`}
                      >
                        {showAnonymized ? (
                          <>
                            <Eye size={14} />
                            Anonymized Preview Active
                          </>
                        ) : (
                          <>
                            <EyeOff size={14} />
                            Showing Raw Production Data
                          </>
                        )}
                      </button>
                    </div>

                    {/* Table Render */}
                    {sampleRows.length === 0 ? (
                      <div className="text-center py-12 text-slate-500 text-sm">
                        No rows found for table "{selectedTable}".
                      </div>
                    ) : (
                      <div className="border border-slate-200 rounded-xl overflow-x-auto bg-white max-h-[45vh]">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead>
                            <tr className="bg-slate-50 text-slate-500 border-b border-slate-200 font-bold uppercase tracking-wider text-[10px]">
                              {sampleHeaders.map((h) => (
                                <th key={h} className="p-3.5 whitespace-nowrap">{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-200 text-slate-600">
                            {sampleRows.map((row, idx) => (
                              <tr key={idx} className="hover:bg-slate-50 transition-colors">
                                {sampleHeaders.map((h) => (
                                  <td key={h} className="p-3.5 font-mono text-[11px] whitespace-nowrap">
                                    {row[h] === null ? (
                                      <span className="text-red-400/50 font-bold uppercase text-[9px] bg-red-400/5 px-1 py-0.5 rounded border border-red-400/10">NULL</span>
                                    ) : showAnonymized ? (
                                      <span className={getAnonymizedValue(h, selectedTable, row[h]) !== row[h] ? "text-emerald-400 font-semibold" : ""}>
                                        {String(getAnonymizedValue(h, selectedTable, row[h]))}
                                      </span>
                                    ) : (
                                      <span>{String(row[h])}</span>
                                    )}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )
              )}
            </div>

            {/* Actions */}
            <div className="p-6 border-t border-slate-200 bg-slate-50 flex justify-end gap-3 flex-shrink-0">
              <button
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-slate-200 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={isSubmitting || isLoading}
                className="px-5 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold text-xs rounded-xl flex items-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.25)] hover:shadow-[0_0_25px_rgba(16,185,129,0.35)] transition-all duration-300 disabled:opacity-50 active:scale-95"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    Executing Sign-off...
                  </>
                ) : (
                  <>
                    <Check size={14} />
                    Approve & Resume Pipeline
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
