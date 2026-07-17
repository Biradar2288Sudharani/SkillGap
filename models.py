import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Analysis(db.Model):
    """
    One row = one resume-vs-JD comparison.
    Storing history in MySQL is what turns this from a 'script' into
    a real application -- you can show HR a history page of past runs.
    """

    __tablename__ = "analysis"

    id = db.Column(db.Integer, primary_key=True)

    resume_text = db.Column(db.Text, nullable=False)
    jd_text = db.Column(db.Text, nullable=False)

    # Stored as JSON strings so we don't need extra child tables for a list
    resume_skills = db.Column(db.Text, nullable=False)   # JSON list
    jd_skills = db.Column(db.Text, nullable=False)        # JSON list
    matched_skills = db.Column(db.Text, nullable=False)   # JSON list
    missing_skills = db.Column(db.Text, nullable=False)   # JSON list

    match_percentage = db.Column(db.Float, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "resume_skills": json.loads(self.resume_skills),
            "jd_skills": json.loads(self.jd_skills),
            "matched_skills": json.loads(self.matched_skills),
            "missing_skills": json.loads(self.missing_skills),
            "match_percentage": self.match_percentage,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }
