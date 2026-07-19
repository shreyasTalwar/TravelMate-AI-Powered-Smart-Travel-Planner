import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENWEATHER_API_KEY")
destination = "Goa"

print(f"Loaded OPENWEATHER_API_KEY: {api_key}")
if not api_key:
    print("Error: OPENWEATHER_API_KEY is missing from environment.")
    exit(1)

# Step 1: Geocoding Request
print("\n--- Testing Geocoding API ---")
geo_url = f"http://api.openweathermap.org/geo/1.0/direct"
geo_params = {"q": destination, "limit": 1, "appid": api_key}
try:
    print(f"Requesting: {geo_url} with params {geo_params}")
    response = requests.get(geo_url, params=geo_params, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200 and response.json():
        location = response.json()[0]
        lat = location['lat']
        lon = location['lon']
        print(f"Success! Coordinates for {destination}: Lat {lat}, Lon {lon}")
        
        # Step 2: Forecast Request
        print("\n--- Testing 5-Day Forecast API ---")
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast"
        forecast_params = {"lat": lat, "lon": lon, "units": "metric", "appid": api_key}
        print(f"Requesting: {forecast_url} with params {forecast_params}")
        f_response = requests.get(forecast_url, params=forecast_params, timeout=10)
        print(f"Status Code: {f_response.status_code}")
        print(f"Response (truncated): {f_response.text[:500]}")
    else:
        print("Geocoding returned empty results or failed.")
except Exception as e:
    print(f"Request failed with exception: {e}")
