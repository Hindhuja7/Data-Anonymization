"""
Policy Execution Engine for Database Anonymization

Handles:
- Policy approval validation
- Chunk-based database reading and processing
- Referential integrity preservation
- Destination database schema creation
- Transaction safety with rollback
- Progress logging
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Path bootstrapper to allow flat imports across layers
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _layer in ["01_Connection_Extraction", "02_Enterprise_Classification", "03_PII_Detection", "04_Change_Detection", "05_Redis_Hash_Vault", "06_Redis_AOF_Safety", "07_Polling_Worker", "08_Destination_Loader", "09_Validation_Engine", "10_Audit_Report", "11_Admin_Dashboard", "12_Approval_Workflow"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from database_connector import DatabaseConnector
from schema_extractor import SchemaExtractor
from anonymizer import Anonymizer
from redis_mapping import RedisMappingSystem
from approval_workflow import ApprovalWorkflow
from validation_engine import ValidationEngine


class PolicyExecutor:
    """
    Executes anonymization policies on databases with chunk processing.
    """
    
    def __init__(
        self,
        source_db_config: Dict[str, Any],
        destination_db_config: Dict[str, Any],
        policy_file: str = "anonymization_policy.json",
        chunk_size: int = 5000,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        hmac_secret: Optional[str] = None,
        destination_table_prefix: str = "anon_"
    ):
        """
        Initialize policy executor.
        
        Args:
            source_db_config: Source database configuration
            destination_db_config: Destination database configuration
            policy_file: Path to anonymization policy file
            chunk_size: Number of rows to process per chunk
            redis_host: Redis host for mapping
            redis_port: Redis port
            hmac_secret: HMAC secret for secure key generation
            destination_table_prefix: Prefix for destination table names
        """
        self.source_db_config = source_db_config
        self.destination_db_config = destination_db_config
        self.policy_file = policy_file
        self.chunk_size = chunk_size
        self.hmac_secret = hmac_secret or os.getenv("HMAC_SECRET", "default-hmac-secret")
        self.destination_table_prefix = destination_table_prefix
        self.redis_host = redis_host
        self.redis_port = redis_port
        
        self.source_connector = None
        self.destination_connector = None
        self.schema_extractor = None
        self.anonymizer = None
        self.redis_mapping = None
        self.policy = None
        self.source_schema = None
        
        # Progress tracking
        self.progress = {
            "start_time": None,
            "end_time": None,
            "tables_processed": [],
            "total_rows_processed": 0,
            "failed_chunks": [],
            "current_table": None,
            "current_chunk": 0,
            "total_chunks": 0
        }
    
    def load_policy(self) -> bool:
        """
        Load and validate the anonymization policy.
        
        Returns:
            True if policy is valid and approved, False otherwise
        """
        try:
            with open(self.policy_file, 'r') as f:
                self.policy = json.load(f)
            
            # Check policy approval status
            if not ApprovalWorkflow.is_policy_approved(self.policy):
                return False
            return True
            
        except FileNotFoundError:
            print(f"ERROR: Policy file not found: {self.policy_file}")
            return False
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON in policy file: {self.policy_file}")
            return False
    
    def connect_databases(self) -> bool:
        """
        Connect to both source and destination databases.
        
        Returns:
            True if connections successful, False otherwise
        """
        try:
            # Connect to source database
            self.source_connector = DatabaseConnector(**self.source_db_config)
            self.source_connector.connect(read_only=True)
            print(f"[OK] Connected to source database: {self.source_db_config['database_name']}")
            
            # Connect to destination database
            self.destination_connector = DatabaseConnector(**self.destination_db_config)
            self.destination_connector.connect(read_only=False)
            print(f"[OK] Connected to destination database: {self.destination_db_config['database_name']}")
            
            # Initialize schema extractor
            self.schema_extractor = SchemaExtractor(self.source_connector.engine)
            
            # Initialize Redis mapping (shared with anonymizer)
            self.redis_mapping = RedisMappingSystem(
                host=self.redis_host,
                port=self.redis_port,
                hmac_secret=self.hmac_secret
            )
            
            # Initialize anonymizer with shared Redis mapping
            self.anonymizer = Anonymizer(
                redis_host=self.redis_host,
                redis_port=self.redis_port
            )
            # Use the same Redis mapping instance
            self.anonymizer.redis_mapping = self.redis_mapping
            
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to connect to databases: {e}")
            return False
    
    def get_source_schema(self) -> Dict[str, Any]:
        """
        Extract schema from source database.
        
        Returns:
            Dictionary mapping table names to schema information
        """
        table_schemas = self.schema_extractor.get_all_schemas()
        self.source_schema = {schema["table_name"]: schema for schema in table_schemas}
        print(f"[OK] Extracted schema for {len(self.source_schema)} tables")
        return self.source_schema
    
    def determine_table_processing_order(self) -> List[str]:
        """
        Determine table processing order based on foreign key dependencies.
        Tables with no dependencies are processed first.
        
        Returns:
            List of table names in processing order
        """
        # Build dependency graph
        dependencies = {}
        all_tables = set(self.source_schema.keys())
        
        for table_name, schema in self.source_schema.items():
            deps = set()
            for fk in schema.get("foreign_keys", []):
                referred_table = fk.get("referred_table")
                if referred_table in all_tables:
                    deps.add(referred_table)
            dependencies[table_name] = deps
        
        # Topological sort
        processed = set()
        order = []
        
        while len(processed) < len(all_tables):
            # Find tables with no unprocessed dependencies
            ready = [
                table for table in all_tables - processed
                if dependencies[table].issubset(processed)
            ]
            
            if not ready:
                # Circular dependency or missing table - process remaining
                ready = list(all_tables - processed)
            
            order.extend(ready)
            processed.update(ready)
        
        print(f"[OK] Table processing order: {' -> '.join(order)}")
        return order
    
    def analyze_pk_fk_relationships(self):
        """Analyze PK/FK relationships in the approved policy and report technical keys."""
        print("PK/FK Relationship Analysis:")
        print("-" * 80)
        
        for table_name, schema in self.source_schema.items():
            # Get policy for this table
            table_policy = [
                col for col in self.policy["column_policies"]
                if col["table_name"] == table_name
            ]
            
            policy_map = {
                col["column_name"]: col for col in table_policy
            }
            
            # Check primary keys
            for pk in schema.get("primary_keys", []):
                if pk in policy_map:
                    technique = policy_map[pk]["anonymization_technique"]
                    pii_type = policy_map[pk].get("pii_type")
                    
                    if technique != "NO_CHANGE":
                        print(f"[WARN] Primary Key: {table_name}.{pk}")
                        print(f"  Technique: {technique}")
                        print(f"  PII Type: {pii_type}")
                        print(f"  Note: This is a technical primary key. Ensure consistent mapping is applied.")
                        print()
            
            # Check foreign keys
            for fk in schema.get("foreign_keys", []):
                fk_col = fk["constrained_columns"][0]
                if fk_col in policy_map:
                    technique = policy_map[fk_col]["anonymization_technique"]
                    pii_type = policy_map[fk_col].get("pii_type")
                    
                    if technique != "NO_CHANGE":
                        print(f"[WARN] Foreign Key: {table_name}.{fk_col}")
                        print(f"  References: {fk['referred_table']}.{fk['referred_columns'][0]}")
                        print(f"  Technique: {technique}")
                        print(f"  PII Type: {pii_type}")
                        print(f"  Note: Ensure same transformation as referenced primary key.")
                        print()
        
        print("[OK] PK/FK analysis complete")
    
    def get_destination_data_type(self, source_type: str, technique: str) -> str:
        """
        Determine appropriate destination data type based on source type and anonymization technique.
        
        Args:
            source_type: Original source column data type
            technique: Anonymization technique to be applied
            
        Returns:
            Appropriate destination data type
        """
        # If NO_CHANGE, preserve original type
        if technique == "NO_CHANGE":
            return source_type
        
        # HASHING produces 64-character SHA-256 hex strings
        if technique == "HASHING":
            return "VARCHAR(64)"
        
        # MASKING produces strings with preserved format
        if technique == "MASKING":
            # Use TEXT to accommodate any length
            return "TEXT"
        
        # TOKENIZATION produces realistic fake values
        if technique == "TOKENIZATION":
            # Use TEXT to accommodate any length
            return "TEXT"
        
        # REDACTION produces redacted strings
        if technique == "REDACTION":
            return "TEXT"
        
        # DIFFERENTIAL_PRIVACY preserves numeric types
        if technique == "DIFFERENTIAL_PRIVACY":
            return source_type
        
        # Default: preserve original type
        return source_type
    
    def validate_destination_schema(self) -> bool:
        """
        Validate that destination column types can accommodate anonymization output.
        
        Returns:
            True if validation passes, False otherwise
        """
        engine = ValidationEngine(
            source_connector=self.source_connector,
            destination_connector=self.destination_connector,
            source_schema=self.source_schema,
            policy=self.policy
        )
        return engine.validate_destination_schema()
    
    def create_destination_schema(self) -> bool:
        """
        Recreate schema in destination database using appropriate data types for anonymization.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.destination_connector.engine.begin() as conn:
                for table_name, schema in self.source_schema.items():
                    # Use original table name for destination
                    dest_table_name = table_name
                    
                    # Drop table if exists
                    if "sqlite" in str(self.destination_connector.engine.url):
                        drop_sql = f'DROP TABLE IF EXISTS "{dest_table_name}"'
                    else:
                        drop_sql = f'DROP TABLE IF EXISTS "{dest_table_name}" CASCADE'
                    conn.execute(text(drop_sql))
                    
                    # Get policy for this table
                    table_policy = [
                        col for col in self.policy["column_policies"]
                        if col["table_name"] == table_name
                    ]
                    
                    policy_map = {
                        col["column_name"]: col for col in table_policy
                    }
                    
                    # Create table with adjusted data types
                    columns_sql = []
                    for col in schema["columns"]:
                        col_name = col["column_name"]
                        source_type = col["data_type"]
                        is_nullable = col.get("is_nullable", True)
                        
                        # Get anonymization technique for this column
                        technique = "NO_CHANGE"
                        if col_name in policy_map:
                            technique = policy_map[col_name]["anonymization_technique"]
                        
                        # Determine appropriate destination data type
                        dest_type = self.get_destination_data_type(source_type, technique)
                        
                        col_sql = f'"{col_name}" {dest_type}'
                        if not is_nullable:
                            col_sql += " NOT NULL"
                        columns_sql.append(col_sql)
                    
                    # Add primary key constraints
                    if schema.get("primary_keys"):
                        pk_cols = ', '.join([f'"{pk}"' for pk in schema["primary_keys"]])
                        columns_sql.append(f"PRIMARY KEY ({pk_cols})")
                    
                    create_sql = f'CREATE TABLE "{dest_table_name}" ({", ".join(columns_sql)})'
                    conn.execute(text(create_sql))
                    
                    print(f"[OK] Created table: {dest_table_name}")
                
                # Add foreign key constraints after all tables are created
                for table_name, schema in self.source_schema.items():
                    dest_table_name = table_name
                    
                    for fk in schema.get("foreign_keys", []):
                        fk_col = fk["constrained_columns"][0]
                        ref_table = fk["referred_table"]
                        ref_col = fk["referred_columns"][0]
                        dest_ref_table = ref_table
                        
                        fk_sql = f'''
                        ALTER TABLE "{dest_table_name}" 
                        ADD CONSTRAINT fk_{dest_table_name}_{fk_col} 
                        FOREIGN KEY ("{fk_col}") 
                        REFERENCES "{dest_ref_table}" ("{ref_col}")
                        '''
                        try:
                            conn.execute(text(fk_sql))
                            print(f"[OK] Added foreign key: {dest_table_name}.{fk_col} -> {dest_ref_table}.{ref_col}")
                        except Exception as e:
                            print(f"Warning: Could not add foreign key {dest_table_name}.{fk_col}: {e}")
            
            print("[OK] Destination schema created successfully")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to create destination schema: {e}")
            return False
    
    def get_table_row_count(self, table_name: str) -> int:
        """
        Get total row count for a table from source database.
        
        Args:
            table_name: Name of the table
        
        Returns:
            Total row count
        """
        try:
            query = f'SELECT COUNT(*) FROM "{table_name}"'
            result = pd.read_sql(query, self.source_connector.engine)
            return result.iloc[0, 0]
        except Exception as e:
            print(f"ERROR: Failed to get row count for {table_name}: {e}")
            return 0
    
    def get_destination_table_row_count(self, table_name: str) -> int:
        """
        Get total row count for a table from destination database.
        
        Args:
            table_name: Name of the table
        
        Returns:
            Total row count
        """
        try:
            query = f'SELECT COUNT(*) FROM "{table_name}"'
            result = pd.read_sql(query, self.destination_connector.engine)
            return result.iloc[0, 0]
        except Exception as e:
            print(f"ERROR: Failed to get destination row count for {table_name}: {e}")
            return 0
    
    def process_table_chunk(
        self,
        table_name: str,
        offset: int,
        chunk_size: int,
        table_policy: List[Dict[str, Any]]
    ) -> Tuple[bool, int]:
        """
        Process a single chunk of rows from a table.
        
        Args:
            table_name: Name of the table
            offset: Starting row offset
            chunk_size: Number of rows to process
            table_policy: Policy for this table's columns
        
        Returns:
            Tuple of (success, rows_processed)
        """
        try:
            # Read chunk from source database
            query = f'SELECT * FROM "{table_name}" LIMIT {chunk_size} OFFSET {offset}'
            df = pd.read_sql(query, self.source_connector.engine)
            
            if df.empty:
                return True, 0
            
            # Create column policy map
            policy_map = {
                col["column_name"]: col for col in table_policy
            }
            
            # Generate row indices for this chunk
            row_indices = list(range(offset, offset + len(df)))
            
            # Process each column
            anonymized_df = df.copy()
            
            for column_name in df.columns:
                if column_name not in policy_map:
                    continue
                
                column_policy = policy_map[column_name]
                technique = column_policy["anonymization_technique"]
                
                if technique == "NO_CHANGE":
                    continue
                
                pii_type = column_policy.get("pii_type")
                
                # Get schema information for this column
                table_schema = self.source_schema[table_name]
                is_primary_key = column_name in table_schema.get("primary_keys", [])
                is_foreign_key = False
                for fk in table_schema.get("foreign_keys", []):
                    if column_name in fk.get("constrained_columns", []):
                        is_foreign_key = True
                        break
                
                # Apply anonymization based on technique
                anonymized_values = self.anonymizer.anonymize_column(
                    values=df[column_name].tolist(),
                    pii_type=pii_type,
                    technique=technique,
                    column_name=column_name,
                    table_name=table_name,
                    is_foreign_key=is_foreign_key,
                    is_primary_key=is_primary_key,
                    row_indices=row_indices
                )
                anonymized_df[column_name] = anonymized_values
            
            # Write to destination database within transaction
            dest_table_name = table_name  # Use original table name
            with self.destination_connector.engine.begin() as conn:
                anonymized_df.to_sql(
                    dest_table_name,
                    conn,
                    if_exists="append",
                    index=False,
                    method="multi"
                )
            
            return True, len(df)
            
        except Exception as e:
            print(f"ERROR: Failed to process chunk {offset}-{offset+chunk_size} for {table_name}: {e}")
            return False, 0
    
    def process_table(self, table_name: str) -> bool:
        """
        Process all rows for a single table in chunks.
        
        Args:
            table_name: Name of the table
        
        Returns:
            True if successful, False otherwise
        """
        # Get policy for this table
        table_policy = [
            col for col in self.policy["column_policies"]
            if col["table_name"] == table_name
        ]
        
        if not table_policy:
            print(f"Warning: No policy found for table {table_name}")
            return True
        
        # Get total row count
        total_rows = self.get_table_row_count(table_name)
        if total_rows == 0:
            print(f"Table {table_name} is empty, skipping")
            return True
        
        # Calculate chunks
        total_chunks = (total_rows + self.chunk_size - 1) // self.chunk_size
        self.progress["current_table"] = table_name
        self.progress["total_chunks"] = total_chunks
        
        print(f"\nProcessing table: {table_name}")
        print(f"Total rows: {total_rows:,}")
        print(f"Chunk size: {self.chunk_size:,}")
        print(f"Total chunks: {total_chunks}")
        
        # Process chunks
        rows_processed = 0
        failed_chunks = []
        
        for chunk_num in range(total_chunks):
            offset = chunk_num * self.chunk_size
            self.progress["current_chunk"] = chunk_num + 1
            
            success, chunk_rows = self.process_table_chunk(
                table_name, offset, self.chunk_size, table_policy
            )
            
            if success:
                rows_processed += chunk_rows
                self.progress["total_rows_processed"] += chunk_rows
                
                # Progress logging
                percent_complete = (rows_processed / total_rows) * 100
                print(f"Table: {table_name}")
                print(f"Chunk: {chunk_num + 1}")
                print(f"Processed: {rows_processed} / {total_rows}")
                print(f"Progress: {percent_complete:.0f}%")
                print()
            else:
                failed_chunks.append(chunk_num)
                print(f"Table: {table_name}")
                print(f"Chunk: {chunk_num + 1}")
                print(f"[FAIL] Failed")
                print()
        
        # Log results
        if failed_chunks:
            print(f"[FAIL] Table {table_name} completed with {len(failed_chunks)} failed chunks")
            self.progress["failed_chunks"].extend([
                {"table": table_name, "chunk": chunk} for chunk in failed_chunks
            ])
        else:
            print(f"[OK] Table {table_name} completed successfully ({rows_processed:,} rows)")
        
        self.progress["tables_processed"].append({
            "table_name": table_name,
            "total_rows": total_rows,
            "rows_processed": rows_processed,
            "failed_chunks": len(failed_chunks)
        })
        
        return len(failed_chunks) == 0
    
    def execute(self) -> bool:
        """
        Execute the complete anonymization pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        self.progress["start_time"] = datetime.now()
        
        print("=" * 80)
        print("ANONYMIZATION POLICY EXECUTION")
        print("=" * 80)
        
        # Step 1: Load and validate policy
        print("\n[STEP 1] Loading and validating policy...")
        if not self.load_policy():
            return False
        
        # Step 2: Connect to databases
        print("\n[STEP 2] Connecting to databases...")
        if not self.connect_databases():
            return False
        
        # Step 3: Extract source schema
        print("\n[STEP 3] Extracting source schema...")
        self.get_source_schema()
        
        # Step 4: Determine table processing order
        print("\n[STEP 4] Determining table processing order...")
        table_order = self.determine_table_processing_order()
        
        # Step 5: Analyze PK/FK relationships in policy
        print("\n[STEP 5] Analyzing PK/FK relationships in policy...")
        self.analyze_pk_fk_relationships()
        
        # Step 6: Create destination schema
        print("\n[STEP 6] Creating destination schema...")
        if not self.create_destination_schema():
            return False
        
        # Step 6.5: Validate destination schema
        print("\n[STEP 6.5] Validating destination schema...")
        if not self.validate_destination_schema():
            print("WARNING: Destination schema validation failed, but proceeding anyway")
        
        # Step 7: Process tables in order
        print("\n[STEP 7] Processing tables...")
        all_success = True
        
        for table_name in table_order:
            success = self.process_table(table_name)
            if not success:
                all_success = False
        
        # Step 8: Validate results
        print("\n[STEP 8] Validating results...")
        validation_passed = self.validate_results()
        if not validation_passed:
            all_success = False
        
        self.progress["end_time"] = datetime.now()
        duration = (self.progress["end_time"] - self.progress["start_time"]).total_seconds()
        
        # Step 9 (Step 16 in 17-steps): Generate Audit Report
        print("\n[STEP 9] Generating Audit & Compliance Report...")
        try:
            from audit_report_generator import AuditReportGenerator
            
            table_reports = getattr(self, "validation_engine", None)
            reports_list = table_reports.table_reports if table_reports else []
            
            stats = {
                "duration_seconds": duration,
                "tables_processed": len(self.progress["tables_processed"]),
                "total_rows_processed": self.progress["total_rows_processed"]
            }
            
            generator = AuditReportGenerator(policy=self.policy)
            generator.generate_report(
                table_reports=reports_list,
                execution_stats=stats,
                output_dir="C:/Users/lokin/.gemini/antigravity/scratch/Data-Anonymization",
                approved_by=self.policy.get("policy_metadata", {}).get("approved_by", "Admin")
            )
            print("[OK] Compliance report and certificate generated successfully.")
        except Exception as e:
            print(f"WARNING: Failed to generate compliance report: {e}")
        
        # Final summary
        print("\n" + "=" * 80)
        print("EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Tables processed: {len(self.progress['tables_processed'])}")
        print(f"Total rows processed: {self.progress['total_rows_processed']:,}")
        print(f"Failed chunks: {len(self.progress['failed_chunks'])}")
        
        if all_success and len(self.progress["failed_chunks"]) == 0:
            print("\n[OK] EXECUTION COMPLETED SUCCESSFULLY")
        else:
            print("\n[FAIL] EXECUTION COMPLETED WITH ERRORS")
        
        return all_success and len(self.progress["failed_chunks"]) == 0
    
    def validate_results(self) -> bool:
        """Validate anonymization results."""
        self.validation_engine = ValidationEngine(
            source_connector=self.source_connector,
            destination_connector=self.destination_connector,
            source_schema=self.source_schema,
            policy=self.policy
        )
        return self.validation_engine.validate_results(self.progress["tables_processed"])
    
    def cleanup(self):
        """Clean up resources."""
        if self.source_connector:
            self.source_connector.disconnect()
        if self.destination_connector:
            self.destination_connector.disconnect()
        if self.redis_mapping:
            self.redis_mapping.close()
