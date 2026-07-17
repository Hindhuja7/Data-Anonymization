"""
Step 8: Change Detection module.
Provides real-time event listening via SQLAlchemy and a background polling worker backup.
"""

import time
import threading
import logging
import re
import json
import os
from typing import Dict, Any, List, Callable, Optional
from sqlalchemy import event, text, Engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class SQLAlchemyEventListener:
    """Listens for real-time INSERT and UPDATE queries at the SQLAlchemy Engine level."""

    def __init__(self, engine: Engine):
        """
        Initialize the event listener.
        
        Args:
            engine: SQLAlchemy Engine instance to listen on
        """
        self.engine = engine
        self.changes_queue: List[Dict[str, Any]] = []
        self.is_listening = False

    def start_listening(self):
        """Register the before_cursor_execute event listener on the engine."""
        if self.is_listening:
            return

        @event.listens_for(self.engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            stmt_upper = statement.strip().upper()
            
            # Match INSERT INTO or UPDATE queries and extract table name
            if stmt_upper.startswith("INSERT") or stmt_upper.startswith("UPDATE"):
                # Regex matching INSERT INTO <table> or UPDATE <table>
                match = re.search(
                    r'(?:INSERT\s+INTO|UPDATE)\s+["`]?([a-zA-Z0-9_-]+)["`]?',
                    statement,
                    re.IGNORECASE
                )
                if match:
                    table_name = match.group(1).lower()
                    op_type = "INSERT" if stmt_upper.startswith("INSERT") else "UPDATE"
                    
                    event_data = {
                        "table_name": table_name,
                        "operation": op_type,
                        "timestamp": time.time(),
                        "source": "orm_realtime"
                    }
                    self.changes_queue.append(event_data)
                    logger.info(
                        f"[Real-Time Change] Detected {op_type} query on table: {table_name}"
                    )

        self.is_listening = True
        logger.info("SQLAlchemy Real-Time Engine Event Listener started")

    def pop_changes(self) -> List[Dict[str, Any]]:
        """Retrieve all accumulated real-time changes and clear the queue."""
        changes = list(self.changes_queue)
        self.changes_queue.clear()
        return changes


class ChangePollingWorker:
    """Background polling worker that checks for database changes periodically."""

    def __init__(
        self,
        engine: Engine,
        policy_path: str = "anonymization_policy.json",
        interval_seconds: float = 30.0,
        change_callback: Callable[[str, str], None] = None
    ):
        """
        Initialize the polling worker.
        
        Args:
            engine: SQLAlchemy Engine instance
            policy_path: Path to the anonymization_policy.json file
            interval_seconds: Polling frequency (default 30s)
            change_callback: Callback function triggered when changes are found,
                            called with (table_name, change_reason)
        """
        self.engine = engine
        self.policy_path = policy_path
        self.interval = interval_seconds
        self.change_callback = change_callback
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # High-water mark state caches
        self.row_counts: Dict[str, int] = {}
        self.max_ids: Dict[str, Any] = {}
        self.max_timestamps: Dict[str, Any] = {}
        
        # Load tables from policy
        self.tables = self._load_tables_from_policy()

    def _load_tables_from_policy(self) -> List[str]:
        """Load configured tables from the policy JSON file."""
        if not os.path.exists(self.policy_path):
            logger.warning(f"PII policy file not found at {self.policy_path}. Using empty table list.")
            return []
        try:
            with open(self.policy_path, "r", encoding="utf-8") as f:
                policy = json.load(f)
            
            # Support both new list-based and old dict-based policy formats
            if "column_policies" in policy:
                tables = set(col["table_name"] for col in policy["column_policies"])
                return list(tables)
            else:
                return list(policy.get("tables", {}).keys())
        except Exception as e:
            logger.error(f"Failed to load tables from policy: {e}")
            return []

    def start(self):
        """Start the background polling worker thread."""
        if self.running:
            return
        
        # Reload tables list
        self.tables = self._load_tables_from_policy()
        if not self.tables:
            logger.warning("No tables configured for polling. Worker not starting.")
            return

        self.running = True
        # Establish initial baseline
        self.poll_once(initialize=True)
        
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Change Polling Worker started with {self.interval}s interval for tables: {self.tables}")

    def stop(self):
        """Stop the background polling worker thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            logger.info("Change Polling Worker stopped")

    def _run_loop(self):
        """Background thread execution loop."""
        while self.running:
            time.sleep(self.interval)
            if not self.running:
                break
            try:
                self.poll_once(initialize=False)
            except Exception as e:
                logger.error(f"Error in polling worker loop: {e}")

    def poll_once(self, initialize: bool = False):
        """
        Check database state for each table once.
        
        Args:
            initialize: If True, caches the current state without triggering callbacks.
        """
        try:
            with self.engine.connect() as conn:
                for table_name in self.tables:
                    self._check_table_state(conn, table_name, initialize)
                conn.rollback()
        except Exception as e:
            logger.error(f"Error connecting to database for polling: {e}")

    def _detect_and_handle_schema_shift(self, conn, table_name: str, inspector) -> bool:
        """
        Detects if new columns have been added to the table.
        If found, extracts 20 samples, scans PII, updates policy to DRAFT, and returns True.
        """
        if not os.path.exists(self.policy_path):
            return False
            
        try:
            # 1. Load current policy
            with open(self.policy_path, "r", encoding="utf-8") as f:
                policy = json.load(f)
                
            column_policies = policy.get("column_policies", [])
            if not column_policies:
                return False
                
            # Get columns currently in policy for this table
            policy_cols = {col["column_name"] for col in column_policies if col["table_name"] == table_name}
            
            # 2. Get live columns from database
            live_cols = inspector.get_columns(table_name)
            
            # Find new columns not in policy
            new_cols = [col for col in live_cols if col["name"] not in policy_cols]
            
            if not new_cols:
                return False
                
            logger.warning(f"[SCHEMA SHIFT DETECTED] Found {len(new_cols)} new columns in table '{table_name}': {[c['name'] for c in new_cols]}")
            
            # Get primary key and foreign key constraints for mapping
            pk_constraint = inspector.get_pk_constraint(table_name)
            pk_cols = pk_constraint.get("constrained_columns", [])
            fkeys = inspector.get_foreign_keys(table_name)
            
            # 3. Process each new column
            for col in new_cols:
                col_name = col["name"]
                col_type = str(col["type"])
                
                # Query 20 random sample values
                random_func = "RANDOM()"
                if "mysql" in str(self.engine.url):
                    random_func = "RAND()"
                elif "mssql" in str(self.engine.url):
                    random_func = "NEWID()"
                    
                query = text(f'SELECT "{col_name}" FROM "{table_name}" ORDER BY {random_func} LIMIT 20')
                try:
                    sample_vals = [str(r[0]) for r in conn.execute(query).fetchall() if r[0] is not None]
                except Exception as e:
                    logger.error(f"Failed to query samples for {table_name}.{col_name}: {e}")
                    sample_vals = []
                
                # Run Combined PII detection dynamically
                from combined_detector import CombinedPIIDetector
                detector = CombinedPIIDetector()
                detection = detector.detect_column(
                    column_name=col_name,
                    data_type=col_type,
                    sample_values=sample_vals,
                    table_name=table_name
                )
                
                # Check PK/FK
                is_primary_key = col_name in pk_cols
                is_foreign_key = False
                fk_details = None
                
                for fk in fkeys:
                    if col_name in fk.get("constrained_columns", []):
                        is_foreign_key = True
                        fk_details = {
                            "referred_table": fk.get("referred_table"),
                            "referred_columns": fk.get("referred_columns")
                        }
                        break
                
                # Build new policy entry
                new_entry = {
                    "table_name": table_name,
                    "column_name": col_name,
                    "is_pii": detection.get("is_pii", False),
                    "pii_type": detection.get("pii_type") if detection.get("is_pii") else None,
                    "confidence": detection.get("confidence", 0.0),
                    "anonymization_technique": detection.get("recommended_technique", "NO_CHANGE") if detection.get("is_pii") else "NO_CHANGE",
                    "reason": detection.get("reasoning", "Automatically detected schema shift column."),
                    "is_primary_key": is_primary_key,
                    "is_foreign_key": is_foreign_key,
                    "foreign_key_details": fk_details,
                    "data_type": col_type,
                    "admin_override": False,
                    "admin_comments": ""
                }
                
                column_policies.append(new_entry)
                logger.info(f"Generated policy for new column {table_name}.{col_name} (PII Type: {new_entry['pii_type']}, Technique: {new_entry['anonymization_technique']})")
            
            # 4. Revert status to DRAFT and save
            policy["policy_metadata"]["status"] = "DRAFT"
            policy["policy_metadata"]["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            policy["policy_metadata"]["comments"].append(
                f"Schema shift automatically detected and scanned new columns in table '{table_name}'."
            )
            
            with open(self.policy_path, "w", encoding="utf-8") as f:
                json.dump(policy, f, indent=2, ensure_ascii=False)
                
            print("\n" + "!" * 80)
            print(f"[SCHEMA SHIFT DETECTED] New columns added in table '{table_name}'!")
            print(f"PII scanned, entries appended to '{self.policy_path}'.")
            print("Policy has been reset to 'DRAFT'. Please review and approve in the terminal.")
            print("!" * 80 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling schema shift: {e}")
            return False

    def _check_table_state(self, conn, table_name: str, initialize: bool, inspector=None):
        """Check schema shifts, row count, max ID, and max timestamp constraints."""
        try:
            if inspector is None:
                from sqlalchemy import inspect
                inspector = inspect(self.engine)
            
            # Detect and handle schema shift first (Scenario B)
            if self._detect_and_handle_schema_shift(conn, table_name, inspector):
                # If schema shifted, policy reverted to DRAFT.
                # Stop further change detection actions on this table until approved.
                return

            # 1. Check Row Count
            count_query = text(f'SELECT COUNT(*) FROM "{table_name}"')
            row_count = conn.execute(count_query).scalar()
            
            # Detect row count changes (insertions/deletions)
            if not initialize and table_name in self.row_counts:
                old_count = self.row_counts[table_name]
                if row_count != old_count:
                    self.row_counts[table_name] = row_count
                    self._trigger_change(table_name, f"Row count changed from {old_count} to {row_count}")
                    return  # Early exit if change found
            self.row_counts[table_name] = row_count

            # 2. Check Auto-Increment Primary Key Max Value
            pk_constraint = inspector.get_pk_constraint(table_name)
            pk_cols = pk_constraint.get("constrained_columns", [])
            
            if pk_cols:
                pk_col = pk_cols[0]
                # Check data type of primary key to ensure it is numeric/comparable
                col_type = next((col["type"] for col in inspector.get_columns(table_name) if col["name"] == pk_col), None)
                
                # Check if it is an integer/numeric type
                if col_type and ("INT" in str(col_type).upper() or "SERIAL" in str(col_type).upper() or "NUMERIC" in str(col_type).upper()):
                    max_id_query = text(f'SELECT MAX("{pk_col}") FROM "{table_name}"')
                    max_id = conn.execute(max_id_query).scalar()
                    
                    if not initialize and table_name in self.max_ids:
                        old_max_id = self.max_ids[table_name]
                        if max_id is not None and (old_max_id is None or max_id > old_max_id):
                            self.max_ids[table_name] = max_id
                            self._trigger_change(table_name, f"New rows inserted (Max primary key {pk_col} changed from {old_max_id} to {max_id})")
                            return
                    self.max_ids[table_name] = max_id

            # 3. Check High-Water Mark Timestamp Columns
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            time_cols = [c for c in columns if c.lower() in ["updated_at", "modified_at", "last_modified", "timestamp"]]
            
            if time_cols:
                time_col = time_cols[0]
                max_time_query = text(f'SELECT MAX("{time_col}") FROM "{table_name}"')
                max_time = conn.execute(max_time_query).scalar()
                
                if not initialize and table_name in self.max_timestamps:
                    old_max_time = self.max_timestamps[table_name]
                    if max_time is not None and (old_max_time is None or max_time > old_max_time):
                        self.max_timestamps[table_name] = max_time
                        self._trigger_change(table_name, f"Rows updated/inserted (Max timestamp {time_col} changed from {old_max_time} to {max_time})")
                        return
                self.max_timestamps[table_name] = max_time

        except SQLAlchemyError as e:
            logger.error(f"Database error during polling for table {table_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error polling table {table_name}: {e}")

    def _trigger_change(self, table_name: str, reason: str):
        """Execute change notification trigger."""
        logger.info(f"[Polling Worker Change] Detected modifications on table: {table_name}. Reason: {reason}")
        if self.change_callback:
            try:
                self.change_callback(table_name, reason)
            except Exception as e:
                logger.error(f"Error executing change callback: {e}")
