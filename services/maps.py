import json
import requests
from flask import current_app
from extensions import db
from models.poi import POI

def get_coordinates(destination):
    """
    Geocodes a destination name into latitude and longitude using Nominatim API.
    """
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "TravelMate/1.0 (contact@travelmate.com)"
    }
    params = {
        "q": destination,
        "format": "json",
        "limit": 1
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return float(data['lat']), float(data['lon'])
    except Exception as e:
        current_app.logger.error(f"Nominatim Geocoding Error for {destination}: {str(e)}")
    return None

def fetch_overpass_pois(lat, lon):
    """
    Queries Overpass API for nearby hospitals, police stations, ATMs, hotels, 
    restaurants, and attractions within a 5000m radius.
    """
    url = "https://overpass-api.de/api/interpreter"
    
    # Overpass QL query
    query = f"""
    [out:json][timeout:15];
    (
      node["amenity"="hospital"](around:5000,{lat},{lon});
      node["amenity"="police"](around:5000,{lat},{lon});
      node["amenity"="atm"](around:5000,{lat},{lon});
      node["tourism"="hotel"](around:5000,{lat},{lon});
      node["tourism"="hostel"](around:5000,{lat},{lon});
      node["amenity"="restaurant"](around:5000,{lat},{lon});
      node["tourism"="attraction"](around:5000,{lat},{lon});
    );
    out body 30; // Limit to 30 nodes for speed
    """
    try:
        response = requests.post(url, data={"data": query}, timeout=15)
        if response.status_code == 200:
            raw_elements = response.json().get('elements', [])
            
            # Categorize elements
            pois = {
                "hospitals": [],
                "police": [],
                "atms": [],
                "hotels": [],
                "restaurants": [],
                "attractions": []
            }
            
            for elem in raw_elements:
                tags = elem.get('tags', {})
                name = tags.get('name', 'Unnamed Location')
                lat_p = elem.get('lat')
                lon_p = elem.get('lon')
                
                if not lat_p or not lon_p:
                    continue
                    
                poi_item = {
                    "name": name,
                    "lat": lat_p,
                    "lon": lon_p,
                    "address": tags.get('addr:street', 'Nearby Area')
                }
                
                # Sort into categories
                if tags.get('amenity') == 'hospital':
                    pois['hospitals'].append(poi_item)
                elif tags.get('amenity') == 'police':
                    pois['police'].append(poi_item)
                elif tags.get('amenity') == 'atm':
                    pois['atms'].append(poi_item)
                elif tags.get('tourism') in ['hotel', 'hostel']:
                    pois['hotels'].append(poi_item)
                elif tags.get('amenity') == 'restaurant':
                    pois['restaurants'].append(poi_item)
                elif tags.get('tourism') == 'attraction' or tags.get('historic') or tags.get('leisure') == 'park':
                    pois['attractions'].append(poi_item)
                    
            return pois
    except Exception as e:
        current_app.logger.error(f"Overpass POI Fetch Error: {str(e)}")
        
    return None

def generate_fallback_pois(lat, lon, destination):
    """
    Returns a set of fallback POIs in case Overpass API is down or times out.
    Generates coordinates offset slightly from the center.
    """
    return {
        "hospitals": [
            {"name": f"{destination} General Hospital", "lat": lat + 0.005, "lon": lon + 0.005, "address": "Main Medical Center"},
            {"name": "City Emergency Clinic", "lat": lat - 0.004, "lon": lon + 0.003, "address": "Downtown Wing"}
        ],
        "police": [
            {"name": "Central Police Station", "lat": lat + 0.002, "lon": lon - 0.004, "address": "Civic Center"}
        ],
        "atms": [
            {"name": "State Bank ATM", "lat": lat + 0.001, "lon": lon + 0.001, "address": "Market Square"},
            {"name": "HDFC Bank ATM", "lat": lat - 0.002, "lon": lon - 0.002, "address": "Transit Station"}
        ],
        "hotels": [
            {"name": "Traveler's Cozy Lodge", "lat": lat - 0.003, "lon": lon + 0.005, "address": "Tourist Boulevard"},
            {"name": "Grand Landmark Hotel", "lat": lat + 0.004, "lon": lon - 0.003, "address": "Luxury Row"}
        ],
        "restaurants": [
            {"name": "The Local Spoon Cafe", "lat": lat + 0.003, "lon": lon + 0.002, "address": "Food Street"},
            {"name": "Traditional Tastes Bistro", "lat": lat - 0.005, "lon": lon - 0.001, "address": "Old Bazaar Road"}
        ],
        "attractions": [
            {"name": f"Historic {destination} Monument", "lat": lat - 0.001, "lon": lon + 0.004, "address": "Heritage Zone"},
            {"name": "Scenic City Park", "lat": lat + 0.002, "lon": lon - 0.002, "address": "Green Ridge Area"}
        ]
    }

def get_destination_map_data(destination):
    """
    Gets lat, lon and categorized POIs for a destination.
    Utilizes SQL database caching.
    """
    destination_key = destination.strip().lower()
    
    # Check database cache first
    cached_poi = POI.query.filter_by(destination=destination_key).first()
    if cached_poi:
        current_app.logger.info(f"Serving POI map data from MySQL cache for: {destination}")
        return {
            "lat": cached_poi.lat,
            "lon": cached_poi.lon,
            "pois": cached_poi.poi_data
        }
        
    # Query Nominatim for coordinates
    coords = get_coordinates(destination)
    if not coords:
        # Extreme fallback to India center coordinates if geocoding fails completely
        coords = (20.5937, 78.9629) 
        
    lat, lon = coords
    
    # Query Overpass for POIs
    pois = fetch_overpass_pois(lat, lon)
    
    # If Overpass fails or returns empty categories, generate fallbacks
    if not pois or not any(pois.values()):
        current_app.logger.info("Overpass API returned empty results. Generating fallback POIs.")
        pois = generate_fallback_pois(lat, lon, destination)
        
    # Save to database cache
    try:
        new_cache = POI(
            destination=destination_key,
            lat=lat,
            lon=lon,
            poi_data=pois
        )
        db.session.add(new_cache)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to save POI data to MySQL cache: {str(e)}")
        
    return {
        "lat": lat,
        "lon": lon,
        "pois": pois
    }
