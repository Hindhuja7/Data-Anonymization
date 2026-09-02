from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from app.core.logger import logger

STEP_NAMES = [
    "Connect Database",
    "Extract Schema",
    "Enterprise Detection",
    "Privacy-Safe Sampling",
    "PII Detection",
    "Policy Generation",
    "Admin Approval",
    "Redis Vault Init",
    "Change Detection",
    "Redis Sync",
    "AOF Safety Check",
    "Policy Anonymization",
    "Destination Loading",
    "Automatic Validation",
    "Audit Report",
    "Admin Dashboard Sync",
    "Continuous Sync Init"
]

class PipelineState:
    """Manages pipeline execution state with explicit run identity and monotonic versioning"""

    def _create_initial_steps(self) -> List[Dict[str, Any]]:
        return [
            {"id": i + 1, "name": STEP_NAMES[i], "status": "pending"}
            for i in range(17)
        ]

    def __init__(self):
        self._state: Dict[str, Any] = {
            "run_id": None,
            "state_version": 0,
            "status": "idle",
            "active_step": 0,
            "current_step_name": "",
            "target_table": "",
            "database_name": "",
            "steps": self._create_initial_steps(),
            "step_results": {},
            "completed_steps": 0,
            "total_steps": 17,
            "progress_percent": 0,
            "records_processed": 0,
            "total_records": 0,
            "dynamic_chunk_size": 1000,
            "estimated_chunks": 0,
            "batches_loaded": 0,
            "privacy_score": None,
            "risk_score": None,
            "risk_level": "",
            "elapsed_seconds": 0,
            "start_time": None,
            "started_at": None,
            "completed_at": None,
            "logs": [],
            "errors": [],
            "polling_status": "inactive",
            "approval_session": {
                "approval_state": "none",
                "run_id": None,
                "target_table": None,
                "approved_at": None,
                "approved_by": None,
                "final_risk_score": None,
                "final_privacy_score": None,
                "column_policies": [],
                "modifications": []
            }
        }

    def start_new_run(self, target_table: str, database_name: str) -> str:
        """Initialize a new unique pipeline execution run."""
        new_run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        steps = self._create_initial_steps()
        steps[0]["status"] = "running"

        import time
        # Delete stale disk policy file from previous runs
        try:
            from app.core.config import config
            disk_path = os.path.join(config.DIRECTORY, "anonymization_policy.json")
            if os.path.exists(disk_path):
                os.remove(disk_path)
        except Exception:
            pass

        dest_name = f"{database_name}_anonymized" if not str(database_name).endswith("_anonymized") else database_name
        self._state.update({
            "run_id": new_run_id,
            "state_version": 1,
            "status": "running",
            "active_step": 1,
            "current_step_name": STEP_NAMES[0],
            "target_table": target_table,
            "database_name": database_name,
            "dest_database_name": dest_name,
            "steps": steps,
            "step_results": {},
            "generated_policy": None,
            "modified_policy": None,
            "approved_policy": None,
            "approval_session": None,
            "approval_state": "pending",
            "vulnerabilities": [],
            "validation_report": None,
            "completed_steps": 0,
            "progress_percent": 0,
            "records_processed": 0,
            "privacy_score": None,
            "risk_score": None,
            "risk_level": "",
            "step_12_status": "pending",
            "step_13_status": "pending",
            "step_14_status": "pending",
            "step_12_chunk": 0,
            "step_13_chunk": 0,
            "step_12_total_chunks": 0,
            "step_13_total_chunks": 0,
            "step_12_rows_anonymized": 0,
            "step_13_rows_loaded": 0,
            "step_12_rate": 0,
            "step_13_rate": 0,
            "start_time": time.time(),
            "last_active_timestamp": time.time(),
            "accumulated_active_seconds": 0,
            "elapsed_seconds": 0,
            "started_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "completed_at": None,
            "logs": [],
            "errors": [],
            "polling_status": "inactive"
        })
        logger.info(f"Started new pipeline run {new_run_id} for target_table={target_table}")
        return new_run_id

    def _is_write_permitted(self, run_id: Optional[str] = None) -> bool:
        """Central invariant guard: A terminated or mismatched run MUST NEVER WRITE state again."""
        active_run_id = self._state.get("run_id")
        current_status = self._state.get("status")

        if run_id and active_run_id and run_id != active_run_id:
            logger.warning(f"STALE WRITE REJECTED: Caller run_id '{run_id}' != Active run_id '{active_run_id}'")
            return False

        if run_id and active_run_id is None:
            logger.warning(f"STALE WRITE REJECTED: Caller run_id '{run_id}' attempted write to idle state")
            return False

        if current_status in ["cancelled", "failed", "completed"] and run_id and run_id == active_run_id:
            # Allow status transition to cancelled/completed/failed if setting terminal state
            pass

        return True

    def set_step_status(self, step_id: int, status: str, step_name: Optional[str] = None, run_id: Optional[str] = None) -> None:
        """Monotonically update step status and increment state_version with run_id guard."""
        if not self._is_write_permitted(run_id):
            return

        if 1 <= step_id <= 17:
            self._state["state_version"] = self._state.get("state_version", 0) + 1
            curr_active = self._state.get("active_step", 0)
            self._state["active_step"] = max(curr_active, step_id) if curr_active <= 17 else step_id
            name = step_name or STEP_NAMES[step_id - 1]
            self._state["current_step_name"] = name
            
            # Overall status remains 'running' for steps 1..16 when an individual step completes
            if step_id == 17 and status == "completed":
                self._state["status"] = "completed"
            elif status in ["running", "waiting_for_approval", "PAUSED_BY_USER", "paused", "cancelled", "failed", "STOPPING"]:
                self._state["status"] = status
            elif status == "completed":
                self._state["status"] = "running"

            # Monotonic step array update
            for s in self._state["steps"]:
                if s["id"] < step_id:
                    s["status"] = "completed"
                elif s["id"] == step_id:
                    s["status"] = status
                elif s["id"] > step_id:
                    s["status"] = "pending"

            completed = sum(1 for s in self._state["steps"] if s["status"] == "completed")
            self._state["completed_steps"] = completed
            self._state["progress_percent"] = int((completed / 17.0) * 100)
            logger.info(f"Run {self._state.get('run_id')} state_version={self._state['state_version']} | Step {step_id} ({name}) -> {status}")

    def record_step_result(self, step_id: int, status: str, summary: str, details: Optional[Dict[str, Any]] = None, duration_ms: Optional[int] = None, run_id: Optional[str] = None) -> None:
        """Record structured execution results for a completed step with run_id guard"""
        if not self._is_write_permitted(run_id):
            return

        name = STEP_NAMES[step_id - 1] if 1 <= step_id <= 17 else f"Step {step_id}"
        if "step_results" not in self._state:
            self._state["step_results"] = {}
        
        existing = self._state["step_results"].get(str(step_id), {})
        started_at = existing.get("started_at", datetime.utcnow().isoformat())
        completed_at = datetime.utcnow().isoformat()
        
        self._state["step_results"][str(step_id)] = {
            "step_id": step_id,
            "step_name": name,
            "status": status,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_ms": duration_ms or 0,
            "summary": summary,
            "details": details or {}
        }
        self._state["state_version"] = self._state.get("state_version", 0) + 1

        # Atomically sync steps array in backend state
        if 1 <= step_id <= 17:
            for s in self._state["steps"]:
                if s["id"] == step_id:
                    s["status"] = status
                elif s["id"] < step_id and status == "completed":
                    s["status"] = "completed"

            completed = sum(1 for s in self._state["steps"] if s["status"] == "completed")
            self._state["completed_steps"] = completed
            self._state["progress_percent"] = int((completed / 17.0) * 100)

        # Log real-time audit event for user
        try:
            from app.services.audit_service import audit_service
            uid = self._state.get("user_id") or "b@gmail.com"
            audit_service.log_event(
                user_id=uid,
                action=f"STEP_{step_id}_{status.upper()}",
                category="PIPELINE",
                level="INFO" if status in ["completed", "running"] else "WARNING",
                step_name=name,
                details=summary,
                run_id=self._state.get("run_id")
            )
            if step_id == 17 and status == "completed":
                policy = self._state.get("approved_policy") or self._state.get("generated_policy") or {}
                audit_service.record_run_history(
                    user_id=uid,
                    run_id=self._state.get("run_id") or f"RUN-{step_id}",
                    table_name=self._state.get("target_table") or "employees",
                    policy_data=policy,
                    status="completed"
                )
        except Exception as e:
            logger.warning(f"Error logging audit/history on step result: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any, run_id: Optional[str] = None) -> None:
        if not self._is_write_permitted(run_id):
            return
        self._state["state_version"] = self._state.get("state_version", 0) + 1
        self._state[key] = value
        logger.debug(f"Pipeline state updated: {key} = {value}")

    def update(self, updates: Dict[str, Any]) -> None:
        self._state["state_version"] = self._state.get("state_version", 0) + 1
        self._state.update(updates)

    def reset(self) -> None:
        self._state = {
            "run_id": None,
            "state_version": 0,
            "status": "idle",
            "active_step": 0,
            "current_step_name": "",
            "target_table": "",
            "database_name": "",
            "steps": self._create_initial_steps(),
            "completed_steps": 0,
            "total_steps": 17,
            "progress_percent": 0,
            "records_processed": 0,
            "total_records": 0,
            "dynamic_chunk_size": 1000,
            "estimated_chunks": 0,
            "batches_loaded": 0,
            "privacy_score": None,
            "risk_score": None,
            "risk_level": "",
            "elapsed_seconds": 0,
            "start_time": None,
            "started_at": None,
            "completed_at": None,
            "logs": [],
            "errors": [],
            "polling_status": "inactive"
        }
        logger.info("Pipeline state reset to initial clean state")

    def add_log(self, log: str) -> None:
        self._state["logs"].append(log)
        if len(self._state["logs"]) > 100:
            self._state["logs"] = self._state["logs"][-100:]

    def add_error(self, error: str) -> None:
        self._state["errors"].append({
            "message": error,
            "timestamp": datetime.now().isoformat()
        })

    def to_dict(self) -> Dict[str, Any]:
        state_copy = self._state.copy()
        import time
        status = state_copy.get("status")
        started_at = state_copy.get("started_at")
        start_time = state_copy.get("start_time")
        
        if started_at and start_time:
            accumulated = state_copy.get("accumulated_active_seconds", 0)
            last_active = state_copy.get("last_active_timestamp") or start_time
            
            if status == "running":
                current_secs = int(accumulated + (time.time() - last_active))
                state_copy["elapsed_seconds"] = max(0, current_secs)
            elif status in ["PAUSED_BY_USER", "paused", "waiting_for_approval", "WAITING_FOR_APPROVAL"]:
                state_copy["elapsed_seconds"] = int(accumulated)
            elif status in ["completed", "cancelled", "failed", "error"]:
                state_copy["elapsed_seconds"] = state_copy.get("elapsed_seconds", int(accumulated))
        else:
            state_copy["elapsed_seconds"] = 0

        # Dynamically compute privacy_score and risk_score from active policy using RiskScoringEngine
        try:
            from app.services.audit_service import audit_service
            cols = (
                (state_copy.get("approved_policy") or {}).get("column_policies") or
                (state_copy.get("generated_policy") or {}).get("column_policies") or
                (state_copy.get("modified_policy") or {}).get("column_policies") or
                []
            )
            if not cols:
                hist = audit_service.get_run_history()
                if hist:
                    cols = hist[0].get("policy_snapshot", {}).get("column_policies", [])

            risk_calc = audit_service._calculate_policy_risk_dynamic(cols)
            state_copy["privacy_score"] = risk_calc["privacy_score"]
            state_copy["risk_score"] = risk_calc["policy_risk_score"]
            state_copy["risk_level"] = risk_calc["risk_level"]
        except Exception:
            pass

        # Dynamically resolve destination database name for active user config
        if not state_copy.get("dest_database_name"):
            try:
                import glob, json, os, re
                from app.core.config import config
                active_u = state_copy.get("user_id") or "b@gmail.com"
                clean_u = re.sub(r'[^a-zA-Z0-9]', '', str(active_u)).lower()
                
                user_cfg_file = os.path.join(config.DIRECTORY, f"database_config_{clean_u}.json")
                default_cfg_file = os.path.join(config.DIRECTORY, "database_config.json")
                
                target_cfg = user_cfg_file if os.path.exists(user_cfg_file) else (default_cfg_file if os.path.exists(default_cfg_file) else None)
                
                if target_cfg:
                    with open(target_cfg, "r", encoding="utf-8") as f:
                        cfg_d = json.load(f)
                    db_type = cfg_d.get("database_type") or cfg_d.get("type") or "mysql"
                    db_n = cfg_d.get("database_name") or cfg_d.get("database") or ("neondb" if db_type == "postgresql" else "defaultdb")
                    dest_n = "neondb_anonymized"
                    state_copy["dest_database_name"] = "neondb_anonymized"
                    state_copy["database_name"] = db_n
                    state_copy["database_type"] = db_type
                else:
                    state_copy["dest_database_name"] = "neondb_anonymized"
            except Exception:
                state_copy["dest_database_name"] = "neondb_anonymized"
            
        return state_copy

    @property
    def status(self) -> str:
        return self._state["status"]

    @property
    def active_step(self) -> int:
        return self._state["active_step"]

    @property
    def is_running(self) -> bool:
        return self._state["status"] in ["running", "paused", "PAUSED_BY_USER", "WAITING_FOR_APPROVAL", "cancelling"]

    @property
    def is_idle(self) -> bool:
        return self._state["status"] == "idle"

pipeline_state = PipelineState()
