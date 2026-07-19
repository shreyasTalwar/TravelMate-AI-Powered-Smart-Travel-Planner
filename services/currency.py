import time
import requests

# In-memory exchange rate cache
# Format: { "base_currency": { "timestamp": float, "rates": { "USD": 0.012, ... } } }
_rate_cache = {}
CACHE_DURATION_SECONDS = 12 * 3600  # Cache rates for 12 hours

SUPPORTED_CURRENCIES = [
    'INR', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'AED', 'SGD', 'SAR'
]

def get_exchange_rates(base="INR"):
    """
    Fetches exchange rates from a public key-free endpoint.
    Uses caching to limit network calls.
    """
    base = base.upper().strip()
    now = time.time()
    
    # Check cache
    if base in _rate_cache:
        cached = _rate_cache[base]
        if now - cached['timestamp'] < CACHE_DURATION_SECONDS:
            return cached['rates']
            
    try:
        url = f"https://open.er-api.com/v6/latest/{base}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("result") == "success":
                rates = data.get("rates", {})
                # Filter down to supported currencies to keep payloads small
                filtered_rates = {cur: float(rates[cur]) for cur in SUPPORTED_CURRENCIES if cur in rates}
                
                # Cache results
                _rate_cache[base] = {
                    'timestamp': now,
                    'rates': filtered_rates
                }
                return filtered_rates
    except Exception as e:
        # Fallback to hardcoded mock rates if offline
        print(f"Currency exchange API error: {str(e)}")
        
    # Standard static fallbacks if API fails
    fallbacks = {
        "INR": {"INR": 1.0, "USD": 0.012, "EUR": 0.011, "GBP": 0.009, "JPY": 1.8, "AUD": 0.018, "CAD": 0.016, "CHF": 0.010, "CNY": 0.086, "AED": 0.044, "SGD": 0.016, "SAR": 0.045},
        "USD": {"INR": 83.3, "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 150.0, "AUD": 1.5, "CAD": 1.35, "CHF": 0.88, "CNY": 7.2, "AED": 3.67, "SGD": 1.34, "SAR": 3.75}
    }
    return fallbacks.get(base, fallbacks["INR"])

def convert_amount(amount, from_cur="INR", to_cur="USD"):
    """Converts a specific amount from one currency to another."""
    from_cur = from_cur.upper().strip()
    to_cur = to_cur.upper().strip()
    
    if from_cur == to_cur:
        return float(amount)
        
    rates = get_exchange_rates(from_cur)
    if to_cur in rates:
        return float(amount) * rates[to_cur]
        
    # If starting currency is not supported, cross-convert via INR fallback
    inr_rates = get_exchange_rates("INR")
    if from_cur in inr_rates and to_cur in inr_rates:
        amount_in_inr = float(amount) / inr_rates[from_cur]
        return amount_in_inr * inr_rates[to_cur]
        
    return float(amount)
