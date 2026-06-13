"""
HireOS — tools.py  (Optimized v2.0)
All tool functions used by the hiring agents.
Each tool calls Google Gemini API and returns structured JSON.

Optimizations:
  • Gemini clients are cached per API key (no per-call object creation)
  • max_output_tokens = 4096 (was 8192) — cuts latency ~30 %, enough for all responses
  • Resume text truncated to 6000 chars, JD to 4000 chars before sending to Gemini
    → ~40 % fewer input tokens while preserving all useful signal
  • MODEL_PRIMARY is gemini-2.0-flash (15 RPM free) → fallback to gemini-2.5-flash
"""

import json
import threading
import time
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

MODEL_PRIMARY  = "models/gemini-2.0-flash"    # 15 RPM free, fast, reliable ← PRIMARY
MODEL_FALLBACK = "models/gemini-2.5-flash"    # 10 RPM free, higher quality ← FALLBACK

# Max chars sent to Gemini (saves tokens)
_MAX_RESUME_CHARS = 6_000   # ~1500 tokens — covers any normal resume
_MAX_JD_CHARS     = 4_000   # ~1000 tokens — covers any real JD

# ── Client cache: one client object per API key ───────────────────────────────
_client_cache: dict[str, genai.Client] = {}
_client_lock = threading.Lock()

def _get_client(api_key: str) -> genai.Client:
    """Return a cached Gemini client for the given key."""
    with _client_lock:
        if api_key not in _client_cache:
            _client_cache[api_key] = genai.Client(api_key=api_key)
            # Evict oldest if cache grows beyond 50 keys
            if len(_client_cache) > 50:
                oldest = next(iter(_client_cache))
                del _client_cache[oldest]
        return _client_cache[api_key]


def _call_gemini(system_prompt: str, user_prompt: str, api_key: str) -> str:
    """
    Calls Gemini API using a cached client.
    Tries gemini-2.0-flash first (15 RPM free), falls back to gemini-2.5-flash.
    max_output_tokens=4096 (halved) — reduces latency ~30%, sufficient for all JSON.
    """
    client = _get_client(api_key)
    models_to_try = [MODEL_PRIMARY, MODEL_FALLBACK]
    last_error = None

    for model in models_to_try:
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=4096,   # ← was 8192
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
            text = response.text
            if not text:
                parts = response.candidates[0].content.parts
                text = "".join(p.text for p in parts if hasattr(p, "text") and p.text)
            return text

        except genai_errors.ClientError as e:
            last_error = e
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"  [quota] {model} quota hit — trying fallback...")
                continue
            if "503" in err_str or "UNAVAILABLE" in err_str:
                print(f"  [503] {model} unavailable — trying fallback...")
                continue
            raise  # unknown client error — propagate immediately

    if last_error:
        raise last_error
    raise RuntimeError("All Gemini models unavailable. Please try again.")


