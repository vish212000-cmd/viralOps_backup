# ViralOps - AI-Powered Social Asset Repurposing Workspace

ViralOps is an enterprise-grade AI-powered SaaS platform that extracts short-form social-ready assets (hooks, titles, captions, CTAs, hashtags, and short scripts) from long-form content sources (video uploads, YouTube links, audio, articles, transcripts, PDFs).

---

## Technical Stack
* **Frontend**: React (Vite) + Vanilla CSS (highly premium glassmorphic dark UI)
* **Backend**: Django + Django REST Framework + SimpleJWT Auth
* **Queue**: Celery (with auto Eager mode fallback for local developer setups)
* **Containerization**: Docker & Docker Compose (MySQL, Redis, Django, Celery, React/Nginx)

---

## Local Development (Without Docker / Redis)

Since Docker/Redis are not installed on this local Windows machine, the application is configured to run out of the box using **SQLite** as the database and **Celery Eager Mode** (inline synchronous background jobs).

### 1. Setup Backend
1. Open PowerShell and navigate to the `backend` folder:
   ```powershell
   cd backend
   ```
2. Activate virtual environment (if not active) or run commands using `.\venv\Scripts\`:
   ```powershell
   # Apply database migrations
   .\venv\Scripts\python manage.py migrate

   # Create a Django Superuser (to access Admin ops center)
   .\venv\Scripts\python manage.py createsuperuser

   # Run Django server
   .\venv\Scripts\python manage.py runserver
   ```
   Django REST APIs will run on `http://localhost:8000/`.

### 2. Setup Frontend
1. Navigate to the `frontend` folder:
   ```powershell
   cd ../frontend
   ```
2. Start the Vite React development server:
   ```powershell
   npm run dev
   ```
   Vite React frontend will run on `http://localhost:5173/`. Open it in your browser!

### 3. Adding your Gemini API Key
To connect the AI generation pipeline to the real Google Gemini models, create a `.env` file in the `backend/` directory:
```bash
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
If no key is provided, the ingestion pipeline will run using a rich local mock generator, maintaining 100% features and flows.

---

## Production Deployment (With Docker & Docker Compose)

In production or Docker environment, spin up the entire cluster (MySQL, Redis, Django API, Celery Worker, Nginx React):
```bash
docker-compose up --build
```
Ensure you define `GEMINI_API_KEY` in your environment.
