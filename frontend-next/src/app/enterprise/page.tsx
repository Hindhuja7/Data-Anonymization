"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ShieldCheck, Building2, Scale, Cpu, Sparkles, ArrowLeft, Database, Info } from 'lucide-react';

export default function EnterprisePage() {
  const router = useRouter();
  const [pipelineState, setPipelineState] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
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
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const step3Result = pipelineState?.step_results?.["3"] || null;
  const enterpriseInfo = pipelineState?.enterprise_info || step3Result?.details || null;

  const targetTable = pipelineState?.target_table || step3Result?.details?.target_table || 'employees';
  const enterpriseType = enterpriseInfo?.enterprise_type || step3Result?.details?.enterprise_type || null;
  const classificationSource = enterpriseInfo?.classification_source || (enterpriseInfo?.confidence !== undefined ? 'AI' : 'unavailable');
  const confidence = (enterpriseInfo?.confidence !== undefined && enterpriseInfo?.confidence !== null)
    ? (enterpriseInfo.confidence * 100).toFixed(1)
    : null;
  const complianceLaw = enterpriseInfo?.compliance_law || 'DPDP Act 2023';
  const reasoning = enterpriseInfo?.reasoning || step3Result?.summary || null;
  const runId = pipelineState?.run_id || 'Idle';

  const sourceLabel = classificationSource === 'AI' ? 'AI' : classificationSource === 'local_heuristic' ? 'Local Heuristic' : 'Unavailable';
  const confidenceSubtitle = classificationSource === 'AI' ? 'AI Schema Detection Confidence' : classificationSource === 'local_heuristic' ? 'Heuristic Matching Confidence' : 'AI Classification Unavailable';

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => router.push('/pipeline')}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-900 text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 border border-slate-200 shadow"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Pipeline
        </button>

        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-50 text-blue-600 rounded-lg border border-blue-200">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Enterprise Domain Classification</h1>
            <p className="text-xs text-slate-500">Authoritative Step-3 AI Domain Detection</p>
          </div>
        </div>
      </div>

      {!enterpriseType ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center space-y-4">
          <Info className="w-8 h-8 text-slate-500 mx-auto" />
          <h3 className="text-sm font-bold text-slate-600">No Enterprise Analysis Available</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            No enterprise detection analysis has been performed for the current run <span className="font-mono text-slate-600">({runId})</span> yet. Start the pipeline to execute Step 3.
          </p>
        </div>
      ) : (
        <>
          {/* Top Run Metadata Bar */}
          <div className="bg-white border border-slate-200 p-4 rounded-xl flex items-center justify-between font-mono text-xs">
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">Active Run ID</span>
              <span className="text-slate-900 font-bold">{runId}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">Target Table</span>
              <span className="text-blue-600 font-bold">{targetTable}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">Detection Status</span>
              <span className="text-emerald-600 font-bold">COMPLETED (STEP 03)</span>
            </div>
          </div>

          {/* Main Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Detected Domain</span>
                <Sparkles className="w-4 h-4 text-blue-600" />
              </div>
              <p className="text-xl font-extrabold text-blue-600 font-mono tracking-wide uppercase">{enterpriseType}</p>
              <p className="text-[11px] text-slate-500">Target Table Domain Classification ({sourceLabel})</p>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Confidence Score</span>
                <Cpu className="w-4 h-4 text-emerald-600" />
              </div>
              <p className="text-xl font-extrabold text-emerald-600 font-mono tracking-wide">{confidence ? `${confidence}%` : '—'}</p>
              <p className="text-[11px] text-slate-500">{confidenceSubtitle}</p>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Applicable Law</span>
                <Scale className="w-4 h-4 text-purple-600" />
              </div>
              <p className="text-sm font-bold text-purple-700 font-mono leading-tight">{complianceLaw}</p>
              <p className="text-[11px] text-slate-500">Mandatory Statutory Regulation</p>
            </div>
          </div>

          {/* Reasoning Section */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-200">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Step-3 Enterprise Analysis Rationale</h2>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 leading-relaxed text-xs font-mono text-slate-600 space-y-2">
              <p className="text-blue-600">// Authoritative Step 3 Output Log for table '{targetTable}':</p>
              <p>{reasoning}</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
