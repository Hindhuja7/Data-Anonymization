# Data Anonymization Pipeline Architecture

## Complete Pipeline Flow (13 Steps)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SOURCE DATABASE                                        │
│                    (PostgreSQL / MySQL / SQL Server)                              │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 1: Schema Extraction
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      ENTERPRISE DETECTION LAYER                                   │
│                    (LLM-based Enterprise Classification)                          │
│                                                                                 │
│  • Detect enterprise type (BANKING, HR, HEALTHCARE, etc.)                       │
│  • Map to compliance laws (RBI, DPDP Act 2023, etc.)                            │
│  • Enterprise confidence score for context-aware PII detection                   │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 2: PII Detection Context
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          PII DETECTION LAYER                                     │
│                   (LLM + India-Specific Regex Patterns)                          │
│                                                                                 │
│  • Column-wise random sampling for privacy                                     │
│  • LLM-based detection with enterprise context                                  │
│  • India-specific patterns (Aadhaar, PAN, GSTIN, etc.)                         │
│  • Recommended anonymization techniques                                         │
│  • Confidence scores for each detection                                         │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 3: Real-Time Change Detection
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME ETL: CHANGE DETECTION                               │
│                  (SQLAlchemy Event Listeners)                                    │
│                                                                                 │
│  • Detect INSERT/UPDATE operations on source database                           │
│  • Trigger anonymization pipeline for new records                              │
│  • Database-agnostic change detection                                          │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 4: In-Memory Transformation
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME ETL: REDIS HASH VAULT                                │
│                   (Real-to-Fake Mapping Storage)                                 │
│                                                                                 │
│  • Store anonymization mappings (original → fake)                               │
│  • Ensure referential integrity across tables                                   │
│  • Fast key-value lookups for real-time processing                              │
│  • Application-side encryption before storage                                   │
│  • Only ciphertext stored (compliance)                                          │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 5: Crash Safety
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME ETL: REDIS AOF                                      │
│                   (Append-Only File Persistence)                                  │
│                                                                                 │
│  • Log all write operations to disk                                             │
│  • Recover mapping history after system restart                                 │
│  • Prevent data loss during crashes                                             │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 6: Batch Collection
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME ETL: POLLING WORKER                                 │
│                   (30-Second Batch Processing)                                   │
│                                                                                 │
│  • Poll Redis queue every 30 seconds                                           │
│  • Collect newly anonymized records in batches                                  │
│  • Reduce database load with batch operations                                  │
│  • Prepare data for destination loading                                         │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 7: Transactional Loading
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME ETL: DESTINATION LOADER                             │
│                   (SQLAlchemy ORM with ACID)                                    │
│                                                                                 │
│  • Insert anonymized records to destination database                           │
│  • Full ACID transactional guarantees                                            │
│  • Automatic rollback on batch failures                                         │
│  • Database-agnostic ORM                                                        │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 8: Data Quality Validation
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      VALIDATION ENGINE                                           │
│                   (Anonymized Data Quality Checks)                                │
│                                                                                 │
│  • Validate referential integrity maintained                                     │
│  • Check data type preservation                                                 │
│  • Verify no PII leakage in anonymized data                                    │
│  • Statistical distribution validation                                           │
│  • Schema consistency checks                                                    │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 9: Compliance Tracking
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        AUDIT REPORT GENERATION                                    │
│                   (Compliance & Operation Logging)                               │
│                                                                                 │
│  • Log all anonymization operations                                             │
│  • Track mapping history (original → anonymized)                                │
│  • Record technique applied per column                                          │
│  • Timestamp and user attribution                                               │
│  • Compliance checklist verification                                            │
│  • Export for regulatory filing                                                │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 10: Admin Review
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      ADMIN REVIEW DASHBOARD                                     │
│                   (Human-in-the-Loop Verification)                              │
│                                                                                 │
│  • Review anonymized data samples                                               │
│  • Override technique recommendations                                           │
│  • Approve or reject anonymization                                              │
│  • Modify mappings if needed                                                    │
│  • Final approval for production use                                           │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 11: Final Approval
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      APPROVAL WORKFLOW                                          │
│                   (Production Readiness Check)                                  │
│                                                                                 │
│  • Validate all compliance requirements met                                    │
│  • Confirm referential integrity preserved                                      │
│  • Verify no PII leakage                                                        │
│  • Approve for production deployment                                           │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 12: Anonymized Data
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DESTINATION DATABASE                                      │
│                    (Sandbox / Testing Environment)                                │
│                                                                                 │
│  • Real-time anonymized data (no lag)                                          │
│  • Preserves referential integrity                                              │
│  • Maintains schema structure                                                   │
│  • Validated for quality and compliance                                         │
│  • Ready for testing/development                                                │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │
                             │ Step 13: Production Deployment
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      PRODUCTION ENVIRONMENT                                      │
│                   (Approved Anonymized Data)                                    │
│                                                                                 │
│  • Deployed to production systems                                               │
│  • Continuous real-time updates                                                  │
│  • Monitoring and alerting                                                      │
│  • Ongoing compliance verification                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Enterprise Detection Layer
- **Purpose**: Detect enterprise type from database schema
- **Technology**: LLM (GitHub Models)
- **Output**: Enterprise type, compliance law, confidence score
- **Integration**: Provides context to PII detection layer

