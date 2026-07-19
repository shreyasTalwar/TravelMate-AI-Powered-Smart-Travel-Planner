# TravelMate – AI Powered Smart Travel Planner

TravelMate is a premium, full-stack, AI-powered travel planning SaaS platform. The application combines itinerary generation, live weather, interactive maps, safety recommendations, emergency assistance, budgeting, and travel management into a single, cohesive interface.

## 🚀 Tech Stack

- **Frontend**: HTML5, CSS3 (Custom Variables, CSS Grids, Glassmorphism, Micro-animations), Vanilla JavaScript, Chart.js, Leaflet.js.
- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Limiter, xhtml2pdf.
- **Database**: MySQL.
- **APIs**:
  - **OpenRouter (Gemini 2.5 Flash)**: AI Itinerary generation, weather adaptations, safety assessments, and phrase translations.
  - **OpenWeather API**: Synchronized live weather forecasts.
  - **OpenStreetMap & Leaflet.js**: Geolocation mapping canvas.
  - **Nominatim & Overpass API**: Coordinate resolving and localized Points of Interest (POIs).
  - **ExchangeRate API**: Real-time foreign exchange rate caching.

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

### ✅ Phase 6: Budget Planner & Cost Tracker
- Interactive manual expense ledger allowing travelers to log costs categorized by Hotel, Food, Transport, Shopping, Activities, and Emergency Funds.
- Built-in AI cost extraction that parses the active itinerary to sum predicted budgets.
- Visual spent-breakdown doughnut charts and side-by-side estimation comparison graphs using Chart.js.
- CSV export logs for personal auditing.

### ✅ Phase 7: Women's Safety Module
- AI-graded Travel Safety Scores (1-5 scale) providing localized safety guidelines, common tourist scam warning lists, and emergency helper phone numbers.
- Emergency Speed Dial buttons for Police, Medical, Fire, and Women's Helplines.
- Pulse Panic SOS trigger counting down for 5 seconds (with audio beeps), requesting browser Geolocation coordinates, and broadcasting coordinates to emergency server logs.

### ✅ Phase 8: Offline PDF Exporter
- PDF compilation engines utilizing `xhtml2pdf` to output styled A4 printable snapshots of complete itineraries.
- "Print View" route enabling native browser printing with page-break cleanups.

### ✅ Phase 9: Live Group Chat & Sharing
- 6-character unique invitation codes generated automatically for each trip.
- Dashboard invite code inputs enabling users to join travel groups as collaborators.
- Real-time collaborative chat rooms styled with glassmorphism, supporting instant messaging synchronized via AJAX polling.

### ✅ Phase 10: Language & Currency Converter
- Live currency converters referencing public APIs (`open.er-api.com`) with 12-hour caching limits.
- Dynamic conversion banners showing overall trip budgets and expenses in foreign denominations (USD, EUR, GBP, JPY, AED, etc.).
- AI-powered travel translations converting customized phrases to destination languages, complete with phonetic pronunciation guides.

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
