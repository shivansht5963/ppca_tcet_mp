import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("RAPIDAPI_KEY")
HOST = os.getenv("RAPIDAPI_HOST")
BASE = f"https://{HOST}"
headers = {"X-RapidAPI-Key": KEY, "X-RapidAPI-Host": HOST}

today_str = datetime.today().strftime('%Y-%m-%d')
print(f"Using date: {today_str}")

def test_endpoint(name, path, params):
    try:
        r = requests.get(BASE + path, headers=headers, params=params, timeout=10)
        print(f"\n{'='*55}")
        print(f"{name}: {path}")
        print(f"{'='*55}")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data.get('data'), list) and len(data['data']) > 0:
                print(json.dumps(data['data'][0], indent=2))
            elif isinstance(data.get('data'), dict):
                print(json.dumps(data['data'], indent=2)[:1000])
            else:
                print(json.dumps(data, indent=2)[:1000])
        else:
            print(f"HTTP {r.status_code} - {r.text[:200]}")
    except Exception as e:
        print(f"[ERROR] {e}")

# 1. Trains Between
test_endpoint("Trains Between", "/api/v3/trainBetweenStations", {
    "fromStationCode": "NDLS",
    "toStationCode": "MMCT",
    "dateOfJourney": today_str
})

# 2. Live Status
test_endpoint("Live Status", "/api/v1/liveTrainStatus", {
    "trainNo": "12951",
    "startDay": "1"
})

# 3. PNR Status - PNRs are hard to find, but we can see the structure if it returns an error with the expected schema, or just pass a real-looking dummy.
test_endpoint("PNR Status", "/api/v2/getPNRStatus", {
    "pnrNumber": "1234567890"
})
