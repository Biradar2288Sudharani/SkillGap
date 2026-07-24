import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """
    UserMixin (from Flask-Login) supplies the standard properties/methods
    Flask-Login expects (is_authenticated, is_active, get_id, etc.) so we
    don't have to implement them ourselves.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Plain string column, NOT a separate "roles" table -- simple and
    # sufficient for two fixed roles. Never settable by public registration;
    # only ever set directly in the database or by an existing admin.
    role = db.Column(db.String(20), nullable=False, default="user")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    analyses = db.relationship("Analysis", backref="user", lazy=True)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self):
        return self.role == "admin"


class Analysis(db.Model):
    """
    One row = one resume-vs-JD comparison.
    Storing history in MySQL is what turns this from a 'script' into
    a real application -- you can show HR a history page of past runs.
    """

    __tablename__ = "analysis"

    id = db.Column(db.Integer, primary_key=True)

    # Every analysis belongs to whoever ran it. Admins can see all rows;
    # regular users only see rows where user_id matches their own id.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    resume_text = db.Column(db.Text, nullable=False)
    jd_text = db.Column(db.Text, nullable=False)

    resume_skills = db.Column(db.Text, nullable=False)   # JSON list
    jd_skills = db.Column(db.Text, nullable=False)        # JSON list
    matched_skills = db.Column(db.Text, nullable=False)   # JSON list
    missing_skills = db.Column(db.Text, nullable=False)   # JSON list

    match_percentage = db.Column(db.Float, nullable=False)

    verdict = db.Column(db.String(32), nullable=True)     # "Qualified" / "Almost There" / "Not Yet"
    reasons = db.Column(db.Text, nullable=True)            # JSON list of 3 strings

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "owner": self.user.username,
            "resume_skills": json.loads(self.resume_skills),
            "jd_skills": json.loads(self.jd_skills),
            "matched_skills": json.loads(self.matched_skills),
            "missing_skills": json.loads(self.missing_skills),
            "match_percentage": self.match_percentage,
            "verdict": self.verdict,
            "reasons": json.loads(self.reasons) if self.reasons else [],
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }