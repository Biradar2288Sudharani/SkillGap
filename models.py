import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Analysis(db.Model):
    __tablename__ = "analysis"

    id = db.Column(db.Integer, primary_key=True)

    resume_text = db.Column(db.Text, nullable=False)
    jd_text = db.Column(db.Text, nullable=False)

    resume_skills = db.Column(db.Text, nullable=False)
    jd_skills = db.Column(db.Text, nullable=False)
    matched_skills = db.Column(db.Text, nullable=False)
    missing_skills = db.Column(db.Text, nullable=False)

    match_percentage = db.Column(db.Float, nullable=False)

    verdict = db.Column(db.String(32), nullable=True)
    reasons = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "resume_skills": json.loads(self.resume_skills),
            "jd_skills": json.loads(self.jd_skills),
            "matched_skills": json.loads(self.matched_skills),
            "missing_skills": json.loads(self.missing_skills),
            "match_percentage": self.match_percentage,
            "verdict": self.verdict,
            "reasons": json.loads(self.reasons) if self.reasons else [],
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }