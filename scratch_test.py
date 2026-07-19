import os
import requests
from dotenv import load_dotenv

# Load environmental variables
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")

print("--- Testing OpenRouter Integration ---")
print(f"Using Model: {model}")
print(f"API Key Prefix: {api_key[:12]}... (total length {len(api_key)})" if api_key else "No API Key found!")

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/travelmate", # Optional, for OpenRouter analytics
    "X-Title": "TravelMate"
}

payload = {
    "model": model,
    "messages": [
        {"role": "user", "content": "Hello, respond with a short message: 'OpenRouter connection successful!'"}
    ],
    "max_tokens": 100
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"HTTP Status Code: {response.status_code}")
    if response.status_code == 200:
        res_data = response.json()
        print("\nSuccess! OpenRouter Output:")
        print(res_data['choices'][0]['message']['content'])
    else:
        print(f"\nFailed to connect. Error detail:")
        print(response.text)
except Exception as e:
    print(f"\nConnection Error: {str(e)}")
