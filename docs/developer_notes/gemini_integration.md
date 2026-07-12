# Gemini API Integration

How HireOS communicates with Google Gemini API.

## Models Used

- Primary: gemini-2.0-flash
- Fallback: gemini-2.5-flash

## Optimizations

- Input text is trimmed to reduce token overhead
- Output max tokens capped at 4096 to minimize latency

## JSON Handling

- Strictly requests MIME type application/json
- Implements fallback JSON repair for truncated text

## Errors

- Handles 429 quota exhaustion and 503 unavailability gracefully
