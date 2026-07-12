# Rate Limiting Implementation

HireOS implements in-memory sliding window rate limiting.

## Design

Pure python implementation. No redis dependency required.

## Thresholds

- AI Endpoints: 10 calls per minute per IP
- Eval Endpoints: 20 calls per minute per IP
