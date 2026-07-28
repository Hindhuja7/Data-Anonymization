import requests
import json

# Test database connection with auto-start enabled
url = "http://localhost:8000/api/database/test"
data = {
    "host": "localhost",
    "port": "5432",
    "username": "test",
    "password": "test",
    "database": "testdb",
    "auto_start": True
}

try:
    print("Sending request with auto_start=True...")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data)
    result = response.json()
    print("Response Status:", response.status_code)
    print("Response Data:", json.dumps(result, indent=2))
    
    if result.get("pipeline_started"):
        print("\n✓ Auto-start functionality working!")
        print(f"Pipeline message: {result.get('pipeline_message')}")
    else:
        print("\n✗ Auto-start not triggered")
        print(f"Has pipeline_started field: {'pipeline_started' in result}")
        print(f"Auto-start in request: {data.get('auto_start')}")
        
except Exception as e:
    print(f"Error: {e}")
