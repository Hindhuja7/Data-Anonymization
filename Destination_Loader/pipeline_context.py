"""
Pipeline Context for 17-step DataVault AI pipeline execution.
Manages execution state and allows outputs from earlier steps to be reused by later steps.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class StepStatus(Enum):
    """Step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_APPROVAL = "waiting_for_approval"


class PipelineContext:
    """
    Execution state object for the 17-step DataVault AI pipeline.
    Allows outputs from earlier steps to be reused by later steps.
    """
    
    def __init__(self):
        """Initialize pipeline context with all step states."""
        self.steps = {
            1: {"name": "Connect Database", "status": StepStatus.PENDING, "output": None, "error": None},
            2: {"name": "Extract Schema", "status": StepStatus.PENDING, "output": None, "error": None},
            3: {"name": "Enterprise Detection", "status": StepStatus.PENDING, "output": None, "error": None},
            4: {"name": "Privacy-Safe Sampling", "status": StepStatus.PENDING, "output": None, "error": None},
            5: {"name": "PII Detection", "status": StepStatus.PENDING, "output": None, "error": None},
            6: {"name": "Policy Generation", "status": StepStatus.PENDING, "output": None, "error": None},
            7: {"name": "Admin Approval", "status": StepStatus.PENDING, "output": None, "error": None},
            8: {"name": "Change Detection", "status": StepStatus.PENDING, "output": None, "error": None},
            9: {"name": "Redis Hash Vault", "status": StepStatus.PENDING, "output": None, "error": None},
            10: {"name": "Crash Recovery", "status": StepStatus.PENDING, "output": None, "error": None},
            11: {"name": "Chunk Processing", "status": StepStatus.PENDING, "output": None, "error": None},
            12: {"name": "Data Anonymization", "status": StepStatus.PENDING, "output": None, "error": None},
            13: {"name": "Batch Loading", "status": StepStatus.PENDING, "output": None, "error": None},
            14: {"name": "Validation Approval", "status": StepStatus.PENDING, "output": None, "error": None},
            15: {"name": "Safe Database Generation", "status": StepStatus.PENDING, "output": None, "error": None},
            16: {"name": "Audit Report", "status": StepStatus.PENDING, "output": None, "error": None},
            17: {"name": "Output Delivery", "status": StepStatus.PENDING, "output": None, "error": None},
        }
        
        # Shared execution state
        self.source_connector = None
        self.destination_connector = None
        self.schema_extractor = None
        self.source_schema = None
        self.enterprise_info = None
        self.sample_data = None
        self.pii_detection_result = None
        self.generated_policy = None
        self.approved_policy = None
        self.change_detection_result = None
        self.redis_mapping = None
        self.anonymizer = None
        self.recovery_state = None
        self.current_table = None
        self.current_chunk = 0
        self.total_chunks = 0
        self.anonymized_batches = []
        self.validation_result = None
        self.audit_report = None
        self.final_outputs = None
        
        # Progress tracking
        self.start_time = None
        self.end_time = None
        self.tables_processed = []
        self.total_rows_processed = 0
        self.failed_chunks = []
        self.errors = []
        
        # Configuration
        self.source_db_config = None
        self.destination_db_config = None
        self.policy_file = None
        self.chunk_size = 1000
        self.dynamic_chunk_size = 1000
        self.redis_host = "localhost"
        self.redis_port = 6379
        self.hmac_secret = None
        
    def set_step_status(self, step_number: int, status: StepStatus, output: Any = None, error: Any = None):
        """Set step status and optional output/error."""
        if step_number in self.steps:
            self.steps[step_number]["status"] = status
            if output is not None:
                self.steps[step_number]["output"] = output
            if error is not None:
                self.steps[step_number]["error"] = error
                self.errors.append({
                    "step": step_number,
                    "step_name": self.steps[step_number]["name"],
                    "error": str(error),
                    "timestamp": datetime.now().isoformat()
                })
    
    def get_step_status(self, step_number: int) -> StepStatus:
        """Get step status."""
        if step_number in self.steps:
            return self.steps[step_number]["status"]
        return StepStatus.PENDING
    
    def get_step_output(self, step_number: int) -> Any:
        """Get step output."""
        if step_number in self.steps:
            return self.steps[step_number]["output"]
        return None
    
    def is_step_completed(self, step_number: int) -> bool:
        """Check if step is completed."""
        return self.get_step_status(step_number) == StepStatus.COMPLETED
    
    def is_step_failed(self, step_number: int) -> bool:
        """Check if step failed."""
        return self.get_step_status(step_number) == StepStatus.FAILED
    
    def is_waiting_for_approval(self, step_number: int) -> bool:
        """Check if step is waiting for approval."""
        return self.get_step_status(step_number) == StepStatus.WAITING_FOR_APPROVAL
    
    def get_current_step(self) -> int:
        """Get the current active step number."""
        for step_num, step_info in self.steps.items():
            if step_info["status"] == StepStatus.RUNNING:
                return step_num
        return 0
    
    def get_progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        completed = sum(1 for step in self.steps.values() if step["status"] == StepStatus.COMPLETED)
        return (completed / len(self.steps)) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for progress reporting (serializable only)."""
        current_step = self.get_current_step()
        step_info = self.steps.get(current_step, {})
        step_status = step_info.get("status")
        
        # Convert StepStatus enum to string if needed
        if hasattr(step_status, 'value'):
            status_str = step_status.value
        else:
            status_str = str(step_status)
        
        # Convert steps to serializable format
        steps_serializable = {}
        for k, v in self.steps.items():
            steps_serializable[k] = {
                "name": v["name"],
                "status": v["status"].value if hasattr(v["status"], 'value') else str(v["status"]),
                "output": str(v.get("output", "")) if v.get("output") is not None else None,
                "error": str(v.get("error", "")) if v.get("error") is not None else None
            }
        
        return {
            "current_step": current_step,
            "step_name": step_info.get("name", ""),
            "step_status": status_str,
            "progress": self.get_progress_percentage(),
            "current_table": self.current_table,
            "current_chunk": self.current_chunk,
            "total_chunks": self.total_chunks,
            "processed_rows": self.total_rows_processed,
            "total_rows": self.get_step_output(4).get("total_records", 0) if self.is_step_completed(4) else 0,
            "errors": [str(e) for e in self.errors[-10:]],  # Convert errors to strings
            "steps": steps_serializable
        }
