<div align="center">

# 🌍 TravelMate
### AI-Powered Smart Travel Planner

A premium, full-stack SaaS platform that brings itinerary generation, live weather, interactive maps, safety intelligence, budgeting, and collaborative trip planning together in one cohesive interface.

[![Python](https://img.shields.io/badge/Python-3.x-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Backend-black)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-Database-orange)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)

</div>

---

## 📖 Overview

TravelMate turns raw trip ideas into fully structured, AI-generated itineraries — then keeps them useful on the road with live weather rerouting, offline PDF exports, safety tooling, and real-time trip collaboration.

## ✨ Features

| Category | Highlights |
|---|---|
| 🔐 **Auth & Accounts** | CSRF-protected registration/login, bcrypt password hashing, rate-limited endpoints, editable profiles |
| 🗺️ **AI Itineraries** | Gemini-generated day-by-day plans with restaurants, transit tips, hidden gems, and rain alternatives — with version history |
| 🌦️ **Weather Intelligence** | Live OpenWeather forecasts with AI-driven itinerary adaptation when rain is forecast |
| 📍 **Smart Maps** | Leaflet.js maps with toggleable POI layers (hotels, restaurants, attractions, hospitals, police, ATMs) via Overpass API |
| 💰 **Budget Planner** | Manual expense ledger, AI-extracted predicted costs, Chart.js visual breakdowns, CSV export |
| 🚨 **Safety Module** | AI safety scores, scam warnings, emergency helplines, and a Panic SOS button that shares live geolocation |
| 📄 **Offline Access** | One-click PDF export and print-friendly itinerary views |
| 👥 **Group Travel** | Shareable invite codes and real-time collaborative trip chat |
| 💱 **Currency & Language** | Live currency conversion and AI-powered phrase translation with phonetic guides |

## 🧱 Tech Stack

**Frontend** — HTML5, CSS3 (custom properties, grid, glassmorphism, micro-animations), Vanilla JavaScript, Chart.js, Leaflet.js

**Backend** — Python, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Limiter, xhtml2pdf

**Database** — MySQL

**External APIs**
- OpenRouter (Gemini 2.5 Flash) — itinerary generation, weather adaptation, safety scoring, translation
- OpenWeather — live forecasts
- OpenStreetMap + Leaflet.js — mapping
- Nominatim & Overpass — geocoding and points of interest
- ExchangeRate API — live currency conversion

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- MySQL server running locally or remotely
- API keys for OpenRouter and OpenWeather

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/shreyasTalwar/TravelMate-AI-Powered-Smart-Travel-Planner.git
cd TravelMate-AI-Powered-Smart-Travel-Planner

# 2. Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your_secret_key
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/travelmate
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=google/gemini-2.5-flash
OPENWEATHER_API_KEY=your_openweather_api_key
```

### Run

```bash
# Create the database and tables
python verify_db.py

# Start the server
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## 🗺️ Development Roadmap

<details>
<summary><b>Click to expand full phase-by-phase build history</b></summary>

| Phase | Focus | Status |
|---|---|---|
| 0 | Environment setup, DB config, secure `.env` loading | ✅ |
| 1 | Auth & foundation — CSRF, rate limiting, bcrypt, custom error pages | ✅ |
| 2 | Dashboard & trip CRUD — budget aggregates, upcoming/past trips | ✅ |
| 3 | AI itinerary generator — Gemini integration, versioned snapshots | ✅ |
| 4 | Weather intelligence — geocoding, caching, rain-adaptive replanning | ✅ |
| 5 | Smart maps — Leaflet + Overpass POIs with real-time filters | ✅ |
| 6 | Budget planner — expense ledger, AI cost extraction, Chart.js views | ✅ |
| 7 | Women's safety module — safety scores, helplines, Panic SOS | ✅ |
| 8 | Offline PDF exporter — styled A4 export, print view | ✅ |
| 9 | Live group chat & sharing — invite codes, AJAX-polled chat | ✅ |
| 10 | Language & currency converter — live rates, AI phrase translation | ✅ |

</details>

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙋 Author

**Shreyas Talwar**
GitHub: [@shreyasTalwar](https://github.com/shreyasTalwar)
