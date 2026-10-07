import requests
import os
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("RAPIDAPI_KEY")
HOST = os.getenv("RAPIDAPI_HOST")
BASE = f"https://{HOST}"
headers = {"X-RapidAPI-Key": KEY, "X-RapidAPI-Host": HOST}

def test_endpoint(path, params):
    try:
        r = requests.get(BASE + path, headers=headers, params=params, timeout=5)
        print(f"[{r.status_code}] {path}")
        if r.status_code == 200:
            print(f"   SUCCESS! Response: {str(r.json())[:100]}")
            return True
    except Exception as e:
        print(f"[ERROR] {path} - {e}")
    return False

print("Hunting for Trains Between Stations...")
between_paths = [
    "/api/v1/trainsBetweenStations",
    "/api/v1/trainBetweenStation",
    "/api/v2/trainBetweenStations",
    "/api/v3/trainBetweenStations",
    "/api/v1/searchTrainBetweenStations",
    "/api/v1/getTrainsBetweenStations",
]
for p in between_paths:
    if test_endpoint(p, {"fromStationCode": "NDLS", "toStationCode": "MMCT", "dateOfJourney": "1"}): break
    
print("\nHunting for Live Status...")
live_paths = [
    "/api/v1/liveTrainStatus",
    "/api/v1/getLiveTrainStatus",
    "/api/v1/trainRunningStatus",
    "/api/v2/liveTrainStatus",
]
for p in live_paths:
    if test_endpoint(p, {"trainNo": "12951", "startDay": "1"}): break

print("\nHunting for PNR Status...")
pnr_paths = [
    "/api/v1/pnrStatus",
    "/api/v1/checkPNRStatus",
    "/api/v2/getPNRStatus",
    "/api/v1/pnr",
]
for p in pnr_paths:
    if test_endpoint(p, {"pnrNumber": "2222222222"}): break
