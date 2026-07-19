# TravelMate – AI Powered Smart Travel Planner (Revised)

> Changes from your draft are marked **[NEW]** or **[CHANGED]**. Everything else is kept as you wrote it. See the "Summary of Changes" section at the end for why.

## 1. Product Vision

TravelMate is a full-stack AI-powered travel planning platform that enables users to plan personalized trips using artificial intelligence. The application combines itinerary generation, live weather, interactive maps, safety recommendations, emergency assistance, budgeting, and travel management into a single platform.

The application should feel like a real SaaS product rather than a college project.

**Target Audience**
Solo Travelers, Students, Backpackers, Couples, Families, Business Travelers

**Primary currency/locale [NEW]:** INR / India-first (implied by Razorpay), with room to add currency conversion later.

### Tech Stack

**Frontend:** HTML5, CSS3, Vanilla JavaScript
**Backend:** Python, Flask
**Database:** MySQL
**External APIs:** Gemini API, OpenWeather API, OpenStreetMap, Nominatim, Overpass API, Razorpay
**Deployment:** GitHub, Render

**[NEW] Supporting infra to add:**
- `.env` + `python-dotenv` for all API keys/secrets — never commit keys, never expose them to the vanilla-JS frontend. All third-party calls (Gemini, OpenWeather, Overpass) must be proxied through Flask.
- Flask-Migrate (or Alembic) for MySQL schema migrations, since 13 phases means the schema will change many times.
- Basic caching (Flask-Caching, even in-memory for MVP) in front of OpenWeather/Overpass calls — both have rate limits and you'll hit them fast during demos.
- A `requirements.txt` pin + a simple GitHub Actions workflow to lint/test on push, since you're building this "like a startup."

## PHASE 0 — Planning & Environment Setup [NEW]

**Goal:** Avoid the most common reason these builds stall — undocumented config.

- Define `.env.example` with all keys needed (Gemini, OpenWeather, Razorpay, MySQL creds, `SECRET_KEY`)
- Set up MySQL locally + a Render-hosted MySQL (or PlanetScale/managed equivalent) for deploy
- Decide on a single itinerary data shape (JSON) up front — Phase 3, 4, and 6 all read/write itinerary data, so agreeing on the schema now avoids rework later
- Add a `role` field to the eventual Users table now (`user` / `admin`) — Phase 12 needs it and retrofitting a role column later means a migration + backfill

**Deliverables:** Repo scaffolded, `.env.example` committed, local + Render MySQL both reachable.

## PHASE 1 — Project Foundation & Authentication

**Goal:** Create the application's core structure with secure user authentication and profile management.

**Features**

Landing Page: Hero section, Features section, Testimonials, Footer, Responsive design

Authentication: Register, Login, Logout, Session management, Password hashing, Input validation
**[NEW]** Forgot-password / reset flow, email verification (or at least a stub), CSRF protection (Flask-WTF), basic rate limiting on login (Flask-Limiter) to block brute force

Profile: View profile, Edit profile, Upload profile image (optional)
**[CHANGED]** Specify image storage now (local `/static/uploads` for MVP, swap for S3/Cloudinary later) — this same decision is reused in Phase 9 (travel profile) and Phase 10 (review images), so it's worth deciding once here.

**Database — Users table**
- id
- name
- email (unique, indexed)
- password_hash
- phone
- **role** ('user' / 'admin') **[NEW — needed by Phase 12]**
- **email_verified** (bool) **[NEW]**
- created_at
- updated_at

**Folder Structure** (kept as-is)
```
TravelMate/
  app.py
  config.py
  requirements.txt
  templates/
  static/
  models/
  routes/
  services/
  utils/
  instance/
```

**Deliverables:** Authentication complete, database connected, responsive UI, secure sessions, MVC-like folder structure.

## PHASE 2 — Dashboard & Trip Management

**Goal:** Users can create and manage trips.

**Dashboard:** Upcoming trips, Recent trips, Quick Actions, Weather card (placeholder), Popular destinations

**Create Trip:** Destination, Budget, Start date, End date, Number of travelers, Interests

**Database — Trips**
- id
- user_id
- destination
- budget
- start_date
- end_date
- travellers
- interests
- **status** ('draft' / 'planned' / 'completed' / 'cancelled') **[NEW — dashboard needs to distinguish "upcoming" vs "recent" somehow]**
- created_at

**[NEW]** interests: store as a normalized `trip_interests` join table (or a JSON column) rather than a free-text field — Phase 3's AI prompt and Phase 9's matching both need to query on individual interests, not parse a string.

**Features:** Create Trip, Edit Trip, Delete Trip, View Trip, Save Trip

**Deliverables:** Working CRUD.

## PHASE 3 — AI Itinerary Generator

**Goal:** Generate intelligent itineraries.

**User Input:** Destination, Budget, Days, Interests, Trip Type

**AI Prompt — Gemini generates:** Morning, Afternoon, Evening, Restaurants, Transportation, Estimated Cost, Packing List, Travel Tips, Best visiting hours, Hidden gems, Local food, Tourist traps, Rain alternatives

**[NEW]** Ask Gemini to return **structured JSON** (day → slots → activity/cost/notes), not prose — every later phase (weather adaptation, budget breakdown, map pins) needs to parse this programmatically. Validate the JSON server-side before saving; have a fallback/retry if the model returns malformed output.

**[NEW]** Add basic cost control: cap regenerations per trip per day, log token usage — Gemini calls add up fast once this is public.

