import asyncio
import os
import sys
import json
import threading
from typing import Optional, Dict, Any
from datetime import datetime
from app.pipeline.state import pipeline_state
from app.pipeline.parser import log_parser
from app.utils.chunk_calculator import chunk_calculator
from app.core.config import config
from app.core.logger import logger
from app.core.exceptions import PipelineException

# Add path for PolicyExecutor and PollingWorker import
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _layer in ["Connection_Extraction", "Enterprise_Classification", "PII_Detection", "Change_Detection", "Redis_Hash_Vault", "Redis_AOF_Safety", "Polling_Worker", "Destination_Loader", "Validation_Engine", "Audit_Report", "Admin_Dashboard", "Approval_Workflow"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

class PipelineController:
    """Controls 17-step pipeline execution lifecycle and PollingWorker integration"""
    
    def __init__(self):
        self.pipeline_task: Optional[asyncio.Task] = None
        self.subprocess = None
        self.policy_executor = None
        self.polling_worker = None
        self.cancel_event: Optional[threading.Event] = None
    
    def _clear_stale_approval_state(self):
        """Clear any stale approval flags or approved status metadata for a fresh run."""
        try:
            for flag in ["pipeline_approved.txt", "approval_granted.txt"]:
                if os.path.exists(flag):
                    try:
                        os.remove(flag)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Error removing approval flag files: {e}")

        try:
            policy_path = os.path.join(config.DIRECTORY, "anonymization_policy.json")
            if os.path.exists(policy_path):
                with open(policy_path, "r") as f:
                    policy_data = json.load(f)
                if isinstance(policy_data, dict) and policy_data.get("policy_metadata"):
                    policy_data["policy_metadata"]["status"] = "DRAFT"
                    with open(policy_path, "w") as f:
                        json.dump(policy_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Error resetting policy metadata status to DRAFT: {e}")

    async def start_pipeline(self, user_id: Optional[str] = None, database_config: Optional[dict] = None, target_table: Optional[str] = None) -> dict:
        """Start the 17-step anonymization pipeline execution with authoritative user-scoped configuration"""
        if pipeline_state.is_running:
            return {"status": "already_running", "message": "Pipeline is already active."}
        
        try:
            # Clear stale approval metadata from prior runs
            self._clear_stale_approval_state()

            # Create fresh per-run cancellation event
            self.cancel_event = threading.Event()

            # Stop any previous PollingWorker daemon before starting a new pipeline run
            if self.polling_worker:
                try:
                    self.polling_worker.stop()
                except Exception:
                    pass
                self.polling_worker = None

            # Resolve authoritative user-scoped configuration
            db_conf = database_config or {}
            if not db_conf:
                # Resolve config path for user_id if available
                config_file = "database_config.json"
                if user_id and user_id not in ["null", "undefined", "anonymous"]:
                    safe_user = "".join(c for c in str(user_id) if c.isalnum() or c in ['-', '_'])
                    user_file = os.path.join(config.DIRECTORY, f"database_config_{safe_user}.json")
                    if os.path.exists(user_file):
                        config_file = f"database_config_{safe_user}.json"

                config_path = os.path.join(config.DIRECTORY, config_file)
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            db_conf = json.load(f)
                    except Exception as e:
                        logger.warning(f"Error reading database config file '{config_file}': {e}")

            resolved_target_table = target_table or db_conf.get("target_table")
            if not resolved_target_table:
                raise PipelineException("No target_table specified in database configuration.")

            database_name = db_conf.get("database") or db_conf.get("database_name") or "neondb"

            # Start fresh run identity
            run_id = pipeline_state.start_new_run(target_table=resolved_target_table, database_name=database_name)
            if user_id:
                pipeline_state.set("user_id", user_id)
            
            # Launch pipeline subprocess
            self.pipeline_task = asyncio.create_task(self._run_pipeline_subprocess())
            
            logger.info(f"17-step pipeline run {run_id} started successfully for user='{user_id or 'default'}', target_table={resolved_target_table}")
            return {
                "status": "started",
                "run_id": run_id,
                "target_table": resolved_target_table,
                "message": f"17-step DataVault AI pipeline run {run_id} active for table '{resolved_target_table}'."
            }
            
        except Exception as e:
            pipeline_state.set("status", "error")
            pipeline_state.add_error(str(e))
            logger.error(f"Failed to start pipeline: {e}")
            raise PipelineException(f"Failed to start pipeline: {e}")
    
    async def pause_pipeline(self) -> dict:
        """Pause the pipeline execution with explicit PAUSED_BY_USER state"""
        current_status = pipeline_state.get("status")
        if current_status not in ["running"]:
            return {"status": "cannot_pause", "message": f"Pipeline status '{current_status}' cannot be paused."}
        
        try:
            pipeline_state.set("status", "PAUSED_BY_USER")
            logger.info("Pipeline paused cleanly by user (status='PAUSED_BY_USER')")
            return {"status": "PAUSED_BY_USER", "message": "Pipeline execution paused."}
        except Exception as e:
            logger.error(f"Failed to pause pipeline: {e}")
            raise PipelineException(f"Failed to pause pipeline: {e}")
    
    async def resume_pipeline(self) -> dict:
        """Resume paused pipeline execution preserving existing run_id and state"""
        current_status = pipeline_state.get("status")
        if current_status != "PAUSED_BY_USER":
            return {"status": "not_paused", "message": "Pipeline is not paused by user."}
        
        try:
            pipeline_state.set("status", "running")
            logger.info("Pipeline resumed successfully from PAUSED_BY_USER state")
            return {"status": "running", "message": "Pipeline execution resumed."}
        except Exception as e:
            logger.error(f"Failed to resume pipeline: {e}")
            raise PipelineException(f"Failed to resume pipeline: {e}")
    
    async def stop_pipeline(self, requested_run_id: Optional[str] = None) -> dict:
        """Stop/cancel the pipeline execution with run_id validation and termination handshake"""
        try:
            active_run_id = pipeline_state.get("run_id")
            if requested_run_id and active_run_id and requested_run_id != active_run_id:
                logger.warning(f"Stop request run_id mismatch: requested '{requested_run_id}', active is '{active_run_id}'")
                return {
                    "status": "mismatch",
                    "message": f"Stale stop request for run_id '{requested_run_id}'. Active run is '{active_run_id}'."
                }

            # 1. Trigger per-run cancellation event
            if self.cancel_event:
                self.cancel_event.set()
            if self.policy_executor and hasattr(self.policy_executor, 'stop_event'):
                self.policy_executor.stop_event.set()

            # 2. Transition state to 'STOPPING' (cancellation requested)
            pipeline_state.set("status", "STOPPING")
            pipeline_state.set("stop_requested_at", datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')
            pipeline_state.set("polling_status", "inactive")

            if self.polling_worker:
                try:
                    self.polling_worker.stop()
                except Exception:
                    pass
                self.polling_worker = None

            logger.info(f"Pipeline cancellation requested for run_id '{active_run_id}'. Awaiting worker task termination...")

            # 3. Termination Handshake: Wait for background task to terminate
            if self.pipeline_task and not self.pipeline_task.done():
                try:
                    await asyncio.wait_for(asyncio.shield(self.pipeline_task), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Pipeline task termination timed out after 5s. Forcing cancelled state.")
                except Exception as e:
                    logger.info(f"Pipeline task exit observed cleanly: {e}")

            pipeline_state.set("status", "cancelled")
            pipeline_state.set("ended_at", datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')
            pipeline_state.set("completed_at", datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')
            self.pipeline_task = None

            logger.info(f"Pipeline run_id '{active_run_id}' fully terminated with status='cancelled'.")
            return {"status": "cancelled", "run_id": active_run_id, "message": "Pipeline cancelled successfully."}
        except Exception as e:
            logger.error(f"Failed to stop pipeline: {e}")
            raise PipelineException(f"Failed to stop pipeline: {e}")

    async def approve_pipeline(self) -> dict:
        """Approve policy at Step 7 and resume pipeline execution."""
        try:
            flag_file = "pipeline_approved.txt"
            with open(flag_file, "w") as f:
                f.write("APPROVED")

            policy_path = os.path.join(config.DIRECTORY, "anonymization_policy.json")
            if os.path.exists(policy_path):
                try:
                    with open(policy_path, "r") as f:
                        pdata = json.load(f)
                    if isinstance(pdata, dict) and "policy_metadata" in pdata:
                        pdata["policy_metadata"]["status"] = "APPROVED"
                        pdata["policy_metadata"]["approved_by"] = "Dashboard Admin"
                        pdata["policy_metadata"]["approved_at"] = str(datetime.now())
                        with open(policy_path, "w") as f:
                            json.dump(pdata, f, indent=2)
                except Exception as e:
                    logger.warning(f"Failed updating policy metadata on approval: {e}")

            state_policy = pipeline_state.get("modified_policy") or pipeline_state.get("generated_policy") or pipeline_state.get("approved_policy") or {}
            policy_path = os.path.join(config.DIRECTORY, "anonymization_policy.json")
            if (not state_policy.get("column_policies")) and os.path.exists(policy_path):
                try:
                    with open(policy_path, "r", encoding="utf-8") as f:
                        disk_p = json.load(f)
                    if isinstance(disk_p, dict):
                        state_policy = disk_p
                except Exception:
                    pass

            cols = state_policy.get("column_policies", [])
            if not cols and isinstance(state_policy.get("tables"), dict):
                cols = []
                for tname, cdict in state_policy["tables"].items():
                    if isinstance(cdict, dict):
                        for cname, ccfg in cdict.items():
                            cols.append({
                                "table_name": tname,
                                "column_name": cname,
                                "is_pii": True,
                                "pii_type": cname.upper(),
                                "confidence": 0.9,
                                "anonymization_technique": (ccfg.get("technique") if isinstance(ccfg, dict) else "MASKING").upper()
                            })

            final_risk = pipeline_state.get("risk_score") or state_policy.get("policy_metadata", {}).get("risk_score") or 0.0
            final_privacy = pipeline_state.get("privacy_score") or max(0.0, round(100.0 - float(final_risk), 1))

            approval_session_data = {
                "approval_state": "approved",
                "run_id": pipeline_state.get("run_id"),
                "target_table": pipeline_state.get("target_table") or "customers",
                "approved_at": datetime.now().isoformat(),
                "approved_by": "Dashboard Admin",
                "final_risk_score": final_risk,
                "final_privacy_score": final_privacy,
                "column_policies": cols,
                "modifications": state_policy.get("admin_modifications", [])
            }
            pipeline_state.set("approved_policy", state_policy)
            pipeline_state.set("approval_session", approval_session_data)
            pipeline_state.set("approval_state", "approved")

            pipeline_state.set("status", "running")
            pipeline_state.set("active_step", 8)
            logger.info("Admin approval granted. Step 7 marked APPROVED and pipeline resumed to Step 8.")
            return {"status": "success", "approval_session": approval_session_data, "message": "Policy approved successfully. Pipeline resumed."}
        except Exception as e:
            logger.error(f"Failed to approve pipeline: {e}")
            raise PipelineException(f"Failed to approve pipeline: {e}")

    async def modify_policy(self, payload: dict) -> dict:
        """Modify draft policy for active run_id and recalculate risk/privacy scores authoritatively"""
        column_policies = payload.get("column_policies", [])
        target_table = payload.get("target_table") or pipeline_state.get("target_table") or "customers"

        try:
            from risk_scoring_engine import RiskScoringEngine
        except ImportError:
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            admin_dash_path = os.path.join(root_dir, "Admin_Dashboard")
            if admin_dash_path not in sys.path:
                sys.path.insert(0, admin_dash_path)
            from risk_scoring_engine import RiskScoringEngine

        engine = RiskScoringEngine()
        risk_result = engine.calculate_policy_risk(column_policies)
        raw_risk = float(risk_result.get("policy_risk_score", 0.0))
        privacy_score = max(0.0, round(100.0 - raw_risk, 1))
        risk_lvl = risk_result.get("risk_level", "LOW")

        modified_draft = {
            "target_table": target_table,
            "column_policies": column_policies,
            "modified_at": datetime.now().isoformat(),
            "modified_by": "Dashboard Admin"
        }
        
        gen_pol = pipeline_state.get("generated_policy") or {}
        gen_pol["column_policies"] = column_policies
        if "policy_metadata" not in gen_pol:
            gen_pol["policy_metadata"] = {}
        gen_pol["policy_metadata"]["risk_score"] = raw_risk
        gen_pol["policy_metadata"]["privacy_score"] = privacy_score
        gen_pol["policy_metadata"]["risk_level"] = risk_lvl
        gen_pol["policy_metadata"]["status"] = "DRAFT_MODIFIED"
        gen_pol["policy_metadata"]["target_table"] = target_table

        pipeline_state.set("generated_policy", gen_pol)
        pipeline_state.set("modified_policy", modified_draft)
        pipeline_state.set("risk_score", raw_risk)
        pipeline_state.set("privacy_score", privacy_score)
        pipeline_state.set("risk_level", risk_lvl)
        pipeline_state.set("approval_state", "pending")

        return {
            "status": "modified",
            "run_id": pipeline_state.get("run_id"),
            "target_table": target_table,
            "risk_score": raw_risk,
            "privacy_score": privacy_score,
            "risk_level": risk_lvl,
            "vulnerabilities": risk_result.get("vulnerabilities", [])
        }

    async def approve_validation(self) -> dict:
        """Approve validation step."""
        try:
            pipeline_state.set("status", "running")
            return {"status": "success", "message": "Validation approved."}
        except Exception as e:
            logger.error(f"Failed to approve validation: {e}")
            raise PipelineException(f"Failed to approve validation: {e}")

    async def modify_and_reanonymize(self, modified_policy: dict) -> dict:
        """Update policy and resume from step 8."""
        try:
            policy_path = os.path.join(config.DIRECTORY, "anonymization_policy.json")
            with open(policy_path, "w") as f:
                json.dump(modified_policy, f, indent=2)
            return await self.approve_pipeline()
        except Exception as e:
            logger.error(f"Failed to modify and reanonymize policy: {e}")
            raise PipelineException(f"Failed to modify policy: {e}")
    
    async def reset_pipeline(self) -> dict:
        """Reset pipeline state to initial idle state"""
        try:
            if pipeline_state.is_running:
                await self.stop_pipeline()
            
            if self.polling_worker:
                try:
                    self.polling_worker.stop()
                except Exception:
                    pass
                self.polling_worker = None

            self._clear_stale_approval_state()
            pipeline_state.reset()
            pipeline_state.set("polling_status", "inactive")
            logger.info("Pipeline state reset")
            return {"status": "reset", "message": "Pipeline state reset to initial state."}
        except Exception as e:
            logger.error(f"Failed to reset pipeline: {e}")
            raise PipelineException(f"Failed to reset pipeline: {e}")
    
    def _sanitize_dict(self, d: Any) -> Any:
        if isinstance(d, dict):
            return {k: self._sanitize_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [self._sanitize_dict(v) for v in d]
        elif hasattr(d, "item"):
            return d.item()
        return d

    def get_status(self) -> dict:
        """Get current pipeline status including PollingWorker status"""
        status = self._sanitize_dict(pipeline_state.to_dict())
        if self.policy_executor and hasattr(self.policy_executor, 'get_serializable_progress'):
            try:
                executor_progress = self._sanitize_dict(self.policy_executor.get_serializable_progress())
                status.update(executor_progress)
            except Exception as e:
                logger.error(f"Error getting executor progress: {e}")
        
        status["polling_status"] = "active" if (self.polling_worker and self.polling_worker.running) else "inactive"
        return status

    def _start_polling_worker(self, source_db_config, destination_db_config, policy_file, redis_host, redis_port, hmac_secret):
        """Safely start continuous PollingWorker after Step 17 completion."""
        try:
            if self.polling_worker and self.polling_worker.running:
                logger.info("PollingWorker is already active.")
                return

            from polling_worker import PollingWorker
            
            src_config = {
                "database_type": source_db_config.get("database_type"),
                "host": source_db_config.get("host"),
                "port": source_db_config.get("port"),
                "username": source_db_config.get("username"),
                "password": source_db_config.get("password"),
                "database_name": source_db_config.get("database_name"),
                "sslmode": source_db_config.get("sslmode")
            }
            dst_config = {
                "database_type": destination_db_config.get("database_type"),
                "host": destination_db_config.get("host"),
                "port": destination_db_config.get("port"),
                "username": destination_db_config.get("username"),
                "password": destination_db_config.get("password"),
                "database_name": destination_db_config.get("database_name"),
                "sslmode": destination_db_config.get("sslmode")
            }

            self.polling_worker = PollingWorker(
                source_db_config=src_config,
                destination_db_config=dst_config,
                policy_file=policy_file,
                interval_seconds=30.0,
                redis_host=redis_host,
                redis_port=redis_port,
                hmac_secret=hmac_secret
            )
            
            self.polling_worker.start()
            pipeline_state.set("polling_status", "active")
            logger.info("PollingWorker background daemon started following Step 17 completion.")
        except Exception as e:
            logger.error(f"Failed to start PollingWorker: {e}")
            pipeline_state.set("polling_status", "error")

    async def _run_pipeline_subprocess(self):
        """Run the 17-step PolicyExecutor directly"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            from policy_executor import PolicyExecutor
            
            import json
            dynamic_config = {}
            active_uid = pipeline_state.get("user_id")
            config_file = "database_config.json"
            if active_uid and active_uid not in ["null", "undefined", "anonymous"]:
                safe_user = "".join(c for c in str(active_uid) if c.isalnum() or c in ['-', '_'])
                user_file = os.path.join(config.DIRECTORY, f"database_config_{safe_user}.json")
                if os.path.exists(user_file):
                    config_file = f"database_config_{safe_user}.json"

            config_path = os.path.join(config.DIRECTORY, config_file)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        dynamic_config = json.load(f)
                    logger.info(f"Pipeline runner loaded dynamic database configuration from '{config_file}'")
                except Exception as e:
                    logger.error(f"Failed to load dynamic database config: {e}")

            target_table = pipeline_state.get("target_table") or dynamic_config.get("target_table")
            if not target_table:
                raise ValueError("Target table is not specified for this pipeline run!")

            source_db_type = dynamic_config.get("database_type") or dynamic_config.get("type") or os.getenv("SOURCE_DB_TYPE", "sqlite")
            source_db_config = {
                "database_type": source_db_type,
                "host": dynamic_config.get("host", os.getenv("SOURCE_DB_HOST")) if source_db_type != "sqlite" else None,
                "port": int(dynamic_config.get("port", os.getenv("SOURCE_DB_PORT", 5432))) if source_db_type != "sqlite" and (dynamic_config.get("port") or os.getenv("SOURCE_DB_PORT")) else None,
                "username": dynamic_config.get("username", os.getenv("SOURCE_DB_USERNAME")) if source_db_type != "sqlite" else None,
                "password": dynamic_config.get("password", os.getenv("SOURCE_DB_PASSWORD")) if source_db_type != "sqlite" else None,
                "database_name": dynamic_config.get("database_name") or dynamic_config.get("database", os.getenv("SOURCE_DB_NAME")),
                "target_table": target_table,
                "sslmode": os.getenv("SOURCE_DB_SSLMODE") if source_db_type != "sqlite" else None
            }
            
            dest_db_type = dynamic_config.get("dest_database_type") or dynamic_config.get("dest_type") or ("sqlite" if source_db_type == "sqlite" else os.getenv("DEST_DB_TYPE", "sqlite"))
            dest_db_name = os.getenv("DEST_DB_NAME")
            if not dest_db_name:
                if source_db_type == "sqlite":
                    dest_db_name = "test_destination.db"
                elif dynamic_config.get("database"):
                    dest_db_name = f"{dynamic_config.get('database')}_anonymized"
                
            destination_db_config = {
                "database_type": dest_db_type,
                "host": dynamic_config.get("host", os.getenv("DEST_DB_HOST")) if dest_db_type != "sqlite" else None,
                "port": int(dynamic_config.get("port", os.getenv("DEST_DB_PORT", 5432))) if dest_db_type != "sqlite" and (dynamic_config.get("port") or os.getenv("DEST_DB_PORT")) else None,
                "username": dynamic_config.get("username", os.getenv("DEST_DB_USERNAME")) if dest_db_type != "sqlite" else None,
                "password": dynamic_config.get("password", os.getenv("DEST_DB_PASSWORD")) if dest_db_type != "sqlite" else None,
                "database_name": dest_db_name or f"{source_db_config['database_name']}_anonymized",
                "sslmode": os.getenv("DEST_DB_SSLMODE") if dest_db_type != "sqlite" else None
            }
            
            policy_file = os.getenv("POLICY_FILE", "anonymization_policy.json")
            chunk_size = int(os.getenv("CHUNK_SIZE", 10))
            
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            hmac_secret = os.getenv("HMAC_SECRET")
            
            self.policy_executor = PolicyExecutor(
                source_db_config=source_db_config,
                destination_db_config=destination_db_config,
                policy_file=policy_file,
                chunk_size=chunk_size,
                redis_host=redis_host,
                redis_port=redis_port,
                hmac_secret=hmac_secret,
                destination_table_prefix=""
            )
            
            self.policy_executor.pipeline_state = pipeline_state
            self.policy_executor.cancel_event = self.cancel_event
            self.policy_executor.run_id = pipeline_state.get("run_id")
            target_tbl = pipeline_state.get("target_table") or dynamic_config.get("target_table", "employees")
            self.policy_executor.single_table_mode = True
            self.policy_executor.single_table_name = target_tbl
            logger.info(f"PolicyExecutor configured in single_table_mode=True for target_table='{target_tbl}'")
            
            import asyncio
            loop = asyncio.get_event_loop()
            
            def run_pipeline():
                try:
                    success = self.policy_executor.execute()
                    if self.cancel_event and self.cancel_event.is_set():
                        pipeline_state.set("status", "cancelled")
                        pipeline_state.set("completed_at", datetime.utcnow().isoformat())
                        logger.info("17-step pipeline execution terminated cleanly via cancellation")
                    elif success:
                        pipeline_state.set("status", "completed")
                        pipeline_state.set("completed_at", datetime.utcnow().isoformat())
                        pipeline_state.set("progress_percent", 100)
                        logger.info("17-step pipeline completed successfully")
                        
                        # START POLLING WORKER ONLY AFTER FULL STEP 17 COMPLETION
                        if pipeline_state.get("phase_3_9_completed") or pipeline_state.get("phase_3_8_completed"):
                            logger.info("Phase 3.9 completed successfully: Steps 8, 9, 10, 11 executed. Pipeline paused after Step 11.")
                        else:
                            self._start_polling_worker(source_db_config, destination_db_config, policy_file, redis_host, redis_port, hmac_secret)
                    else:
                        pipeline_state.set("status", "error")
                        pipeline_state.add_error("Pipeline execution returned False")
                        logger.error("17-step pipeline execution failed - PollingWorker WILL NOT start.")
                except Exception as e:
                    pipeline_state.set("status", "error")
                    pipeline_state.add_error(str(e))
                    logger.error(f"17-step pipeline execution error: {e}")
                    import traceback
                    traceback.print_exc()
            
            await loop.run_in_executor(None, run_pipeline)
                
        except Exception as e:
            pipeline_state.set("status", "error")
            pipeline_state.add_error(str(e))
            logger.error(f"Pipeline execution error: {e}")
            import traceback
            traceback.print_exc()

    async def pause_pipeline(self) -> dict:
        """Pause active pipeline execution safely"""
        try:
            import time
            current_st = pipeline_state.get("status")
            if current_st in ["running"]:
                start_t = pipeline_state.get("start_time") or time.time()
                last_active = pipeline_state.get("last_active_timestamp") or start_t
                accumulated = pipeline_state.get("accumulated_active_seconds", 0)
                if last_active:
                    accumulated += (time.time() - last_active)
                pipeline_state.set("accumulated_active_seconds", accumulated)
                pipeline_state.set("elapsed_seconds", int(accumulated))
                pipeline_state.set("status", "PAUSED_BY_USER")
                pipeline_state.set("paused_at", datetime.utcnow().isoformat())
                logger.info("Pipeline paused by user.")
                return {"status": "PAUSED_BY_USER", "message": "Pipeline paused."}
            return {"status": current_st, "message": f"Cannot pause pipeline in state {current_st}."}
        except Exception as e:
            logger.error(f"Failed to pause pipeline: {e}")
            raise PipelineException(f"Failed to pause pipeline: {e}")

    async def resume_pipeline(self) -> dict:
        """Resume user-paused pipeline on the SAME run_id"""
        try:
            import time
            current_st = pipeline_state.get("status")
            if current_st in ["PAUSED_BY_USER", "paused"]:
                pipeline_state.set("last_active_timestamp", time.time())
                pipeline_state.set("status", "running")
                pipeline_state.set("paused_at", None)
                logger.info("Pipeline execution resumed by user.")
                return {"status": "running", "message": "Pipeline resumed."}
            return {"status": current_st, "message": f"Cannot resume pipeline from state '{current_st}'. Requires PAUSED_BY_USER."}
        except Exception as e:
            logger.error(f"Failed to resume pipeline: {e}")
            raise PipelineException(f"Failed to resume pipeline: {e}")

    def _process_log_line(self, line: str):
        pipeline_state.add_log(line)
        step = log_parser.get_step_from_log(line)
        if step:
            pipeline_state.set("active_step", step)
            step_name = log_parser.get_step_name(step)
            pipeline_state.set("current_step_name", step_name)

pipeline_controller = PipelineController()
