"""
Debug script to test document upload directly
"""
import requests
import json

# Test upload
url = "http://localhost:8001/documents/upload"

# Create a test file
files = {
    'file': ('test.txt', b'This is a test document for debugging.', 'text/plain')
}

print("Attempting upload...")
try:
    response = requests.post(url, files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response text: {response.text if 'response' in locals() else 'No response'}")