**Database**
- trip_id
- ai_itinerary (store as JSON, not plain text)
- **version** **[NEW — "Regenerate itinerary" should keep history, not overwrite]**
- generated_at

**Deliverables:** Working AI planner, saved itinerary, regenerate itinerary (with history).

## PHASE 4 — Weather Intelligence

Integrate OpenWeather.

**Display:** Current Weather (Temperature, Humidity, Wind Speed, Rain Chance, UV Index), 7-Day Forecast

AI should adapt itinerary based on weather.
Example: Rain tomorrow → Move beach visit to Day 3.

**[NEW]** Cache weather responses per destination for ~30–60 min server-side — OpenWeather's free tier has strict call limits and multiple users viewing the same destination shouldn't each trigger a fresh call.

**Deliverables:** Weather Dashboard, Weather Cards, Dynamic Suggestions.

## PHASE 5 — Smart Maps

Use Leaflet.js, OpenStreetMap.

**Features:** Display destination, Nearby Hotels/Restaurants/Hospitals/Police/ATMs/Tourist Attractions, Route Navigation, Distance Calculation, Map Layers

**[NEW]** Overpass API is rate-limited and slow under load — cache POI queries per destination (e.g., in MySQL or a simple key-value table) rather than hitting Overpass on every page load.

**Deliverables:** Interactive Maps, Search, Navigation.

## PHASE 6 — Budget Planner

**Goal:** Estimate expenses.

**Categories:** Hotel, Transport, Food, Activities, Shopping, Emergency Fund

**Graphs:** Budget Breakdown, Remaining Budget, Cost Comparison

**[NEW]** Pull default cost estimates from the structured itinerary (Phase 3) rather than re-entering them — otherwise budget and itinerary data drift apart.

**Deliverables:** Budget Dashboard, Charts, Export.

## PHASE 7 — Women's Safety Module

**Features:** Safety Score, Night Travel Advice, Unsafe Areas, Emergency Contacts, Safe Hotels, Safe Transport, AI Safety Tips

**[NEW]** Flag this one explicitly: you'll need a real data source for "unsafe areas" and safety scores (open crime-data APIs are patchy for many regions). Where no reliable data source exists, be upfront in the UI that a score is an AI estimate, not verified data — presenting an ungrounded "safety score" as authoritative could do real harm to a user's trip decisions.

**Deliverables:** Safety Dashboard, Safety Alerts.

## PHASE 8 — Emergency Assistance

Show nearby: Hospitals, Police, Fire Station, Embassy, Pharmacy

**Emergency Button:** One click → Nearby help.

**[NEW]** Specify the fallback: if the browser denies geolocation permission, what happens? (e.g., manual location entry, or last known saved location.) This is the one feature where "it just doesn't work" is unacceptable.

**Deliverables:** Emergency Dashboard, Live Map.

## PHASE 9 — Travel Buddy

Users create a Travel Profile: Destination, Travel Date, Interests, Budget

**Matching:** Same destination, Same dates, Compatibility Score

Friend Request, Chat (future)

**[CHANGED]** Since chat is explicitly deferred, make sure the friend-request data model doesn't assume chat exists yet (e.g., don't build a "conversation_id" you don't use). Keep it to a simple `connections` table (requester_id, recipient_id, status) for now.

**Deliverables:** Matching System, Request System.

## PHASE 10 — Reviews

Users review Hotels, Restaurants, Tourist Places: Rating, Comments, Images

Like Reviews, Report Reviews

**[NEW]** "Report Reviews" implies moderation — this needs a queue the admin (Phase 12) can act on; add a `status` field ('visible' / 'reported' / 'removed') to reviews now so Phase 12 has something to hook into.

**Deliverables:** Review Module.

## PHASE 11 — Payment Gateway

Integrate Razorpay: Premium, Bookings, Subscriptions, Invoices, Payment History

**[NEW]** Never store raw card data — Razorpay handles that (PCI compliance is on them if integrated correctly); you only store transaction IDs/status. Use Razorpay webhooks (not just client-side callbacks) to confirm payment success server-side, since client callbacks alone can be spoofed.

**Deliverables:** Payment Module.

## PHASE 12 — Admin Panel

Admin Login (**[CHANGED]** reuse Phase 1's `role` field rather than a separate admin auth system), Dashboard, Users, Trips, Payments, Analytics, Delete Spam, Reports, System Health

**Deliverables:** Admin Dashboard.

## PHASE 13 — UI Polish

Animations, Loading Screens, Skeleton Loading, Error Pages, Dark Mode, Responsive Design, Accessibility

---

## Summary of Changes

1. **Added Phase 0** — env/secrets setup and upfront schema decisions (role field, JSON itinerary shape) that later phases depend on, so you don't retrofit migrations mid-build.
2. **Security gaps closed** — CSRF protection, login rate limiting, forgot-password flow, no client-exposed API keys, Razorpay webhook verification instead of trusting client callbacks.
3. **Data model fixes** — `role` and `email_verified` on Users; `status` on Trips and Reviews; itinerary stored as versioned JSON instead of a single overwritten text blob; interests normalized instead of free text.
4. **Rate-limit/caching notes** — added wherever an external API (OpenWeather, Overpass, Gemini) will get hit repeatedly, since free tiers cap out fast and a demo failing on an API 429 is a common failure mode.
5. **One scope flag, not a change** — 13 phases end-to-end (including payments + admin + matching) is a large build. Nothing here removes scope, but if you're time-boxed, Phases 1–6 form a complete, demoable core product on their own; 7–13 can ship as a v2.

Everything else in your original document is unchanged.
