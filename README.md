# TravelMate – AI Powered Smart Travel Planner

TravelMate is a premium, full-stack, AI-powered travel planning SaaS platform. The application combines itinerary generation, live weather, interactive maps, safety recommendations, emergency assistance, budgeting, and travel management into a single, cohesive interface.

## 🚀 Tech Stack

- **Frontend**: HTML5, CSS3 (Custom Variables, CSS Grids, Glassmorphism, Micro-animations), Vanilla JavaScript.
- **Backend**: Python, Flask.
- **Database**: MySQL (configured with Flask-SQLAlchemy and Flask-Migrate).
- **APIs**:
  - **OpenRouter (Gemini 2.5 Flash)**: AI Itinerary & weather adaptation.
  - **OpenWeather API**: Synchronized live weather forecasts.
  - **OpenStreetMap & Leaflet.js**: Geolocation mapping canvas.
  - **Nominatim & Overpass API**: Coordinate resolving and localized Points of Interest (POIs).

---

## 📅 Development Roadmap & Status

### ✅ Phase 0: Environment Setup
- Initialized python packages, database configurations, and secure `.env` loaders.
- Configured local database connection pipelines.

### ✅ Phase 1: Foundation & Authentication
- Secure registration and login modules protected by `Flask-WTF` CSRF and rate-limited via `Flask-Limiter`.
- Hashed passwords using `bcrypt`.
- Custom user profile editing and local storage upload stub.
- Custom styled error pages (404, 500, 429).

### ✅ Phase 2: Dashboard & Trip Management CRUD
- Dynamic traveler dashboard tracking planned budget aggregates and total trips.
- Differentiated listings for **Upcoming Adventures** vs **Past Journeys**.
- Trip creator form verifying sequential dates and parsing travel interests checklist.

### ✅ Phase 3: AI Itinerary Generator
- Connected to OpenRouter to query Gemini.
- Formulated instruction sets producing structured JSON itineraries containing day slots, restaurant guides, transit advice, hidden gems, and rain alternatives.
- Implemented database itinerary versioning snapshots so users can view and toggle between generations.

### ✅ Phase 4: Weather Intelligence
- Geocoded locations and fetched daily forecasts from OpenWeather.
- Configured 30-minute in-memory caching to respect API limits.
- Built AI-driven itinerary adaptation rearranger adjusting plans based on rain forecasts.

### ✅ Phase 5: Smart Maps
- Embedded Leaflet.js maps centering on destinations.
- Queried Overpass API to fetch nearby Hotels, Restaurants, Attractions, Hospitals, Police stations, and ATMs.
- Structured filter switches allowing users to toggle marker categories on the map in real-time.
- Cached map POI results in MySQL database.

---

## 🛠️ Local Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/shreyasTalwar/TravelMate-AI-Powered-Smart-Travel-Planner.git
   cd TravelMate-AI-Powered-Smart-Travel-Planner
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment variables**:
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_secret_key
   DATABASE_URL=mysql+pymysql://username:password@localhost:3306/travelmate
   OPENROUTER_API_KEY=your_openrouter_api_key
   OPENROUTER_MODEL=google/gemini-2.5-flash
   OPENWEATHER_API_KEY=your_openweather_api_key
   ```

4. **Verify Database Setup**:
   Creates the `travelmate` database and SQLAlchemy tables automatically:
   ```bash
   python verify_db.py
   ```

5. **Start Flask Server**:
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.
