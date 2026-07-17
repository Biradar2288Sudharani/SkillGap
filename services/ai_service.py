"""
This is the 'AI' half of the assignment: given raw resume text and raw
JD text, ask the LLM to extract a clean, normalized list of skills from
each -- so "ReactJS", "React.js" and "React" all collapse to one entry.

Uses Google's Gemini API (free tier, no credit card required).

Design choice worth mentioning in the interview:
    The AI ONLY extracts and normalizes skills. It does NOT decide the
    matched/missing/percentage itself. That comparison is done in plain
    deterministic Python (see services/matcher.py). This keeps the AI's
    job narrow (something it's genuinely good at: messy text -> clean
    list) and keeps the scoring logic 100% predictable, testable, and
    free of AI hallucination risk.
"""

import json
import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)
_model = genai.GenerativeModel(Config.GEMINI_MODEL)

EXTRACTION_PROMPT = """You are a precise skill-extraction engine for a resume-screening tool.

Given a block of raw text (either a resume or a job description), extract every
professional/technical/tool skill mentioned (programming languages, frameworks,
libraries, databases, cloud platforms, tools, methodologies).

Rules:
- Normalize variants to one canonical name (e.g. "ReactJS", "React.js" -> "React").
- Do not invent skills that are not mentioned or clearly implied.
- Do not include soft skills like "communication" or "teamwork" unless explicitly
  the main subject of a bullet point.
- Return STRICT JSON only, no markdown, no explanation, in this exact shape:
  {{"skills": ["Skill One", "Skill Two", ...]}}

Text to analyze:
---
{text}
---
"""


def extract_skills(text: str) -> list:
    """Calls the LLM once and returns a clean Python list of skill strings."""
    if not text or not text.strip():
        return []

    prompt = EXTRACTION_PROMPT.format(text=text.strip())

    response = _model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )

    raw = response.text
    try:
        parsed = json.loads(raw)
        skills = parsed.get("skills", [])
        seen = set()
        cleaned = []
        for s in skills:
            key = s.strip().lower()
            if key and key not in seen:
                seen.add(key)
                cleaned.append(s.strip())
        return cleaned
    except (json.JSONDecodeError, AttributeError):
        return []


def extract_skills_from_both(resume_text: str, jd_text: str) -> dict:
    """Convenience wrapper: runs extraction for resume and JD."""
    return {
        "resume_skills": extract_skills(resume_text),
        "jd_skills": extract_skills(jd_text),
    }