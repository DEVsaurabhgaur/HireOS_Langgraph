"""
examples/quick_start.py
Quick start example — analyze a single resume against a job description.

Usage:
    export GOOGLE_API_KEY=your-key
    python examples/quick_start.py
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import analyze_resume_complete


def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Set GOOGLE_API_KEY environment variable first.")
        sys.exit(1)

    resume = """
    Jane Doe
    Senior Software Engineer | 7 years experience
    Skills: Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis
    Education: M.S. Computer Science, Stanford University
    Experience:
    - Tech Lead at StartupXYZ (2021-present): Led team of 5, built microservices
    - Senior Engineer at BigCorp (2018-2021): Designed REST APIs serving 1M+ users
    """

    jd = """
    Senior Backend Engineer
    Requirements: 5+ years Python, experience with FastAPI or Django,
    Docker/Kubernetes, SQL databases, REST API design.
    Nice to have: Redis, message queues, CI/CD pipelines.
    """

    print("Analyzing resume...")
    result = analyze_resume_complete(resume.strip(), jd.strip(), api_key)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
