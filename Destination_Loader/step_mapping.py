"""
17-Step Pipeline Mapping to Existing Implementations

This document maps each of the 17 DataVault AI pipeline steps to the existing
module implementations that should be used.
"""

STEP_MAPPING = {
    1: {
        "name": "Connect Database",
        "module": "Connection_Extraction/database_connector.py",
        "class": "DatabaseConnector",
        "method": "connect",
        "output": "source_connector, destination_connector",
        "dependencies": [],
        "happy_path": "Both database connections established successfully",
        "sad_path": "Database connection failure → Step 1 FAILED → stop execution"
    },
    2: {
        "name": "Extract Schema",
        "module": "Connection_Extraction/schema_extractor.py",
        "class": "SchemaExtractor",
        "method": "get_all_schemas",
        "output": "source_schema (dict of table schemas)",
        "dependencies": [1],
        "happy_path": "Schema extracted for all tables successfully",
        "sad_path": "Schema extraction failure → Step 2 FAILED → stop execution"
    },
    3: {
        "name": "Enterprise Detection",
        "module": "Enterprise_Classification/enterprise_detector.py",
        "class": "EnterpriseDetector",
        "method": "detect_enterprise",
        "output": "enterprise_info (type, confidence, reasoning, compliance_law)",
        "dependencies": [2],
        "happy_path": "Enterprise type detected with confidence",
        "sad_path": "LLM failure or low confidence → Step 3 FAILED → fallback to GENERAL"
    },
    4: {
        "name": "Privacy-Safe Sampling",
        "module": "Connection_Extraction/sample_extractor.py",
        "class": "SampleExtractor",
        "method": "get_table_samples",
        "output": "sample_data (dict of column samples)",
        "dependencies": [2],
        "happy_path": "Sample data extracted for PII detection",
        "sad_path": "Sampling failure → Step 4 FAILED → use empty samples"
    },
    5: {
        "name": "PII Detection",
        "module": "PII_Detection/combined_detector.py",
        "class": "CombinedDetector",
        "method": "detect_pii",
        "output": "pii_detection_result (detected PII columns and types)",
        "dependencies": [3, 4],
        "happy_path": "PII columns identified across all tables",
        "sad_path": "Detection failure → Step 5 FAILED → fallback to basic detection"
    },
    6: {
        "name": "Policy Generation",
        "module": "PII_Detection/policy_generator.py",
        "class": "PolicyGenerator",
        "method": "generate_policy",
        "output": "generated_policy",
        "dependencies": [5],
        "happy_path": "Policy generated successfully",
        "sad_path": "Policy generation failure → Step 6 FAILED → stop execution"
    },
    7: {
        "name": "Admin Approval",
        "module": "Approval_Workflow/approval_workflow.py",
        "class": "ApprovalWorkflow",
        "method": "is_policy_approved",
        "output": "approved_policy (if approved)",
        "dependencies": [6],
        "happy_path": "Admin approves policy → proceed to step 8",
        "sad_path": "Admin rejects policy → Step 7 FAILED → stop execution",
        "special": "WAITING_FOR_APPROVAL state until admin action"
    },
    8: {
        "name": "Change Detection",
        "module": "Change_Detection/change_detector.py",
        "class": "SQLAlchemyEventListener",
        "method": "start_listening",
        "output": "change_detection_result (changes queue)",
        "dependencies": [7],
        "happy_path": "Change detection started successfully",
        "sad_path": "Change detection failure → Step 8 FAILED → continue without monitoring"
    },
    9: {
        "name": "Redis Hash Vault",
        "module": "Redis_Hash_Vault/redis_mapping.py",
        "class": "RedisMappingSystem",
        "method": "__init__",
        "output": "redis_mapping (Redis mapping system instance)",
        "dependencies": [7],
        "happy_path": "Redis mapping system initialized",
        "sad_path": "Redis failure → Step 9 FAILED → fallback to in-memory mapping"
    },
    10: {
        "name": "Crash Recovery",
        "module": "Redis_AOF_Safety/aof_config.py",
        "class": "configure_redis_mitigations",
        "method": "configure_redis_mitigations",
        "output": "recovery_state (checkpoint status)",
        "dependencies": [9],
        "happy_path": "Recovery system configured successfully",
        "sad_path": "Recovery config failure → Step 10 FAILED → continue without recovery"
    },
    11: {
        "name": "Chunk Processing",
        "module": "Destination_Loader/policy_executor.py",
        "class": "PolicyExecutor",
        "method": "read_chunk (new method)",
        "output": "chunks (queue of data chunks)",
        "dependencies": [2, 10],
        "happy_path": "Chunks read and queued for processing",
        "sad_path": "Chunk reading failure → Step 11 FAILED → stop execution"
    },
    12: {
        "name": "Data Anonymization",
        "module": "Redis_Hash_Vault/anonymizer.py",
        "class": "Anonymizer",
        "method": "anonymize_column",
        "output": "anonymized_chunks (queue of anonymized data)",
        "dependencies": [9, 11],
        "happy_path": "Chunks anonymized consistently",
        "sad_path": "Anonymization failure → Step 12 FAILED → stop execution"
    },
    13: {
        "name": "Batch Loading",
        "module": "Destination_Loader/policy_executor.py",
        "class": "PolicyExecutor",
        "method": "load_batch (new method)",
        "output": "loaded_batches (committed batches)",
        "dependencies": [12],
        "happy_path": "Batches loaded to destination transactionally",
        "sad_path": "Batch loading failure → Step 13 FAILED → rollback and retry"
    },
    14: {
        "name": "Validation Approval",
        "module": "Validation_Engine/validation_engine.py",
        "class": "ValidationEngine",
        "method": "validate_results",
        "output": "validation_result (privacy score, leaks)",
        "dependencies": [13],
        "happy_path": "Validation passed → proceed to step 15",
        "sad_path": "Validation failed → Step 14 FAILED → do not complete pipeline",
        "special": "WAITING_FOR_APPROVAL state for validation approval"
    },
    15: {
        "name": "Safe Database Generation",
        "module": "Destination_Loader/policy_executor.py",
        "class": "PolicyExecutor",
        "method": "create_destination_schema (existing)",
        "output": "destination_schema (created schema)",
        "dependencies": [14],
        "happy_path": "Destination schema finalized safely",
        "sad_path": "Schema finalization failure → Step 15 FAILED → stop execution",
        "note": "Schema creation happens before step 13, but finalization here"
    },
    16: {
        "name": "Audit Report",
        "module": "Audit_Report/audit_report_generator.py",
        "class": "AuditReportGenerator",
        "method": "generate_report",
        "output": "audit_report (JSON and text reports)",
        "dependencies": [14, 15],
        "happy_path": "Audit report generated successfully",
        "sad_path": "Report generation failure → Step 16 FAILED → warning but continue"
    },
    17: {
        "name": "Output Delivery",
        "module": "Destination_Loader/policy_executor.py",
        "class": "PolicyExecutor",
        "method": "finalize_output (new method)",
        "output": "final_outputs (delivery confirmation)",
        "dependencies": [16],
        "happy_path": "Final outputs delivered successfully",
        "sad_path": "Output delivery failure → Step 17 FAILED → partial completion"
    }
}

# Dependencies between steps (step_number: [dependent_steps])
STEP_DEPENDENCIES = {
    1: [],
    2: [1],
    3: [2],
    4: [2],
    5: [3, 4],
    6: [5],
    7: [6],
    8: [7],
    9: [7],
    10: [9],
    11: [2, 10],
    12: [9, 11],
    13: [12],
    14: [13],
    15: [14],
    16: [14, 15],
    17: [16]
}

# Steps that require approval approval
APPROVAL_STEPS = [7, 14]

# Steps that can be parallelized within their stage
PARALLEL_STAGES = {
    "data_processing": [11, 12, 13]  # Pipeline flow: 11→12→13
}
