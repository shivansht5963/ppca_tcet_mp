import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("RAPIDAPI_KEY")
HOST = os.getenv("RAPIDAPI_HOST")
BASE = f"https://{HOST}"
headers = {"X-RapidAPI-Key": KEY, "X-RapidAPI-Host": HOST}

try:
    r = requests.get(
        BASE + "/api/v2/getPNRStatus", 
        headers=headers, 
        params={"pnrNumber": "6208182668"}, 
        timeout=10
    )
    if r.status_code == 200:
        data = r.json()
        passengers = data['data'].get('passenger', [])
        if passengers:
            print("First passenger:", json.dumps(passengers[0], indent=2))
        else:
            print("No passengers.")
    else:
        print(f"HTTP {r.status_code} - {r.text[:200]}")
except Exception as e:
    print(f"[ERROR] {e}")
