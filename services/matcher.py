"""
Pure Python, zero AI here on purpose -- once we have clean skill lists
from ai_service.py, comparison is just set logic. Keeping this separate
from the AI call means it's independently unit-testable.
"""

def compare_skills(resume_skills: list, jd_skills: list) -> dict:
    # Case-insensitive matching, but we display the JD's original casing
    resume_lookup = {s.lower(): s for s in resume_skills}
    jd_lookup = {s.lower(): s for s in jd_skills}
    matched = [jd_lookup[key] for key in jd_lookup if key in resume_lookup]
    missing = [jd_lookup[key] for key in jd_lookup if key not in resume_lookup]
    total_required = len(jd_skills)
    match_percentage = round((len(matched) / total_required) * 100, 1) if total_required else 0.0
    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": match_percentage,
    }
