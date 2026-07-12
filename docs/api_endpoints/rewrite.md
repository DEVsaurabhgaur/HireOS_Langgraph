# /api/rewrite

Rewrites resume sections to match job requirements (premium feature).

## Request

- resume: UploadFile
- job_description: Form string
- api_key: Form string (optional)

## Response

JSON with rewritten summary, skills, bullet points, and missing ATS keywords.
