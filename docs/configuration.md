# Configuration Reference

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Google Gemini API key (required) |
| `RAZORPAY_KEY_ID` | — | Razorpay key ID for payments |
| `RAZORPAY_KEY_SECRET` | — | Razorpay secret for payment verification |
| `PORT` | `8000` | Server port |
| `WEB_CONCURRENCY` | `1` | Number of uvicorn workers |

## Internal Constants

### API Layer (`api.py`)
| Constant | Value | Purpose |
|---|---|---|
| `MAX_FILE_BYTES` | 3 MB | Maximum upload file size |
| `MAX_JD_CHARS` | 8,000 | Maximum job description length |
| `MAX_ANSWER_CHARS` | 3,000 | Maximum interview answer length |
| `MAX_QUESTION_CHARS` | 1,000 | Maximum question length |

### Tools Layer (`tools.py`)
| Constant | Value | Purpose |
|---|---|---|
| `_MAX_RESUME_CHARS` | 6,000 | Resume truncation limit (saves ~40% tokens) |
| `_MAX_JD_CHARS` | 4,000 | JD truncation limit |
| `MODEL_PRIMARY` | `gemini-2.0-flash` | Primary model (15 RPM free) |
| `MODEL_FALLBACK` | `gemini-2.5-flash` | Fallback model (10 RPM free) |

### Agents Layer (`src/agents.py`)
| Constant | Value | Purpose |
|---|---|---|
| `MAX_RETRIES` | 2 | Retry attempts after first failure |
| `BASE_DELAY_S` | 1.5 | Base delay for exponential backoff |

### Circuit Breaker (`src/circuit_breaker.py`)
| Parameter | Default | Purpose |
|---|---|---|
| `failure_threshold` | 3 | Failures before OPEN |
| `recovery_timeout` | 45s | Time in OPEN before probe |
| `success_threshold` | 1 | Successes in HALF_OPEN to close |

### Checkpoints (`src/checkpoint.py`)
| Constant | Value | Purpose |
|---|---|---|
| `MAX_CHECKPOINTS` | 12 | Maximum stored checkpoints per run |
