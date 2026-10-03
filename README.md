# PocketSmart AI: Your Smart Budget & Recommendation Assistant

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Google Gemini Flash](https://img.shields.io/badge/Google%20GenAI-Gemini%20Flash-orange.svg)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**PocketSmart AI** is a GenAI-powered cross-platform budget and lifestyle recommendation assistant. It bridges user budgets, aesthetic preferences, contextual requirements, and optional outfit images with multi-platform product and service catalogs.

The platform provides intelligent budget allocation and personalized recommendations across three lifestyle planning domains:
1. 🛋️ **Home Interior Budget Planner** (Living room, bedrooms, lighting fixtures, ceiling fans, dining tables, furniture, decor, and design styles via **IKEA, Amazon, Flipkart**).
2. 🎉 **Party Budget Planner** (Event budgeting for birthdays, weddings, anniversaries, corporate events with per-guest catering, venue halls, DJ sound, cake, and decor via **Swiggy, Zomato, OYO, MakeMyTrip, Amazon**).
3. 💎 **Jewelry & Styling Planner** (Multimodal visual outfit analysis + budget styling for weddings, receptions, festivals, and evening parties via **CaratLane, Myntra, Amazon, Flipkart**).

---

## 🌟 Key Features

- **Multimodal Visual Outfit Styling**: Upload dress/outfit photos (JPG, PNG, WEBP) to extract color palettes, formality, necklines, and receive style-coordinated jewelry.
- **Deterministic Python Budget Engine**: Gemini is never solely trusted for mathematical financial calculations. Python strictly validates and deterministically rebalances prices and quantities to ensure `total_estimated_cost <= user_budget`.
- **Multi-Platform Search Provider Architecture**: Clean abstraction generating valid, URL-encoded search links across Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, CaratLane, and Myntra.
- **Full Authentication & Session Tracking**: Secure registration, bcrypt password hashing, JWT tokens, HTTP-only session cookies, and user dashboards.
- **Recommendation History**: SQLite database persistence allowing users to view, print, or delete previous planning sessions.
- **Smart Fallback Engine**: If no Gemini API key is configured or network is offline, the application seamlessly operates in intelligent fallback heuristic mode without crashing.
- **Modern Responsive Glassmorphic UI**: Custom CSS with dark aesthetic, micro-animations, loading feedback overlays, and mobile responsiveness.

---

## 🏗️ Architecture & Technology Stack

```
PocketSmart-AI/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application setup & lifecycle
│   ├── config.py                   # Pydantic Settings & environment variables
│   ├── database.py                 # SQLAlchemy engine & SQLite session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                 # User ORM model
│   │   ├── recommendation.py       # RecommendationRecord ORM model
│   │   └── schemas.py              # Pydantic validation & input/output schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py                 # Login, Register, Logout, Token, Session API
│   │   ├── dashboard.py            # User Dashboard
│   │   ├── home_planner.py         # Home Interior Budget Planner
│   │   ├── party_planner.py        # Party Budget Planner
│   │   ├── jewelry_planner.py      # Jewelry Planner (with multimodal uploads)
│   │   └── history.py              # Saved Recommendation History
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gemini_service.py       # Centralized Gemini GenAI service
│   │   ├── recommendation_service.py# Master plan orchestrator
│   │   ├── budget_service.py       # Deterministic Python financial engine
│   │   ├── product_provider.py     # Search provider link routing
│   │   └── image_service.py        # Upload verification & Pillow processing
│   └── utils/
│       ├── __init__.py
│       ├── security.py             # Bcrypt hashing & JWT utilities
│       ├── validators.py           # Email & password validation
│       └── helpers.py              # Currency formatting & helpers
├── templates/
│   ├── base.html                   # Base layout with navigation & footer
│   ├── index.html                  # Landing page & feature presentation
│   ├── login.html                  # User sign in
│   ├── register.html               # User registration
│   ├── dashboard.html              # User dashboard & statistics
│   ├── home_planner.html           # Home interior input form
│   ├── party_planner.html          # Party & event input form
│   ├── jewelry_planner.html        # Jewelry & outfit upload form
│   ├── recommendation_result.html  # Comprehensive plan result view
│   ├── history.html                # Saved plans history
│   └── error.html                  # Friendly error page
├── static/
│   ├── css/
│   │   └── style.css               # Design system & stylesheet
│   ├── js/
│   │   └── app.js                  # Frontend client interactions & dropzone
│   ├── images/
│   └── uploads/                    # Local storage for uploaded outfit images
├── tests/
│   ├── test_auth.py                # Auth & registration tests
│   ├── test_budget.py              # Budget engine & rebalancing tests
│   ├── test_home.py                # Home planner tests
│   ├── test_party.py               # Party planner tests
│   └── test_jewelry.py             # Jewelry & image validation tests
├── .env.example
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── run.py                          # Simple application startup script
```

### Core Technologies:
- **Backend**: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic 2.0
- **AI**: Official Google GenAI SDK (`google-genai` / `google.genai` Client) supporting configurable Flash models (e.g., `gemini-2.5-flash`, `gemini-2.0-flash`)
- **Frontend**: HTML5, Vanilla CSS3 (Custom Glassmorphic Design System), Vanilla JavaScript, Jinja2 Templates
- **Image Processing**: Pillow (PIL)
- **Database**: SQLite
- **Security**: Bcrypt password hashing, PyJWT, HTTP-only secure cookies

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10 or 3.11 installed.

### 2. Clone / Open Directory
```bash
cd "d:\naan mudhalvan project"
```

### 3. Create & Activate Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Setup
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and optionally set your Google Gemini API key:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
SECRET_KEY=pocketsmart_secret_key_change_in_production
DATABASE_URL=sqlite:///./pocketsmart.db
```
*(Note: If `GEMINI_API_KEY` is not supplied, the app automatically runs in Smart Heuristic Fallback mode so all features work reliably without crashing).*

### 6. Run the Application
```bash
python run.py
```
Or with Uvicorn directly:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The application will be accessible locally at:
👉 **`http://127.0.0.1:8000`**

---

## 🧪 Automated Testing

To run the complete automated test suite:
```bash
pytest -v
```

Test coverage includes:
- Registration, login, duplicate validation, and token issuance (`test_auth.py`).
- Deterministic budget validation, overflow rebalancing, and arithmetic precision (`test_budget.py`).
- Home interior planner end-to-end flow and fixture allocations (`test_home.py`).
- Party planner event types, per-guest food allocations, and vendor routing (`test_party.py`).
- Jewelry planner with and without outfit image upload (`test_jewelry.py`).
- Image upload format, size, and MIME validation.

---

## 📖 Module Descriptions

### 1. Home Interior Planner (`/home-planner`)
- **Inputs**: Budget, Currency, Living Room, Bedroom Count, Kitchen, Dining Room, Number of Lights, Fans, Dining Tables, Style (Modern, Scandinavian, Traditional, Minimalist, Industrial, Bohemian), Color Preferences, Furniture & Decor requirements.
- **Outputs**: Balanced recommendation items, estimated unit prices, quantities, subtotals, category breakdown (Furniture, Lighting, Fans, Dining, Decor), and direct shopping search links on IKEA, Amazon, and Flipkart.

### 2. Party Budget Planner (`/party-planner`)
- **Inputs**: Total Budget, Guest Count, Event Type (Birthday, Wedding, Anniversary, Corporate Event, House Party), City/Location, Service Toggles (Catering, Venue, Theme Decor, Cake, DJ/Music, Photography, Transport, Hotel Stay), Food Preference.
- **Outputs**: Proportional per-guest catering budget, venue booking options, entertainment packages, and search links on Swiggy, Zomato, OYO, MakeMyTrip, and Amazon.

### 3. Jewelry & Outfit Styling Planner (`/jewelry-planner`)
- **Inputs**: Budget, Occasion (Wedding, Reception, Festive, Casual, Party, Office), Jewelry Type (Complete Set, Necklace & Earrings, Earrings, Bangles, Rings), Style Preference, Metal/Finish (Gold Plated, Silver, Diamond CZ, Rose Gold, Platinum, Oxidized), Color Accents, and **Optional Outfit Image Upload**.
- **Outputs**: Multimodal outfit color palette analysis, neckline & formality advice, curated jewelry pieces, and direct search links on CaratLane, Myntra, Amazon, and Flipkart.

---

## 🛡️ Financial Safety & Budget Engine

PocketSmart AI employs strict deterministic Python calculations:
1. Calculates item subtotals: $\text{subtotal} = \text{estimated\_price} \times \text{quantity}$.
2. Validates total spending: $\text{total\_estimated\_cost} = \sum \text{subtotal} \le \text{user\_budget}$.
3. Computes remaining savings: $\text{remaining\_budget} = \text{user\_budget} - \text{total\_estimated\_cost}$.
4. If AI proposals ever exceed the budget, the budget engine applies scaling and clamping to guarantee strict compliance before presenting results to the user.

---

## 📄 License
Built for educational and project purposes under the MIT License.
