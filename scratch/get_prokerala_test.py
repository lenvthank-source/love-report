import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def fetch_prokerala_data():
    client_id = os.getenv("PROKERALA_CLIENT_ID")
    client_secret = os.getenv("PROKERALA_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("PROKERALA_CLIENT_ID and PROKERALA_CLIENT_SECRET are required in environment/dotenv.")
        return

    # Obtain token
    auth_url = "https://api.prokerala.com/token"
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    print("Obtaining token from Prokerala API...")
    res = requests.post(auth_url, data=auth_data)
    res.raise_for_status()
    token = res.json()["access_token"]
    print("Token obtained successfully.")

    # Details to call
    # Input details for Aarav: birth at 1992-10-25T14:30:00+05:30 (Mumbai, India: lat 19.076, lon 72.8777)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    params = {
        "datetime": "1992-10-25T14:30:00+05:30",
        "coordinates": "19.076,72.8777",
        "ayanamsa": 1 # Lahiri
    }
    
    print("Calling Prokerala /v2/astrology/planet-position...")
    pos_res = requests.get(
        "https://api.prokerala.com/v2/astrology/planet-position",
        headers=headers,
        params=params
    )
    pos_res.raise_for_status()
    
    output_path = "scratch/prokerala_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pos_res.json(), f, indent=2)
    print(f"Saved Prokerala payload to {output_path}")

if __name__ == "__main__":
    fetch_prokerala_data()
