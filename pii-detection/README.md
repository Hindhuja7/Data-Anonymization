# Database PII Detection System

A privacy-preserving PII detection pipeline for databases with enterprise-aware context and sequential model fallback.

## Architecture

```
Database Connection
        │
        ▼
Schema Extractor ◄──────────────────────────────┐
        │                                        │
        ▼                                        │
Enterprise Detector (LLM)                        │
        │                                        │
        ▼                                        │
Sample Extractor (Column-wise Random)           │
        │                                        │
        ▼                                        │
PII Detector (LLM + Regex) ◄────────────────────┘
        │
        ▼
  Detection Report
```

## Components

| Module | File | Responsibility |
|--------|------|----------------|
| Database Connector | `database_connector.py` | Manages DB connections (PostgreSQL, MySQL, SQL Server) |
| Schema Extractor | `schema_extractor.py` | Extracts table/column metadata from database |
| Enterprise Detector | `enterprise_detector.py` | Detects enterprise type (BANKING, HR, etc.) using LLM |
| Sample Extractor | `sample_extractor.py` | Column-wise random sampling for privacy |
| LLM Client | `llm_client.py` | GitHub Models client with sequential fallback |
| LLM PII Detector | `llm_pii_detection.py` | Context-aware PII detection using LLM |
| India Regex Patterns | `india_regex_patterns.py` | India-specific PII pattern matching |
| Combined Detector | `combined_detector.py` | Merges LLM and regex detection results |
| Database PII Detector | `database_pii_detection.py` | Main pipeline orchestrator |

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API key
```bash
# Create .env file
GITHUB_API_KEY=your_github_pat_here
LLM_MODEL=gpt-4o
LLM_PROVIDER=github
```

### 3. Get GitHub API Key (FREE)
- Go to https://github.com/models
- Select a model (e.g., GPT-4o)
- Click "Use this model" to generate a Personal Access Token
- Add the PAT to `.env` as `GITHUB_API_KEY`

### 4. Run detection
```python
from database_pii_detection import detect_pii_from_database

result = detect_pii_from_database(
    database_type="postgresql",
    host="your-host",
    port=5432,
    username="your-username",
    password="your-password",
    database_name="your-database",
    provider="github",
    model="gpt-4o"
)
```

## Detection Types

### India-Specific PII
| Type | Pattern | Confidence |
|------|---------|------------|
| AADHAAR | 12-digit unique identity | 0.95 |
| PAN | Permanent Account Number | 0.98 |
| INDIAN_PHONE | Mobile numbers starting with 6-9 | 0.90 |
| GSTIN | Goods and Services Tax ID | 0.95 |
| INDIAN_PASSPORT | 8-character passport number | 0.85 |
| DRIVING_LICENSE | State-specific license formats | 0.75 |
| VOTER_ID | Elector's Photo Identity Card | 0.80 |
| UAN | Universal Account Number for EPF | 0.85 |

### Global PII
| Type | Description |
|------|-------------|
| EMAIL | Email addresses |
| CREDIT_CARD | Credit card numbers |
| SSN | Social Security Numbers |
| IP_ADDRESS | IP addresses |
| FULL_NAME | Full names |
| ADDRESS | Physical addresses |
| DATE_OF_BIRTH | Birth dates |

### Financial/Sensitive (DPDP Act 2023)
| Type | Description |
|------|-------------|
| FINANCIAL | Salary, balance, income, credit_score, transaction_amount |
| BANK_ACCOUNT | Bank account numbers |
| MEDICAL | Diagnosis, blood_type, prescription |

## Anonymization Techniques

| Technique | Use Case | Description |
|-----------|----------|-------------|
| TOKENIZATION | Names, emails, phones | Replace with realistic fake values |
| MASKING | Aadhaar, PAN, credit_card | Replace sensitive characters with X |
| HASHING | IDs (user_id, customer_id) | One-way hash |
| DIFFERENTIAL_PRIVACY | Numerical (salary, age) | Add statistical noise |
| NO_CHANGE | Non-PII columns | No modification |

## Enterprise Types

