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

JOINT_EXTRACTION_PROMPT = """You are a precise skill-extraction engine for a resume-screening tool.

You are given a RESUME and a JOB DESCRIPTION. Extract skills from each
separately, but you MUST use the exact same canonical name for the same
real-world skill whenever it appears in both lists. This is critical: if a
skill in the resume and a skill in the JD refer to the same thing (even if
worded differently), they must appear as the identical string in both lists,
so they can be matched later by exact comparison.

What counts as a skill: programming languages, frameworks, libraries,
databases, cloud platforms, tools, methodologies, required spoken/written
languages if the JD asks for them, and concrete job-function skills relevant
to the role (e.g. "Resume Screening", "Interview Coordination", "Job Posting").

Rules:
- Normalize variants to ONE canonical name shared across both lists
  (e.g. "ReactJS" / "React.js" -> "React"; "MS Word" / "Microsoft Word" -> "Microsoft Word").
- If the resume describes doing something that the JD also asks for, even in
  different words, use the SAME canonical label in both lists (e.g. resume
  "screening resumes and shortlisting candidates" and JD "screening resumes"
  should both produce the label "Resume Screening").
- Do not invent skills that are not mentioned or clearly implied.
- Do not include generic soft skills like "communication" or "teamwork"
  unless explicitly the main subject of a bullet point.
- Return STRICT JSON only, no markdown, no explanation, in this exact shape:
  {{"resume_skills": ["Skill One", "Skill Two", ...], "jd_skills": ["Skill One", "Skill Three", ...]}}

RESUME TEXT:
---
{resume_text}
---

JOB DESCRIPTION TEXT:
---
{jd_text}
---
"""


def extract_skills_from_both(resume_text: str, jd_text: str) -> dict:
    """
    Single AI call that extracts skills from BOTH resume and JD together.

    Why one call instead of two independent ones: when extracted separately,
    the model can normalize the same real skill to slightly different labels
    on each side (e.g. "Resume Screening" vs "Candidate Shortlisting" for the
    same underlying bullet point), which breaks the downstream exact-match
    comparison and produces false "missing skill" results. A single joint
    call forces the model to use one consistent canonical name across both
    lists, so equivalent skills always line up correctly.
    """
    if not resume_text.strip() or not jd_text.strip():
        return {"resume_skills": [], "jd_skills": []}

    prompt = JOINT_EXTRACTION_PROMPT.format(
        resume_text=resume_text.strip(),
        jd_text=jd_text.strip(),
    )

    response = _model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
        request_options={"timeout": 45},
    )
    
    try:
        parsed = json.loads(response.text)
        return {
            "resume_skills": _dedupe(parsed.get("resume_skills", [])),
            "jd_skills": _dedupe(parsed.get("jd_skills", [])),
        }
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"[ai_service] Failed to parse joint extraction JSON: {e}")
        print(f"[ai_service] Raw response was: {response.text!r}")
        return {"resume_skills": [], "jd_skills": []}


def _dedupe(skills: list) -> list:
    seen = set()
    cleaned = []
    for s in skills:
        key = s.strip().lower()
        if key and key not in seen:
            seen.add(key)
            cleaned.append(s.strip())
    return cleaned

# ---------------------------------------------------------------------------
# Assignment 2: Fit Verdict (Qualified / Almost There / Not Yet)
# ---------------------------------------------------------------------------

VERDICT_PROMPT = """You are an expert technical recruiter giving a fast, honest
fit assessment of a candidate against a job description.

You are given:
- The skills required by the job description
- The skills the candidate's resume shows
- Which required skills matched, which are missing
- The computed match percentage

Task: Return a verdict and exactly three concise reasons supporting it.

Verdict must be exactly one of: "Qualified", "Almost There", "Not Yet"
Guidance (not a strict rule, use judgment near the edges):
- "Qualified": candidate covers nearly all required skills, minor gaps at most
- "Almost There": candidate has a solid core match but meaningful gaps remain
- "Not Yet": candidate is missing multiple important required skills

Each reason should be one short sentence, specific (name actual skills), and
professional in tone -- as if written for a hiring manager, not the candidate.

Return STRICT JSON only, no markdown, no explanation, in this exact shape:
{{"verdict": "Almost There", "reasons": ["reason one", "reason two", "reason three"]}}

Data:
- Required skills (from JD): {jd_skills}
- Candidate skills (from resume): {resume_skills}
- Matched skills: {matched_skills}
- Missing skills: {missing_skills}
- Match percentage: {match_percentage}%
"""


def _allowed_verdicts_for(match_percentage: float) -> list:
    if match_percentage >= 75:
        return ["Qualified", "Almost There"]
    elif match_percentage >= 40:
        return ["Almost There", "Not Yet"]
    else:
        return ["Not Yet"]


def generate_verdict(resume_skills: list, jd_skills: list,
                      matched_skills: list, missing_skills: list,
                      match_percentage: float) -> dict:
    prompt = VERDICT_PROMPT.format(
        jd_skills=", ".join(jd_skills) or "none detected",
        resume_skills=", ".join(resume_skills) or "none detected",
        matched_skills=", ".join(matched_skills) or "none",
        missing_skills=", ".join(missing_skills) or "none",
        match_percentage=match_percentage,
    )

    response = _model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )

    fallback = _fallback_verdict(match_percentage, matched_skills, missing_skills)

    try:
        parsed = json.loads(response.text)
        verdict = parsed.get("verdict", "").strip()
        reasons = [r.strip() for r in parsed.get("reasons", []) if r.strip()][:3]

        allowed = _allowed_verdicts_for(match_percentage)
        if verdict not in allowed or len(reasons) < 1:
            return fallback

        while len(reasons) < 3:
            reasons.append(fallback["reasons"][len(reasons)])

        return {"verdict": verdict, "reasons": reasons}

    except (json.JSONDecodeError, AttributeError, IndexError):
        return fallback


def _fallback_verdict(match_percentage: float, matched_skills: list, missing_skills: list) -> dict:
    allowed = _allowed_verdicts_for(match_percentage)
    verdict = allowed[0]

    reasons = []
    if matched_skills:
        reasons.append(f"Strong overlap in {', '.join(matched_skills[:3])}.")
    else:
        reasons.append("No significant overlap found with the required skills.")

    reasons.append(f"Match score of {match_percentage}% against the job's required skills.")

    if missing_skills:
        reasons.append(f"Missing experience with {', '.join(missing_skills[:3])}.")
    else:
        reasons.append("No missing required skills detected.")

    return {"verdict": verdict, "reasons": reasons}