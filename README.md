# 🚀 HireOS — AI Resume Intelligence Platform

<div align="center">

![HireOS Banner](https://img.shields.io/badge/HireOS-AI%20Resume%20Intelligence-6366f1?style=for-the-badge&logo=google&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Google%20Gemini-2.0%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Vercel](https://img.shields.io/badge/Live%20on-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Razorpay](https://img.shields.io/badge/Payments-Razorpay-02042B?style=for-the-badge&logo=razorpay&logoColor=white)
![Tests](https://github.com/DEVsaurabhgaur/HireOS_Langgraph/actions/workflows/tests.yml/badge.svg)
![Lint](https://github.com/DEVsaurabhgaur/HireOS_Langgraph/actions/workflows/lint.yml/badge.svg)

### **The only AI tool that actually rewrites your resume — not just scores it.**

[🌐 **Try Live →**](https://hire-os-langgraph.vercel.app) &nbsp;·&nbsp; [⭐ Star this repo](#) &nbsp;·&nbsp; [🐛 Issues](https://github.com/DEVsaurabhgaur/HireOS_Langgraph/issues)

</div>

---

## 📑 Table of Contents

- [What is HireOS?](#-what-is-hireos)
- [Live Demo](#-live-demo)
- [Tech Stack](#️-tech-stack)
- [Run Locally](#-run-locally)
- [Deploy to Vercel](#-deploy-to-vercel-1-click)
- [API Reference](#-api-reference)
- [Security](#️-security)
- [Performance](#-performance)
- [Pricing](#-pricing)
- [Contributing](#-contributing)
- [Author](#-author)
- [License](#-license)

---

## 🎯 What is HireOS?

Most resume tools just give you a score and leave you guessing. **HireOS goes further** — it tells you *exactly* what to fix and rewrites your resume with the precise keywords from the job description.

Built for **job seekers** who want to beat ATS filters, and **recruiters** who need to rank candidates fast.

| Feature | What it does | Access |
|---|---|---|
| 📊 **Resume Score** | 0–100 match score vs. JD with reasoning | **Free** |
| 💪 **Strengths & Gaps** | AI identifies what you have and what's missing | **Free** |
| 🎯 **Interview Questions** | 5 custom questions based on your resume + JD | **Free** |
| ✍️ **Practice Mode** | Answer questions, get AI coaching score (1–10) | **Free** |
| 🏆 **Candidate Ranker** | Upload 10 resumes, rank all instantly | **Free** |
| ✨ **AI Resume Rewriter** | Rewrites Summary, Skills, Bullets with JD keywords | **₹199 one-time** |
| 🔑 **ATS Keywords** | Exact keywords missing from your resume | **₹199 one-time** |
| 💌 **Cover Letter Opening** | AI-generated tailored opening paragraph | **₹199 one-time** |

---

## 🎬 Live Demo

👉 **[hire-os-langgraph.vercel.app](https://hire-os-langgraph.vercel.app)**

> Upload your resume (PDF/DOCX/TXT) → Pick a role → Get instant AI analysis in ~15 seconds

---

## 🏗️ Tech Stack

```
HireOS_Langgraph/
├── api.py                 # FastAPI backend — security hardened, async, rate-limited
├── tools.py               # Gemini AI tools — cached client, token-optimized
├── webapp/
│   └── index.html         # Complete SaaS frontend — vanilla HTML/CSS/JS
├── src/
│   ├── agents.py          # LangGraph agent nodes
│   ├── graph.py           # Multi-agent supervisor workflow
│   └── state.py           # Shared state schema
├── vercel.json            # Vercel serverless config
├── railway.json           # Railway 4-worker config (500 users)
└── requirements.txt       # Minimal production dependencies
```

**Stack:**
- **Backend:** Python 3.11 · FastAPI · Google Gemini 2.0 Flash (free tier optimized)
- **AI:** LangGraph multi-agent · Single combined Gemini call (3× less quota)
- **Frontend:** Vanilla HTML/CSS/JS · No framework · Glassmorphism dark UI
- **Payments:** Razorpay — UPI, Cards, Net Banking
- **Security:** Per-IP rate limiting · Input sanitization · TTL result cache
- **Deploy:** Vercel (serverless) · Railway-ready (4 workers, 500 concurrent users)

---

## 🚀 Run Locally

```bash
# 1. Clone
git clone https://github.com/DEVsaurabhgaur/HireOS_Langgraph.git
cd HireOS_Langgraph

# 2. Install
pip install -r requirements.txt

# 3. Set up env
cp .env.example .env
# Add your free Gemini key → https://aistudio.google.com/app/apikey

# 4. Run
python api.py
# Open → http://localhost:8000
```

---

## 🌐 Deploy to Vercel (1 click)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/DEVsaurabhgaur/HireOS_Langgraph)

Add one environment variable in Vercel dashboard:

```
GOOGLE_API_KEY = your_gemini_key_here
```

---

## 🔌 API Reference

All endpoints: `multipart/form-data` POST.

| Endpoint | Description | Auth |
|---|---|---|
| `POST /api/analyze` | Full resume analysis (score + questions) | Server key |
| `POST /api/rewrite` | AI resume rewrite (premium) | Server key |
| `POST /api/evaluate` | Score a practice interview answer | Server key |
| `POST /api/rank` | Rank multiple candidate resumes | Server key |
| `GET /api/health` | Health check | Public |

Optional `api_key` field on all endpoints — falls back to server `GOOGLE_API_KEY`.

---

## 🛡️ Security

- ✅ Per-IP rate limiting (10 heavy AI calls/min, pure Python — no Redis needed)
- ✅ Input sanitization — null bytes, control chars, max sizes enforced
- ✅ File type allowlist — PDF, DOCX, TXT only
- ✅ Errors never leak internal stack traces
- ✅ API keys only in environment variables — never in code
- ✅ No user data stored — resumes processed in memory and discarded
- ✅ Premium stored in browser `localStorage` — no user database needed
- ✅ Owner bypass protected by SHA-256 hash (secret never in source)

---

## ⚡ Performance

- **1 Gemini call** for full analysis (parse + score + questions combined)
- **Gemini client cached** per API key — no per-request object creation
- **TTL result cache** — identical resume+JD → instant response (0 API calls)
- **`asyncio.to_thread()`** — event loop never blocked, handles 500 concurrent users
- **Token budget optimized** — 4096 max output (was 8192), inputs pre-truncated

---

## 💳 Pricing

| Tier | Price | What you get |
|---|---|---|
| **Free** | ₹0 | Score, strengths/gaps, interview prep, candidate ranking |
| **Premium** | **₹199 one-time** | AI resume rewrite + ATS keywords + cover letter · **Use forever** |

> Resume writers charge ₹2,000–₹10,000. HireOS does it in 60 seconds for ₹199.

---

## 🤝 Contributing

Contributions are welcome! Please read the [Contributing Guide](CONTRIBUTING.md) before submitting a PR.

- 🐛 [Report a bug](https://github.com/DEVsaurabhgaur/HireOS_Langgraph/issues/new?template=bug_report.md)
- ✨ [Request a feature](https://github.com/DEVsaurabhgaur/HireOS_Langgraph/issues/new?template=feature_request.md)

---

## 👨‍💻 Author

**Saurabh Gaur** — AI/ML Engineer · Building tools that matter

[![GitHub](https://img.shields.io/badge/GitHub-DEVsaurabhgaur-181717?style=flat&logo=github)](https://github.com/DEVsaurabhgaur)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-saurabhgaur-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/DEVsaurabhgaur)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-HireOS-6366f1?style=flat)](https://hire-os-langgraph.vercel.app)

---

## 📄 License

MIT — free to use, modify, and distribute with attribution.

---

<div align="center">
Built with ❤️ using Google Gemini + LangGraph · 🇮🇳 Made in India
</div>


## Security

For details on input validation, rate limiting, and core system sanitization, see the [Security Developer Notes](docs/developer_notes/security_guidelines.md).
