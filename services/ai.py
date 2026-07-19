import os
import json
import requests
from flask import current_app

def generate_itinerary_data(trip_data):
    """
    Communicates with OpenRouter API to generate a structured JSON itinerary.
    trip_data is a dictionary containing:
      - destination
      - budget (INR)
      - start_date
      - end_date
      - travellers
      - interests (list)
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    
    if not api_key:
        raise ValueError("OpenRouter API key is missing. Set OPENROUTER_API_KEY in your env.")
        
    duration_days = (trip_data['end_date'] - trip_data['start_date']).days + 1
    
    # Constructing a detailed prompt instructing structured JSON output
    prompt = f"""
    You are an expert travel planner. Generate a highly detailed, personalized travel itinerary for a trip to {trip_data['destination']}.
    
    Trip Details:
    - Destination: {trip_data['destination']}
    - Duration: {duration_days} Days (from {trip_data['start_date']} to {trip_data['end_date']})
    - Budget: {trip_data['budget']} INR
    - Number of Travelers: {trip_data['travellers']}
    - Interests: {', '.join(trip_data['interests']) if trip_data['interests'] else 'General sightseeing'}
    
    You MUST respond with a valid, clean JSON object ONLY. Do not write any preamble, explanation, or markdown code blocks (like ```json).
    The JSON structure MUST follow this exact schema:
    {{
      "days": [
        {{
          "day_number": 1,
          "date": "YYYY-MM-DD",
          "slots": {{
            "morning": {{
              "activity": "Specific name of place or activity",
              "description": "Engaging description of what to see and do there",
              "cost": 0.0
            }},
            "afternoon": {{
              "activity": "Specific name of place or activity",
              "description": "Engaging description of what to see and do there",
              "cost": 0.0
            }},
            "evening": {{
              "activity": "Specific name of place or activity",
              "description": "Engaging description of what to see and do there",
              "cost": 0.0
            }}
          }},
          "restaurants": [
            {{
              "name": "Name of highly-rated local restaurant",
              "cuisine": "Cuisine type",
              "recommended_dishes": ["Dish Name 1", "Dish Name 2"],
              "estimated_cost_per_person": 0.0
            }}
          ],
          "transportation": {{
            "mode": "Recommended local transport mode (e.g. Cab, Metro, Auto-rickshaw)",
            "details": "Advice on routes or how to pay",
            "cost": 0.0
          }}
        }}
      ],
      "packing_list": ["Item 1", "Item 2", "Item 3"],
      "travel_tips": ["General safety or culture tip 1", "Tip 2"],
      "best_visiting_hours": "Overview of when to explore main spots for best experience",
      "hidden_gems": [
        {{
          "name": "Name of offbeat spot",
          "description": "Why it is unique and how to get there",
          "location": "Area name"
        }}
      ],
      "local_food": [
        {{
          "name": "Must-try street food or dish name",
          "description": "What it is and where to find it"
        }}
      ],
      "tourist_traps": [
        {{
          "name": "Overrated place or common scam",
          "warning": "How to avoid or what to watch out for"
        }}
      ],
      "rain_alternatives": [
        {{
          "activity": "Indoor activity (museum, cafe, gallery, indoor arcade)",
          "description": "Engaging description of the alternative indoor option"
        }}
      ]
    }}
    
    Provide activities tailored to their interests: {trip_data['interests']}. Ensure all estimated costs are in INR and fit within the total budget of {trip_data['budget']} INR. Ensure the 'days' array contains exactly {duration_days} days.
    """
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/travelmate",
        "X-Title": "TravelMate AI Planner"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a professional travel agency API that outputs strictly raw JSON itineraries according to user specs. Do not output markdown, HTML, or conversational text. Output pure valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 3000
    }
    
    # Implement retry mechanism
    retries = 2
    for attempt in range(retries + 1):
        try:
            current_app.logger.info(f"Sending request to OpenRouter (Attempt {attempt+1}/{retries+1})...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                res_json = response.json()
                content = res_json['choices'][0]['message']['content'].strip()
                
                # Check for and clean markdown code fences if LLM ignored response_format
                if content.startswith("```"):
                    lines = content.split("\n")
                    if lines[0].startswith("```json") or lines[0].startswith("```"):
                        lines = lines[1:-1]
                    content = "\n".join(lines).strip()
                
                # Try parsing to validate it is a true JSON object
                parsed_data = json.loads(content)
                return parsed_data
            else:
                current_app.logger.error(f"OpenRouter returned status {response.status_code}: {response.text}")
                if attempt == retries:
                    raise Exception(f"OpenRouter Error {response.status_code}: {response.text}")
                    
        except json.JSONDecodeError as jde:
            current_app.logger.error(f"JSON Parsing Error on attempt {attempt+1}: {str(jde)}")
            if attempt == retries:
                raise Exception("AI generated malformed JSON. Please try again.")
        except Exception as e:
            current_app.logger.error(f"API Request Exception on attempt {attempt+1}: {str(e)}")
            if attempt == retries:
                raise e
                
    raise Exception("Failed to generate itinerary.")

def adapt_itinerary_for_weather(trip_data, current_itinerary_json, weather_forecast_json):
    """
    Prompts OpenRouter to adapt the current itinerary based on the weather forecast.
    Moves outdoor activities to indoor/alternative slots on days where rain is forecasted.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    
    if not api_key:
        raise ValueError("OpenRouter API key is missing. Set OPENROUTER_API_KEY in your env.")
        
    prompt = f"""
    You are an expert travel coordinator. Adapt the current travel itinerary for a trip to {trip_data['destination']} based on the local weather forecast.
    
    Current Itinerary (JSON):
    {json.dumps(current_itinerary_json, indent=2)}
    
    Local Weather Forecast:
    {json.dumps(weather_forecast_json, indent=2)}
    
    Task:
    1. Inspect the weather forecast. If there are days with a high chance of rain (e.g., above 50% or descriptive storms/showers), rearrange the schedule to move outdoor activities (like beach visits, open-air walking tours, hiking) to days that are clear, or replace them with indoor alternatives (such as museums, indoor galleries, covered shopping, cafes) from either other days or the 'rain_alternatives' list.
    2. Try to swap activities between days where possible so no activities are completely lost, or substitute them with comparable indoor items.
    3. Ensure the structure of the JSON remains EXACTLY the same as the original. DO NOT change the format, keys, or types.
    4. Provide the output in clean, raw JSON ONLY. Do not write any markdown blocks (```json) or conversational text.
    """
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/travelmate",
        "X-Title": "TravelMate AI Weather Adaptor"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a professional travel agency API that outputs strictly raw JSON itineraries adjusted for local weather. Do not output markdown, HTML, or conversational text. Output pure valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 3000
    }
    
    retries = 2
    for attempt in range(retries + 1):
        try:
            current_app.logger.info(f"Sending weather adaptation request to OpenRouter (Attempt {attempt+1}/{retries+1})...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                res_json = response.json()
                content = res_json['choices'][0]['message']['content'].strip()
                
                if content.startswith("```"):
                    lines = content.split("\n")
                    if lines[0].startswith("```json") or lines[0].startswith("```"):
                        lines = lines[1:-1]
                    content = "\n".join(lines).strip()
                
                parsed_data = json.loads(content)
                return parsed_data
            else:
                current_app.logger.error(f"OpenRouter returned status {response.status_code}: {response.text}")
                if attempt == retries:
                    raise Exception(f"OpenRouter Error {response.status_code}: {response.text}")
                    
        except json.JSONDecodeError as jde:
            current_app.logger.error(f"JSON Parsing Error on attempt {attempt+1}: {str(jde)}")
            if attempt == retries:
                raise Exception("AI generated malformed JSON. Please try again.")
        except Exception as e:
            current_app.logger.error(f"API Request Exception on attempt {attempt+1}: {str(e)}")
            if attempt == retries:
                raise e
                
    raise Exception("Failed to adapt itinerary.")

def generate_safety_assessment(destination):
    """
    Communicates with OpenRouter API to generate a safety assessment for a destination.
    Returns:
      - safety_score: Integer (1-5)
      - safety_data: Dictionary
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    
    if not api_key:
        raise ValueError("OpenRouter API key is missing. Set OPENROUTER_API_KEY in your env.")
        
    prompt = f"""
    Perform a comprehensive safety assessment for travelers visiting {destination}, with a special focus on women solo travelers.
    
    You MUST respond with a valid, clean JSON object ONLY. Do not write any preamble, explanation, or markdown code blocks (like ```json).
    The JSON structure MUST follow this exact schema:
    {{
      "safety_score": 4, // Integer from 1 to 5 (1 = Dangerous, 5 = Extremely Safe)
      "emergency_contacts": {{
        "police": "100 or specific local number",
        "medical": "102 or specific local number",
        "fire": "101 or specific local number",
        "women_helpline": "1091 or specific helpline"
      }},
      "neighborhoods": {{
        "safe_zones": [
          {{"name": "Area Name 1", "reason": "Well-lit, highly patrolled, tourist-friendly"}},
          {{"name": "Area Name 2", "reason": "Residential, safe and friendly vibe"}}
        ],
        "caution_zones": [
          {{"name": "Area Name 3", "reason": "Poorly lit at night, pickpocketing hot spot"}},
          {{"name": "Area Name 4", "reason": "Isolated industrial area, skip after dark"}}
        ]
      }},
      "solo_travel_advice": [
        "Solo advice item 1",
        "Solo advice item 2"
      ],
      "transit_safety": [
        "Transport warning/advice 1",
        "Transport warning/advice 2"
      ],
      "cultural_guidelines": [
        "Dress code or cultural norm advice 1",
        "Norm advice 2"
      ],
      "common_scams": [
        {{"name": "Scam Name 1", "warning": "How the scam works and how to avoid it"}},
        {{"name": "Scam Name 2", "warning": "Details on avoiding this taxi/vendor trick"}}
      ]
    }}
    """
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.3
    }
    
    retries = 2
    for attempt in range(retries + 1):
        try:
            current_app.logger.info(f"Sending safety assessment request for {destination} to OpenRouter (Attempt {attempt+1}/{retries+1})...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                res_json = response.json()
                content = res_json['choices'][0]['message']['content'].strip()
                
                if content.startswith("```"):
                    lines = content.split("\n")
                    if lines[0].startswith("```json") or lines[0].startswith("```"):
                        lines = lines[1:-1]
                    content = "\n".join(lines).strip()
                
                parsed_data = json.loads(content)
                
                score = parsed_data.get('safety_score', 4)
                try:
                    score = max(1, min(5, int(score)))
                except:
                    score = 4
                    
                return score, parsed_data
            else:
                current_app.logger.error(f"OpenRouter Safety Error: status {response.status_code}: {response.text}")
                if attempt == retries:
                    raise Exception(f"OpenRouter Error {response.status_code}: {response.text}")
        except json.JSONDecodeError as jde:
            current_app.logger.error(f"Safety JSON Parsing Error on attempt {attempt+1}: {str(jde)}")
            if attempt == retries:
                raise Exception("AI generated malformed safety JSON.")
        except Exception as e:
            current_app.logger.error(f"Safety API Request Exception on attempt {attempt+1}: {str(e)}")
            if attempt == retries:
                raise e
                
    fallback_data = {
        "safety_score": 4,
        "emergency_contacts": {
            "police": "112 / 100",
            "medical": "102 / 108",
            "fire": "101",
            "women_helpline": "1091"
        },
        "neighborhoods": {
            "safe_zones": [{"name": "Tourist Center & City Square", "reason": "High surveillance, well-patrolled, well-lit"}],
            "caution_zones": [{"name": "Outer Suburb Transit hubs", "reason": "Crowded, prone to petty thefts and pickpocketing"}]
        },
        "solo_travel_advice": ["Keep emergency contacts on speed dial.", "Share your live location with trusted family members."],
        "transit_safety": ["Prefer pre-booked official cabs or public transport in crowded areas."],
        "cultural_guidelines": ["Respect local dress guidelines when entering historical or religious spots."],
        "common_scams": [{"name": "Overpriced unofficial taxis", "warning": "Always ask for taxi meters or use ride-hailing apps."}]
    }
    return 4, fallback_data

def translate_phrase(text, target_language):
    """
    Translates text to the target language and provides a phonetic pronunciation guide.
    Returns: {"translation": "...", "pronunciation": "..."}
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    
    if not api_key:
        return {"translation": text, "pronunciation": "N/A"}
        
    prompt = f"""
    Translate the following English travel phrase to {target_language}.
    Provide the translation AND a simple, phonetic English-based pronunciation guide in parentheses for a tourist.
    
    Phrase: "{text}"
    
    Respond in JSON format ONLY:
    {{
      "translation": "translated text here",
      "pronunciation": "phonetic guide here (e.g. bohn-zhoor)"
    }}
    """
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            },
            timeout=10
        )
        if response.status_code == 200:
            res_json = response.json()
            content = res_json['choices'][0]['message']['content'].strip()
            data = json.loads(content)
            return {
                "translation": data.get("translation", ""),
                "pronunciation": data.get("pronunciation", "")
            }
    except Exception as e:
        print(f"AI Translation Exception: {str(e)}")
        
    return {"translation": f"[Error translating to {target_language}]", "pronunciation": ""}

def get_essential_phrases(destination, target_language):
    """
    Generates 5 essential travel phrases in the local language for a given destination.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    
    if not api_key:
        # Default fallback phrases
        return [
            {"english": "Hello", "translation": "Hola", "pronunciation": "oh-lah"},
            {"english": "Thank you", "translation": "Gracias", "pronunciation": "grah-syahs"},
            {"english": "Please", "translation": "Por favor", "pronunciation": "por fah-vor"},
            {"english": "Where is the bathroom?", "translation": "¿Dónde está el baño?", "pronunciation": "dohn-deh es-tah el bah-nyoh"},
            {"english": "Help", "translation": "Ayuda", "pronunciation": "ah-yoo-dah"}
        ]
        
    prompt = f"""
    Generate 5 essential travel phrases for a tourist visiting {destination} who needs to speak in {target_language}.
    Each phrase should have the English phrase, the localized translation, and a phonetic pronunciation guide.
    
    Respond in JSON format ONLY:
    {{
      "phrases": [
        {{
          "english": "Hello / Good morning",
          "translation": "local translation",
          "pronunciation": "phonetic guide (e.g. bohn-zhoor)"
        }},
        ...
      ]
    }}
    """
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            },
            timeout=10
        )
        if response.status_code == 200:
            res_json = response.json()
            content = res_json['choices'][0]['message']['content'].strip()
            data = json.loads(content)
            return data.get("phrases", [])
    except Exception as e:
        print(f"AI Essential Phrases Exception: {str(e)}")
        
    return [
        {"english": "Hello", "translation": "Hola", "pronunciation": "oh-lah"},
        {"english": "Thank you", "translation": "Gracias", "pronunciation": "grah-syahs"},
        {"english": "Please", "translation": "Por favor", "pronunciation": "por fah-vor"},
        {"english": "Where is the bathroom?", "translation": "¿Dónde está el baño?", "pronunciation": "dohn-deh es-tah el bah-nyoh"},
        {"english": "Help", "translation": "Ayuda", "pronunciation": "ah-yoo-dah"}
    ]
