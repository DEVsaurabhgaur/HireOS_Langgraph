# Result Caching Guide

How HireOS caches analysis results in memory.

## TTL Cache

LRU-style cache with 10 minutes (600s) time-to-live.

## Key Generation

SHA-256 hash generated from sanitized resume and job description.
