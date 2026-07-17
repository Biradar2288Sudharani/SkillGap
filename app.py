import json
from flask import Flask, render_template, request, jsonify

from config import Config
from models import db, Analysis
from services.ai_service import extract_skills_from_both
from services.matcher import compare_skills
from services.file_parser import extract_text_from_file


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()  # creates the `analysis` table if it doesn't exist

    register_routes(app)
    return app


def register_routes(app):

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/analyze", methods=["POST"])
    def analyze():
        """
        Accepts EITHER pasted text fields (resume_text, jd_text)
        OR uploaded files (resume_file, jd_file) via multipart/form-data.
        """
        try:
            resume_text = request.form.get("resume_text", "").strip()
            jd_text = request.form.get("jd_text", "").strip()

            # File upload overrides pasted text if provided
            if "resume_file" in request.files and request.files["resume_file"].filename:
                resume_text = extract_text_from_file(request.files["resume_file"])

            if "jd_file" in request.files and request.files["jd_file"].filename:
                jd_text = extract_text_from_file(request.files["jd_file"])

            if not resume_text or not jd_text:
                return jsonify({"error": "Both resume and job description are required."}), 400

            # Step 1: AI extracts normalized skill lists
            extracted = extract_skills_from_both(resume_text, jd_text)
            resume_skills = extracted["resume_skills"]
            jd_skills = extracted["jd_skills"]

            if not jd_skills:
                return jsonify({"error": "Could not detect any skills in the job description."}), 422

            # Step 2: plain Python does the deterministic comparison
            result = compare_skills(resume_skills, jd_skills)

            # Step 3: persist to MySQL for history
            record = Analysis(
                resume_text=resume_text,
                jd_text=jd_text,
                resume_skills=json.dumps(resume_skills),
                jd_skills=json.dumps(jd_skills),
                matched_skills=json.dumps(result["matched_skills"]),
                missing_skills=json.dumps(result["missing_skills"]),
                match_percentage=result["match_percentage"],
            )
            db.session.add(record)
            db.session.commit()

            return jsonify({
                "id": record.id,
                "resume_skills": resume_skills,
                "jd_skills": jd_skills,
                "matched_skills": result["matched_skills"],
                "missing_skills": result["missing_skills"],
                "match_percentage": result["match_percentage"],
            })

        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            app.logger.exception("Analysis failed")
            return jsonify({"error": "Something went wrong while analyzing. Please try again."}), 500

    @app.route("/history", methods=["GET"])
    def history():
        records = Analysis.query.order_by(Analysis.created_at.desc()).limit(20).all()
        return jsonify([r.to_dict() for r in records])


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
