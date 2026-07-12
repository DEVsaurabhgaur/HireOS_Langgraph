# /api/rank

Ranks up to 10 resumes against a JD.

## Request

- resumes: List of UploadFile
- job_description: Form string
- api_key: Form string (optional)

## Response

List of scored candidates with ranked position and summary recommendations.

Note: Parallel parsing is executed concurrently.
