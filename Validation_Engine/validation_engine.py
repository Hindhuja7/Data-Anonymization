"""
Anonymized database validation engine.
Compares destination tables against source tables for data type changes and count matching.
"""

import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

class ValidationEngine:
    """Validates destination database schema compatibility and row count matches."""
    
    def __init__(self, source_connector, destination_connector, source_schema, policy):
        self.source_connector = source_connector
        self.destination_connector = destination_connector
        self.source_schema = source_schema
        self.policy = policy

    def get_destination_data_type(self, source_type: str, technique: str) -> str:
        """Determine appropriate destination data type based on technique."""
        # HASHING requires a larger field to accommodate the hash string output
        if technique == "HASHING":
            return "VARCHAR(64)"
            
        # TOKENIZATION or PSEUDONYMIZATION produce variable-length text strings
        if technique == "TOKENIZATION" or technique == "PSEUDONYMIZATION":
            return "TEXT"
            
        # MASKING produces a masked string output
        if technique == "MASKING":
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
        """Validate destination schema against anonymization techniques."""
        print("\nValidating destination schema against anonymization techniques...")
        print("-" * 80)
        
        all_valid = True
        
        for table_name, schema in self.source_schema.items():
            # Get policy for this table
            table_policy = [
                col for col in self.policy["column_policies"]
                if col["table_name"] == table_name
            ]
            policy_map = {col["column_name"]: col for col in table_policy}
            
            for col in schema["columns"]:
                col_name = col["column_name"]
                source_type = col["data_type"]
                
                # Get anonymization technique
                technique = "NO_CHANGE"
                if col_name in policy_map:
                    technique = policy_map[col_name]["anonymization_technique"]
                
                # Get expected destination type
                expected_type = self.get_destination_data_type(source_type, technique)
                
                # Check if the technique requires a different type than source
                if technique != "NO_CHANGE" and technique != "DIFFERENTIAL_PRIVACY":
                    if source_type != expected_type:
                        print(f"[OK] {table_name}.{col_name}: {source_type} -> {expected_type} ({technique})")
                    else:
                        print(f"[WARN] {table_name}.{col_name}: {source_type} may not accommodate {technique} output")
                        all_valid = False
        
        if all_valid:
            print("[OK] Destination schema validation passed")
        else:
            print("[FAIL] Destination schema validation failed")
            
        return all_valid

    def validate_results(self, tables_processed) -> bool:
        """Validate row count matching between source and destination."""
        print("\nValidation Results:")
        print("-" * 80)
        
        all_match = True
        for table_result in tables_processed:
            table_name = table_result["table_name"]
            source_count = table_result["total_rows"]
            dest_table_name = table_name
            
            # Fetch destination row count
            dest_count = 0
            try:
                with self.destination_connector.engine.connect() as conn:
                    result = conn.execute(text(f'SELECT COUNT(*) FROM "{dest_table_name}"'))
                    # Support both SQLAlchemy Result objects and sqlite3 fallback
                    dest_count = result.scalar() if hasattr(result, 'scalar') else result.fetchone()[0]
            except Exception as e:
                logger.error(f"Failed to get row count for destination table {dest_table_name}: {e}")
                all_match = False
                
            print(f"{table_name}:")
            print(f"  Source: {source_count}")
            print(f"  Destination: {dest_count}")
            
            if source_count == dest_count:
                print(f"  [OK] Row counts match")
            else:
                print(f"  [FAIL] Row count mismatch")
                all_match = False
                
        return all_match
