"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Play, Square, Check, Circle, Pause, ShieldCheck, Database, AlertTriangle, Terminal, ExternalLink, ArrowRight } from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';

interface WorkflowStep {
  id: number;
  name: string;
  status: 'completed' | 'current' | 'pending' | 'failed' | 'waiting_for_approval' | 'paused' | 'stopped';
  output?: string;
}

interface StepResult {
  step_id: number;
  step_name: string;
  status: string;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  summary: string;
  details: Record<string, any>;
}

interface LogEntry {
  id: string;
  timestamp: string;
  message: string;
  level: string;
}

const INITIAL_STEPS: WorkflowStep[] = [
  { id: 1, name: "Step 01. Connect Database", status: "pending" },
  { id: 2, name: "Step 02. Extract Schema", status: "pending" },
  { id: 3, name: "Step 03. Enterprise Detection", status: "pending" },
  { id: 4, name: "Step 04. Privacy-Safe Sampling", status: "pending" },
  { id: 5, name: "Step 05. PII Detection", status: "pending" },
  { id: 6, name: "Step 06. Policy Generation", status: "pending" },
  { id: 7, name: "Step 07. Admin Approval", status: "pending" },
  { id: 8, name: "Step 08. Redis Vault Init", status: "pending" },
  { id: 9, name: "Step 09. Change Detection", status: "pending" },
  { id: 10, name: "Step 10. Redis AOF Crash Recovery", status: "pending" },
  { id: 11, name: "Step 11. Chunk Processing", status: "pending" },
  { id: 12, name: "Step 12. Data Anonymization", status: "pending" },
  { id: 13, name: "Step 13. Destination Loading", status: "pending" },
  { id: 14, name: "Step 14. Validation Engine", status: "pending" },
  { id: 15, name: "Step 15. Safe Database Generation", status: "pending" },
  { id: 16, name: "Step 16. Audit Report Generator", status: "pending" },
  { id: 17, name: "Step 17. Output Delivery", status: "pending" },
];

