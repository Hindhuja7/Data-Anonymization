import requests
import json

# Test validation approval endpoint
url = "http://localhost:8000/api/pipeline/approve-validation"

try:
    print("Testing validation approval endpoint...")
    response = requests.post(url)
    result = response.json()
    print("Response Status:", response.status_code)
    print("Response Data:", json.dumps(result, indent=2))
    
    if result.get("status") == "success":
        print("\n✓ Validation approval endpoint working!")
    else:
        print("\n✗ Validation approval endpoint returned unexpected status")
        
except Exception as e:
    print(f"Error: {e}")

# Test modify and re-anonymize endpoint
url2 = "http://localhost:8000/api/pipeline/modify-and-reanonymize"
test_policy = {
    "tables": {
        "users": {
            "name": {"technique": "tokenization"},
            "email": {"technique": "hashing"}
        }
    }
}

try:
    print("\n\nTesting modify and re-anonymize endpoint...")
    response = requests.post(url2, json=test_policy)
    result = response.json()
    print("Response Status:", response.status_code)
    print("Response Data:", json.dumps(result, indent=2))
    
    if result.get("status") == "success":
        print("\n✓ Modify and re-anonymize endpoint working!")
    else:
        print("\n✗ Modify and re-anonymize endpoint returned unexpected status")
        
except Exception as e:
    print(f"Error: {e}")
