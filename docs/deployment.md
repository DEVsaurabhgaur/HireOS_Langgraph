# Deployment Guide

## Vercel (Recommended — Serverless)

### One-Click Deploy
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/DEVsaurabhgaur/HireOS_Langgraph)

### Manual Setup
1. Install Vercel CLI: `npm i -g vercel`
2. Login: `vercel login`
3. Deploy: `vercel --prod`
4. Set environment variable: `vercel env add GOOGLE_API_KEY`

### Environment Variables
| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |
| `RAZORPAY_KEY_ID` | No | Razorpay key for payments |
| `RAZORPAY_KEY_SECRET` | No | Razorpay secret for payments |

## Railway

### Setup
1. Create a new project on [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Set environment variables in the dashboard
4. Railway auto-detects `railway.json` configuration

### Configuration (`railway.json`)
```json
{
  "build": {"builder": "NIXPACKS"},
  "deploy": {
    "startCommand": "uvicorn api:app --host 0.0.0.0 --port $PORT --workers 4",
    "healthcheckPath": "/api/health"
  }
}
```

### Scaling
- 4 workers handle ~500 concurrent users
- 512 MB RAM minimum
- Scale workers with `WEB_CONCURRENCY` env var

## Docker (Self-Hosted)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Local Development

```bash
git clone https://github.com/DEVsaurabhgaur/HireOS_Langgraph.git
cd HireOS_Langgraph
pip install -r requirements.txt
cp .env.example .env
# Add your Gemini key to .env
python api.py
# Open http://localhost:8000
```
