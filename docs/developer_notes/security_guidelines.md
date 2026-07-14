# Developer Security Reference Guidelines

This guide explains security designs within HireOS.

## Input Validation Layer

All incoming texts and payloads are validated and sanitized via `src/validators.py`.
