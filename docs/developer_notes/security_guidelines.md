# Developer Security Reference Guidelines

This guide explains security designs within HireOS.

## Input Validation Layer

All incoming texts and payloads are validated and sanitized via `src/validators.py`.

## Rate Limiting

Sliding window limiters track IP attempts in-memory to prevent DoS on LLM tokens.

## Secret Storage

API keys are injected via environment variables and parsed safely.
