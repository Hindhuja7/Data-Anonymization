# Data Anonymization System

A comprehensive privacy-preserving data anonymization platform for Indian enterprises, designed to comply with DPDP Act 2023 and sector-specific regulations.

## Overview

This system provides automated detection and anonymization of Personally Identifiable Information (PII) in databases, with enterprise-aware context and regulatory compliance for Indian businesses.

## Architecture

```
data-anonymization/
├── pii-detection/           # PII detection module
│   ├── database_connector.py
│   ├── schema_extractor.py
│   ├── sample_extractor.py
│   ├── enterprise_detector.py
│   ├── llm_client.py
│   ├── llm_pii_detection.py
│   ├── india_regex_patterns.py
│   ├── combined_detector.py
│   └── database_pii_detection.py
└── README.md
```

## Features

### PII Detection Module (`pii-detection/`)

- **Structured Database Support**: PostgreSQL, MySQL, SQL Server
- **Enterprise-Aware Detection**: Automatically detects enterprise type (BANKING, HR, HEALTHCARE, etc.) from database schema
- **Context-Aware LLM Detection**: Uses GitHub Models with enterprise context for accurate PII identification
- **India-Specific Patterns**: Regex patterns for Aadhaar, PAN, GSTIN, Indian Phone, etc.
- **Sequential Model Fallback**: Automatic fallback between GitHub models (gpt-4o → gpt-4o-mini → gpt-4-turbo)
- **Column-Wise Random Sampling**: Privacy-preserving sample extraction
- **Compliance Mapping**: Automatic compliance law mapping based on enterprise type
- **Real-Time PII Detection**: On-demand scanning of database schemas and sample data

### Supported Enterprise Types

| Type | Compliance Law |
|------|----------------|
| BANKING | RBI Guidelines + DPDP Act 2023 |
| HEALTHCARE | DPDP Act 2023 + Medical Council |
| HR | DPDP Act 2023 + Labour Code |
| ECOMMERCE | DPDP Act 2023 + Consumer Protection |
| INSURANCE | IRDAI Guidelines + DPDP Act 2023 |
| TELECOM | TRAI Guidelines + DPDP Act 2023 |
| GENERAL | DPDP Act 2023 |

### Supported Databases

- PostgreSQL
- MySQL
- SQL Server

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/Hindhuja7/Data-Anonymization.git
cd data-anonymization
```

### 2. Navigate to PII detection module
```bash
cd pii-detection
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API keys
```bash
# Create .env file
GITHUB_API_KEY=your_github_pat_here
LLM_MODEL=gpt-4o
LLM_PROVIDER=github
```

### 5. Get GitHub API Key (FREE)
- Go to https://github.com/models
- Select a model (e.g., GPT-4o)
- Click "Use this model" to generate a Personal Access Token
- Add the PAT to `.env` as `GITHUB_API_KEY`

### 6. Run PII detection
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

## PII Detection Types

### India-Specific PII
- AADHAAR - 12-digit unique identity
- PAN - Permanent Account Number
- INDIAN_PHONE - Mobile numbers starting with 6-9
- GSTIN - Goods and Services Tax ID
- INDIAN_PASSPORT - 8-character passport number
- DRIVING_LICENSE - State-specific license formats
- VOTER_ID - Elector's Photo Identity Card
- UAN - Universal Account Number for EPF

### Global PII
- EMAIL - Email addresses
- CREDIT_CARD - Credit card numbers
- SSN - Social Security Numbers
- IP_ADDRESS - IP addresses
- FULL_NAME - Full names
- ADDRESS - Physical addresses
- DATE_OF_BIRTH - Birth dates

### Financial/Sensitive (DPDP Act 2023)
- FINANCIAL - Salary, balance, income, credit_score
- BANK_ACCOUNT - Bank account numbers
- MEDICAL - Diagnosis, blood_type, prescription

## Anonymization Techniques

| Technique | Use Case | Description |
|-----------|----------|-------------|
| TOKENIZATION | Names, emails, phones | Replace with realistic fake values |
| MASKING | Aadhaar, PAN, credit_card | Replace sensitive characters with X |
| HASHING | IDs (user_id, customer_id) | One-way hash |
| DIFFERENTIAL_PRIVACY | Numerical (salary, age) | Add statistical noise |
| NO_CHANGE | Non-PII columns | No modification |

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

## Compliance

This system is designed to comply with:
- **DPDP Act 2023** (Digital Personal Data Protection Act, India)
- **RBI Guidelines** (for banking enterprises)
- **IRDAI Guidelines** (for insurance enterprises)
- **TRAI Guidelines** (for telecom enterprises)

## Project Structure

```
data-anonymization/
├── pii-detection/              # PII detection module
│   ├── database_connector.py   # DB connection management
│   ├── schema_extractor.py     # Schema metadata extraction
│   ├── sample_extractor.py     # Column-wise random sampling
│   ├── enterprise_detector.py  # Enterprise type detection
│   ├── llm_client.py           # GitHub Models client with fallback
│   ├── llm_pii_detection.py    # LLM-based PII detection
│   ├── india_regex_patterns.py # India-specific regex patterns
│   ├── combined_detector.py    # LLM + regex merger
│   ├── database_pii_detection.py # Main pipeline entry point
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables
│   └── README.md               # Module documentation
├── .gitignore
└── README.md                   # This file
```

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

## Ethical Notice

This tool is intended solely for authorized privacy assessments of databases you own or have explicit permission to analyze. Misuse against third-party databases without consent is unethical and potentially illegal.

## Future Enhancements

- [ ] Anonymization module implementation
- [ ] Admin dashboard for review and overrides
- [ ] Integration with data pipelines
- [ ] Automated compliance reporting
