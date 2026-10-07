"""
Inspect full response structure of working endpoints
"""
import requests, json
from dotenv import load_dotenv
import os

load_dotenv()
KEY  = os.getenv("RAPIDAPI_KEY")
HOST = os.getenv("RAPIDAPI_HOST")
BASE = f"https://{HOST}"
headers = {"X-RapidAPI-Key": KEY, "X-RapidAPI-Host": HOST}

working = [
    ("/api/v1/searchStation",   {"query": "New Delhi"}),
    ("/api/v1/searchTrain",     {"query": "12951"}),
    ("/api/v1/getTrainSchedule",{"trainNo": "12951"}),
]

for path, params in working:
    r = requests.get(BASE + path, headers=headers, params=params, timeout=6)
    data = r.json()
    print(f"\n{'='*55}")
    print(f"ENDPOINT: {path}")
    print(f"{'='*55}")
    # Pretty print just first item to understand structure
    if isinstance(data.get('data'), list) and len(data['data']) > 0:
        print("First item in data[]:")
        print(json.dumps(data['data'][0], indent=2))
    elif isinstance(data.get('data'), dict):
        print("data is a dict, keys:", list(data['data'].keys()))
        print(json.dumps(data['data'], indent=2)[:800])
