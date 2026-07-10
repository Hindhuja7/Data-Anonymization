# PII Detection System

## What This Does
A complete PII (Personally Identifiable Information) detection system for databases with Indian-specific PII patterns. The system:
1. Connects to databases (PostgreSQL, MySQL, SQL Server)
2. Extracts table schemas and sample data
3. Detects PII using LLM-based and regex-based approaches
4. Generates synthetic Indian enterprise test data
5. Loads data into Neon PostgreSQL for testing

## Implementation Details

### Detection Layers

#### Layer 1: LLM-based Detection (Primary)
- Context-aware detection using column name, data type, sample values, and table name
- Handles ambiguous column names (e.g., "emp_contact", "kyc_uid")
- India-specific awareness (Aadhaar, PAN, +91 phone)
- Returns confidence score, PII type, recommended anonymization technique, and reasoning

#### Layer 2: India-specific Regex Patterns (Secondary)
1. **Aadhaar** - 12-digit unique identity number (confidence: 0.95)
2. **PAN** - Permanent Account Number (confidence: 0.98)
3. **Indian Phone** - Mobile numbers starting with 6-9 (confidence: 0.90)
4. **GSTIN** - Goods and Services Tax Identification Number (confidence: 0.95)
5. **Indian Passport** - 8-character passport number (confidence: 0.85)
6. **Driving License** - State-specific license formats (confidence: 0.75)
7. **Voter ID (EPIC)** - Elector's Photo Identity Card (confidence: 0.80)
8. **UAN** - Universal Account Number for EPF (confidence: 0.85)

### API Provider Options

**GitHub Models (FREE - Recommended)**
- 100% free access to GPT-4o and other models
- No credit card required
- Get your key: https://github.com/models
- Uses OpenAI SDK with custom base_url

**OpenAI (Paid)**
- Requires billing setup
- Models: GPT-4, GPT-4o

**Anthropic/Claude (Paid)**
- Requires billing setup
- Models: Claude 3.5 Sonnet

### Usage

#### Complete Database PII Detection
```bash
# 1. Generate synthetic test data
python generate_test_data.py

# 2. Load data into Neon PostgreSQL
python load_to_neon.py

# 3. Run PII detection on database
python database_pii_detection.py
```

#### LLM-based Detection
```python
from llm_pii_detection import detect_pii_with_llm

result = detect_pii_with_llm(
    column_name="customer_aadhaar",
    data_type="VARCHAR(12)",
    sample_values=["1234 5678 9012", "2345-6789-0123"],
    table_name="customers",
    provider="github"  # or "openai" or "anthropic"
)
```

#### Regex-based Detection
```python
from india_regex_patterns import detect_india_pii

result = detect_india_pii("ABCDE1234F")
# Returns: {"is_pii": True, "pii_type": "pan", "confidence": 0.98, "matched_value": "ABCDE1234F"}
```

### Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```bash
# Database configuration
DB_TYPE=postgresql
DB_HOST=your-neon-host
DB_PORT=5432
DB_USERNAME=your-username
DB_PASSWORD=your-password
DB_NAME=neondb

# LLM configuration
LLM_PROVIDER=github
LLM_MODEL=gpt-4o
GITHUB_API_KEY=your-github-token
```

3. For GitHub Models (Free):
   - Go to https://github.com/models
   - Select a model (e.g., GPT-4o)
   - Click "Use this model" to generate a Personal Access Token (PAT)
   - Add the PAT to `.env` as `GITHUB_API_KEY`

4. For Neon PostgreSQL (Free):
   - Sign up at https://neon.tech
   - Create a project
   - Get connection details from the dashboard

### Testing
```bash
# Test regex patterns
python india_regex_patterns.py

# Test LLM detection (requires API key)
python llm_pii_detection.py

# Generate synthetic test data
python generate_test_data.py

# Load data to Neon PostgreSQL
python load_to_neon.py

# Run complete PII detection on database
python database_pii_detection.py
```

## Test Data
The system generates synthetic Indian enterprise dataset:
- **100,000 customers** with Aadhaar, PAN, phone, address
- **5,000 employees** with Aadhaar, PAN, UAN, salary
- **150,000 accounts** with account numbers, GSTIN, balance
- **500,000 transactions** with amounts, beneficiaries

Test data is saved in `test_data/` directory and can be loaded into Neon PostgreSQL using `load_to_neon.py`.

## Files Added
- `database_connector.py` - Database connection management
- `schema_extractor.py` - Extract table schemas
- `sample_extractor.py` - Fetch sample data for analysis
- `database_pii_detection.py` - Main PII detection orchestrator
- `generate_test_data.py` - Synthetic data generator
- `load_to_neon.py` - Neon PostgreSQL data loader
- `test_data/` - Generated test data and schema

## Next Steps
- Implement global regex patterns (email, credit card, SSN, etc.)
- Create combined detection engine (LLM OR regex logic)
- Add more anonymization techniques
- Test on real production databases
