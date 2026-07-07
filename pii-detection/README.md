# PII Detection Module

## What This Does
This module detects Personally Identifiable Information (PII) using two approaches:
1. **LLM-based detection** (Primary) - Context-aware using Claude/OpenAI/GitHub Models API
2. **Regex patterns** (Secondary) - India-specific and global pattern matching

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

2. Configure API keys:
```bash
cp .env.example .env
# Edit .env and add your API key
```

3. For GitHub Models (Free):
   - Go to https://github.com/models
   - Select a model (e.g., GPT-4o)
   - Click "Use this model" to generate a Personal Access Token (PAT)
   - Add the PAT to `.env` as `GITHUB_API_KEY`

### Testing
```bash
# Test regex patterns
python india_regex_patterns.py

# Test LLM detection (requires API key)
python llm_pii_detection.py
```

## Next Steps
- Implement global regex patterns (email, credit card, SSN, etc.)
- Create combined detection engine (LLM OR regex logic)
- Create sample database schema with Indian PII columns
- Test detection on real database data
