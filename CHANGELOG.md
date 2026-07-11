# Changelog

All notable changes to HireOS are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.0.0] — 2026-07-11

### Added
- AI resume rewriter (premium feature) — rewrites summary, skills, bullets
- ATS keyword extraction with actionable tips
- Cover letter opening paragraph generation
- Razorpay payment integration (₹199 one-time)
- Candidate ranking for batch resume analysis
- Interview practice mode with AI coaching
- Per-IP rate limiting (pure Python, no Redis)
- TTL result cache for identical resume+JD pairs
- Circuit breaker pattern for fault tolerance
- Checkpoint and rollback system
- Telemetry and execution logging
- Streamlit dashboard for pipeline visualization

### Changed
- Migrated from Anthropic Claude to Google Gemini 2.0 Flash
- Reduced max_output_tokens from 8192 to 4096 (30% faster)
- Combined parse+score+questions into single API call (3x less quota)
- Input trimming: resume 6000 chars, JD 4000 chars (40% fewer tokens)

### Security
- Input sanitization (null bytes, control chars, max sizes)
- File type allowlist (PDF, DOCX, TXT only)
- Error messages never leak internal stack traces
- API keys only in environment variables
- Owner bypass protected by SHA-256 hash

## [1.0.0] — 2025-06-01

### Added
- Initial release with resume parsing and scoring
- CLI pipeline with LangGraph multi-agent architecture
- Basic web interface
