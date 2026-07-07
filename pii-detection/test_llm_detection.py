"""
Test script for LLM-based PII detection using GitHub Models API with model selection.
"""

from llm_pii_detection import detect_pii_with_llm, LLMPiiDetector

# Test columns with various PII types
test_columns = [
    {
        "column_name": "customer_aadhaar",
        "data_type": "VARCHAR(12)",
        "sample_values": ["1234 5678 9012", "2345-6789-0123", "345678901234"],
        "table_name": "customers"
    },
    {
        "column_name": "emp_contact",
        "data_type": "VARCHAR(15)",
        "sample_values": ["+91 9876543210", "919876543210", "9876543210"],
        "table_name": "employees"
    },
    {
        "column_name": "pan_number",
        "data_type": "VARCHAR(10)",
        "sample_values": ["ABCDE1234F", "FGHIJ5678K", "LMNOP9012Q"],
        "table_name": "kyc_details"
    },
    {
        "column_name": "user_email",
        "data_type": "VARCHAR(100)",
        "sample_values": ["user@example.com", "test@test.org", "admin@company.in"],
        "table_name": "users"
    },
    {
        "column_name": "product_name",
        "data_type": "VARCHAR(50)",
        "sample_values": ["Laptop", "Mouse", "Keyboard"],
        "table_name": "products"
    }
]

print("Available GitHub Models:")
print("=" * 70)
for model_id, description in LLMPiiDetector.GITHUB_MODELS.items():
    print(f"  {model_id}: {description}")
print("=" * 70)

# Test with default model (gpt-4o)
print("\nTesting with default model (gpt-4o)")
print("=" * 70)

for col in test_columns[:2]:  # Test first 2 columns
    print(f"\nTesting column: {col['column_name']}")
    print(f"Table: {col['table_name']}")
    print(f"Data type: {col['data_type']}")
    print(f"Samples: {col['sample_values'][:3]}")
    print("-" * 70)
    
    try:
        result = detect_pii_with_llm(
            column_name=col["column_name"],
            data_type=col["data_type"],
            sample_values=col["sample_values"],
            table_name=col["table_name"],
            provider="github"
        )
        
        print(f"Is PII: {result['is_pii']}")
        print(f"PII Type: {result['pii_type']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Recommended Technique: {result['recommended_technique']}")
        print(f"Model Used: {result['model_used']}")
        print(f"Provider: {result['provider_used']}")
        print(f"Reasoning: {result['reasoning']}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("=" * 70)

# Test with different model (gpt-4o-mini)
print("\nTesting with gpt-4o-mini (faster)")
print("=" * 70)

for col in test_columns[2:4]:  # Test next 2 columns
    print(f"\nTesting column: {col['column_name']}")
    print(f"Table: {col['table_name']}")
    print(f"Data type: {col['data_type']}")
    print(f"Samples: {col['sample_values'][:3]}")
    print("-" * 70)
    
    try:
        result = detect_pii_with_llm(
            column_name=col["column_name"],
            data_type=col["data_type"],
            sample_values=col["sample_values"],
            table_name=col["table_name"],
            provider="github",
            model="gpt-4o-mini"
        )
        
        print(f"Is PII: {result['is_pii']}")
        print(f"PII Type: {result['pii_type']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Recommended Technique: {result['recommended_technique']}")
        print(f"Model Used: {result['model_used']}")
        print(f"Provider: {result['provider_used']}")
        print(f"Reasoning: {result['reasoning']}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("=" * 70)
