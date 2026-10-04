HillGuard AI
Intelligent Mountain Disaster Risk & Safe Route Awareness System

Academic prototype for Shoolini University, BCA — Artificial Intelligence and Machine Learning.

HillGuard AI is a decision-support and awareness platform for mountain hazards in a Himachal Pradesh pilot. It combines a live OpenStreetMap map, community incident reports, weather observations, experimental AI indicators, clustering, and route context.

HillGuard AI does not replace government warnings, emergency services, disaster-management authorities, official weather advisories, or local authorities.

AI outputs are supporting indicators, not guaranteed disaster predictions.The system never claims that a road or location is completely safe.

Features

Interactive Leaflet map (zoom, pan, layers/tiles, markers, clusters, search, geolocation)
Community incident reporting with image upload
Moderator/admin verification (role-based JWT auth)
Weather via Open-Meteo (optional OpenWeather key) with labeled demo fallback
AI-assisted relative risk indicator (Risk Model v1.0-demo)
AI-assisted image triage (demonstration model unless you plug in a trained artifact)
DBSCAN incident clustering
Route awareness (OSRM when reachable, otherwise labeled demo geometry)
Dashboard KPIs, charts, filters
Data freshness, source badges, responsible-AI and emergency pages
Demo mode with seeded Himachal Pradesh reports

Architecture

frontend/   React + TypeScript + Vite + Leaflet
backend/    FastAPI REST API
database/   PostGIS schema (optional Docker Postgres)
ml/         Adapters so a trained model can replace demo inference
seed/       Created on first backend start (empty DB)

Default local database is SQLite so the viva works without installing PostGIS. Use PostgreSQL + PostGIS for spatial production-style queries (database/schema.sql + docker-compose.yml).

Tech stack

Layer



Choice





UI



React 18, React Router, Recharts, Lucide





Map



Leaflet, OSM-compatible Carto tiles





API



FastAPI, Pydantic, JWT, bcrypt





DB



SQLite (demo) or PostgreSQL + PostGIS





ML



scikit-learn DBSCAN + heuristic/demo image triage





Weather



Open-Meteo (no key) or OpenWeatherMap





Quick start (Windows)



1. Environment

cd C:\Users\krish\HillGuard-AI
copy .env.example .env

Edit .env if needed. JWT_SECRET must be changed before any real deployment.

2. Backend

cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

API: http://127.0.0.1:8000/docs

3. Frontend

cd frontend
npm install
npm run dev

App: http://localhost:5173

Vite proxies /api and /uploads to the backend.





Demo accounts







Role



Email



Password





Admin



admin@hillguard.local



HillGuardAdmin123!





Moderator



moderator@hillguard.local



HillGuardMod123!





User



user@hillguard.local



HillGuardUser123!

A DEMO MODE banner appears when DEMO_MODE=true. Seeded incidents are sample community data, not live government feeds.





Environment variables

See .env.example:





DATABASE_URL — SQLite file or postgresql+psycopg://hillguard:hillguard@localhost:5432/hillguard



WEATHER_API_KEY — optional OpenWeather key; leave empty to use Open-Meteo



MAP_TILE_URL — OSM-compatible tile template



ROUTING_API_KEY / OSRM_URL — routing; public OSRM is tried, then demo fallback



JWT_SECRET



Official links: IMD, NDMA, Himachal SDMA (do not invent additional authorities)





PostgreSQL + PostGIS

docker compose up -d

Set DATABASE_URL=postgresql+psycopg://hillguard:hillguard@localhost:5432/hillguard then apply database/schema.sql (or let SQLAlchemy create tables; PostGIS geometry is documented in schema.sql for spatial indexes).





Adding a weather API





Put an OpenWeather key in WEATHER_API_KEY



Set WEATHER_PROVIDER=openweather



Restart the backend

Keys stay on the server only.





Adding a routing API

Point OSRM_URL at your own OSRM instance. backend/app/routing.py already isolates the provider. If the request fails, the API returns a labeled demo straight-line approximation.





Replacing the demo AI model





Train a classifier and save it under ml/



Implement predict in ml/adapter.py with the same response keys as triage_image in backend/app/ml_service.py



Call that adapter from triage_image / analyze_risk



Keep disclaimers: no “confirmed hazard”, no uncalibrated probabilities as official odds





API overview







Method



Path



Notes





POST



/api/auth/register /api/auth/login



JWT





GET



/api/incidents



Filters: category, status, source, risk, location, hours, page





GET



/api/incidents/nearby



lat, lng, km





GET



/api/incidents/{id}









POST



/api/incidents



multipart form + optional image





GET



/api/weather









POST



/api/ai/risk









POST



/api/ai/image-analysis



info; analysis runs on incident upload





GET



/api/clusters









GET



/api/analytics









GET/POST



/api/routes /api/routes/analyze









GET



/api/admin/reports



MODERATOR/ADMIN





PATCH



/api/admin/reports/{id}/status



updates public map status





GET



/api/sources /api/notifications /api/health









Tests

cd backend
.\.venv\Scripts\activate
pytest -q

Covers auth, incident create/filter/retrieve, nearby search, admin verification, image rejection, risk, clusters, route analysis.





Deployment (academic)





Set a strong JWT_SECRET, DEMO_MODE=false if you have live providers



Serve FastAPI behind HTTPS (uvicorn/gunicorn + reverse proxy)



Build frontend: npm run build and host frontend/dist or keep Vite preview for demo



Use Postgres+PostGIS for class servers



Restrict CORS FRONTEND_ORIGIN



Never put API keys in the React bundle





Known limitations





Image triage and risk scores are demonstration / uncalibrated



Public OSRM and Nominatim are best-effort and rate-limited



SQLite has no PostGIS geometry type; nearby search uses haversine



Community reports can be wrong until verified



Absence of reports is not evidence of safe conditions





Emergency information

Use official sources linked in the app (IMD, NDMA, Himachal SDMA). HillGuard AI does not dispatch emergency response.