"""
examples/batch_analysis.py
Batch analysis — analyze multiple resumes from a file.

Usage:
    export GOOGLE_API_KEY=your-key
    python examples/batch_analysis.py samples/resumes.txt samples/jd_ml_engineer.txt
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import analyze_resume_complete


def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Set GOOGLE_API_KEY environment variable first.")
        sys.exit(1)

    if len(sys.argv) < 3:
        print("Usage: python batch_analysis.py <resumes_file> <jd_file>")
        sys.exit(1)

    resumes_file = Path(sys.argv[1])
    jd_file = Path(sys.argv[2])

    resumes = [r.strip() for r in resumes_file.read_text().split("---") if r.strip()]
    jd = jd_file.read_text().strip()

    print(f"Analyzing {len(resumes)} resumes...")
    results = []

    for i, resume in enumerate(resumes, 1):
        print(f"  [{i}/{len(resumes)}] Processing...")
        try:
            result = analyze_resume_complete(resume, jd, api_key)
            results.append(result)
            score = result.get("score", {}).get("score", "?")
            name = result.get("candidate", {}).get("name", "Unknown")
            print(f"    {name}: {score}/100")
        except Exception as e:
            print(f"    Error: {e}")
            results.append({"error": str(e)})

    output = Path("batch_results.json")
    output.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {output}")


if __name__ == "__main__":
    main()
