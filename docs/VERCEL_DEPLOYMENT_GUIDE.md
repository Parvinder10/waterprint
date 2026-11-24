# WATERPRINT: Vercel Frontend Deployment & Backend Hosting Guide

This guide details the exact procedures for deploying the **WATERPRINT** React frontend to **Vercel** and hosting the Python FastAPI analytics service on a cloud container platform (Render, Railway, Fly.io, or AWS).

---

## 1. Exact Vercel Deployment Settings

### Option A: Via Vercel Web Dashboard (Recommended)
1. Go to your Vercel Dashboard at [https://vercel.com/parvinder10s-projects](https://vercel.com/parvinder10s-projects).
2. Click **Add New...** → **Project**.
3. Import your Git repository containing `water`.
4. In the **Configure Project** screen, configure the exact build settings:

| Vercel Setting | Value to Enter | Notes |
| :--- | :--- | :--- |
| **Framework Preset** | `Vite` | Auto-detected from `package.json` |
| **Root Directory** | `frontend` | Click "Edit" and select the `frontend` folder |
| **Build Command** | `npm run build` | Builds bundle via `vite build` |
| **Output Directory** | `dist` | Production assets generated in `frontend/dist` |
| **Install Command** | `npm install` | Installs dependencies |

5. Under **Environment Variables**, add:
   * **Key:** `VITE_API_BASE_URL`
   * **Value:** URL of your hosted backend (e.g. `https://waterprint-api.onrender.com` or leave blank for local/demo mode)
6. Click **Deploy**.

---

### Option B: Via Vercel CLI
If using Vercel CLI from your terminal:

```bash
cd frontend

# Login to your Vercel account
vercel login

# Link and deploy to your project scope (parvinder10s-projects)
vercel --prod
```

When prompted:
* Set up and deploy `waterprint-frontend`? **Yes**
* Which scope do you want to deploy to? **parvinder10s-projects**
* Link to existing project? **No** (or select if already created)
* What's your project's name? **waterprint**
* In which directory is your code located? **`./`** (since you are inside `frontend`)
* Want to modify settings? **No** (Vercel automatically detects Vite from `vercel.json`)

---

## 2. SPA Routing & Page Refresh Configuration (`vercel.json`)

Single-Page Applications (SPAs) built with React/Vite require URL rewrites so that direct deep links and browser refreshes do not result in `404 Not Found`.

This is pre-configured in `frontend/vercel.json`:
```json
{
  "framework": "vite",
  "cleanUrls": true,
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

---

## 3. Backend Analytics Service Hosting (FastAPI)

Because Vercel is optimized for static frontends and serverless edge functions, the long-running scientific computing and ML analytics pipeline is hosted on a containerized backend.

### Quick Deployment on Render / Railway

#### Deploying on Render (Free / Starter Tier)
1. In Render, select **New Web Service** → Connect your repository.
2. Select **Docker** (it automatically uses the root `Dockerfile`) or **Python 3**.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `python -m uvicorn src.api.server:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables:
   * `PORT`: `8000` (or leave default assigned by Render)
   * `CORS_ORIGINS`: `https://*.vercel.app,https://vercel.com,http://localhost:5173`
6. Copy your assigned service URL (e.g., `https://waterprint-api.onrender.com`) and paste it as `VITE_API_BASE_URL` in your Vercel project settings.

#### Deploying on Railway
1. In Railway, click **New Project** → **Deploy from GitHub repo**.
2. Railway detects the `Dockerfile` and builds the container automatically.
3. In **Variables**, add:
   * `CORS_ORIGINS`: `https://*.vercel.app,https://vercel.com`
4. Generate a public domain under **Networking** and link to Vercel.

---

## 4. Environment Variables Reference

| Variable | Scope | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Frontend (Vercel) | No (graceful fallback) | Base URL of the live FastAPI backend | `https://waterprint-api.onrender.com` |
| `PORT` | Backend (Cloud) | Optional | Server listening port | `8000` / `8088` |
| `CORS_ORIGINS` | Backend (Cloud) | Yes | Comma-separated allowed frontend domains | `https://*.vercel.app,http://localhost:5173` |

---

## 5. Security & Secret Management

* **Zero Credentials in Frontend:** Database credentials, file paths, and private keys are never bundled into the client build.
* **CORS Protection:** The FastAPI backend rejects cross-origin requests from origins not listed in `CORS_ORIGINS`.
* **Safe Offline Fallback:** If the backend is cold-starting or temporarily offline, the frontend gracefully loads the pre-calibrated L-Town benchmark dataset and displays an indicator badge (`BENCHMARK CACHE (OFFLINE)`).
