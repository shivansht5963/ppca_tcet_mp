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

try:
    r = requests.get(
        BASE + "/api/v3/trainBetweenStations", 
        headers=headers, 
        params={"fromStationCode": "NDLS", "toStationCode": "MMCT", "dateOfJourney": today_str}, 
        timeout=10
    )
    if r.status_code == 200:
        data = r.json()
        print("SUCCESS! Keys in response:", data.keys())
        if isinstance(data.get('data'), list) and len(data['data']) > 0:
            print("Structure of first train:")
            print(json.dumps(data['data'][0], indent=2))
        else:
            print("No data array or empty array. Full response:")
            print(json.dumps(data, indent=2)[:1000])
    else:
        print(f"HTTP {r.status_code} - {r.text[:200]}")
except Exception as e:
    print(f"[ERROR] {e}")
