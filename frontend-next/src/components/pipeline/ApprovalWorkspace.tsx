"use client";

import React, { useState, useEffect } from 'react';
import { ShieldCheck, Database, Filter, ArrowUpDown, ChevronDown, CheckCircle2, RefreshCw, XCircle, AlertTriangle, HelpCircle, Save, Check } from 'lucide-react';

interface PolicyColumn {
  table_name: string;
  column_name: string;
  is_pii: boolean;
  pii_type: string;
  confidence: number;
  anonymization_technique: string;
  reason?: string;
  is_primary_key?: boolean;
  is_foreign_key?: boolean;
  data_type?: string;
  is_modified?: boolean;
  modified_by?: string;
  modified_at?: string;
  original_pii_type?: string;
  original_technique?: string;
}

interface ApprovalWorkspaceProps {
  onClose?: () => void;
  state?: any;
}

export default function ApprovalWorkspace({ onClose, state }: ApprovalWorkspaceProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [isApprovedState, setIsApprovedState] = useState(false);
  const [rawPolicy, setRawPolicy] = useState<any>(null);
  const [allPolicyColumns, setAllPolicyColumns] = useState<PolicyColumn[]>([]);
  const [columns, setColumns] = useState<PolicyColumn[]>([]);
  const [samples, setSamples] = useState<Record<string, any[]>>({});
  const [selectedTable, setSelectedTable] = useState<string>('');

  // Dynamic Risk & Privacy Score State
  const [currentScore, setCurrentScore] = useState<number | null>(null);
  const [previousScore, setPreviousScore] = useState<number | null>(null);
  const [privacyScore, setPrivacyScore] = useState<number | null>(null);
  const [riskLevel, setRiskLevel] = useState<string>('—');
  const [rawIntrinsicRisk, setRawIntrinsicRisk] = useState<number | null>(null);
  const [rawRiskLevel, setRawRiskLevel] = useState<string>('—');
  const [vulnerabilities, setVulnerabilities] = useState<string[]>([]);

  // Filter, Search, and Sort state
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPiiType, setFilterPiiType] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // Fetch Policy and Samples on mount
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        let policyRes = await fetch('http://localhost:8000/api/pipeline/policy');
        const policyData = await policyRes.json();
        setRawPolicy(policyData);
        
        let columnsList: PolicyColumn[] = [];
        if (policyData && policyData.column_policies) {
          columnsList = policyData.column_policies;
        } else if (policyData && policyData.tables && Array.isArray(policyData.tables)) {
          policyData.tables.forEach((t: any) => {
            if (t.columns) {
              t.columns.forEach((c: any) => {
                columnsList.push({
                  table_name: t.table_name,
                  column_name: c.column_name,
                  is_pii: c.is_pii || true,
                  pii_type: c.pii_type || 'PII',
                  confidence: c.confidence || 0.9,
                  anonymization_technique: (c.anonymization_technique || 'MASKING').toUpperCase(),
                  reason: c.reason || 'Detected sensitive column'
                });
              });
            }
          });
        }

        setAllPolicyColumns(columnsList);

        let activeTarget = state?.target_table || policyData?.target_table || policyData?.policy_metadata?.target_table;
        if (columnsList.length > 0) {
          const availableTables = Array.from(new Set(columnsList.map(c => c.table_name).filter(Boolean)));
          if (!activeTarget || (availableTables.length > 0 && !availableTables.includes(activeTarget))) {
            activeTarget = availableTables[0] || columnsList[0].table_name;
          }
        }
        setSelectedTable(activeTarget || 'accounts');

        let activeColumnsList = columnsList.filter(c => !c.table_name || c.table_name === activeTarget);
        if (activeColumnsList.length === 0 && columnsList.length > 0) {
          activeColumnsList = columnsList;
        }
        setColumns(activeColumnsList);

        // Check if policy is already approved
        if (policyData?.policy_metadata?.status === 'APPROVED' || policyData?.approval_state === 'approved') {
          setIsApprovedState(true);
        }

        // Calculate initial authoritative risk score for active target table from backend
        if (activeColumnsList.length > 0) {
          try {
            const riskRes = await fetch('http://localhost:8000/api/pipeline/recalculate-risk', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ target_table: activeTarget, column_policies: activeColumnsList })
            });
            if (riskRes.ok) {
              const riskData = await riskRes.json();
              setCurrentScore(riskData.risk_score);
              setPrivacyScore(riskData.privacy_score);
              setRiskLevel(riskData.risk_level);
              setRawIntrinsicRisk(riskData.details?.raw_intrinsic_risk !== undefined ? riskData.details.raw_intrinsic_risk : (riskData.raw_intrinsic_risk !== undefined ? riskData.raw_intrinsic_risk : null));
              setRawRiskLevel(riskData.details?.raw_risk_level || riskData.raw_risk_level || '—');
              if (riskData.details && Array.isArray(riskData.details.vulnerabilities)) {
                setVulnerabilities(riskData.details.vulnerabilities);
              }
            }
          } catch (e) {
            console.error('Initial risk calculation failed:', e);
          }
        }

        let samplesRes = await fetch('http://localhost:8000/api/pipeline/samples');
        if (samplesRes.ok) {
          const samplesData = await samplesRes.json();
          setSamples(samplesData.sample_data || {});
        }
      } catch (e) {
        console.error("Error loading workspace data:", e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleTableChange = async (newTable: string) => {
    setSelectedTable(newTable);
    const tableCols = allPolicyColumns.filter((c) => c.table_name === newTable);
    const colsToUse = tableCols.length > 0 ? tableCols : allPolicyColumns;
    setColumns(colsToUse);

    try {
      const riskRes = await fetch('http://localhost:8000/api/pipeline/recalculate-risk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_table: newTable, column_policies: colsToUse })
      });
      if (riskRes.ok) {
        const riskData = await riskRes.json();
        setCurrentScore(riskData.risk_score);
        setPrivacyScore(riskData.privacy_score);
        setRiskLevel(riskData.risk_level);
        setRawIntrinsicRisk(riskData.details?.raw_intrinsic_risk !== undefined ? riskData.details.raw_intrinsic_risk : (riskData.raw_intrinsic_risk !== undefined ? riskData.raw_intrinsic_risk : null));
        setRawRiskLevel(riskData.details?.raw_risk_level || riskData.raw_risk_level || '—');
        if (riskData.details && Array.isArray(riskData.details.vulnerabilities)) {
          setVulnerabilities(riskData.details.vulnerabilities);
        } else {
          setVulnerabilities([]);
        }
      }
    } catch (e) {
      console.error('Failed to recalculate per-table risk score:', e);
    }
  };

  const inferPiiType = (colName: string): string => {
    const colLower = colName.toLowerCase();
    if (colLower.includes('email')) return 'EMAIL';
    if (colLower.includes('phone') || colLower.includes('mobile')) return 'PHONE';
    if (colLower.includes('name')) return 'FULL_NAME';
    if (colLower.includes('aadhaar')) return 'AADHAAR';
    if (colLower.includes('pan')) return 'PAN';
    if (colLower.includes('ssn')) return 'SSN';
    if (colLower.includes('card')) return 'CREDIT_CARD';
    if (colLower.includes('dob') || colLower.includes('birth')) return 'DATE_OF_BIRTH';
    if (colLower.includes('address') || colLower.includes('city') || colLower.includes('location')) return 'LOCATION';
    if (colLower.includes('salary') || colLower.includes('balance') || colLower.includes('amount')) return 'FINANCIAL';
    if (colLower.includes('id')) return 'IDENTIFIER';
    return 'SENSITIVE';
  };

  const handlePiiTypeChange = (globalIndex: number, newPiiType: string) => {
    const updated = [...columns];
    const item = { ...updated[globalIndex] };
    const isPii = newPiiType !== 'NON_PII' && newPiiType !== 'NONE';
    item.is_pii = isPii;
    item.pii_type = isPii ? newPiiType : 'NON_PII';
    if (!isPii) {
      item.anonymization_technique = 'NO_CHANGE';
    } else if (item.anonymization_technique === 'NO_CHANGE') {
      const p = newPiiType.toUpperCase();
      if (['EMAIL', 'PHONE', 'FULL_NAME', 'NAME'].includes(p)) item.anonymization_technique = 'TOKENIZATION';
      else if (['AADHAAR', 'PAN', 'LOCATION', 'ADDRESS'].includes(p)) item.anonymization_technique = 'MASKING';
      else if (['IDENTIFIER', 'SSN', 'GSTIN', 'CREDIT_CARD'].includes(p)) item.anonymization_technique = 'HASHING';
      else item.anonymization_technique = 'DIFFERENTIAL_PRIVACY';
    }
    item.is_modified = true;
    item.modified_by = 'Dashboard Admin';
    item.modified_at = new Date().toISOString();
    updated[globalIndex] = item;
    setColumns(updated);
  };

  const handleTechniqueChange = (globalIndex: number, technique: string) => {
    const updated = [...columns];
    const item = { ...updated[globalIndex] };
    item.anonymization_technique = technique;

    // If technique is NOT NO_CHANGE and column was NON_PII, promote it to PII
    if (technique !== 'NO_CHANGE' && (!item.is_pii || item.pii_type === 'NON_PII' || item.pii_type === 'NONE')) {
      item.is_pii = true;
      item.pii_type = inferPiiType(item.column_name);
    }
    item.is_modified = true;
    item.modified_by = 'Dashboard Admin';
    item.modified_at = new Date().toISOString();
    updated[globalIndex] = item;
    setColumns(updated);
  };

  const handleModifyPolicy = async () => {
    setIsRecalculating(true);
    const oldScore = currentScore;
    try {
      const res = await fetch('http://localhost:8000/api/pipeline/policy/modify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          run_id: rawPolicy?.run_id || rawPolicy?.policy_metadata?.run_id,
          target_table: selectedTable || rawPolicy?.policy_metadata?.target_table || 'customers',
          column_policies: columns
        })
      });
      if (res.ok) {
        const data = await res.json();
        setPreviousScore(oldScore);
        setCurrentScore(data.risk_score);
        setPrivacyScore(data.privacy_score);
        setRiskLevel(data.risk_level);
        if (data.details && Array.isArray(data.details.vulnerabilities)) {
          setVulnerabilities(data.details.vulnerabilities);
        } else {
          setVulnerabilities([]);
        }
        if (data.column_policies && Array.isArray(data.column_policies) && data.column_policies.length > 0) {
          setColumns(data.column_policies);
        }
      } else {
        alert("Unable to recalculate policy scores. Your changes have not been approved.");
      }
    } catch (err) {
      console.error('Error modifying policy:', err);
      alert("Unable to recalculate policy scores. Your changes have not been approved.");
    } finally {
      setIsRecalculating(false);
    }
  };

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      const approveRes = await fetch('http://localhost:8000/api/pipeline/approve', { method: 'POST' });
      if (approveRes.ok) {
        setIsApprovedState(true);
      } else {
        const errData = await approveRes.json();
        alert('Approval failed: ' + (errData.detail || 'unknown error'));
      }
    } catch (e: any) {
      alert('Error during approval: ' + e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    try {
      const response = await fetch('http://localhost:8000/api/pipeline/stop', { method: 'POST' });
      if (response.ok) {
        if (onClose) onClose();
      }
    } catch (e: any) {
      alert('Error cancelling pipeline: ' + e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const tableNames = Array.from(new Set(columns.map(c => c.table_name)));
  const activeTable = selectedTable || (tableNames.length > 0 ? tableNames[0] : 'employees');
  const tableColumns = columns.filter(c => c.table_name === activeTable);

  const filteredColumns = tableColumns.filter(c => {
    const matchesSearch = c.column_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          c.pii_type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPii = filterPiiType === 'ALL' || c.pii_type === filterPiiType;
    return matchesSearch && matchesPii;
  });

  return (
    <div className="space-y-6">
      {/* Top Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white border border-slate-200 p-4 rounded-xl">
        <div className="flex items-center gap-4">
          <div>
            <span className="text-[10px] text-slate-500 font-mono uppercase block mb-1">Target Table</span>
            {tableNames.length > 1 ? (
              <select
                value={selectedTable || activeTable}
                onChange={(e) => handleTableChange(e.target.value)}
                className="bg-slate-50 border border-slate-200 text-blue-600 text-xs font-bold font-mono rounded px-2.5 py-1 focus:outline-none focus:border-blue-500 cursor-pointer"
              >
                {tableNames.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            ) : (
              <span className="text-sm font-bold text-blue-600 font-mono">{activeTable}</span>
            )}
          </div>

          <div className="h-8 w-px bg-slate-200" />
          <div>
            <span className="text-[10px] text-slate-500 font-mono uppercase block">Active Policy Risk</span>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-amber-600 font-mono">
                {currentScore !== null ? `${currentScore.toFixed(1)} / 100` : '—'}
              </span>
              {previousScore !== null && currentScore !== null && previousScore !== currentScore && (
                <span className="text-[10px] text-slate-500 font-mono">
                  (Prev: {previousScore.toFixed(1)})
                </span>
              )}
              {isRecalculating && <RefreshCw className="w-3.5 h-3.5 text-blue-600 animate-spin" />}
            </div>
          </div>
          <div className="h-8 w-px bg-slate-200" />
          <div>
            <span className="text-[10px] text-slate-500 font-mono uppercase block">Protected Privacy Score</span>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-emerald-600 font-mono">
                {privacyScore !== null ? `${privacyScore.toFixed(1)} / 100` : '—'}
              </span>
              {isRecalculating && <span className="text-[10px] text-blue-600 animate-pulse font-mono">Recalculating...</span>}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isApprovedState ? (
            <span className="px-4 py-2 bg-emerald-50 text-emerald-600 border border-emerald-200 text-xs font-bold rounded-lg flex items-center gap-2">
              <Check className="w-4 h-4" />
              POLICY APPROVED ✓
            </span>
          ) : (
            <>
              <button
                onClick={handleModifyPolicy}
                disabled={isSubmitting || isRecalculating}
                className="px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-600 text-xs font-bold rounded-lg transition-colors flex items-center gap-2 border border-blue-200 disabled:opacity-40 shadow-sm"
              >
                {isRecalculating ? <RefreshCw className="w-4 h-4 animate-spin text-blue-600" /> : <Save className="w-4 h-4 text-blue-600" />}
                {isRecalculating ? "MODIFYING / RECALCULATING..." : "MODIFY"}
              </button>
              <button
                onClick={handleApprove}
                disabled={isSubmitting || isRecalculating}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-2 shadow-lg shadow-emerald-600/20 disabled:opacity-40"
              >
                <Check className="w-4 h-4 stroke-[3]" />
                APPROVE
              </button>
            </>
          )}
        </div>
      </div>

      {vulnerabilities.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl space-y-2">
          <div className="flex items-center gap-2 text-amber-600 text-xs font-bold font-mono uppercase">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            Detected Policy Vulnerabilities ({vulnerabilities.length})
          </div>
          <ul className="list-disc list-inside text-xs font-mono text-amber-700 space-y-1">
            {vulnerabilities.map((v, i) => (
              <li key={i}>{v}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Rules & Technique Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">PII Protection Rules</h4>
          <span className="text-[10px] font-mono text-slate-500">{filteredColumns.length} Columns</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] border-b border-slate-200">
              <tr>
                <th className="p-3">Column Name</th>
                <th className="p-3">PII Type</th>
                <th className="p-3">Confidence</th>
                <th className="p-3">Anonymization Technique</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-600">
              {filteredColumns.map((col, idx) => {
                const globalIndex = columns.findIndex(c => c.table_name === col.table_name && c.column_name === col.column_name);
                const currentPiiType = (!col.is_pii || !col.pii_type || col.pii_type === 'null') ? 'NON_PII' : col.pii_type;
                const piiOptions = Array.from(new Set([
                  currentPiiType,
                  'IDENTIFIER', 'NAME', 'EMAIL', 'PHONE', 'AADHAAR', 'PAN', 'GSTIN', 'SSN', 'CREDIT_CARD',
                  'QUASI_IDENTIFIER', 'DOB', 'AGE', 'GENDER', 'LOCATION', 'SALARY', 'BALANCE',
                  'SENSITIVE', 'FINANCIAL', 'HEALTH', 'ADDRESS', 'ACCOUNT_TYPE', 'BRANCH_NAME', 'NON_PII'
                ]));

                return (
                  <tr key={idx} className="hover:bg-slate-50 transition-colors">
                    <td className="p-3 font-semibold text-slate-900">{col.column_name}</td>
                    <td className="p-3">
                      <select
                        value={currentPiiType}
                        disabled={isApprovedState}
                        onChange={(e) => handlePiiTypeChange(globalIndex, e.target.value)}
                        className="bg-slate-50 border border-slate-200 text-blue-600 font-semibold rounded px-2 py-1 text-xs outline-none focus:border-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
                      >
                        {piiOptions.map(type => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </select>
                    </td>
                    <td className="p-3 text-slate-500">{(col.confidence * 100).toFixed(0)}%</td>
                    <td className="p-3">
                      <select
                        value={col.anonymization_technique}
                        disabled={isApprovedState}
                        onChange={(e) => handleTechniqueChange(globalIndex, e.target.value)}
                        className="bg-slate-50 border border-slate-200 text-slate-900 rounded px-2 py-1 text-xs outline-none focus:border-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
                      >
                        <option value="MASKING">MASKING</option>
                        <option value="HASHING">HASHING</option>
                        <option value="TOKENIZATION">TOKENIZATION</option>
                        <option value="ENCRYPTION">ENCRYPTION</option>
                        <option value="GENERALIZATION">GENERALIZATION</option>
                        <option value="NO_CHANGE">NO_CHANGE</option>
                      </select>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