| Type | Compliance Law | Keywords |
|------|----------------|----------|
| BANKING | RBI Guidelines + DPDP Act 2023 | accounts, loans, transactions, ifsc_code, emi |
| HEALTHCARE | DPDP Act 2023 + Medical Council | patients, doctors, prescriptions, diagnosis |
| HR | DPDP Act 2023 + Labour Code | employees, payroll, attendance, uan, designation |
| ECOMMERCE | DPDP Act 2023 + Consumer Protection | orders, products, cart, delivery_address |
| INSURANCE | IRDAI Guidelines + DPDP Act 2023 | policies, claims, premiums, coverage |
| TELECOM | TRAI Guidelines + DPDP Act 2023 | subscribers, calls, data_usage, recharge |
| GENERAL | DPDP Act 2023 | Generic/unclear enterprise |

## Model Fallback

Priority order (sequential, not parallel):
1. User-specified model (if provided)
2. gpt-4o (highest quality)
3. gpt-4o-mini (faster, cheaper)
4. gpt-4-turbo (fallback)

**Note:** Only GitHub models are supported. Invalid models will raise an error.

## Output Files

After a run, the following files are generated:

```
pii_detection_report.json    # Complete detection report with enterprise info
```

### Sample Report Structure
```json
{
  "database_name": "neondb",
  "database_type": "postgresql",
  "enterprise_type": "BANKING",
  "enterprise_confidence": 0.9,
  "compliance_law": "RBI Guidelines, DPDP Act 2023",
  "tables": [
    {
      "table_name": "employees",
      "columns": [
        {
          "column_name": "salary",
          "is_pii": true,
          "pii_type": "FINANCIAL",
          "confidence": 1.0,
          "recommended_technique": "DIFFERENTIAL_PRIVACY"
        }
      ]
    }
  ]
}
```

## CLI Reference

```bash
python database_pii_detection.py
```

**Environment Variables:**
- `GITHUB_API_KEY` - GitHub Personal Access Token (required)
- `LLM_MODEL` - Model to use (default: gpt-4o)
- `LLM_PROVIDER` - Provider (default: github)

## Project Structure

```
pii-detection/
├── database_connector.py       # DB connection management
├── schema_extractor.py         # Schema metadata extraction
├── sample_extractor.py         # Column-wise random sampling
├── enterprise_detector.py      # Enterprise type detection
├── llm_client.py               # GitHub Models client with fallback
├── llm_pii_detection.py        # LLM-based PII detection
├── india_regex_patterns.py     # India-specific regex patterns
├── combined_detector.py        # LLM + regex merger
├── database_pii_detection.py   # Main pipeline entry point
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── README.md                   # This file
```

## Cost Estimation

**Per database scan:**
- 1 enterprise detection call
- 4 PII detection calls (one per table)
- ~2K-4K tokens per call
- **Total cost:** ~$0.01-0.02 per scan (with GitHub Models)

**GitHub Models Pricing:**
- gpt-4o: ~$5-15 per 1M tokens
- gpt-4o-mini: ~$0.15-0.60 per 1M tokens

## Privacy Features

1. **Column-wise random sampling** - No single user's complete record exposed
2. **Read-only database access** - Prevents accidental data modification
3. **Enterprise context awareness** - Improves detection accuracy
4. **Conservative fallback** - Flags as PII if detection fails (better safe than sorry)

## Configuration

### Database Connection
```python
detector = DatabasePIIDetector(
    database_type="postgresql",  # or "mysql", "sqlserver"
    host="localhost",
    port=5432,
    username="user",
    password="password",
    database_name="mydb",
    provider="github",
    model="gpt-4o"
)
```

### Model Selection
```python
# Via parameter
detector = DatabasePIIDetector(..., model="gpt-4o-mini")

# Via .env file
LLM_MODEL=gpt-4o-mini

# Via environment variable
export LLM_MODEL=gpt-4o-mini
```

## Extending the System

### Add new PII types
Edit the prompt in `llm_pii_detection.py` to include new PII types in the `PII TYPES TO DETECT` section.

### Add new enterprise types
Edit the prompt in `enterprise_detector.py` to include new enterprise types in the `Enterprise Types` section.

### Add new regex patterns
Edit `india_regex_patterns.py` to add new patterns to the `IndiaPIIPatterns` class.

## Compliance

This system is designed to comply with:
- **DPDP Act 2023** (Digital Personal Data Protection Act, India)
- **RBI Guidelines** (for banking enterprises)
- **IRDAI Guidelines** (for insurance enterprises)
- **TRAI Guidelines** (for telecom enterprises)

## Ethical Notice

This tool is intended solely for authorized privacy assessments of databases you own or have explicit permission to analyze. Misuse against third-party databases without consent is unethical and potentially illegal.
