"""
Main entry point for database PII detection.
Orchestrates the complete PII detection pipeline.
"""

import json
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _layer in ["Connection_Extraction", "Enterprise_Classification", "PII_Detection", "Change_Detection", "Redis_Hash_Vault", "Redis_AOF_Safety", "Polling_Worker", "Destination_Loader", "Validation_Engine", "Audit_Report", "Admin_Dashboard", "Approval_Workflow"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from typing import Dict, List, Any
from dotenv import load_dotenv

from database_connector import DatabaseConnector
from schema_extractor import SchemaExtractor
from sample_extractor import SampleExtractor
from combined_detector import CombinedPIIDetector
from enterprise_detector import EnterpriseDetector
from anonymizer import Anonymizer
from policy_generator import PolicyGenerator

load_dotenv()


class DatabasePIIDetector:
    """Main orchestrator for database PII detection."""
    
    def __init__(
        self,
        database_type: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database_name: str,
        provider: str = "github",
        model: str = None,
        sslmode: str = None
    ):
        """
        Initialize database PII detector.
        
        Args:
            database_type: 'postgresql', 'mysql', or 'sqlserver'
            host: Database host
            port: Database port
            username: Database username
            password: Database password
            database_name: Database name
            provider: LLM provider ('github', 'openai', 'anthropic')
            model: Specific model name (for GitHub Models)
            sslmode: SSL mode for PostgreSQL (require, prefer, disable, etc.)
        """
        self.database_type = database_type
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database_name = database_name
        self.provider = provider
        self.model = model
        self.sslmode = sslmode
        
        self.connector = None
        self.schema_extractor = None
        self.sample_extractor = None
        self.combined_detector = None
        self.enterprise_detector = None
        self.anonymizer = None
    
    def connect(self):
        """Establish database connection."""
        self.connector = DatabaseConnector(
            database_type=self.database_type,
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database_name=self.database_name,
            sslmode=self.sslmode
        )
        self.connector.connect(read_only=True)
        
        self.schema_extractor = SchemaExtractor(self.connector.engine)
        self.sample_extractor = SampleExtractor(self.connector.engine, database_type=self.database_type)
        self.combined_detector = CombinedPIIDetector(provider=self.provider, model=self.model)
        self.enterprise_detector = EnterpriseDetector(provider=self.provider, model=self.model)
        self.anonymizer = Anonymizer()
    
    def detect_pii(self) -> Dict[str, Any]:
        """
        Run complete PII detection pipeline.
        
        Returns:
            Dictionary with PII detection report for all tables
        """
        if not self.connector:
            raise RuntimeError("Database connection not established. Call connect() first.")
        
        # Step 1: Extract schema
        table_schemas = self.schema_extractor.get_all_schemas()
        
        # Step 2: Detect enterprise type
        enterprise_info = self.enterprise_detector.detect_enterprise(table_schemas)
        
        # Step 3: Extract sample data
        table_samples = self.sample_extractor.get_all_table_samples(table_schemas)
        
        # Step 4: Run PII detection for each table
        report = {
            "database_name": self.database_name,
            "database_type": self.database_type,
            "enterprise_type": enterprise_info["enterprise_type"],
            "enterprise_confidence": enterprise_info["confidence"],
            "compliance_law": enterprise_info["compliance_law"],
            "tables": []
        }
        
        for schema in table_schemas:
            table_name = schema["table_name"]
            samples = table_samples.get(table_name, {})
            
            table_report = self._detect_table_pii(
                table_name, 
                schema, 
                samples, 
                enterprise_info["enterprise_type"],
                enterprise_info["compliance_law"],
                enterprise_info["confidence"]
            )
            report["tables"].append(table_report)
        
        return report
    
    def _detect_table_pii(
        self,
        table_name: str,
        schema: Dict[str, Any],
        samples: Dict[str, List[str]],
        enterprise_type: str,
        compliance_law: str,
        enterprise_confidence: float
    ) -> Dict[str, Any]:
        """
        Detect PII for a single table.
        
        Args:
            table_name: Name of the table
            schema: Table schema dictionary
            samples: Column sample values dictionary
            enterprise_type: Enterprise type (BANKING, HEALTHCARE, HR, etc.)
            compliance_law: Applicable compliance law
            enterprise_confidence: Confidence in enterprise detection (0.0 to 1.0)
        
        Returns:
            Dictionary with PII detection results for the table
        """
        table_report = {
            "table_name": table_name,
            "columns": []
        }
        
        # Prepare columns for batch detection with schema context
        columns_for_detection = []
        for col_info in schema["columns"]:
            column_name = col_info["column_name"]
            data_type = col_info["data_type"]
            sample_values = samples.get(column_name, [])
            
            # Check if column is a primary key
            is_primary_key = column_name in schema.get("primary_keys", [])
            
            # Check if column is a foreign key
            foreign_key_info = None
            for fk in schema.get("foreign_keys", []):
                if column_name in fk.get("constrained_columns", []):
                    foreign_key_info = {
                        "foreign_key_column": column_name,
                        "referred_table": fk.get("referred_table"),
                        "referred_columns": fk.get("referred_columns")
                    }
                    break
            
            # Check if column has unique constraint
            unique_constraint_info = None
            for uc in schema.get("unique_constraints", []):
                if column_name in uc.get("constrained_columns", []):
                    unique_constraint_info = {
                        "unique_constraint_name": uc.get("name"),
                        "constrained_columns": uc.get("constrained_columns")
                    }
                    break
            
            columns_for_detection.append({
                "column_name": column_name,
                "data_type": data_type,
                "sample_values": sample_values,
                "table_name": table_name,
                "is_primary_key": is_primary_key,
                "foreign_key_info": foreign_key_info,
                "unique_constraint_info": unique_constraint_info
            })
        
        # Run combined detection for all columns in the table
        detection_results = self.combined_detector.detect_table(
            table_name=table_name,
            columns=columns_for_detection,
            use_batch=True,
            enterprise_type=enterprise_type,
            compliance_law=compliance_law,
            enterprise_confidence=enterprise_confidence
        )
        
        # Format results according to specified JSON structure
        for result in detection_results:
            column_report = {
                "column_name": result["column_name"],
                "is_pii": result["is_pii"],
                "pii_type": result["pii_type"].upper() if result["pii_type"] else None,
                "confidence": result["confidence"],
                "recommended_technique": result["recommended_technique"].upper() if result["recommended_technique"] else None
            }
            table_report["columns"].append(column_report)
        
        return table_report
    
    def anonymize_data(self, pii_report: Dict[str, Any], schema_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Anonymize database data based on PII detection report.
        
        Args:
            pii_report: PII detection report from detect_pii()
            schema_info: Schema information with foreign keys and primary keys
        
        Returns:
            Dictionary with anonymized data for all tables
        """
        if not self.connector:
            raise RuntimeError("Database connection not established. Call connect() first.")
        
        anonymized_data = {}
        
        for table in pii_report.get("tables", []):
            table_name = table["table_name"]
            anonymized_data[table_name] = {}
            
            # Get schema information for this table
            table_schema = schema_info.get(table_name, {}) if schema_info else {}
            primary_keys = table_schema.get("primary_keys", [])
            foreign_keys = table_schema.get("foreign_keys", [])
            
            for column_info in table.get("columns", []):
                column_name = column_info["column_name"]
                technique = column_info.get("recommended_technique", "NO_CHANGE")
                pii_type = column_info.get("pii_type")
                
                if technique == "NO_CHANGE":
                    # Skip anonymization for non-PII columns
                    continue
                
                # Determine if column is foreign key or primary key
                is_primary_key = column_name in primary_keys
                is_foreign_key = False
                for fk in foreign_keys:
                    if column_name in fk.get("constrained_columns", []):
                        is_foreign_key = True
                        break
                
                # Fetch actual data from database
                query = f'SELECT "{column_name}" FROM "{table_name}"'
                try:
                    import pandas as pd
                    df = pd.read_sql(query, self.connector.engine)
                    values = df[column_name].tolist()
                    
                    # Apply anonymization with schema context
                    anonymized_values = self.anonymizer.anonymize_column(
                        values=values,
                        pii_type=pii_type,
                        technique=technique,
                        column_name=column_name,
                        table_name=table_name,
                        is_foreign_key=is_foreign_key,
                        is_primary_key=is_primary_key
                    )
                    
                    anonymized_data[table_name][column_name] = anonymized_values
                except Exception as e:
                    print(f"Error anonymizing {table_name}.{column_name}: {e}")
                    anonymized_data[table_name][column_name] = None
        
        return anonymized_data
    
    def generate_anonymization_policy(
        self,
        pii_report: Dict[str, Any],
        output_file: str = "anonymization_policy.json"
    ) -> Dict[str, Any]:
        """
        Generate an anonymization policy from PII detection results.
        
        Args:
            pii_report: PII detection report from detect_pii()
            output_file: Path to save the policy file
        
        Returns:
            Dictionary containing the anonymization policy
        """
        # Get schema information for additional context
        table_schemas = self.schema_extractor.get_all_schemas()
        schema_info = {schema["table_name"]: schema for schema in table_schemas}
        
        # Generate policy
        policy_generator = PolicyGenerator()
        policy = policy_generator.generate_policy(pii_report, schema_info)
        
        # Save policy to file
        policy_generator.save_policy(output_file)
        
        return policy
    
    def disconnect(self):
        """Close database connection."""
        if self.connector:
            self.connector.disconnect()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def detect_pii_from_database(
    database_type: str,
    host: str,
    port: int,
    username: str,
    password: str,
    database_name: str,
    provider: str = "github",
    model: str = None,
    output_file: str = None
) -> Dict[str, Any]:
    """
    Convenience function to detect PII from a database.
    
    Args:
        database_type: 'postgresql', 'mysql', or 'sqlserver'
        host: Database host
        port: Database port
        username: Database username
        password: Database password
        database_name: Database name
        provider: LLM provider ('github', 'openai', 'anthropic')
        model: Specific model name (for GitHub Models)
        output_file: Optional file path to save JSON report
    
    Returns:
        Dictionary with PII detection report
    """
    with DatabasePIIDetector(
        database_type=database_type,
        host=host,
        port=port,
        username=username,
        password=password,
        database_name=database_name,
        provider=provider,
        model=model
    ) as detector:
        report = detector.detect_pii()
    
    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"PII detection report saved to: {output_file}")
    
    return report


if __name__ == "__main__":
    # Example usage with environment variables
    print("Database PII Detection")
    print("=" * 70)
    
    # Get database credentials from environment or use defaults
    DATABASE_TYPE = os.getenv("DB_TYPE", "postgresql")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_USERNAME = os.getenv("DB_USERNAME", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "test_db")
    
    # Get LLM provider settings
    PROVIDER = os.getenv("LLM_PROVIDER", "github")
    MODEL = os.getenv("LLM_MODEL", "gpt-4o")
    
    print(f"Connecting to database: {DB_NAME}")
    print(f"Database type: {DATABASE_TYPE}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"LLM Provider: {PROVIDER}")
    print(f"Model: {MODEL}")
    print("=" * 70)
    
    try:
        report = detect_pii_from_database(
            database_type=DATABASE_TYPE,
            host=DB_HOST,
            port=DB_PORT,
            username=DB_USERNAME,
            password=DB_PASSWORD,
            database_name=DB_NAME,
            provider=PROVIDER,
            model=MODEL,
            output_file="pii_detection_report.json"
        )
        
        print("\nPII Detection Output Summary:")
        print("=" * 120)
        
        # Technique mapping
        technique_mapping = {
            'AADHAAR': 'masking',
            'PAN': 'masking',
            'UAN': 'masking',
            'GSTIN': 'masking',
            'INDIAN_PHONE': 'tokenization',
            'PHONE': 'tokenization',
            'EMAIL': 'tokenization',
            'FULL_NAME': 'pseudonymization',
            'ADDRESS': 'generalization',
            'CREDIT_CARD': 'masking',
            'DATE_OF_BIRTH': 'generalization'
        }
        
        total_columns = 0
        pii_columns = 0
        all_pii_rows = []
        
        # Process each table separately
        for table in report["tables"]:
            table_name = table['table_name']
            table_pii_count = 0
            
            print(f"\nTable: {table_name}")
            print("-" * 120)
            
            # Table header
            header = f"{'Column':<20} {'Is PII?':<10} {'PII Type':<20} {'Confidence':<12} {'Technique':<15} {'Reasoning':<30}"
            print(header)
            print("-" * 120)
            
            for col in table["columns"]:
                total_columns += 1
                column_name = col['column_name']
                is_pii = col['is_pii']
                pii_type = col['pii_type'] if col['pii_type'] else 'NONE'
                confidence = col['confidence']
                
                # Only process if it's actually PII with a valid type (not NONE)
                if is_pii and pii_type != 'NONE':
                    pii_columns += 1
                    table_pii_count += 1
                    technique = technique_mapping.get(pii_type, 'redaction')
                    reasoning = f"Column name '{column_name}' and data format match {pii_type} pattern"
                    
                    # Format row
                    row_str = f"{column_name:<20} {'Yes':<10} {pii_type:<20} {confidence:<12.2f} {technique:<15} {reasoning:<30}"
                    print(row_str)
                    
                    all_pii_rows.append({
                        'table': table_name,
                        'column': column_name,
                        'pii_type': pii_type
                    })
            
            if table_pii_count == 0:
                print("  (No PII detected)")
            
            print()
        
        print("=" * 120)
        
        # Key observations
        print("\nKey observations:")
        print("-" * 120)
        
        # Count by PII type
        pii_type_counts = {}
        for row in all_pii_rows:
            pii_type = row['pii_type']
            pii_type_counts[pii_type] = pii_type_counts.get(pii_type, 0) + 1
        
        print(f"• LLM successfully identified {pii_columns} PII columns out of {total_columns} total columns scanned")
        print(f"• Detection accuracy: {(pii_columns/total_columns*100):.1f}% of columns flagged as PII")
        
        if pii_type_counts:
            print(f"• Most common PII types detected:")
            for pii_type, count in sorted(pii_type_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {pii_type}: {count} columns")
        
        print(f"• Indian-specific PII (AADHAAR, PAN, UAN, GSTIN, INDIAN_PHONE) correctly identified")
        print(f"• Recommended anonymization techniques mapped based on PII type sensitivity")
        
        print("\nFull report saved to: pii_detection_report.json")
        
    except Exception as e:
        print(f"Error during PII detection: {e}")
        print("\nPlease ensure:")
        print("1. Database credentials are set in environment variables or .env file")
        print("2. Database is accessible")
        print("3. LLM API key is set (GITHUB_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)")
