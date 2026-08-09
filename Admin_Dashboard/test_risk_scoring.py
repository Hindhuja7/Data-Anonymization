"""
Test script for Risk Scoring Engine
"""

from risk_scoring_engine import RiskScoringEngine

# Create instance
engine = RiskScoringEngine()

# Test case 1: No policies (should be LOW risk)
print("=" * 80)
print("Test Case 1: No policies")
print("=" * 80)
result1 = engine.calculate_policy_risk([])
print(f"Risk Score: {result1['policy_risk_score']}")
print(f"Privacy Score: {result1['privacy_score']}")
print(f"Risk Level: {result1['risk_level']}")
print(f"Vulnerabilities: {result1['vulnerabilities']}")
print()

# Test case 2: Safe policies (all anonymized)
print("=" * 80)
print("Test Case 2: All anonymized (HASHING, MASKING)")
print("=" * 80)
safe_policies = [
    {
        "column_name": "email",
        "table_name": "customers",
        "anonymization_technique": "HASHING",
        "pii_type": "EMAIL",
        "is_pii": True
    },
    {
        "column_name": "phone",
        "table_name": "customers",
        "anonymization_technique": "MASKING",
        "pii_type": "PHONE",
        "is_pii": True
    }
]
result2 = engine.calculate_policy_risk(safe_policies)
print(f"Risk Score: {result2['policy_risk_score']}")
print(f"Privacy Score: {result2['privacy_score']}")
print(f"Risk Level: {result2['risk_level']}")
print(f"Vulnerabilities: {result2['vulnerabilities']}")
print()

# Test case 3: High risk (direct PII left un-anonymized)
print("=" * 80)
print("Test Case 3: Direct PII left un-anonymized (NO_CHANGE)")
print("=" * 80)
high_risk_policies = [
    {
        "column_name": "email",
        "table_name": "customers",
        "anonymization_technique": "NO_CHANGE",
        "pii_type": "EMAIL",
        "is_pii": True
    },
    {
        "column_name": "phone",
        "table_name": "customers",
        "anonymization_technique": "NO_CHANGE",
        "pii_type": "PHONE",
        "is_pii": True
    }
]
result3 = engine.calculate_policy_risk(high_risk_policies)
print(f"Risk Score: {result3['policy_risk_score']}")
print(f"Privacy Score: {result3['privacy_score']}")
print(f"Risk Level: {result3['risk_level']}")
print(f"Vulnerabilities:")
for vuln in result3['vulnerabilities']:
    print(f"  - {vuln}")
print()

# Test case 4: Medium risk (quasi-identifiers left un-anonymized)
print("=" * 80)
print("Test Case 4: Quasi-identifiers left un-anonymized (NO_CHANGE)")
print("=" * 80)
medium_risk_policies = [
    {
        "column_name": "dob",
        "table_name": "customers",
        "anonymization_technique": "NO_CHANGE",
        "pii_type": "DOB",
        "is_pii": True
    },
    {
        "column_name": "address",
        "table_name": "customers",
        "anonymization_technique": "NO_CHANGE",
        "pii_type": "ADDRESS",
        "is_pii": True
    }
]
result4 = engine.calculate_policy_risk(medium_risk_policies)
print(f"Risk Score: {result4['policy_risk_score']}")
print(f"Privacy Score: {result4['privacy_score']}")
print(f"Risk Level: {result4['risk_level']}")
print(f"Vulnerabilities:")
for vuln in result4['vulnerabilities']:
    print(f"  - {vuln}")
print()

# Test case 5: Mixed risk (some protected, some not)
print("=" * 80)
print("Test Case 5: Mixed policies (some protected, some not)")
print("=" * 80)
mixed_policies = [
    {
        "column_name": "email",
        "table_name": "customers",
        "anonymization_technique": "HASHING",
        "pii_type": "EMAIL",
        "is_pii": True
    },
    {
        "column_name": "phone",
        "table_name": "customers",
        "anonymization_technique": "NO_CHANGE",
        "pii_type": "PHONE",
        "is_pii": True
    },
    {
        "column_name": "dob",
        "table_name": "customers",
        "anonymization_technique": "NO_CHANGE",
        "pii_type": "DOB",
        "is_pii": True
    }
]
result5 = engine.calculate_policy_risk(mixed_policies)
print(f"Risk Score: {result5['policy_risk_score']}")
print(f"Privacy Score: {result5['privacy_score']}")
print(f"Risk Level: {result5['risk_level']}")
print(f"Vulnerabilities:")
for vuln in result5['vulnerabilities']:
    print(f"  - {vuln}")
print()

print("=" * 80)
print("All tests completed successfully!")
print("=" * 80)