### 2. PII Detection Layer
- **Purpose**: Identify PII columns and recommend techniques
- **Technology**: LLM + India-specific regex patterns
- **Output**: PII detection report with techniques
- **Integration**: Guides anonymization layer

### 3. Real-Time ETL: Change Detection
- **Purpose**: Detect database changes in real-time
- **Technology**: SQLAlchemy event listeners
- **Trigger**: INSERT/UPDATE operations
- **Benefit**: No Airbyte/Debezium infrastructure needed

### 4. Real-Time ETL: Redis Hash Vault
- **Purpose**: Store real-to-fake mappings
- **Technology**: Redis Hash structure
- **Feature**: Referential integrity across tables
- **Security**: Application-side encryption before storage

### 5. Real-Time ETL: Redis AOF
- **Purpose**: Crash safety and persistence
- **Technology**: Redis Append-Only File
- **Feature**: Log all writes to disk
- **Benefit**: Recover mappings after restart

### 6. Real-Time ETL: Polling Worker
- **Purpose**: Batch loading optimization
- **Technology**: Background worker
- **Interval**: 30 seconds
- **Benefit**: Reduce database load

### 7. Real-Time ETL: Destination Loader
- **Purpose**: Insert anonymized data
- **Technology**: SQLAlchemy ORM
- **Features**: ACID transactions, rollback on failure
- **Benefit**: Database-agnostic

### 8. Validation Engine
- **Purpose**: Validate anonymized data quality
- **Technology**: Data quality checks and validation rules
- **Features**: Referential integrity, data type preservation, PII leakage detection
- **Benefit**: Ensures anonymized data is safe and usable

### 9. Audit Report Generation
- **Purpose**: Track and log all anonymization operations
- **Technology**: Compliance logging system
- **Features**: Operation logs, mapping history, compliance verification
- **Benefit**: Regulatory compliance and audit trail

### 10. Admin Review Dashboard
- **Purpose**: Human-in-the-loop verification
- **Technology**: Web interface for review
- **Features**: Sample review, technique override, approval workflow
- **Benefit**: Final quality control before production

### 11. Approval Workflow
- **Purpose**: Production readiness check
- **Technology**: Compliance verification system
- **Features**: Compliance validation, integrity checks, approval gates
- **Benefit**: Ensures production readiness

## Data Flow Summary

1. **Detection Phase** (Steps 1-2: One-time or periodic)
   - Extract schema → Detect enterprise → Detect PII → Generate report

2. **Streaming Phase** (Steps 3-9: Continuous)
   - Database change → Event listener → Redis mapping → Encryption → AOF log → Polling → Destination insert → Validation → Audit logging

3. **Review & Approval Phase** (Steps 10-11: Human-in-the-loop)
   - Admin review dashboard → Technique overrides → Approval workflow → Production readiness check

4. **Deployment Phase** (Steps 12-13: Production)
   - Destination database (sandbox) → Production deployment → Monitoring

5. **Benefits**
   - Real-time anonymization (no daily lag)
   - All processing in memory (no raw data on disk)
   - Consistent mappings (referential integrity)
   - Encryption compliance (only ciphertext stored)
   - Crash recovery (AOF persistence)
   - Data quality validation (ensures safety)
   - Audit trail (regulatory compliance)
   - Human-in-the-loop review (quality control)
   - Production readiness verification

## Security & Compliance

- **Application-side encryption**: Sensitive data encrypted before Redis storage
- **No raw data on disk**: All anonymization in memory
- **AOF stores ciphertext**: Encrypted mappings logged to disk
- **DPDP Act 2023 compliant**: Enterprise-aware detection
- **Referential integrity**: Consistent mappings across tables
