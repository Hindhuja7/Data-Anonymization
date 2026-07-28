"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ShieldCheck, Clock, ArrowLeft } from 'lucide-react';
import ApprovalWorkspace from '@/components/pipeline/ApprovalWorkspace';

export default function ApprovalPage() {
  const router = useRouter();
  const [pipelineState, setPipelineState] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/pipeline/status');
      if (response.ok) {
        const data = await response.json();
        setPipelineState(data.state || data);
      }
    } catch (error) {
      console.error('Failed to fetch pipeline status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const approvalSession = pipelineState?.approval_session || {};
  const approvalState = approvalSession?.approval_state || 
    ((pipelineState?.active_step === 7 || pipelineState?.currentStep === 7) ? 'pending' : 
     (pipelineState?.approved_policy ? 'approved' : 'none'));

  const isWaitingForApproval = approvalState === 'pending' || 
    (pipelineState && (pipelineState.status === 'paused' || pipelineState.status === 'waiting_for_approval') && (pipelineState.active_step === 7 || pipelineState.currentStep === 7));

  const isApprovedRun = approvalState === 'approved' || 
    (pipelineState && pipelineState.run_id && (pipelineState.approved_policy || pipelineState.step_results?.["7"]?.status === 'completed'));

  const approvedPolicy = pipelineState?.approved_policy || pipelineState?.generated_policy;
  const approvedCols = approvalSession?.column_policies?.length > 0 ? approvalSession.column_policies : (approvedPolicy?.column_policies || []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => router.push('/pipeline')}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 border border-slate-700 shadow"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Pipeline
        </button>

        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <h1 className="text-xl font-bold text-white">Policy Approval Workspace</h1>
        </div>
      </div>

      {isWaitingForApproval ? (
        <>
          <div className="p-4 rounded-xl border bg-amber-500/10 border-amber-500/30 text-amber-400 flex items-center justify-between shadow-lg">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 animate-pulse flex-shrink-0" />
              <div>
                <p className="text-sm font-semibold">Step 07 Admin Policy Approval Required</p>
                <p className="text-xs text-slate-300 mt-0.5">
                  The 17-step pipeline is currently paused at Step 7 for target table <strong className="text-amber-200 font-mono">{pipelineState?.target_table || 'employees'}</strong>.
                </p>
              </div>
            </div>
            <span className="text-xs font-mono bg-amber-950 text-amber-300 px-3 py-1 rounded border border-amber-800 font-semibold">
              STEP 07 PAUSED
            </span>
          </div>

          <ApprovalWorkspace 
            onClose={() => fetchStatus()} 
            state={pipelineState} 
          />
        </>
      ) : isApprovedRun ? (
        <div className="space-y-6">
          {/* Read-Only Approved Banner */}
          <div className="p-5 rounded-xl border bg-emerald-500/10 border-emerald-500/30 text-emerald-400 flex items-center justify-between shadow-xl">
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-6 h-6 text-emerald-400 flex-shrink-0" />
              <div>
                <p className="text-base font-bold text-white">Policy Status: APPROVED (Immutable Snapshot)</p>
                <p className="text-xs text-slate-300 mt-0.5">
                  Run ID <strong className="text-emerald-300 font-mono">{pipelineState.run_id}</strong> • Target Table <strong className="text-blue-300 font-mono">{pipelineState.target_table}</strong> • Pipeline is executing Steps 8–17.
                </p>
              </div>
            </div>
            <span className="text-xs font-mono bg-emerald-950 text-emerald-300 px-3 py-1.5 rounded-lg border border-emerald-800 font-bold uppercase tracking-wider">
              APPROVED
            </span>
          </div>

          {/* Approved Snapshot Summary Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 shadow-xl">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pb-4 border-b border-slate-800">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">Run ID</span>
                <span className="text-white font-bold font-mono text-sm">{pipelineState.run_id}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">Target Table</span>
                <span className="text-blue-400 font-bold font-mono text-sm">{pipelineState.target_table}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">Approved Risk Score</span>
                <span className="text-amber-400 font-bold font-mono text-sm">{pipelineState.risk_score !== null ? pipelineState.risk_score : '—'}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">Approved Privacy Score</span>
                <span className="text-emerald-400 font-bold font-mono text-sm">{pipelineState.privacy_score !== null ? pipelineState.privacy_score : (pipelineState.privacyScore || '—')}</span>
              </div>
            </div>

            {/* Read-Only Column Policy Table */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Approved Anonymization Rules</h3>
              <div className="overflow-x-auto border border-slate-800 rounded-lg">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase text-[10px]">
                    <tr>
                      <th className="p-3">Column Name</th>
                      <th className="p-3">PII Type</th>
                      <th className="p-3">Confidence</th>
                      <th className="p-3">Final Technique</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50 bg-slate-900/50 text-slate-300">
                    {approvedCols.length > 0 ? (
                      approvedCols.map((col: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-800/40">
                          <td className="p-3 font-semibold text-white">{col.column_name}</td>
                          <td className="p-3 text-amber-300">{col.pii_type || 'PII'}</td>
                          <td className="p-3 text-slate-400">{col.confidence ? `${(col.confidence * 100).toFixed(0)}%` : '90%'}</td>
                          <td className="p-3 font-bold text-emerald-400">{col.anonymization_technique || 'MASKING'}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="p-4 text-center text-slate-500">
                          No specific column policies recorded.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center space-y-3 shadow-lg">
          <ShieldCheck className="w-12 h-12 text-slate-600 mx-auto" />
          <h2 className="text-lg font-semibold text-slate-200">No Pending Approvals</h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            There is no active 17-step pipeline execution currently waiting for Admin Approval at Step 7. Start a new pipeline execution from the Pipeline page to generate a policy for review.
          </p>
        </div>
      )}
    </div>
  );
}
