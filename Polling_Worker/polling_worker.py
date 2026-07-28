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
        # Check table existence via dialect to prevent crashing
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

    def initialize_checkpoints(self):
        """Align high-water marks using the checkpoints metadata table in the destination database."""
        logger.info("Initializing baseline checkpoints from checkpoints metadata table...")
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
                
                # Check source schema keys
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
                
                # Try fetching existing checkpoint from metadata table
                checkpoint_query = text(
                    "SELECT max_id, max_time FROM anonymization_checkpoints WHERE table_name = :table_name"
                )
                res = dest_conn.execute(checkpoint_query, {"table_name": table_name}).fetchone()
                
                if res:
                    # Loaded from existing checkpoints
                    max_id_val, max_time_val = res
                    pk_type = self.checkpoints[table_name]["pk_type"]
                    
                    if max_id_val is not None:
                        if pk_type and ("INT" in pk_type or "SERIAL" in pk_type or "NUMERIC" in pk_type):
                            self.checkpoints[table_name]["max_id"] = int(max_id_val)
                        else:
                            self.checkpoints[table_name]["max_id"] = max_id_val
                            # Re-load seen PKs list for diff mode if string key
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
                    # No checkpoint saved yet. Verify destination completeness BEFORE creating baseline.
                    with self.source_connector.engine.connect() as src_conn:
                        src_count_query = text(f'SELECT COUNT(*) FROM "{table_name}"')
                        src_count = src_conn.execute(src_count_query).scalar() or 0

                        with self.destination_connector.engine.connect() as dst_conn_chk:
                            dst_count_query = text(f'SELECT COUNT(*) FROM "{table_name}"')
                            try:
                                dst_count = dst_conn_chk.execute(dst_count_query).scalar() or 0
                            except Exception:
                                dst_count = 0

                        # STRICT BASELINE VALIDATION GUARD:
                        # If destination row count does not match source row count, REFUSE to create an unsafe checkpoint!
                        if src_count != dst_count:
                            err_msg = f"Baseline synchronization error for table '{table_name}': Source count ({src_count}) does not match Destination count ({dst_count}). Refusing to create unsafe baseline checkpoint."
                            logger.error(err_msg)
                            raise ValueError(err_msg)

                        max_id_val = None
                        max_time_val = None
                        
                        if pk_col:
                            pk_type = self.checkpoints[table_name]["pk_type"]
                            if pk_type and ("INT" in pk_type or "SERIAL" in pk_type or "NUMERIC" in pk_type):
                                max_query = text(f'SELECT MAX("{pk_col}") FROM "{table_name}"')
                                max_id_val = src_conn.execute(max_query).scalar()
                                self.checkpoints[table_name]["max_id"] = max_id_val
                            else:
                                # For UUIDs/String keys, mark all current source keys as seen
                                pk_query = text(f'SELECT "{pk_col}" FROM "{table_name}"')
                                try:
                                    src_pks = [r[0] for r in src_conn.execute(pk_query).fetchall() if r[0] is not None]
                                    with self.destination_connector.engine.connect() as conn:
                                        dest_pks = [r[0] for r in conn.execute(pk_query).fetchall() if r[0] is not None]
                                        self.checkpoints[table_name]["seen_pks"] = set(dest_pks)
                                except Exception:
                                    pass
                                
                        if self.checkpoints[table_name]["timestamp_column"]:
                            t_col = self.checkpoints[table_name]["timestamp_column"]
                            max_time_query = text(f'SELECT MAX("{t_col}") FROM "{table_name}"')
                            max_time_val = src_conn.execute(max_time_query).scalar()
                            if max_time_val is not None:
                                self.checkpoints[table_name]["max_time"] = str(max_time_val)
                        
                        # Save baseline to metadata table
                        save_query = text("""
                            INSERT INTO anonymization_checkpoints (table_name, max_id, max_time)
                            VALUES (:table_name, :max_id, :max_time)
                        """)
                        dest_conn.execute(save_query, {
                            "table_name": table_name,
                            "max_id": str(max_id_val) if max_id_val is not None else None,
                            "max_time": str(max_time_val) if max_time_val is not None else None
                        })
                        logger.info(f"Table '{table_name}': Verified baseline completeness ({src_count} rows). Saved initial baseline checkpoints (Max ID: {max_id_val}, Max Time: {max_time_val})")

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
                    else:
                        logger.debug(f"Table '{table_name}' has no new incremental changes.")
                        
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
