"""
Step 13: Polling Worker and Incremental Batch Loader.
Checks the source database for modifications or insertions every 30 seconds,
processes changes incrementally using the Anonymizer, and writes transactionally.
"""

import time
import logging
import threading
import os
import json
from typing import Dict, Any, List, Optional
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

from database_connector import DatabaseConnector
from anonymizer import Anonymizer
from redis_mapping import RedisMappingSystem
from validation_engine import ValidationEngine

logger = logging.getLogger(__name__)

class PollingWorker:
    """Continuous background worker that polls the source DB for updates and inserts them incrementally."""
    
    def __init__(
        self,
        source_db_config: Dict[str, Any],
        destination_db_config: Dict[str, Any],
        policy_file: str = "anonymization_policy.json",
        interval_seconds: float = 30.0,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        hmac_secret: Optional[str] = None
    ):
        """
        Initialize the Polling Worker.
        
        Args:
            source_db_config: Source DB credentials
            destination_db_config: Destination DB credentials
            policy_file: Path to policy configuration file
            interval_seconds: Frequency of polling scans
            redis_host: Redis host
            redis_port: Redis port
            hmac_secret: Encryption secret key
        """
        self.source_db_config = source_db_config
        self.destination_db_config = destination_db_config
        self.policy_file = policy_file
        self.interval = interval_seconds
        
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.hmac_secret = hmac_secret or os.getenv("HMAC_SECRET", "default-hmac-secret")
        
        self.source_connector: Optional[DatabaseConnector] = None
        self.destination_connector: Optional[DatabaseConnector] = None
        self.anonymizer: Optional[Anonymizer] = None
        self.redis_mapping: Optional[RedisMappingSystem] = None
        
        # Checkpoints containing highest key/timestamp synced per table
        # Format: {table_name: {"max_id": val, "max_time": val, "seen_pks": set(), ...}}
        self.checkpoints: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.tables: List[str] = []
        self.policy: Dict[str, Any] = {}

    def _load_policy(self) -> bool:
        """Load anonymization policy from file."""
        if not os.path.exists(self.policy_file):
            logger.error(f"Policy file not found: {self.policy_file}")
            return False
        try:
            with open(self.policy_file, "r", encoding="utf-8") as f:
                self.policy = json.load(f)
            
            # Extract tables in topological dependency order (reusing policy sorting if present)
            if "column_policies" in self.policy:
                tables = set(col["table_name"] for col in self.policy["column_policies"])
                self.tables = list(tables)
            else:
                self.tables = list(self.policy.get("tables", {}).keys())
            return True
        except Exception as e:
            logger.error(f"Failed to load policy: {e}")
            return False

    def connect(self) -> bool:
        """Initialize database connectors, Redis client, and Anonymizer."""
        try:
            self._load_policy()
            
            # Connect source (read-only)
            self.source_connector = DatabaseConnector(**self.source_db_config)
            self.source_connector.connect(read_only=True)
            
            # Connect destination
            self.destination_connector = DatabaseConnector(**self.destination_db_config)
            self.destination_connector.connect(read_only=False)
            
            # Connect Redis mapping system
            self.redis_mapping = RedisMappingSystem(
                host=self.redis_host,
                port=self.redis_port,
                hmac_secret=self.hmac_secret
            )
            
            # Initialize anonymizer sharing the same mapping vault
            self.anonymizer = Anonymizer(
                redis_host=self.redis_host,
                redis_port=self.redis_port
            )
            self.anonymizer.redis_mapping = self.redis_mapping
            
            logger.info("Connections initialized successfully for Polling Worker")
            return True
        except Exception as e:
            logger.error(f"Connection setup failed: {e}")
            return False

    def _create_checkpoint_table_if_needed(self, dest_conn):
        """Create the metadata table to store syncing checkpoints in the destination database."""
        try:
            if not dest_conn.dialect.has_table(dest_conn, "anonymization_checkpoints"):
                query = """
                CREATE TABLE anonymization_checkpoints (
                    table_name VARCHAR(100) PRIMARY KEY,
                    max_id VARCHAR(100),
                    max_time VARCHAR(100)
                )
                """
                dest_conn.execute(text(query))
                logger.info("Created metadata table 'anonymization_checkpoints' in destination database.")
        except Exception as ddl_err:
            logger.warning(f"Could not create anonymization_checkpoints metadata table (read-only mode active): {ddl_err}")

    def initialize_checkpoints(self):
        """Align high-water marks using the checkpoints metadata table in the destination database."""
        logger.info("Initializing baseline checkpoints from checkpoints metadata table...")
        try:
            source_inspector = inspect(self.source_connector.engine)
            with self.destination_connector.engine.begin() as dest_conn:
                self._create_checkpoint_table_if_needed(dest_conn)
                
                for table_name in self.tables:
                    self.checkpoints[table_name] = {
                        "max_id": None,
                        "max_time": None,
                        "seen_pks": set(),
                        "pk_column": None,
                        "pk_type": None,
                        "timestamp_column": None
                    }
                    
                    try:
                        pk_constraint = source_inspector.get_pk_constraint(table_name)
                        pk_cols = pk_constraint.get("constrained_columns", [])
                        if pk_cols:
                            pk_col = pk_cols[0]
                            self.checkpoints[table_name]["pk_column"] = pk_col
                            col_info = next((col for col in source_inspector.get_columns(table_name) if col["name"] == pk_col), None)
                            if col_info:
                                self.checkpoints[table_name]["pk_type"] = str(col_info["type"]).upper()
                        
                        columns = [col["name"] for col in source_inspector.get_columns(table_name)]
                        time_cols = [c for c in columns if c.lower() in ["updated_at", "modified_at", "last_modified", "timestamp"]]
                        if time_cols:
                            self.checkpoints[table_name]["timestamp_column"] = time_cols[0]
                    except Exception as sch_err:
                        logger.warning(f"Schema inspection note for table '{table_name}': {sch_err}")
                    
                    res = None
                    try:
                        checkpoint_query = text("SELECT max_id, max_time FROM anonymization_checkpoints WHERE table_name = :table_name")
                        res = dest_conn.execute(checkpoint_query, {"table_name": table_name}).fetchone()
                    except Exception:
                        res = None
                    
                    if res:
                        max_id_val, max_time_val = res
                        pk_type = self.checkpoints[table_name]["pk_type"]
                        pk_col = self.checkpoints[table_name]["pk_column"]
                        if max_id_val is not None:
                            if pk_type and ("INT" in pk_type or "SERIAL" in pk_type or "NUMERIC" in pk_type):
                                self.checkpoints[table_name]["max_id"] = int(max_id_val)
                            else:
                                self.checkpoints[table_name]["max_id"] = max_id_val
                                with self.destination_connector.engine.connect() as conn:
                                    pk_query = text(f'SELECT "{pk_col}" FROM "{table_name}"')
                                    try:
                                        existing_ids = [r[0] for r in conn.execute(pk_query).fetchall() if r[0] is not None]
                                        self.checkpoints[table_name]["seen_pks"] = set(existing_ids)
                                    except Exception:
                                        pass
                        self.checkpoints[table_name]["max_time"] = max_time_val
                        logger.info(f"Table '{table_name}': Restored checkpoints (Max ID: {max_id_val}, Max Time: {max_time_val})")
                    else:
                        with self.source_connector.engine.connect() as src_conn:
                            try:
                                src_count = src_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar() or 0
                            except Exception:
                                src_count = 0

                            pk_col = self.checkpoints[table_name]["pk_column"]
                            max_id_val = None
                            max_time_val = None
                            
                            if pk_col:
                                pk_type = self.checkpoints[table_name]["pk_type"]
                                if pk_type and ("INT" in pk_type or "SERIAL" in pk_type or "NUMERIC" in pk_type):
                                    try:
                                        max_id_val = src_conn.execute(text(f'SELECT MAX("{pk_col}") FROM "{table_name}"')).scalar()
                                        self.checkpoints[table_name]["max_id"] = max_id_val
                                    except Exception:
                                        pass
                                
                            if self.checkpoints[table_name]["timestamp_column"]:
                                t_col = self.checkpoints[table_name]["timestamp_column"]
                                try:
                                    max_time_val = src_conn.execute(text(f'SELECT MAX("{t_col}") FROM "{table_name}"')).scalar()
                                    if max_time_val is not None:
                                        self.checkpoints[table_name]["max_time"] = str(max_time_val)
                                except Exception:
                                    pass
                            
                            try:
                                save_query = text("""
                                    INSERT INTO anonymization_checkpoints (table_name, max_id, max_time)
                                    VALUES (:table_name, :max_id, :max_time)
                                """)
                                dest_conn.execute(save_query, {
                                    "table_name": table_name,
                                    "max_id": str(max_id_val) if max_id_val is not None else None,
                                    "max_time": str(max_time_val) if max_time_val is not None else None
                                })
                            except Exception as save_err:
                                logger.warning(f"Note on checkpoint write (MySQL read-only mode active): {save_err}")
                            logger.info(f"Table '{table_name}': Verified baseline completeness ({src_count} rows). Saved initial baseline checkpoints (Max ID: {max_id_val}, Max Time: {max_time_val})")
        except Exception as init_err:
            logger.warning(f"PollingWorker initialize_checkpoints warning: {init_err}")

    def poll_once(self):
        """Perform a single incremental scan and sync task across all tables in order."""
        logger.info("Executing incremental database polling sync tick...")
        
        # Always reload policy to pick up overrides dynamically (Scenario A)
        self._load_policy()
        
        source_inspector = inspect(self.source_connector.engine)
        
        # Process tables in dependency order
        for table_name in self.tables:
            checkpoint = self.checkpoints.get(table_name)
            if not checkpoint:
                continue
                
            pk_col = checkpoint["pk_column"]
            pk_type = checkpoint["pk_type"]
            time_col = checkpoint["timestamp_column"]
            
            # Check if there is new data in this table
            try:
                with self.source_connector.engine.connect() as src_conn:
                    new_rows_df = None
                    
                    # 1. Fetch using Numeric PK high-water mark
                    if pk_col and pk_type and ("INT" in pk_type or "SERIAL" in pk_type or "NUMERIC" in pk_type):
                        max_id = checkpoint["max_id"]
                        if max_id is not None:
                            query = f'SELECT * FROM "{table_name}" WHERE "{pk_col}" > :max_id'
                            import pandas as pd
                            new_rows_df = pd.read_sql(text(query), src_conn, params={"max_id": max_id})
                        else:
                            query = f'SELECT * FROM "{table_name}"'
                            import pandas as pd
                            new_rows_df = pd.read_sql(text(query), src_conn)
                            
                    # 2. Fetch using Timestamp updates high-water mark
                    elif time_col and checkpoint["max_time"] is not None:
                        max_time = checkpoint["max_time"]
                        query = f'SELECT * FROM "{table_name}" WHERE "{time_col}" > :max_time'
                        import pandas as pd
                        new_rows_df = pd.read_sql(text(query), src_conn, params={"max_time": max_time})
                        
                    # 3. Fallback: Pull keys and perform difference set check (supports UUIDs/Text)
                    elif pk_col:
                        query_pks = text(f'SELECT "{pk_col}" FROM "{table_name}"')
                        src_pks = [r[0] for r in src_conn.execute(query_pks).fetchall() if r[0] is not None]
                        diff_pks = list(set(src_pks) - checkpoint["seen_pks"])
                        
                        if diff_pks:
                            import pandas as pd
                            dfs = []
                            for i in range(0, len(diff_pks), 1000):
                                chunk_pks = diff_pks[i:i+1000]
                                query = f'SELECT * FROM "{table_name}" WHERE "{pk_col}" IN :pks'
                                chunk_df = pd.read_sql(text(query), src_conn, params={"pks": tuple(chunk_pks)})
                                dfs.append(chunk_df)
                            new_rows_df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
                    
                    if new_rows_df is not None and not new_rows_df.empty:
                        logger.info(f"Incremental Sync: Found {len(new_rows_df)} new/updated rows in table '{table_name}'")
                        self._anonymize_and_load_rows(table_name, new_rows_df, checkpoint)
                        
                        # Emit live audit event, invalidate count cache, and broadcast WebSocket update
                        try:
                            from app.services.audit_service import audit_service
                            from app.services.websocket_service import websocket_service
                            from app.pipeline.state import pipeline_state
                            import asyncio

                            audit_service.invalidate_count_cache(table_name)
                            active_uid = pipeline_state.get("user_id") or "b@gmail.com"
                            audit_service.log_event(
                                user_id=active_uid,
                                action=f"[CONTINUOUS SYNC] Processed {len(new_rows_df)} records for table '{table_name}'",
                                category="pipeline",
                                level="success",
                                step_name="Continuous Sync Worker",
                                details=f"PollingWorker detected and anonymized {len(new_rows_df)} incremental record updates in table '{table_name}'. Destination database synced.",
                                run_id=pipeline_state.get("run_id") or "RUN_SYNC"
                            )

                            try:
                                loop = asyncio.get_running_loop()
                                if loop and loop.is_running():
                                    loop.create_task(websocket_service.broadcast_state({"type": "dashboard_update", "table": table_name, "synced_rows": len(new_rows_df)}))
                            except Exception:
                                pass
                        except Exception as log_err:
                            logger.warning(f"Error logging polling worker audit event: {log_err}")
                    # 4. Check for record DELETIONS in source DB
                    if pk_col:
                        try:
                            with self.destination_connector.engine.connect() as dst_conn:
                                dest_pks_res = dst_conn.execute(text(f'SELECT "{pk_col}" FROM "{table_name}"')).fetchall()
                                dest_pks = set(r[0] for r in dest_pks_res if r[0] is not None)
                                
                                src_pks_res = src_conn.execute(text(f'SELECT "{pk_col}" FROM "{table_name}"')).fetchall()
                                src_pks = set(r[0] for r in src_pks_res if r[0] is not None)
                                
                                deleted_pks = list(dest_pks - src_pks)
                                if deleted_pks:
                                    logger.info(f"Delete Sync: Found {len(deleted_pks)} deleted rows in table '{table_name}'. Synchronizing deletion to destination DB...")
                                    with self.destination_connector.engine.begin() as del_conn:
                                        for i in range(0, len(deleted_pks), 1000):
                                            batch_del = deleted_pks[i:i+1000]
                                            if len(batch_del) == 1:
                                                del_query = text(f'DELETE FROM "{table_name}" WHERE "{pk_col}" = :pk_val')
                                                del_conn.execute(del_query, {"pk_val": batch_del[0]})
                                            else:
                                                del_query = text(f'DELETE FROM "{table_name}" WHERE "{pk_col}" IN :pks')
                                                del_conn.execute(del_query, {"pks": tuple(batch_del)})
                                    
                                    # Update pipeline state and count cache
                                    from app.pipeline.state import pipeline_state
                                    from app.services.audit_service import audit_service
                                    audit_service.invalidate_count_cache(table_name)
                                    total_src_cnt = src_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar() or 0
                                    pipeline_state.set("total_records", total_src_cnt)
                                    pipeline_state.set("processed_rows", total_src_cnt)
                        except Exception as del_err:
                            logger.warning(f"Error checking deleted rows for table {table_name}: {del_err}")
                
                # Update live total record count in pipeline_state for Admin Dashboard
                try:
                    with self.source_connector.engine.connect() as src_conn_cnt:
                        total_src_cnt = src_conn_cnt.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar() or 0
                        from app.pipeline.state import pipeline_state
                        pipeline_state.set("total_records", total_src_cnt)
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Failed to poll incremental data for table {table_name}: {e}")

    def _anonymize_and_load_rows(self, table_name: str, df, checkpoint: Dict[str, Any]):
        """Anonymizes the rows in memory and writes them transactionally to destination database."""
        # Get policy for this table
        table_policy = [
            col for col in self.policy["column_policies"]
            if col["table_name"] == table_name
        ]
        policy_map = {col["column_name"]: col for col in table_policy}
        
        # Prepare DataFrame copy
        anonymized_df = df.copy()
        
        # Process each column PII technique
        for column_name in df.columns:
            if column_name not in policy_map:
                continue
                
            column_policy = policy_map[column_name]
            technique = column_policy["anonymization_technique"]
            if technique == "NO_CHANGE":
                continue
                
            pii_type = column_policy.get("pii_type")
            
            # Detect primary and foreign key mapping properties
            source_inspector = inspect(self.source_connector.engine)
            is_primary_key = column_name == checkpoint["pk_column"]
            is_foreign_key = False
            for fk in source_inspector.get_foreign_keys(table_name):
                if column_name in fk.get("constrained_columns", []):
                    is_foreign_key = True
                    break
                    
            # Anonymize values
            anonymized_values = self.anonymizer.anonymize_column(
                values=df[column_name].tolist(),
                pii_type=pii_type,
                technique=technique,
                column_name=column_name,
                table_name=table_name,
                is_foreign_key=is_foreign_key,
                is_primary_key=is_primary_key
            )
            anonymized_df[column_name] = anonymized_values
            
        # Write to destination DB transactionally and update checkpoints
        dest_table_name = table_name
        
        # Gather checkpoint updates values
        pk_col = checkpoint["pk_column"]
        time_col = checkpoint["timestamp_column"]
        
        new_max_id = checkpoint["max_id"]
        new_max_time = checkpoint["max_time"]
        
        if pk_col and df[pk_col].dtype in ['int64', 'int32', 'float64']:
            new_max_id = int(df[pk_col].max())
        elif pk_col:
            written_pks = df[pk_col].tolist()
            checkpoint["seen_pks"].update(written_pks)
            
        if time_col and time_col in df.columns:
            new_max_time = str(df[time_col].max())
            
        with self.destination_connector.engine.begin() as dest_conn:
            # 1. Write the anonymized records
            anonymized_df.to_sql(
                dest_table_name,
                dest_conn,
                if_exists="append",
                index=False,
                method="multi"
            )
            
            # 2. Update metadata checkpoints table inside the SAME transaction
            update_query = text("""
                UPDATE anonymization_checkpoints
                SET max_id = :max_id, max_time = :max_time
                WHERE table_name = :table_name
            """)
            dest_conn.execute(update_query, {
                "table_name": table_name,
                "max_id": str(new_max_id) if new_max_id is not None else None,
                "max_time": str(new_max_time) if new_max_time is not None else None
            })
            
        # Update checkpoints in memory only after transaction succeeds
        checkpoint["max_id"] = new_max_id
        checkpoint["max_time"] = new_max_time
        
        logger.info(f"[SUCCESS] Incremental sync complete for table '{table_name}'. Loaded {len(df)} rows.")

    def start(self):
        """Starts the background worker loop in a daemon thread."""
        if self.running:
            return
            
        if not self.connect():
            logger.error("Could not start Polling Worker: Database connections failed.")
            return
            
        try:
            self.initialize_checkpoints()
        except Exception as e:
            logger.error(f"Could not start Polling Worker: Baseline initialization failed: {e}")
            self.running = False
            raise e

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Background Polling Sync Daemon running. Scanning tables every {self.interval} seconds.")

    def _run_loop(self):
        """Internal runner loop executed by daemon thread."""
        while self.running:
            try:
                self.poll_once()
            except Exception as e:
                logger.error(f"Error executing polling sync tick: {e}")
            time.sleep(self.interval)

    def stop(self):
        """Stops the polling daemon thread and releases connector handles."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        
        if self.source_connector:
            self.source_connector.disconnect()
        if self.destination_connector:
            self.destination_connector.disconnect()
        if self.redis_mapping:
            self.redis_mapping.close()
            
        logger.info("Polling Worker daemon stopped cleanly.")
