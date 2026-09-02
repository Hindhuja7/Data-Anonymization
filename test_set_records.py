import requests
import json

# Test set-records endpoint
url = "http://localhost:8000/api/pipeline/set-records"

test_cases = [
    {"total_records": 100},
    {"total_records": 1000},
    {"total_records": 10000},
    {"total_records": 100000},
    {"total_records": 1000000}
]

print("Testing set-records API endpoint:")
print("=" * 60)

for test_data in test_cases:
    try:
        response = requests.post(url, json=test_data)
        result = response.json()
        
        print(f"\nRecords: {test_data['total_records']:,}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("status") == "success":
            print(f"✓ Dynamic chunk size: {result.get('dynamic_chunk_size'):,}")
            print(f"✓ Estimated chunks: {result.get('estimated_chunks'):,}")
        else:
            print("✗ Unexpected response")
            
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("API endpoint test completed!")
