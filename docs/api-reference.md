# HireOS API Reference

Base URL: `https://hire-os-langgraph.vercel.app`

## Authentication

All AI endpoints accept an optional `api_key` form field.
If omitted, the server's `GOOGLE_API_KEY` environment variable is used.

## Endpoints

### `GET /api/health`

Health check endpoint.

**Response:**
```json
{"status": "ok", "version": "2.0.0"}
```

### `POST /api/analyze`

Full resume analysis: parse + score + interview questions in one call.

**Request:** `multipart/form-data`
| Field | Type | Required | Description |
|---|---|---|---|
| `resume` | File | Yes | PDF, DOCX, or TXT resume |
| `job_description` | String | Yes | Target job description (max 8000 chars) |
| `api_key` | String | No | Your Gemini API key |

**Response:**
```json
{
  "success": true,
  "candidate": {
    "name": "...", "skills": [...], "experience_years": 5,
    "education": "...", "past_roles": [...], "summary": "..."
  },
  "score": {
    "score": 82, "strengths": [...], "gaps": [...],
    "improvements": [...], "hire_recommendation": "Strong Yes",
    "reasoning": "..."
  },
  "questions": {
    "questions": [{"id": 1, "question": "...", "type": "Technical", ...}]
  }
}
```

### `POST /api/rewrite`

AI resume rewrite (premium feature).

**Request:** `multipart/form-data` — same fields as `/api/analyze`

**Response:**
```json
{
  "success": true,
  "rewritten": {
    "rewritten_summary": "...",
    "rewritten_skills": [...],
    "rewritten_bullets": [...],
    "ats_keywords": [...],
    "ats_tips": [...],
    "cover_letter_opening": "..."
  }
}
```

### `POST /api/rank`

Rank multiple candidates against a job description.

**Request:** `multipart/form-data`
| Field | Type | Required | Description |
|---|---|---|---|
| `resumes` | File[] | Yes | Up to 10 resume files |
| `job_description` | String | Yes | Target JD |
| `api_key` | String | No | Gemini API key |

### `POST /api/evaluate`

Score a practice interview answer.

**Request:** `multipart/form-data`
| Field | Type | Required | Description |
|---|---|---|---|
| `question` | String | Yes | Interview question |
| `answer` | String | Yes | Candidate's answer |
| `job_description` | String | Yes | Target JD |
| `api_key` | String | No | Gemini API key |

## Rate Limits

| Endpoint | Limit |
|---|---|
| `/api/analyze`, `/api/rewrite`, `/api/rank` | 10 req/min/IP |
| `/api/evaluate` | 20 req/min/IP |

## Error Codes

| Code | Meaning |
|---|---|
| 400 | Bad request (invalid input, empty file, bad key) |
| 429 | Rate limit exceeded |
| 500 | Internal error (user-friendly message returned) |
