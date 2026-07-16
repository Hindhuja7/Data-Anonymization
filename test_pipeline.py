"""
Test script for Enterprise + PII Detection + Anonymization Pipeline
Tests the complete pipeline with schema-based relationship preservation
"""

import os
import sys
import json

# Add pipeline layer folders to path
_root = os.path.dirname(os.path.abspath(__file__))
for _layer in ["Layer_1_Connection_Extraction", "Layer_2_Enterprise_Classification", "Layer_3_PII_Detection", "Layer_4_Anonymization_Vault"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from database_connector import DatabaseConnector
from schema_extractor import SchemaExtractor
from sample_extractor import SampleExtractor
from enterprise_detector import EnterpriseDetector
from combined_detector import CombinedPIIDetector
from anonymizer import Anonymizer

def create_mock_test():
    """Create mock test to demonstrate pipeline without database."""
    print("\n" + "=" * 80)
    print("MOCK TEST - DEMONSTRATING PIPELINE WITH SAMPLE DATA")
    print("=" * 80)
    
    # Mock schema
    print("\n[STEP 1] Creating mock schema...")
    schemas = [
        {
            "table_name": "customers",
            "columns": [
                {"column_name": "customer_id", "type": "INTEGER"},
                {"column_name": "full_name", "type": "VARCHAR"},
                {"column_name": "email", "type": "VARCHAR"},
                {"column_name": "phone", "type": "VARCHAR"},
                {"column_name": "address", "type": "VARCHAR"}
            ],
            "primary_keys": ["customer_id"],
            "foreign_keys": [],
            "unique_constraints": [{"name": "unique_email", "constrained_columns": ["email"]}],
            "check_constraints": [],
            "indexes": []
        },
        {
            "table_name": "orders",
            "columns": [
                {"column_name": "order_id", "type": "INTEGER"},
                {"column_name": "customer_id", "type": "INTEGER"},
                {"column_name": "order_date", "type": "DATE"},
                {"column_name": "total_amount", "type": "DECIMAL"}
            ],
            "primary_keys": ["order_id"],
            "foreign_keys": [
                {
                    "name": "fk_customer",
                    "constrained_columns": ["customer_id"],
                    "referred_table": "customers",
                    "referred_columns": ["customer_id"]
                }
            ],
            "unique_constraints": [],
            "check_constraints": [],
            "indexes": []
        }
    ]
    print(f"✓ Created mock schema for {len(schemas)} tables")
    for schema in schemas:
        print(f"  - {schema['table_name']}: {len(schema['columns'])} columns")
        print(f"    Primary keys: {schema['primary_keys']}")
        print(f"    Foreign keys: {len(schema['foreign_keys'])}")
        print(f"    Unique constraints: {len(schema['unique_constraints'])}")
    
    # Mock samples
    print("\n[STEP 2] Creating mock sample values...")
    samples = {
        "customers": {
            "customer_id": ["1", "2", "3"],
            "full_name": ["John Doe", "Jane Smith", "Bob Johnson"],
            "email": ["john@example.com", "jane@example.com", "bob@example.com"],
            "phone": ["+91-9876543210", "+91-9876543211", "+91-9876543212"],
            "address": ["123 Main St, Mumbai", "456 Oak Ave, Delhi", "789 Pine Rd, Bangalore"]
        },
        "orders": {
            "order_id": ["101", "102", "103"],
            "customer_id": ["1", "2", "3"],
            "order_date": ["2024-01-15", "2024-01-16", "2024-01-17"],
            "total_amount": ["1500.00", "2500.00", "1800.00"]
        }
    }
    print(f"✓ Created mock samples for {len(samples)} tables")
    
    # Enterprise detection
    print("\n[STEP 3] Enterprise auto-detection...")
    enterprise_detector = EnterpriseDetector()
    enterprise_result = enterprise_detector.detect_enterprise(schemas)
    enterprise_type = enterprise_result.get("enterprise_type", "GENERAL")
    confidence = enterprise_result.get("confidence", 0.5)
    print(f"✓ Detected enterprise: {enterprise_type} (confidence: {confidence:.2f})")
    
    # PII detection
    print("\n[STEP 4] PII detection (LLM + Regex)...")
    combined_detector = CombinedPIIDetector(provider="github")
    pii_report = {}
    
    for schema in schemas:
        table_name = schema['table_name']
        table_samples = samples.get(table_name, {})
        
        # Prepare columns for detection
        columns_for_detection = []
        for col_info in schema["columns"]:
            column_name = col_info["column_name"]
            data_type = col_info["type"]
            sample_values = table_samples.get(column_name, [])
            
            # Add schema context
            is_primary_key = column_name in schema.get("primary_keys", [])
            foreign_key_info = None
            for fk in schema.get("foreign_keys", []):
                if column_name in fk.get("constrained_columns", []):
                    foreign_key_info = {
                        "foreign_key_column": column_name,
                        "referred_table": fk.get("referred_table"),
                        "referred_columns": fk.get("referred_columns")
                    }
                    break
            
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
        
        # Detect PII for this table
        table_results = combined_detector.detect_table(
            table_name=table_name,
            columns=columns_for_detection,
            use_batch=True,
            enterprise_type=enterprise_type,
            compliance_law="DPDP Act 2023",
            enterprise_confidence=confidence
        )
        
        pii_report[table_name] = table_results
    
    print(f"✓ PII detection completed")
    for table_name, columns in pii_report.items():
        pii_count = sum(1 for col in columns if col.get("is_pii"))
        print(f"  - {table_name}: {pii_count} PII columns detected")
        for col in columns:
            if col.get("is_pii"):
                print(f"    * {col['column_name']}: {col.get('pii_type')} ({col.get('recommended_technique')})")
    
    # Build schema info for anonymization
    print("\n[STEP 5] Building schema information for anonymization...")
    schema_info = {}
    for schema in schemas:
        table_name = schema['table_name']
        schema_info[table_name] = {
            'primary_keys': schema['primary_keys'],
            'foreign_keys': schema['foreign_keys'],
            'unique_constraints': schema['unique_constraints']
        }
    print(f"✓ Schema information built for {len(schema_info)} tables")
    
    # Anonymize data
    print("\n[STEP 6] Anonymizing data with schema-based relationship preservation...")
    try:
        anonymizer = Anonymizer()
        anonymized_data = {}
        
        for table_name, columns in pii_report.items():
            anonymized_data[table_name] = {}
            table_schema = schema_info.get(table_name, {})
            primary_keys = table_schema.get('primary_keys', [])
            foreign_keys = table_schema.get('foreign_keys', [])
            
            for col_result in columns:
                column_name = col_result["column_name"]
                technique = col_result.get("recommended_technique", "NO_CHANGE")
                pii_type = col_result.get("pii_type")
                
                if technique == "NO_CHANGE":
                    continue
                
                # Determine if column is foreign key or primary key
                is_primary_key = column_name in primary_keys
                is_foreign_key = False
                for fk in foreign_keys:
                    if column_name in fk.get("constrained_columns", []):
                        is_foreign_key = True
                        break
                
                # Use mock data
                values = samples[table_name].get(column_name, [])
                
                # Apply anonymization with schema context
                anonymized_values = anonymizer.anonymize_column(
                    values=values,
                    pii_type=pii_type,
                    technique=technique,
                    column_name=column_name,
                    table_name=table_name,
                    is_foreign_key=is_foreign_key,
                    is_primary_key=is_primary_key
                )
                
                anonymized_data[table_name][column_name] = anonymized_values
                print(f"  - {table_name}.{column_name}: {len(values)} → {len(anonymized_values)} values")
                print(f"    Schema context: PK={is_primary_key}, FK={is_foreign_key}")
                print(f"    Original: {values[:2]}")
                print(f"    Anonymized: {anonymized_values[:2]}")
        
        print(f"✓ Anonymization completed")
        for table_name, columns in anonymized_data.items():
            print(f"  - {table_name}: {len(columns)} columns anonymized")
    except Exception as e:
        print(f"✗ Anonymization failed: {e}")
        print("Note: This might be due to missing Redis server")
    
    # Save results
    print("\n[STEP 7] Saving results...")
    with open('test_results.json', 'w') as f:
        json.dump({
            'enterprise_detection': {
                'enterprise_type': enterprise_type,
                'confidence': confidence
            },
            'pii_report': pii_report,
            'anonymized_data': anonymized_data
        }, f, indent=2, default=str)
    print("✓ Results saved to test_results.json")
    
    print("\n" + "=" * 80)
    print("MOCK TEST COMPLETED")
    print("=" * 80)
    print("\nKEY DEMONSTRATIONS:")
    print("1. Schema extraction with foreign keys and primary keys")
    print("2. Schema context passed to LLM for PII detection")
    print("3. Schema-based global mapping (not keyword-based)")
    print("4. Relationship preservation using foreign key information")
    print("5. Consistent anonymization across related tables")

def test_pipeline():
    """Test the complete pipeline with actual database."""
    
    print("=" * 80)
    print("TESTING ENTERPRISE + PII DETECTION + ANONYMIZATION PIPELINE")
    print("=" * 80)
    
    # Step 1: Connect to database
    print("\n[STEP 1] Connecting to database...")
    # Construct connection string from environment variables
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    db_user = os.getenv("DB_USERNAME", "neondb_owner")
    db_pass = os.getenv("DB_PASSWORD", "npg_BsO9tyw8dTRW")
    db_host = os.getenv("DB_HOST", "ep-gentle-wave-atqzagux.c-9.us-east-1.aws.neon.tech")
    db_name = os.getenv("DB_NAME", "neondb")
    
    connection_string = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}?sslmode=require"
    
    # Create connector directly with connection string
    connector = DatabaseConnector(connection_string=connection_string)
    
    try:
        connector.connect()
        print("✓ Database connected successfully")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nNote: Database connection failed. Creating mock test data instead...")
        return create_mock_test()
    
    # Step 2: Extract schema
    print("\n[STEP 2] Extracting schema...")
    schema_extractor = SchemaExtractor(connector.engine)
    schemas = schema_extractor.get_all_schemas()
    
    print(f"✓ Extracted schema for {len(schemas)} tables")
    for schema in schemas:
        print(f"  - {schema['table_name']}: {len(schema['columns'])} columns")
        print(f"    Primary keys: {schema['primary_keys']}")
        print(f"    Foreign keys: {len(schema['foreign_keys'])}")
        print(f"    Unique constraints: {len(schema['unique_constraints'])}")
    
    # Step 3: Extract samples
    print("\n[STEP 3] Extracting sample values...")
    sample_extractor = SampleExtractor(connector.engine, sample_size=5)
    samples = {}
    for schema in schemas:
        table_name = schema['table_name']
        column_names = [col['column_name'] for col in schema['columns']]
        table_samples = sample_extractor.get_table_samples(table_name, column_names)
        samples[table_name] = table_samples
        print(f"  - {table_name}: {len(table_samples)} columns with samples")
    
    # Step 4: Enterprise detection
    print("\n[STEP 4] Enterprise auto-detection...")
    enterprise_detector = EnterpriseDetector()
    enterprise_result = enterprise_detector.detect_enterprise(schemas)
    enterprise_type = enterprise_result.get("enterprise_type", "GENERAL")
    confidence = enterprise_result.get("confidence", 0.5)
    print(f"✓ Detected enterprise: {enterprise_type} (confidence: {confidence:.2f})")
    
    # Step 5: PII detection
    print("\n[STEP 5] PII detection (LLM + Regex)...")
    combined_detector = CombinedPIIDetector(provider="github")
    pii_report = {}
    
    for schema in schemas:
        table_name = schema['table_name']
        table_samples = samples.get(table_name, {})
        
        # Prepare columns for detection
        columns_for_detection = []
        for col_info in schema["columns"]:
            column_name = col_info["column_name"]
            data_type = col_info.get("data_type") or col_info.get("type", "VARCHAR")
            sample_values = table_samples.get(column_name, [])
            
            # Add schema context
            is_primary_key = column_name in schema.get("primary_keys", [])
            foreign_key_info = None
            for fk in schema.get("foreign_keys", []):
                if column_name in fk.get("constrained_columns", []):
                    foreign_key_info = {
                        "foreign_key_column": column_name,
                        "referred_table": fk.get("referred_table"),
                        "referred_columns": fk.get("referred_columns")
                    }
                    break
            
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
        
        # Detect PII for this table
        table_results = combined_detector.detect_table(
            table_name=table_name,
            columns=columns_for_detection,
            use_batch=True,
            enterprise_type=enterprise_type,
            compliance_law="DPDP Act 2023",
            enterprise_confidence=confidence
        )
        
        pii_report[table_name] = table_results
    
    print(f"✓ PII detection completed")
    for table_name, columns in pii_report.items():
        pii_count = sum(1 for col in columns if col.get("is_pii"))
        print(f"  - {table_name}: {pii_count} PII columns detected")
    
    # Step 6: Build schema info for anonymization
    print("\n[STEP 6] Building schema information for anonymization...")
    schema_info = {}
    for schema in schemas:
        table_name = schema['table_name']
        schema_info[table_name] = {
            'primary_keys': schema['primary_keys'],
            'foreign_keys': schema['foreign_keys'],
            'unique_constraints': schema['unique_constraints']
        }
    print(f"✓ Schema information built for {len(schema_info)} tables")
    
    # Step 7: Anonymize data
    print("\n[STEP 7] Anonymizing data with schema-based relationship preservation...")
    try:
        anonymizer = Anonymizer()
        anonymized_data = {}
        
        for table_name, columns in pii_report.items():
            anonymized_data[table_name] = {}
            table_schema = schema_info.get(table_name, {})
            primary_keys = table_schema.get('primary_keys', [])
            foreign_keys = table_schema.get('foreign_keys', [])
            
            for col_result in columns:
                column_name = col_result["column_name"]
                technique = col_result.get("recommended_technique", "NO_CHANGE")
                pii_type = col_result.get("pii_type")
                
                if technique == "NO_CHANGE":
                    continue
                
                # Determine if column is foreign key or primary key
                is_primary_key = column_name in primary_keys
                is_foreign_key = False
                for fk in foreign_keys:
                    if column_name in fk.get("constrained_columns", []):
                        is_foreign_key = True
                        break
                
                # Fetch actual data from database (limit to 100 rows for fast verification)
                query = f'SELECT "{column_name}" FROM "{table_name}" LIMIT 100'
                try:
                    import pandas as pd
                    with connector.engine.connect() as conn:
                        df = pd.read_sql(query, conn)
                        conn.rollback()
                    values = df[column_name].tolist()
                    
                    # Apply anonymization with schema context
                    anonymized_values = anonymizer.anonymize_column(
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
                    print(f"  Error anonymizing {table_name}.{column_name}: {e}")
        
        print(f"✓ Anonymization completed")
        for table_name, columns in anonymized_data.items():
            print(f"  - {table_name}: {len(columns)} columns anonymized")
    except Exception as e:
        print(f"✗ Anonymization failed: {e}")
        print("Note: This might be due to missing Redis server or database issues")
    
    # Step 8: Save results
    print("\n[STEP 8] Saving results...")
    with open('test_results.json', 'w') as f:
        json.dump({
            'enterprise_detection': {
                'enterprise_type': enterprise_type,
                'confidence': confidence
            },
            'pii_report': pii_report,
            'anonymized_data': anonymized_data
        }, f, indent=2, default=str)
    print("✓ Results saved to test_results.json")
    
    # Disconnect
    connector.disconnect()
    print("\n" + "=" * 80)
    print("PIPELINE TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    test_pipeline()
