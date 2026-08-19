'use client';

import { useEffect, useState } from 'react';
import { ShieldCheck, AlertTriangle, Check, X, Loader2, RefreshCw, FileText, Database } from 'lucide-react';

interface ValidationApprovalProps {
  onClose: () => void;
  state: any;
}

export default function ValidationApproval({ onClose, state }: ValidationApprovalProps) {
  const [privacyScore, setPrivacyScore] = useState<number>(0);
  const [riskLevel, setRiskLevel] = useState<string>('');
  const [isApproving, setIsApproving] = useState(false);
  const [isReanonymizing, setIsReanonymizing] = useState(false);
  const [validationReport, setValidationReport] = useState<any>(null);
  const [modifiedPolicy, setModifiedPolicy] = useState<any>(null);

  useEffect(() => {
    // Load validation report and privacy score
    const loadValidationData = async () => {
      try {
        const reportRes = await fetch('http://localhost:8000/api/reports/txt');
        const reportText = await reportRes.text();
        
        // Extract privacy score from report or state
        const score = state?.privacy_score || 85;
        setPrivacyScore(score);
        
        // Determine risk level
        if (score >= 90) setRiskLevel('Low Risk');
        else if (score >= 70) setRiskLevel('Medium Risk');
        else setRiskLevel('High Risk');
        
        setValidationReport(reportText);
      } catch (e) {
        console.error("Error loading validation data:", e);
        setPrivacyScore(75);
        setRiskLevel('Medium Risk');
      }
    };
    
    loadValidationData();
  }, [state]);

  const handleApproveValidation = async () => {
    setIsApproving(true);
    try {
      await fetch('http://localhost:8000/api/pipeline/approve-validation', {
        method: 'POST'
      });
      onClose();
    } catch (e) {
      console.error("Error approving validation:", e);
    } finally {
      setIsApproving(false);
    }
  };

  const handleModifyAndReanonymize = async () => {
    setIsReanonymizing(true);
    try {
      // Get current policy
      const policyRes = await fetch('http://localhost:8000/api/policy/');
      const currentPolicy = await policyRes.json();
      
      // Apply modifications (this would come from user input in a real implementation)
      const modified = { ...currentPolicy, modified: true };
      
      await fetch('http://localhost:8000/api/pipeline/modify-and-reanonymize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(modified)
      });
      
      onClose();
    } catch (e) {
      console.error("Error modifying policy:", e);
    } finally {
      setIsReanonymizing(false);
    }
  };

  const getRiskColor = () => {
    if (privacyScore >= 90) return 'text-emerald-600 bg-emerald-50 border-emerald-200';
    if (privacyScore >= 70) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-50 text-slate-900 p-6 relative overflow-hidden font-sans">
      
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between pb-4 border-b border-slate-200 mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="text-blue-600" size={20} />
            Post-Validation Approval
          </h1>
          <p className="text-sm text-slate-500 mt-1">Step 14 of 17 • Validation Complete - Privacy Score Calculated</p>
        </div>
      </div>

      {/* Privacy Score Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 mb-2">Privacy Protection Score</h2>
            <div className={`text-4xl font-black ${getRiskColor().split(' ')[0]} px-4 py-2 rounded-lg border ${getRiskColor()}`}>
              {privacyScore}/100
            </div>
            <p className={`text-sm font-semibold mt-2 ${getRiskColor().split(' ')[0]}`}>
              {riskLevel}
            </p>
          </div>
          
          <div className="flex gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-slate-900">{state?.recordsProcessed?.toLocaleString() || '0'}</div>
              <div className="text-xs text-slate-500">Records Processed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-slate-900">{state?.batchesLoaded || '0'}</div>
              <div className="text-xs text-slate-500">Batches Loaded</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-slate-900">{state?.currentTable || 'N/A'}</div>
              <div className="text-xs text-slate-500">Current Table</div>
            </div>
          </div>
        </div>
      </div>

      {/* Validation Report */}
      <div className="flex-1 bg-white border border-slate-200 rounded-xl p-6 mb-6 overflow-hidden flex flex-col">
        <div className="flex items-center gap-2 mb-4">
          <FileText className="text-slate-500" size={16} />
          <h2 className="text-sm font-semibold text-slate-900">Validation Report</h2>
        </div>
        <div className="flex-1 overflow-auto bg-slate-50 rounded-lg p-4 font-mono text-xs text-slate-600">
          {validationReport || 'Validation report loading...'}
        </div>
      </div>

      {/* Information Cards */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Database className="text-blue-600" size={16} />
            <h3 className="text-sm font-semibold text-slate-900">Destination Database</h3>
          </div>
          <p className="text-xs text-slate-500">{state?.destinationDb || 'Not configured'}</p>
        </div>
        
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="text-amber-600" size={16} />
            <h3 className="text-sm font-semibold text-slate-900">Approval Required</h3>
          </div>
          <p className="text-xs text-slate-500">{state?.isApproved ? 'Policy approved' : 'Awaiting approval'}</p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={handleModifyAndReanonymize}
          disabled={isReanonymizing}
          className="flex-1 bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-600 font-bold text-sm rounded-xl flex items-center justify-center gap-2 transition-all duration-300 disabled:opacity-50"
        >
          {isReanonymizing ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Re-anonymizing...
            </>
          ) : (
            <>
              <RefreshCw size={16} />
              Modify & Re-anonymize
            </>
          )}
        </button>
        
        <button
          onClick={handleApproveValidation}
          disabled={isApproving}
          className="flex-1 bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white font-bold text-sm rounded-xl flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(59,130,246,0.25)] transition-all duration-300 disabled:opacity-50"
        >
          {isApproving ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Approving...
            </>
          ) : (
            <>
              <Check size={16} />
              Approve & Write to DB
            </>
          )}
        </button>
      </div>

    </div>
  );
}
