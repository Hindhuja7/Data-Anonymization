from typing import Set, Any, Dict, List
from fastapi import WebSocket
from app.pipeline.state import pipeline_state
from app.core.logger import logger
from datetime import datetime
import json

class WebSocketService:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send initial state
        await self.send_initial_state(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_initial_state(self, websocket: WebSocket):
        """Send current pipeline state to a newly connected client"""
        state_data = self._prepare_state_data()
        await websocket.send_json(state_data)
    
    async def broadcast_state(self):
        """Broadcast pipeline state to all connected clients"""
        if not self.active_connections:
            return
        
        state_data = self._prepare_state_data()
        message = json.dumps(state_data)
        
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_log(self, log: str, level: str = "info"):
        """Broadcast a new log entry to all connected clients"""
        if not self.active_connections:
            return
        
        log_data = {
            "type": "log",
            "timestamp": datetime.now().isoformat(),
            "message": log,
            "level": level
        }
        
        message = json.dumps(log_data)
        
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting log to WebSocket: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_step_update(self, step: int, status: str):
        """Broadcast step update to all connected clients"""
        if not self.active_connections:
            return
        
        step_data = {
            "type": "step_update",
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status
        }
        
        message = json.dumps(step_data)
        
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting step update to WebSocket: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    def _prepare_state_data(self) -> dict:
        """Prepare pipeline state data for broadcasting"""
        logs_to_send = [
            {
                "id": str(i),
                "timestamp": datetime.now().isoformat(),
                "message": log,
                "level": "error" if "ERROR" in log.upper() else "warning" if "WARN" in log.upper() else "info"
            }
            for i, log in enumerate(pipeline_state.get("logs", []))
        ]
        
        raw_step = pipeline_state.get("active_step")
        active_step_num = 0
        if isinstance(raw_step, int):
            active_step_num = raw_step
        elif isinstance(raw_step, str) and raw_step.isdigit():
            active_step_num = int(raw_step)
        
        start_time_val = pipeline_state.get("start_time")
        elapsed_sec = pipeline_state.get("elapsed_seconds") or 0
        if pipeline_state.get("status") in ["running", "paused"] and start_time_val:
            import time
            elapsed_sec = int(time.time() - start_time_val)
        
        total_recs = pipeline_state.get("total_records") or 100000
        recs_proc = pipeline_state.get("records_processed") or 0
        chunk_sz = pipeline_state.get("dynamic_chunk_size") or 5000
        est_chunks = pipeline_state.get("estimated_chunks") or (total_recs + chunk_sz - 1) // chunk_sz
        batches_ld = pipeline_state.get("batches_loaded") or 0
        
        # Calculate dynamic progress percentage based on active step or rows
        progress_pct = pipeline_state.get("progress_percent") or 0
        if progress_pct == 0 and active_step_num > 0:
            progress_pct = round((active_step_num / 17) * 100, 1)

        privacy_score_val = pipeline_state.get("privacy_score")
        if privacy_score_val is None and pipeline_state.get("risk_score") is not None:
            try:
                privacy_score_val = round(max(0.0, 100.0 - float(pipeline_state.get("risk_score"))), 1)
            except Exception:
                privacy_score_val = None

        state_to_send = {
            "type": "pipeline_state",
            "run_id": pipeline_state.get("run_id"),
            "state_version": pipeline_state.get("state_version", 0),
            "status": pipeline_state.get("status"),
            "active_step": active_step_num,
            "current_step_name": pipeline_state.get("current_step_name"),
            "target_table": pipeline_state.get("target_table"),
            "database_name": pipeline_state.get("database_name"),
            "steps": pipeline_state.get("steps"),
            "step_results": pipeline_state.get("step_results", {}),
            "started_at": pipeline_state.get("started_at"),
            "completed_at": pipeline_state.get("completed_at"),
            "progress": progress_pct,
            "progress_percent": progress_pct,
            "completedSteps": pipeline_state.get("completed_steps") or 0,
            "totalSteps": 17,
            "recordsProcessed": recs_proc,
            "records_processed": recs_proc,
            "totalRecords": pipeline_state.get("total_records") or 0,
            "total_records": pipeline_state.get("total_records") or 0,
            "riskScore": pipeline_state.get("risk_score"),
            "risk_score": pipeline_state.get("risk_score"),
            "riskLevel": pipeline_state.get("risk_level"),
            "privacy_score": privacy_score_val,
            "privacyScore": privacy_score_val,
            "elapsed_seconds": elapsed_sec,
            "elapsedSeconds": elapsed_sec,
            "currentTable": pipeline_state.get("target_table") or pipeline_state.get("current_table"),
            # Step 12 Live Anonymization Metrics
            "step_12_table": pipeline_state.get("step_12_table"),
            "step_12_chunk": pipeline_state.get("step_12_chunk"),
            "step_12_total_chunks": pipeline_state.get("step_12_total_chunks"),
            "step_12_rows_anonymized": pipeline_state.get("step_12_rows_anonymized"),
            "step_12_transformation": pipeline_state.get("step_12_transformation"),
            "step_12_rate": pipeline_state.get("step_12_rate"),
            "step_12_elapsed_seconds": pipeline_state.get("step_12_elapsed_seconds"),
            "step_12_status": pipeline_state.get("step_12_status"),
            "step_12_started_at": pipeline_state.get("step_12_started_at"),
            # Step 13 Live Destination Loading Metrics
            "step_13_table": pipeline_state.get("step_13_table"),
            "step_13_chunk": pipeline_state.get("step_13_chunk"),
            "step_13_total_chunks": pipeline_state.get("step_13_total_chunks"),
            "step_13_rows_loaded": pipeline_state.get("step_13_rows_loaded"),
            "step_13_rows_remaining": pipeline_state.get("step_13_rows_remaining"),
            "step_13_rate": pipeline_state.get("step_13_rate"),
            "step_13_elapsed_seconds": pipeline_state.get("step_13_elapsed_seconds"),
            "step_13_status": pipeline_state.get("step_13_status"),
            "step_13_started_at": pipeline_state.get("step_13_started_at"),
            "logs": logs_to_send
        }
        
        return self._sanitize_for_json(state_to_send)

    def _sanitize_for_json(self, obj: Any) -> Any:
        """Recursively convert numpy int64/float64, datetime, and non-serializable objects to pure JSON types."""
        if isinstance(obj, dict):
            return {str(k): self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(v) for v in obj]
        elif isinstance(obj, tuple):
            return [self._sanitize_for_json(v) for v in obj]
        elif hasattr(obj, 'item'):
            return obj.item()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    @property
    def connection_count(self) -> int:
        """Return number of active connections"""
        return len(self.active_connections)

# Global WebSocket service instance
websocket_service = WebSocketService()
