# /api/analyze

Runs full parse, score and question generation.

## Request

- resume: UploadFile
- job_description: Form string
- api_key: Form string (optional)

## Response

JSON dictionary with success, candidate, score, and questions key.

See /api/health for base testing.