export default function Pipeline() {
  const router = useRouter();
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [stopError, setStopError] = useState<string | null>(null);
  const [showStopModal, setShowStopModal] = useState(false);
  const [selectedStep, setSelectedStep] = useState<number>(1);
  const [executionTime, setExecutionTime] = useState("00:00:00");

  const logContainerRef = useRef<HTMLDivElement>(null);

  // Single Authoritative Snapshot State
  const [currentRun, setCurrentRun] = useState<{
    run_id: string | null;
    state_version: number;
    status: string;
    active_step: number;
    target_table: string;
    database_name: string;
    started_at: string | null;
    completed_at: string | null;
    elapsed_seconds?: number;
    risk_score?: number | null;
    privacy_score?: number | null;
    steps: WorkflowStep[];
    step_results: Record<string, StepResult>;
    step_12_status?: string;
    step_13_status?: string;
    approval_state?: string;
    logs: LogEntry[];
  }>({
    run_id: null,
    state_version: 0,
    status: 'idle',
    active_step: 0,
    target_table: '',
    database_name: '',
    started_at: null,
    completed_at: null,
    elapsed_seconds: 0,
    risk_score: null,
    privacy_score: null,
    steps: INITIAL_STEPS,
    step_results: {},
    logs: []
  });

  const { isConnected, onMessage } = useWebSocket('ws://localhost:8000/api/pipeline/ws');

  // Single Canonical State Normalization Function
  const syncStateWithBackend = (backendState: any) => {
    if (!backendState) return;

    const targetState = backendState.state || backendState;
    const incomingRunId = targetState.run_id || null;
    const incomingVersion = typeof targetState.state_version === 'number' ? targetState.state_version : 0;

    setCurrentRun((prevRun) => {
      if (incomingRunId && prevRun.run_id === incomingRunId && incomingVersion < prevRun.state_version) {
        return prevRun;
      }

      const activeStepNum = typeof targetState.active_step === 'number' ? targetState.active_step : 0;
      const backendStatus = targetState.status || 'idle';

      const stepsArray: WorkflowStep[] = INITIAL_STEPS.map((initStep) => {
        let stepStatus: WorkflowStep['status'] = 'pending';
        
        // Explicit lock for Step 12 (Data Anonymization) to prevent fluctuating
        if (initStep.id === 12) {
          const s12 = targetState.step_12_status || prevRun.step_12_status;
          if (s12 === 'completed') {
            stepStatus = 'completed';
          } else if (s12 === 'running' || initStep.id === activeStepNum) {
            stepStatus = 'current';
          } else if (backendStatus === 'stopped' || backendStatus === 'cancelled') {
            stepStatus = 'stopped';
          } else if (initStep.id < activeStepNum && s12 !== 'running') {
            stepStatus = 'completed';
          } else {
            stepStatus = 'pending';
          }
        }
        // Explicit lock for Step 13 (Destination Loading) to prevent fluctuating
        else if (initStep.id === 13) {
          const s13 = targetState.step_13_status || prevRun.step_13_status;
          if (s13 === 'completed') {
            stepStatus = 'completed';
          } else if (s13 === 'running' || initStep.id === activeStepNum) {
            stepStatus = 'current';
          } else if (backendStatus === 'stopped' || backendStatus === 'cancelled') {
            stepStatus = 'stopped';
          } else if (initStep.id < activeStepNum && s13 !== 'running') {
            stepStatus = 'completed';
          } else {
            stepStatus = 'pending';
          }
        }
        // Standard mapping for other steps
        else {
          if (initStep.id < activeStepNum || (initStep.id === activeStepNum && backendStatus === 'completed') || (initStep.id <= 17 && backendStatus === 'completed')) {
            stepStatus = 'completed';
          } else if (initStep.id === activeStepNum && (backendStatus === 'waiting_for_approval' || backendStatus === 'waiting')) {
            stepStatus = 'waiting_for_approval';
          } else if (initStep.id === activeStepNum && (backendStatus === 'running' || backendStatus === 'RUNNING')) {
            stepStatus = 'current';
          } else if (backendStatus === 'stopped' || backendStatus === 'cancelled' || backendStatus === 'STOPPING' || backendStatus === 'STOPPED') {
            if (initStep.id === activeStepNum) stepStatus = 'stopped';
            else if (initStep.id < activeStepNum) stepStatus = 'completed';
            else stepStatus = 'pending';
          } else if (initStep.id === activeStepNum && backendStatus === 'failed') {
            stepStatus = 'failed';
          } else {
            stepStatus = 'pending';
          }
        }

        return {
          ...initStep,
          status: stepStatus,
          output: stepStatus === 'completed' ? 'Completed' : stepStatus === 'current' ? 'Running' : stepStatus === 'stopped' ? 'Stopped' : undefined
        };
      });

      const isSameRun = incomingRunId && prevRun.run_id === incomingRunId;
      const startedAt = isSameRun
        ? (targetState.started_at !== undefined && targetState.started_at !== null ? targetState.started_at : prevRun.started_at)
        : (targetState.started_at || null);

      const completedAt = isSameRun
        ? (targetState.completed_at !== undefined && targetState.completed_at !== null ? targetState.completed_at : prevRun.completed_at)
        : (targetState.completed_at || null);

      const stepResults = isSameRun
        ? (targetState.step_results && Object.keys(targetState.step_results).length > 0 ? targetState.step_results : prevRun.step_results)
        : (targetState.step_results || {});

      // Filter out raw chunk-level trace lines for 12 & 13 and raw server stream logs
      const rawLogs = targetState.logs || prevRun.logs || [];
      const mainPipelineLogs = rawLogs.filter((logItem: any) => {
        const msg = typeof logItem === 'string' ? logItem : logItem?.message || '';
        
        // Filter out raw chunk-level trace lines for 12 & 13
        const isStep12Chunk = msg.includes('[Step 12]') || msg.includes('Applying Masking') || msg.includes('Applying Differential') || msg.includes('Applying Hashing') || msg.includes('Applying Tokenization') || msg.includes('anonymized successfully') || msg.includes('Reading Chunk');
        const isStep13Chunk = msg.includes('[Step 13]') || msg.includes('Chunk inserted') || msg.includes('Rows Loaded') || msg.includes('Processing Rate') || msg.includes('Writing Chunk') || msg.includes('COPY FROM STDIN') || msg.includes('Transaction committed');
        
        // Filter out raw server stream / HTTP request logs
        const isServerStreamLog = msg.includes('HTTP/') || msg.includes('GET /api') || msg.includes('POST /api') || msg.includes('OPTIONS /api') || msg.includes('WebSocket') || msg.includes('INFO:uvicorn') || msg.includes('INFO:fastapi') || msg.includes('INFO:database_connector') || msg.includes('INFO:polling_worker');

        return !isStep12Chunk && !isStep13Chunk && !isServerStreamLog;
      });

      // Calculate elapsed continuously for active and continuous sync states (frozen when stopped)
      let finalElapsed = Math.max(prevRun.elapsed_seconds || 0, targetState.elapsed_seconds || 0);
      const isStep17Done = backendStatus === 'completed' || activeStepNum >= 17 || targetState.step_17_status === 'completed';
      const isStoppedBackend = backendStatus === 'stopped' || backendStatus === 'cancelled' || backendStatus === 'STOPPED' || backendStatus === 'CANCELLED';
      const isActiveState = (backendStatus === 'running' || backendStatus === 'RUNNING' || backendStatus === 'waiting_for_approval' || isStep17Done) && !isStoppedBackend;
      
      if (isActiveState && startedAt) {
        const startTime = new Date(startedAt).getTime();
        if (!isNaN(startTime)) {
          finalElapsed = Math.max(finalElapsed, Math.floor((Date.now() - startTime) / 1000));
        }
      }

      return {
        run_id: incomingRunId,
        state_version: incomingVersion,
        status: backendStatus,
        active_step: activeStepNum,
        target_table: targetState.target_table || (isSameRun ? prevRun.target_table : ''),
        database_name: targetState.database_name || (isSameRun ? prevRun.database_name : ''),
        started_at: startedAt,
        completed_at: completedAt,
        elapsed_seconds: finalElapsed,
        risk_score: targetState.risk_score !== undefined ? targetState.risk_score : prevRun.risk_score,
        privacy_score: targetState.privacy_score !== undefined ? targetState.privacy_score : prevRun.privacy_score,
        steps: stepsArray,
        step_results: stepResults,
        step_12_status: targetState.step_12_status || prevRun.step_12_status,
        step_13_status: targetState.step_13_status || prevRun.step_13_status,
        logs: mainPipelineLogs
      };
    });
  };

  // Initial Fetch on Mount
  useEffect(() => {
    const fetchStatusOnMount = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/pipeline/status');
        if (response.ok) {
          const data = await response.json();
          syncStateWithBackend(data.state || data);
        }
      } catch (err) {
        console.error('Error fetching pipeline status on mount:', err);
      }
    };
    fetchStatusOnMount();
  }, []);

  // WebSocket Message Listener
  useEffect(() => {
    const cleanup = onMessage((data: any) => {
      syncStateWithBackend(data);
    });
    return cleanup;
  }, [onMessage]);

  const [displayedSeconds, setDisplayedSeconds] = useState<number>(0);

  useEffect(() => {
    if (typeof currentRun.elapsed_seconds === 'number' && currentRun.elapsed_seconds > 0) {
      setDisplayedSeconds((prev) => Math.max(prev, currentRun.elapsed_seconds!));
    }
  }, [currentRun.elapsed_seconds]);

  // Live timer interval runs ONLY during active states and FREEZES completely when stopped
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    const isStep17Done = currentRun.status === 'completed' || currentRun.active_step >= 17 || currentRun.steps.find(s => s.id === 17)?.status === 'completed';
    const isStoppedState = currentRun.status === 'stopped' || currentRun.status === 'cancelled' || currentRun.status === 'STOPPING' || currentRun.status === 'STOPPED';
    const isActiveState = (currentRun.status === 'running' || currentRun.status === 'RUNNING' || currentRun.status === 'waiting_for_approval' || isStep17Done) && !isStoppedState;
    
    if (isActiveState && currentRun.status !== 'idle') {
      timer = setInterval(() => {
        setDisplayedSeconds((prev) => Math.max(prev + 1, currentRun.elapsed_seconds || 0));
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [currentRun.status, currentRun.active_step, currentRun.steps, currentRun.elapsed_seconds]);

  useEffect(() => {
    if (displayedSeconds > 0 || (currentRun.status !== 'idle' && currentRun.status !== 'none')) {
      const hrs = Math.floor(displayedSeconds / 3600);
      const mins = Math.floor((displayedSeconds % 3600) / 60);
      const secs = displayedSeconds % 60;
      setExecutionTime(`${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`);
    } else {
      setExecutionTime("00:00:00");
    }
  }, [displayedSeconds, currentRun.status]);

  // Scroll inside log container element only when user is near bottom
  useEffect(() => {
    if (logContainerRef.current) {
      const container = logContainerRef.current;
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 120;
      if (isNearBottom) {
        container.scrollTop = container.scrollHeight;
      }
    }
  }, [currentRun.logs, currentRun.active_step]);

  // HTTP Heartbeat Polling
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('http://localhost:8000/api/pipeline/status');
        if (response.ok) {
          const data = await response.json();
          syncStateWithBackend(data.state || data);
        }
      } catch (error) {
        console.error('HTTP Status Polling error:', error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleStopPipeline = async () => {
    const activeRunId = currentRun.run_id;
    if (!activeRunId) {
      alert("No active pipeline run to stop.");
      setShowStopModal(false);
      return;
    }

    setIsStopping(true);
    setStopError(null);

    try {
      const res = await fetch('http://localhost:8000/api/pipeline/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: activeRunId })
      });

      if (!res.ok) {
        const errData = await res.json();
        setStopError(errData.detail || `Unable to stop pipeline run ${activeRunId}.`);
      } else {
        setShowStopModal(false);
      }
    } catch (e) {
      console.error('Stop error:', e);
      setStopError("Network error attempting to stop pipeline.");
    } finally {
      setIsStopping(false);
    }
  };

  const isStep17Completed = currentRun.status === 'completed' || currentRun.active_step >= 17 || currentRun.steps.find(s => s.id === 17)?.status === 'completed' || (currentRun.step_results && currentRun.step_results['17']?.status === 'completed');
  const isStopped = currentRun.status === 'stopped' || currentRun.status === 'cancelled' || currentRun.status === 'STOPPING' || currentRun.status === 'STOPPED';
  const canStop = Boolean(currentRun.run_id && !isStopped && currentRun.status !== 'failed' && currentRun.status !== 'idle');
  
  const pipelineStateLabel = isStopped
    ? 'PIPELINE STOPPED'
    : isStep17Completed
    ? 'CONTINUOUS SYNC ACTIVE'
    : currentRun.status === 'running' || currentRun.status === 'RUNNING'
    ? 'PIPELINE RUNNING'
    : currentRun.status === 'waiting_for_approval'
    ? 'WAITING APPROVAL'
    : 'IDLE';

  const workflowSteps = currentRun.steps;
  const pipelineState = currentRun;

  const completedCount = workflowSteps.filter(s => s.status === 'completed').length;
  const calculatedProgress = Math.round((completedCount / 17) * 100);

  const shouldShowStep3Report = currentRun.active_step >= 3;
  const shouldShowStep12Log = currentRun.active_step >= 12 || currentRun.step_12_status === 'running' || currentRun.step_12_status === 'completed';
  const shouldShowStep13Log = currentRun.active_step >= 13 || currentRun.step_13_status === 'running' || currentRun.step_13_status === 'completed';

  // Dynamic Log Generator based on actual step status (RUNNING... vs COMPLETED)
  const getDynamicStepLogs = (step: WorkflowStep) => {
    const isCompleted = step.status === 'completed';
    const isRunning = step.status === 'current';
    const statusLabel = isCompleted ? 'COMPLETED' : isRunning ? 'RUNNING...' : 'PENDING';

    switch (step.id) {
      case 1:
        return [
          `[STEP 1] Connect Database — ${statusLabel}`,
          "✓ Connecting to source database...",
          ...(isCompleted ? ["✓ Connection validated & authenticated successfully."] : [])
        ];
      case 2:
        return [
          `[STEP 2] Extract Schema — ${statusLabel}`,
          "✓ Extracting database schema...",
          ...(isCompleted ? ["✓ Schema extracted for target table."] : [])
        ];
      case 3:
        return [
          `[STEP 3] Enterprise Detection — ${statusLabel}`,
          "✓ Enterprise PII Scanner initialized...",
          ...(isCompleted ? ["✓ Identified sensitive PII fields across target schema."] : [])
        ];
      case 4:
        return [
          `[STEP 4] Privacy-Safe Sampling — ${statusLabel}`,
          "✓ Executing privacy-safe sampling routine...",
          ...(isCompleted ? ["✓ Sampled representative records for compliance analysis."] : [])
        ];
      case 5:
        return [
          `[STEP 5] PII Detection — ${statusLabel}`,
          "✓ Running heuristic PII classification engine...",
          ...(isCompleted ? ["✓ PII classification completed."] : [])
        ];
      case 6:
        return [
          `[STEP 6] Policy Generation — ${statusLabel}`,
          "✓ Generating optimal data protection policy...",
          ...(isCompleted ? ["✓ Draft policy generated with Tokenization, Masking, Hashing & Laplace DP."] : [])
        ];
      case 7:
        return [
          `[STEP 7] Admin Approval — ${statusLabel}`,
          "✓ Policy review authorization check...",
          ...(isCompleted ? ["✓ Policy APPROVED by Dashboard Admin."] : [])
        ];
      case 8:
        return [
          `[STEP 8] Redis Vault Init — ${statusLabel}`,
          "✓ Connecting to Redis vault instance...",
          ...(isCompleted ? ["✓ Redis Hash Vault initialized for secure token mapping storage."] : [])
        ];
      case 9:
        return [
          `[STEP 9] Change Detection — ${statusLabel}`,
          "✓ Initializing delta change detection worker...",
          ...(isCompleted ? ["✓ Change Detection active for continuous synchronization."] : [])
        ];
      case 10:
        return [
          `[STEP 10] Redis AOF Crash Recovery — ${statusLabel}`,
          "✓ Verifying append-only file (AOF) persistence log...",
          ...(isCompleted ? ["✓ Redis AOF crash recovery check completed successfully."] : [])
        ];
      case 11:
        return [
          `[STEP 11] Chunk Processing — ${statusLabel}`,
          "✓ Calculating optimal chunk size...",
          ...(isCompleted ? ["✓ Chunk Processing producer initialized."] : [])
        ];
      default:
        return [`[STEP ${step.id}] ${step.name} — ${statusLabel}`];
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Anonymization Pipeline Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time 17-step data protection and compliance execution dashboard
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs font-mono font-bold px-3 py-1.5 rounded-lg border flex items-center gap-2 ${
            isStep17Completed
              ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
              : currentRun.status === 'running' || currentRun.status === 'RUNNING'
              ? 'bg-blue-50 text-blue-600 border-blue-200'
              : 'bg-slate-100 text-slate-500 border-slate-200'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isStep17Completed ? 'bg-emerald-400 animate-ping' : 'bg-blue-400'}`}></span>
            STATE: {pipelineStateLabel}
          </span>
          <span className={`text-xs font-mono px-3 py-1.5 rounded-lg border ${
            isConnected ? 'bg-emerald-50 text-emerald-600 border-emerald-200' : 'bg-amber-50 text-amber-600 border-amber-200'
          }`}>
            {isConnected ? 'LIVE WEBSOCKET' : 'HTTP POLLING'}
          </span>
        </div>
      </div>

      {/* Observation-Only Status Toolbar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {(pipelineState?.active_step === 7 || pipelineState?.status === 'waiting_for_approval') && (
            <button
              onClick={() => router.push('/approval')}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-2 shadow-lg shadow-amber-600/20"
            >
              <ShieldCheck className="w-4 h-4" />
              Review Policy & Approve
            </button>
          )}

          <button
            onClick={() => setShowStopModal(true)}
            disabled={!canStop}
            className="px-4 py-2 bg-red-600/80 hover:bg-red-600 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Square className="w-4 h-4 fill-current" />
            Stop
          </button>
        </div>

        <div className="flex items-center gap-6 text-xs font-mono">
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Run ID</span>
            <span className="text-slate-900 font-bold">{currentRun.run_id || 'Idle'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Target Table</span>
            <span className="text-blue-600 font-bold">{pipelineState?.target_table || 'None'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Progress</span>
            <span className="text-slate-900 font-bold">{calculatedProgress}%</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Privacy Score</span>
            <span className="text-emerald-600 font-bold font-mono">
              {(pipelineState?.active_step >= 7 || pipelineState?.approval_state === 'approved') && pipelineState?.privacy_score !== undefined && pipelineState?.privacy_score !== null
                ? `${pipelineState.privacy_score}%`
                : 'Pending (Step 7)'}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Risk Score</span>
            <span className="text-amber-600 font-bold font-mono">
              {(pipelineState?.active_step >= 7 || pipelineState?.approval_state === 'approved') && pipelineState?.risk_score !== undefined && pipelineState?.risk_score !== null
                ? `${pipelineState.risk_score}`
                : 'Pending (Step 7)'}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Elapsed Time</span>
            <span className="text-slate-900 font-bold">{executionTime}</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Steps List on Left (5 cols), Complete Pipeline Summary Logs on Right (7 cols) */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        {/* Ocean Blue Section Header */}
        <div className="bg-gradient-to-r from-sky-600 to-blue-600 px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">17-Step Anonymization Pipeline</h2>
            <span className="text-xs font-mono text-white/80 bg-white/10 px-3 py-1 rounded-full border border-white/20">
              DPDP Act 2023 Compliant
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 p-6">
        
        {/* LEFT PANEL: 17 Steps List */}
        <div className="lg:col-span-5 bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Execution Lifecycle</h3>
            <span className="text-[10px] font-mono text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              {completedCount} / 17 COMPLETED
            </span>
          </div>

          <div className="space-y-2 max-h-[580px] overflow-y-auto pr-1">
            {workflowSteps.map((step) => {
              const isSelected = selectedStep === step.id;
              const isStep3 = step.id === 3 && shouldShowStep3Report;
              const isStep12 = step.id === 12 && shouldShowStep12Log;
              const isStep13 = step.id === 13 && shouldShowStep13Log;

              return (
                <div
                  key={step.id}
                  onClick={() => setSelectedStep(step.id)}
                  className={`p-3 rounded-lg cursor-pointer transition-all border ${
                    isSelected
                      ? 'bg-blue-50 border-blue-400 text-slate-900'
                      : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {step.status === 'completed' ? (
                        <div className="p-1 bg-emerald-100 text-emerald-600 rounded-full">
                          <Check className="w-3.5 h-3.5 stroke-[3]" />
                        </div>
                      ) : step.status === 'current' ? (
                        <div className="p-1 bg-blue-100 text-blue-600 rounded-full animate-spin">
                          <Circle className="w-3.5 h-3.5 stroke-[3]" />
                        </div>
                      ) : step.status === 'waiting_for_approval' ? (
                        <div className="p-1 bg-amber-100 text-amber-600 rounded-full animate-pulse">
                          <Pause className="w-3.5 h-3.5 fill-current" />
                        </div>
                      ) : step.status === 'stopped' ? (
                        <div className="p-1 bg-red-100 text-red-600 rounded-full">
                          <Square className="w-3.5 h-3.5 fill-current" />
                        </div>
                      ) : (
                        <div className="p-1 bg-slate-100 text-slate-400 rounded-full">
                          <Circle className="w-3.5 h-3.5" />
                        </div>
                      )}

                      <span className={`text-xs font-mono font-medium ${
                        step.status === 'completed' ? 'text-emerald-600 font-bold' : step.status === 'current' ? 'text-blue-600 font-bold' : 'text-slate-600'
                      }`}>
                        {step.name}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Step 3 Enterprise Detection Link */}
                      {isStep3 && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push('/reports?step=3');
                          }}
                          className="px-2 py-0.5 bg-emerald-100 hover:bg-emerald-200 text-emerald-600 text-[10px] font-mono font-semibold rounded border border-emerald-300 flex items-center gap-1 transition-all"
                        >
                          Report
                          <ExternalLink className="w-2.5 h-2.5" />
                        </button>
                      )}

                      {/* Step 12 Data Anonymization Link */}
                      {isStep12 && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push('/reports?step=12');
                          }}
                          className="px-2 py-0.5 bg-purple-100 hover:bg-purple-200 text-purple-600 text-[10px] font-mono font-semibold rounded border border-purple-300 flex items-center gap-1 transition-all"
                        >
                          Report
                          <ExternalLink className="w-2.5 h-2.5" />
                        </button>
                      )}

                      {/* Step 13 Destination Loading Link */}
                      {isStep13 && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push('/reports?step=13');
                          }}
                          className="px-2 py-0.5 bg-blue-100 hover:bg-blue-200 text-blue-600 text-[10px] font-mono font-semibold rounded border border-blue-300 flex items-center gap-1 transition-all"
                        >
                          Report
                          <ExternalLink className="w-2.5 h-2.5" />
                        </button>
                      )}

                      {/* Step 14 Validation Engine Link */}
                      {step.id === 14 && (step.status === 'completed' || currentRun.active_step >= 14) && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push('/reports?step=14');
                          }}
                          className="px-2 py-0.5 bg-emerald-100 hover:bg-emerald-200 text-emerald-600 text-[10px] font-mono font-semibold rounded border border-emerald-300 flex items-center gap-1 transition-all"
                        >
                          Report
                          <ExternalLink className="w-2.5 h-2.5" />
                        </button>
                      )}

                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                        step.status === 'completed'
                          ? 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                          : step.status === 'current'
                          ? 'bg-blue-50 text-blue-600 border border-blue-200'
                          : step.status === 'waiting_for_approval'
                          ? 'bg-amber-50 text-amber-600 border border-amber-200'
                          : step.status === 'stopped'
                          ? 'bg-red-50 text-red-600 border border-red-200'
                          : 'bg-slate-100 text-slate-500 border border-slate-200'
                      }`}>
                        {step.status === 'completed' ? 'COMPLETED' : step.status === 'current' ? 'RUNNING' : step.status === 'waiting_for_approval' ? 'WAITING APPROVAL' : step.status === 'stopped' ? 'STOPPED' : 'PENDING'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT PANEL: RESTORED PIPELINE SUMMARY LOGS STREAM */}
        <div className="lg:col-span-7 bg-slate-50 border border-slate-200 rounded-xl p-6 flex flex-col justify-between min-h-[580px]">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-sky-600" />
                <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Pipeline Summary Logs</h3>
              </div>
              <span className="text-[10px] font-mono text-sky-600 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                CHRONOLOGICAL EXECUTION HISTORY
              </span>
            </div>

            <div
              ref={logContainerRef}
              className="bg-slate-50 border border-slate-200 rounded-lg p-4 font-mono text-xs text-slate-600 max-h-[480px] overflow-y-auto space-y-3"
            >
              {/* CHRONOLOGICAL LOGS FOR ALL STEPS 1 THROUGH 17 */}
              {workflowSteps.map((step) => {
                const stepResult = currentRun.step_results[String(step.id)];
                const isStepCompleted = step.status === 'completed' || Boolean(stepResult);
                const isStepCurrent = step.status === 'current';
                const isStepActive = isStepCompleted || isStepCurrent || currentRun.active_step >= step.id || (step.id === 12 && currentRun.step_12_status === 'running') || (step.id === 13 && currentRun.step_13_status === 'running');

                if (!isStepActive) return null;

                const dynamicLogs = getDynamicStepLogs(step);
                const summaryMsg = stepResult?.summary;

                // Backend real log lines for this specific step
                const backendStepLogs = (currentRun.logs || []).filter((logItem: any) => {
                  const msg = typeof logItem === 'string' ? logItem : logItem?.message || '';
                  return msg.includes(`[Step ${step.id}]`);
                });

                return (
                  <div key={step.id} className="space-y-1 border-b border-slate-200 pb-3.5">
                    {dynamicLogs.map((line, idx) => (
                      <div
                        key={idx}
                        className={`leading-relaxed ${
                          idx === 0
                            ? step.status === 'completed' ? 'text-emerald-600 font-bold' : 'text-blue-600 font-bold animate-pulse'
                            : line.startsWith('✓')
                            ? 'text-emerald-600'
                            : 'text-slate-600'
                        }`}
                      >
                        {line}
                      </div>
                    ))}

                    {/* Backend Real Logs for this Step */}
                    {backendStepLogs.map((logItem, i) => {
                      const msg = typeof logItem === 'string' ? logItem : logItem?.message || '';
                      return (
                        <div key={i} className="text-slate-600 pl-2 text-[11px] leading-tight">
                          {msg}
                        </div>
                      );
                    })}

                    {summaryMsg && !dynamicLogs.some(l => l.includes(summaryMsg)) && (
                      <div className="text-slate-600 pl-2 text-[11px]">✓ {summaryMsg}</div>
                    )}

                    {/* Step Action Buttons */}
                    {step.id === 3 && shouldShowStep3Report && (
                      <div className="pt-1.5">
                        <button
                          onClick={() => router.push('/reports?step=3')}
                          className="px-3 py-1 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-black font-extrabold text-[11px] font-mono rounded shadow-md shadow-emerald-500/20 flex items-center gap-1.5 transition-all"
                        >
                          View Enterprise Detection →
                        </button>
                      </div>
                    )}

                    {step.id === 12 && shouldShowStep12Log && (
                      <div className="pt-1.5">
                        <button
                          onClick={() => router.push('/reports?step=12')}
                          className="px-3 py-1 bg-gradient-to-r from-purple-500 to-amber-500 hover:from-purple-400 hover:to-amber-400 text-black font-extrabold text-[11px] font-mono rounded shadow-md shadow-purple-500/20 flex items-center gap-1.5 transition-all"
                        >
                          View Detailed Anonymization →
                        </button>
                      </div>
                    )}

                    {step.id === 13 && shouldShowStep13Log && (
                      <div className="pt-1.5">
                        <button
                          onClick={() => router.push('/reports?step=13')}
                          className="px-3 py-1 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-extrabold text-[11px] font-mono rounded shadow-md shadow-cyan-500/20 flex items-center gap-1.5 transition-all"
                        >
                          View Detailed Loading →
                        </button>
                      </div>
                    )}

                    {step.id === 14 && (step.status === 'completed' || currentRun.active_step >= 14) && (
                      <div className="pt-1.5">
                        <button
                          onClick={() => router.push('/reports?step=14')}
                          className="px-3 py-1 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-black font-extrabold text-[11px] font-mono rounded shadow-md shadow-emerald-500/20 flex items-center gap-1.5 transition-all"
                        >
                          View Validation Engine Report →
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-200 text-[11px] text-slate-500 flex items-center justify-between font-mono">
            <span>Authoritative Pipeline Summary Logs</span>
            <span className="text-blue-600">Target Table: {pipelineState?.target_table || '—'}</span>
          </div>
        </div>
        </div>
      </div>

      {/* Custom Application Stop Confirmation Modal */}
      {showStopModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-amber-600">
              <AlertTriangle className="w-6 h-6" />
              <h3 className="text-base font-bold text-slate-900">Stop Pipeline Execution?</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              The current pipeline run <strong className="text-slate-900 font-mono">{currentRun.run_id}</strong> will stop execution at the next safe boundary. Completed step results will remain saved.
            </p>
            {stopError && (
              <div className="p-2.5 bg-red-50 border border-red-200 rounded text-xs text-red-600 font-mono">
                {stopError}
              </div>
            )}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowStopModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold rounded-lg transition-colors"
              >
                Continue Running
              </button>
              <button
                onClick={handleStopPipeline}
                disabled={isStopping}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-lg transition-colors shadow-lg shadow-red-600/20 disabled:opacity-50"
              >
                {isStopping ? 'Stopping...' : 'Stop Pipeline'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