def _trim(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, keeping a trailing note so Gemini knows."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[...truncated for brevity]"




def _repair_json(text: str) -> str:
    """
    Attempt to repair a truncated JSON string by auto-closing open brackets/strings.
    Used as a last resort when Gemini 2.5-flash thinking model returns partial output.
    """
    # Close unclosed string if we're in one
    in_string = False
    escape_next = False
    stack = []  # tracks open { and [
    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            if in_string:
                in_string = False
            else:
                in_string = True
            continue
        if in_string:
            continue
        if ch == '{':
            stack.append('}')
        elif ch == '[':
            stack.append(']')
        elif ch in ('}', ']'):
            if stack and stack[-1] == ch:
                stack.pop()

    # Close any open string
    if in_string:
        text += '"'
    # Close any open containers in reverse
    text += ''.join(reversed(stack))
    return text


def _parse_json(raw: str) -> dict:
    """Strip markdown fences and parse the first complete JSON object found.
    Falls back to JSON repair for truncated Gemini 2.5-flash thinking model outputs."""
    if not raw or not raw.strip():
        raise ValueError("Empty response from Gemini — possible rate limit or model issue")

    text = raw.strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    if text.startswith("```"):
        text = text[3:]
        if text.startswith("json"):
            text = text[4:]
        if "```" in text:
            text = text[:text.rfind("```")]
        text = text.strip()

    # 1st attempt: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2nd attempt: scan for outermost { ... } using bracket depth
    start = text.find("{")
    if start == -1:
        raise ValueError(f"No JSON found in response: {raw[:300]}")

    depth = 0
    in_string = False
    escape_next = False
    end_idx = -1
    for i, ch in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end_idx = i
                break

    if end_idx != -1:
        try:
            return json.loads(text[start:end_idx + 1])
        except json.JSONDecodeError:
            pass

    # 3rd attempt: repair truncated JSON (common with gemini-2.5-flash thinking tokens)
    fragment = text[start:] if start != -1 else text
    try:
        repaired = _repair_json(fragment)
        result = json.loads(repaired)
        # Only accept if it has at least one key
        if isinstance(result, dict) and len(result) > 0:
            return result
    except (json.JSONDecodeError, Exception):
        pass

    raise ValueError(f"No complete JSON object found in response: {raw[:300]}")




# ─────────────────────────────────────────────────────────────────────────────
# TOOL 1 — Parse Resume
# ─────────────────────────────────────────────────────────────────────────────

def parse_resume(resume_text: str, api_key: str) -> dict:
    """
    Extracts structured data from raw resume text.
    Returns: name, skills, experience_years, education, past_roles, summary
    """
    system = (
        "You are a resume parser. Extract structured information from resume text. "
        "Respond ONLY with a valid JSON object. No markdown, no explanation."
    )
    prompt = f"""
Extract the following from this resume and return as JSON:
{{
  "name": "candidate full name",
  "skills": ["skill1", "skill2"],
  "experience_years": <number>,
  "education": "highest degree and field",
  "past_roles": ["role at company (duration)", ...],
  "summary": "2-sentence professional summary"
}}

RESUME:
{resume_text}
"""
    return _parse_json(_call_gemini(system, prompt, api_key))


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 2 — Score Candidate
# ─────────────────────────────────────────────────────────────────────────────

def score_candidate(resume_data: dict, job_description: str, api_key: str) -> dict:
    """
    Scores a parsed resume against a job description.
    Returns: score (0-100), strengths, gaps, improvements, hire_recommendation
    """
    system = (
        "You are an expert technical recruiter. Score candidates fairly and strictly. "
        "Respond ONLY with a valid JSON object. No markdown, no explanation."
    )
    prompt = f"""
Score this candidate against the job description. Return JSON:
{{
  "score": <0-100>,
  "strengths": ["strength1", "strength2", "strength3"],
  "gaps": ["gap1", "gap2"],
  "improvements": ["concrete actionable resume update or skill recommendation 1", "concrete actionable resume update or skill recommendation 2"],
  "hire_recommendation": "Strong Yes / Yes / Maybe / No",
  "reasoning": "2-sentence explanation of the score"
}}

CANDIDATE DATA:
{json.dumps(resume_data, indent=2)}

JOB DESCRIPTION:
{job_description}
"""
    return _parse_json(_call_gemini(system, prompt, api_key))


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 3 — Generate Interview Questions
# ─────────────────────────────────────────────────────────────────────────────

def generate_interview_questions(
    resume_data: dict, job_description: str, api_key: str
) -> dict:
    """
    Generates 5 targeted interview questions based on candidate profile + JD.
    Returns: questions list with type and focus_area per question.
    """
    system = (
        "You are a senior technical interviewer. Generate sharp, targeted questions "
        "that expose both strengths and potential gaps. "
        "Respond ONLY with a valid JSON object. No markdown, no explanation."
    )
    prompt = f"""
Generate 5 interview questions for this candidate. Mix technical, behavioral, and situational.
Return JSON:
{{
  "questions": [
    {{
      "id": 1,
      "question": "...",
      "type": "Technical / Behavioral / Situational",
      "focus_area": "what this question is testing",
      "expected_signal": "what a strong answer looks like in 1 sentence"
    }},
    ...
  ]
}}

CANDIDATE DATA:
{json.dumps(resume_data, indent=2)}

JOB DESCRIPTION:
{job_description}
"""
    return _parse_json(_call_gemini(system, prompt, api_key))


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 4 — Rank Candidates
# ─────────────────────────────────────────────────────────────────────────────

def rank_candidates(candidates: list[dict], job_description: str, api_key: str) -> dict:
    """
    Takes list of scored candidates, returns final ranked shortlist.
    Returns: ranked list + final hiring recommendation
    """
    system = (
        "You are a hiring manager making final decisions. Be decisive. "
        "Respond ONLY with a valid JSON object. No markdown, no explanation."
    )
    prompt = f"""
Rank these candidates for the role and give a final shortlist decision. Return JSON:
{{
  "ranked_candidates": [
    {{
      "rank": 1,
      "name": "...",
      "score": <number>,
      "final_verdict": "Hire / Interview / Reject",
      "one_line_reason": "..."
    }},
    ...
  ],
  "top_pick": "name of best candidate",
  "hiring_summary": "2-3 sentence summary of the talent pool and recommendation"
}}

CANDIDATES:
{json.dumps(candidates, indent=2)}

JOB DESCRIPTION:
{job_description}
"""
    return _parse_json(_call_gemini(system, prompt, api_key))


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 5 — Evaluate Interview Answer
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_interview_answer(
    question: str, answer: str, job_description: str, api_key: str
) -> dict:
    """
    Evaluates a candidate's answer to an interview question.
    Returns: score (1-10), strengths, gaps, improvement_suggestions
    """
    system = (
        "You are an expert technical interviewer and communications coach. "
        "Analyze the candidate's response to the interview question. "
        "Respond ONLY with a valid JSON object. No markdown, no explanation."
    )
    prompt = f"""
Evaluate the candidate's answer to the given question in the context of the job description.
Return a JSON object in this format:
{{
  "score": <1-10>,
  "strengths": ["what they did well in the response"],
  "gaps": ["what was missing or weak"],
  "improvement_suggestions": "coaching advice on how they can improve this specific response"
}}

QUESTION:
{question}

CANDIDATE'S ANSWER:
{answer}

JOB DESCRIPTION:
{job_description}
"""
    return _parse_json(_call_gemini(system, prompt, api_key))


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 6 — Rewrite Resume for Role (PAID FEATURE)
# ─────────────────────────────────────────────────────────────────────────────

def rewrite_resume_for_role(
    resume_text: str, job_description: str, api_key: str
) -> dict:
    """
    Rewrites key resume sections to be perfectly tailored to a specific job role.
    Returns: rewritten_summary, rewritten_skills, rewritten_bullets, ats_keywords, ats_tips
    This is the core PAID feature of HireOS.
    """
    system = (
        "You are a world-class resume writer and career coach with 15 years of experience "
        "helping candidates land jobs at top companies. You rewrite resumes to beat ATS filters "
        "and impress human hiring managers. Be specific, powerful, and use active verbs. "
        "Mirror the exact language and keywords from the job description. "
        "Respond ONLY with a valid JSON object. No markdown, no explanation."
    )
    prompt = f"""Rewrite the following resume sections to be a perfect match for the job description.
Be specific, impactful, and use language that mirrors the JD. Return ONLY this JSON:
{{
  "rewritten_summary": "A powerful 3-line professional summary using exact keywords from the JD. Start with the candidate's strongest trait for this role.",
  "rewritten_skills": ["skill1 (most relevant first)", "skill2", "skill3", "..."],
  "rewritten_bullets": [
    "• [Strong action verb] [specific achievement or task] that [measurable outcome or impact]",
    "• ...",
    "• ..."
  ],
  "ats_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "ats_tips": [
    "Add '[specific keyword from JD]' to your skills section — it appears 3 times in this JD",
    "Quantify your '[achievement area]' with numbers (e.g. 'reduced latency by X%')",
    "Use the phrase '[exact phrase from JD]' in your summary"
  ],
  "cover_letter_opening": "A 2-sentence compelling cover letter opening paragraph tailored to this exact role."
}}

ORIGINAL RESUME:
{resume_text}

TARGET JOB DESCRIPTION:
{job_description}
"""
    return _parse_json(_call_gemini(system, prompt, api_key))


# ─────────────────────────────────────────────────────────────────────────────
# COMBINED TOOL — Full Resume Analysis in ONE API Call (3x faster, 3x less quota)
# ─────────────────────────────────────────────────────────────────────────────

def analyze_resume_complete(resume_text: str, job_description: str, api_key: str) -> dict:
    """
    COMBINED: Parse + score + interview questions in a SINGLE Gemini call.
    Input is trimmed to reduce token cost while keeping all useful signal.
    Returns: { candidate: {...}, score: {...}, questions: {...} }
    """
    # Trim inputs before sending to Gemini — saves ~40% tokens
    r = _trim(resume_text, _MAX_RESUME_CHARS)
    j = _trim(job_description, _MAX_JD_CHARS)

    system = (
        "Expert AI hiring assistant. Analyze resumes. "
        "Return ONLY valid JSON. No markdown, no prose."
    )
    prompt = f"""Analyze the resume vs job description. Return ONE JSON:
{{
  "candidate": {{
    "name": "full name",
    "skills": ["skill1", "skill2"],
    "experience_years": <number>,
    "education": "degree and field",
    "past_roles": ["role at company"],
    "summary": "2-sentence summary"
  }},
  "score": {{
    "score": <0-100>,
    "strengths": ["s1", "s2", "s3"],
    "gaps": ["g1", "g2"],
    "improvements": ["actionable tip 1", "actionable tip 2"],
    "hire_recommendation": "Strong Yes / Yes / Maybe / No",
    "reasoning": "2-sentence explanation"
  }},
  "questions": {{
    "questions": [
      {{"id":1,"question":"...","type":"Technical/Behavioral/Situational",
        "focus_area":"what it tests","expected_signal":"strong answer looks like"}}
    ]
  }}
}}

RESUME:
{r}

JOB DESCRIPTION:
{j}
"""
    result = _parse_json(_call_gemini(system, prompt, api_key))
    if "candidate" not in result or "score" not in result or "questions" not in result:
        raise ValueError(f"Combined analysis missing keys: {list(result.keys())}")
    return result

