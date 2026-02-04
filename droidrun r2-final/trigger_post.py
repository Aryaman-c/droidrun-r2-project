import requests
import json

url = "http://localhost:8000/post"
headers = {"Content-Type": "application/json"}
data = {
    "title": "Test Post",
    "body": "Testing automation reliability",
    "subreddit": "indiasocial"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
