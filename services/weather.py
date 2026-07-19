import os
import time
import requests
from flask import current_app

# Simple in-memory cache for weather forecasts
# Structure: { "destination_name": { "timestamp": float, "data": parsed_forecast } }
_weather_cache = {}
CACHE_EXPIRY_SECONDS = 1800  # 30 minutes

def get_weather_forecast(destination):
    """
    Fetches the 5-day / 3-hour weather forecast for a given destination.
    Utilizes caching to prevent rate-limit exhaustion.
    """
    destination_key = destination.strip().lower()
    now = time.time()
    
    # Check cache first
    if destination_key in _weather_cache:
        cached_entry = _weather_cache[destination_key]
        if now - cached_entry['timestamp'] < CACHE_EXPIRY_SECONDS:
            current_app.logger.info(f"Serving weather forecast from cache for: {destination}")
            return cached_entry['data']
            
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        current_app.logger.warning("OPENWEATHER_API_KEY is not configured in .env.")
        return None
        
    try:
        # Step 1: Geocoding - Convert city name to lat/lon
        current_app.logger.info(f"Fetching coordinates for: {destination}")
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct"
        geo_params = {"q": destination, "limit": 1, "appid": api_key}
        geo_response = requests.get(geo_url, params=geo_params, timeout=10)
        
        if geo_response.status_code != 200 or not geo_response.json():
            current_app.logger.warning(f"Geocoding failed for destination: {destination}")
            return None
            
        location_data = geo_response.json()[0]
        lat = location_data['lat']
        lon = location_data['lon']
        
        # Step 2: Fetch 5-Day Forecast
        current_app.logger.info(f"Fetching 5-day forecast for lat: {lat}, lon: {lon}")
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast"
        forecast_params = {
            "lat": lat,
            "lon": lon,
            "units": "metric",  # Fetch Celsius temperatures
            "appid": api_key
        }
        
        forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)
        if forecast_response.status_code != 200:
            current_app.logger.error(f"OpenWeather API returned status {forecast_response.status_code}")
            return None
            
        raw_data = forecast_response.json()
        
        # Step 3: Process raw 3-hourly forecast data into daily summaries
        daily_forecasts = {}
        for entry in raw_data.get('list', []):
            dt_txt = entry.get('dt_txt', '') # Format: "YYYY-MM-DD HH:MM:SS"
            if not dt_txt:
                continue
                
            date_str = dt_txt.split(" ")[0]
            
            # Extract metrics
            temp = entry['main']['temp']
            humidity = entry['main']['humidity']
            wind_speed = entry['wind']['speed']
            rain_chance = entry.get('pop', 0.0) * 100 # Probability of precipitation (0.0 to 1.0)
            weather_desc = entry['weather'][0]['description']
            weather_icon = entry['weather'][0]['icon']
            
            if date_str not in daily_forecasts:
                daily_forecasts[date_str] = {
                    "date": date_str,
                    "temps": [],
                    "humidities": [],
                    "wind_speeds": [],
                    "rain_chances": [],
                    "descriptions": [],
                    "icons": []
                }
                
            daily_forecasts[date_str]["temps"].append(temp)
            daily_forecasts[date_str]["humidities"].append(humidity)
            daily_forecasts[date_str]["wind_speeds"].append(wind_speed)
            daily_forecasts[date_str]["rain_chances"].append(rain_chance)
            daily_forecasts[date_str]["descriptions"].append(weather_desc)
            daily_forecasts[date_str]["icons"].append(weather_icon)
            
        # Summarize by daily averages/max
        processed_forecast = []
        for date_str, data in sorted(daily_forecasts.items())[:5]: # Cap at 5 days forecast
            avg_temp = sum(data["temps"]) / len(data["temps"])
            max_temp = max(data["temps"])
            min_temp = min(data["temps"])
            avg_humidity = sum(data["humidities"]) / len(data["humidities"])
            max_wind = max(data["wind_speeds"])
            max_rain_chance = max(data["rain_chances"])
            
            # Select the most common weather icon/description for the day
            common_desc = max(set(data["descriptions"]), key=data["descriptions"].count)
            common_icon = max(set(data["icons"]), key=data["icons"].count)
            
            processed_forecast.append({
                "date": date_str,
                "temp_avg": round(avg_temp, 1),
                "temp_max": round(max_temp, 1),
                "temp_min": round(min_temp, 1),
                "humidity": round(avg_humidity),
                "wind_speed": round(max_wind, 1),
                "rain_chance": round(max_rain_chance),
                "description": common_desc.capitalize(),
                "icon": common_icon
            })
            
        # Cache results
        _weather_cache[destination_key] = {
            "timestamp": now,
            "data": processed_forecast
        }
        
        return processed_forecast
        
    except Exception as e:
        current_app.logger.error(f"Error calling OpenWeather: {str(e)}")
        return None
