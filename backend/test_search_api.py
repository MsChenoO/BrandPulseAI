import requests
import json

url = "http://localhost:8000/search"
data = {
    "query": "autonomous driving",
    "limit": 10
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")
