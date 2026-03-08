# UniCollab.

> Find teammates. Build ideas. **Create the future.**

UniCollab is a modern, developer-focused university collaboration platform where students can authenticate, build technical profiles, discover peers based on skill overlaps, and initialize internal operations (projects). 

*(Note: This repository represents a specialized Test Deployment version configured for 10 seed users.)*

## 🚀 Overview

This testing architecture is decoupled into a robust Python JSON API and a blazing fast, static HTML/JS frontend styled with Tailwind CSS and custom Glassmorphism/Neon UI components.

## ✨ Features

- **Secure Authentication**: Pre-configured test user system (CSV-backed logic) resolving JWT-style headers.
- **Identity Formulation**: Deep profiling system tracking Academic Sector, Graduation Cycle, and technical capabilities.
- **Hybrid Technical Loadout**: Define capabilities using predefined system suggestions or custom terminal input.
- **Algorithmic Match Engine**: Discover operatives across the grid sorted by technical overlap scoring.
- **Operation Terminals (Projects)**: Fully broadcast and join internal projects with strict team sizing and skill constraints.
- **Futuristic UI**: A striking dark-mode aesthetic utilizing radial glows, deep space backgrounds, and glowing drop-shadows.

## 💻 Tech Stack

- **Frontend**: Pure HTML5, Vanilla JavaScript (`api.js`), and Tailwind CSS via CDN.
- **Backend API**: Python 3.10+, FastAPI, Uvicorn, Pydantic.
- **Architecture**: `fetch()` driven decoupled client-server model.

## 🏗️ Architecture Split

```
unicollab/
│
├── backend/                  # FastAPI Application Core
│   ├── main.py               # REST Endpoints & CORS Middleware
│   ├── users.py              # User Management & CSV Loader
│   ├── models.py             # Pydantic Schemas
│   ├── test_users.csv        # 10 Seed Operatives
│   └── requirements.txt      # Render Dependencies
│
├── frontend/                 # Vercel-Ready Static Assets
│   ├── index.html            # Routing entry point (redirects to login)
│   ├── login.html            # Auth view
│   ├── dashboard.html        # Projects/Operations hub
│   ├── profile.html          # Onboarding Phase 1
│   ├── skills.html           # Onboarding Phase 2
│   ├── explore.html          # Algorithmic Match Discover view
│   ├── js/api.js             # Singleton fetch() wrapper and state manager
│   └── static/               # Hosted logos and global CSS config
│
└── README.md
```

## 🌐 Deployment Instructions

### 1. Backend (Deploy to Render)

1. Create a **Web Service** on Render.com linked to your repository.
2. Set the Root Directory to `backend/`.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Note the deployment URL (e.g., `https://unicollab-api.onrender.com`).

*(Ensure `CORSMiddleware` in `main.py` is configured to allow `*` or your Vercel URL.)*

### 2. Frontend Connection (Deploy to Vercel)

1. Navigate to `frontend/js/api.js`.
2. Ensure `API_BASE_URL` falls back to the Render URL you established above in production. 
   *(It is currently set up to use `https://unicollab-api.onrender.com` when not on `localhost`)*
3. Link the `frontend/` directory to **Vercel** as a static HTML project. No build commands are required.

## 🧪 Testing Locally

1. **Start the API:**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 10000
   ```
2. **Launch the UI:**
   Serve the `frontend/` folder using any local HTTP static server.
   ```bash
   cd frontend
   python3 -m http.server 3000
   ```
3. Navigate to `http://localhost:3000` and login using credentials from `backend/test_users.csv` (e.g. `user1@srmist.edu.in` / `pass123`).

## 🔮 Future Improvements

- Migrate CSV user-store to a managed PostgreSQL cluster (Supabase/Neon).
- Implement robust bcrypt hashing and actual PyJWT token generation.
- Expand "Matches" to bidirectional websockets for live chat capability.
- Integrate active Kanban tasks specific to confirmed project teams.
