# Skill Gap Checker

Compares a candidate's resume against a job description, using AI to extract
and normalize skills, then a deterministic comparison to produce:
- Matched Skills
- Missing Skills
- Match Percentage

## Stack
Flask + MySQL (SQLAlchemy) + HTML/CSS/JS + OpenAI API

---

## 1. Setup

```bash
cd skillgap_checker
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create your `.env` file from the template:

```bash
cp .env.example .env
```

Then edit `.env` and fill in:
- Your MySQL credentials (`MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`)
- Your `OPENAI_API_KEY` (from https://platform.openai.com/api-keys — new accounts
  get some free trial credit, enough for lots of testing)

Create the database (either option works):

**Option A — let the app create it:**
Just run the app; `db.create_all()` in `app.py` creates the `analysis` table
automatically on first run (you still need the database itself to exist —
create an empty one in MySQL first: `CREATE DATABASE skillgap_db;`)

**Option B — run the schema file yourself:**
```bash
mysql -u root -p < schema.sql
```

## 2. Run it

```bash
python app.py
```

Visit **http://localhost:5000**

---

## 3. How it works (for your interview walkthrough)

**Flow:** paste or upload resume + JD → `/analyze` → AI extracts skills →
Python compares them → result shown + saved to MySQL.

1. **`services/ai_service.py`** — sends the raw resume text and raw JD text to
   OpenAI, one call each, with a strict prompt asking for a normalized JSON
   list of skills (so "ReactJS" / "React.js" / "React" all collapse to one
   canonical entry). This is the only part of the app that touches AI.

2. **`services/matcher.py`** — pure Python, no AI. Takes the two clean skill
   lists and does case-insensitive set comparison to get matched/missing,
   then computes `match % = matched / total_JD_skills * 100`.

   *Why split it this way?* The AI is good at the messy, ambiguous job
   (turning free text into a clean list) but comparison/scoring should be
   deterministic and testable — you don't want an LLM "deciding" a candidate's
   match score differently each run. This separation is a genuinely good
   thing to say out loud in an interview.

3. **`services/file_parser.py`** — lets the user upload a `.pdf`/`.docx`/`.txt`
   instead of pasting text; extracts raw text so the rest of the pipeline
   doesn't care whether the input came from a paste box or a file.

4. **`models.py`** — every analysis is saved to MySQL (`analysis` table):
   resume/JD text, extracted skills, matched/missing, percentage, timestamp.
   This powers the "Recent Analyses" history table on the page — and shows
   you built something with real persistence, not just a one-shot script.

5. **`app.py`** — Flask routes:
   - `GET /` → renders the page
   - `POST /analyze` → runs the full pipeline, returns JSON, saves to DB
   - `GET /history` → returns the last 20 analyses as JSON

6. **Frontend** — vanilla HTML/CSS/JS. Two textareas (or file upload), one
   button, results rendered as a percentage ring + matched/missing skill tags,
   plus a history table fetched from `/history`.

## 4. Things you can extend if asked "what would you add next?"
- Weight skills as required vs. nice-to-have (parse "must have" vs "preferred"
  language in the JD)
- Suggested resume rewrites for near-miss skills
- User accounts, so history is per-recruiter/per-user instead of global
- Deploy it (Render/Railway for the app + a managed MySQL instance)
