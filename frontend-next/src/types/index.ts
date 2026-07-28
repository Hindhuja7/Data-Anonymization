export interface PipelineLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'warning' | 'error' | 'success';
  message: string;
  step_id?: number;
  step?: number;
}

export type PipelineStepStatus = 'completed' | 'current' | 'running' | 'pending' | 'failed' | 'error' | 'waiting_for_approval' | 'paused';

export interface PipelineStep {
  id: number;
  name: string;
  status: PipelineStepStatus;
  output?: string;
}

export type WorkflowStep = PipelineStep;

export interface StepResult {
  step_id: number;
  step_name: string;
  status: string;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  summary: string;
  details: Record<string, any>;
}

export interface PipelineState {
  run_id?: string | null;
  state_version?: number;
  status: string;
  active_step?: number;
  target_table?: string;
  database_name?: string;
  started_at?: string | null;
  completed_at?: string | null;
  elapsed_seconds?: number;
  risk_score?: number | null;
  privacy_score?: number | null;
  steps: WorkflowStep[];
  step_results?: Record<string, StepResult>;
  completedSteps?: number;
  totalSteps?: number;
  currentStep?: number;
  elapsedSeconds?: number;
  progress?: number;
  batchesLoaded?: number;
  recordsProcessed?: number;
  batchSize?: number;
  totalRecords?: number;
  riskScore?: number | null;
  batches_loaded?: number;
  batch_size?: number;
}
