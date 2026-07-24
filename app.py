import json
from flask import Flask, render_template, request, jsonify
from config import Config
from models import db, Analysis
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from models import db, User, Analysis
from services.ai_service import extract_skills_from_both, generate_verdict
from services.matcher import compare_skills
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from services.file_parser import extract_text_from_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

login_manager = LoginManager()
login_manager.login_view = "login"  # where @login_required will redirect to

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    with app.app_context():
        db.create_all()
    register_routes(app)
    return app

@login_manager.user_loader
def load_user(user_id):
    # Flask-Login calls this on every request to reload the logged-in user
    # from the id stored in their session cookie.
    return User.query.get(int(user_id))

def register_routes(app):
    @app.route("/")
    @login_required
    def index():
        return render_template("index.html", user=current_user)

    @app.route("/analyze", methods=["POST"])
    @login_required
    def analyze():
        try:
            resume_text = request.form.get("resume_text", "").strip()
            jd_text = request.form.get("jd_text", "").strip()
            if "resume_file" in request.files and request.files["resume_file"].filename:
                resume_text = extract_text_from_file(request.files["resume_file"])
            if "jd_file" in request.files and request.files["jd_file"].filename:
                jd_text = extract_text_from_file(request.files["jd_file"])
            if not resume_text or not jd_text:
                return jsonify({"error": "Both resume and job description are required."}), 400
            extracted = extract_skills_from_both(resume_text, jd_text)
            resume_skills = extracted["resume_skills"]
            jd_skills = extracted["jd_skills"]
            if not jd_skills:
                return jsonify({"error": "Could not detect any skills in the job description."}), 422
            result = compare_skills(resume_skills, jd_skills)
            verdict_result = generate_verdict(
                resume_skills=resume_skills,
                jd_skills=jd_skills,
                matched_skills=result["matched_skills"],
                missing_skills=result["missing_skills"],
                match_percentage=result["match_percentage"],
            )
            record = Analysis(
                user_id=current_user.id,
                resume_text=resume_text,
                jd_text=jd_text,
                resume_skills=json.dumps(resume_skills),
                jd_skills=json.dumps(jd_skills),
                matched_skills=json.dumps(result["matched_skills"]),
                missing_skills=json.dumps(result["missing_skills"]),
                match_percentage=result["match_percentage"],
                verdict=verdict_result["verdict"],
                reasons=json.dumps(verdict_result["reasons"]),
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
                "verdict": verdict_result["verdict"],
                "reasons": verdict_result["reasons"],
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

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "GET":
            return render_template("register.html")

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("That username is already taken.")
            return redirect(url_for("register"))

        # Public registration ALWAYS creates a normal "user" -- never an
        # admin. Admin accounts are only ever created directly in the
        # database, so nobody can grant themselves elevated access.
        new_user = User(username=username, role="user")
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()        

        flash("Account created! Please log in.")
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Invalid username or password.")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("index"))

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

app = create_app()
if __name__ == "__main__":
    app.run(debug=True, port=5000)