import requests
import json

# Set the API endpoint URL
url = "http://localhost:8002/query"

# Define the request parameters
params = {
    "query": "What is the capital of France?",
    "session_id": "abc123"
}

# Make the HTTP GET request
response = requests.get(url, params=params)

# Check the response status code
if response.status_code == 200:
    # Parse the JSON response
    data = json.loads(response.text)
    print(f"Response: {data['response']}")
else:
    print(f"Error: {response.status_code} - {response.text}")