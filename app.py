"""
app.py
UDYAMSetu — Concessional Finance Navigator & Eligibility Shield
Flask Web Backend

Serves the unified platform pages:
  - index.html     : Applicant profile input form
  - results.html   : Scheme eligibility compatibility dashboard
  - compare.html   : Multi-channel lender comparison
  - navigator.html : Interactive scheme-aware EMI calculator & geo-spatial partner locator
  - /api/schemes   : Dynamic JSON API exposing schemes database

Connects frontend profile submission to the deterministic rules engine (engine.py).
"""

import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from jinja2 import ChoiceLoader, FileSystemLoader
from engine import load_schemes, run_engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure Flask with static directory and robust dual-path Jinja loader
# so templates are found both in templates/ and in the workspace root.
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static"
)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(BASE_DIR, "templates")),
    FileSystemLoader(BASE_DIR),
])

# ---------------------------------------------------------------
# Load the scheme database once on startup using absolute file path.
# ---------------------------------------------------------------
SCHEMES_FILE = os.path.join(BASE_DIR, "schemes.json")
SCHEMES = load_schemes(SCHEMES_FILE)


@app.route("/", methods=["GET"])
def index():
    """Renders the applicant profile input form."""
    return render_template("index.html")


@app.route("/results", methods=["GET", "POST"])
def results():
    """
    Handles form submission from index.html and renders compatibility results.
    Redirects GET requests to the profile form to prevent 405 errors.
    """
    if request.method == "GET":
        return redirect(url_for("index"))

    try:
        age_str = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        caste_category = request.form.get("caste_category", "").strip()
        edu_str = request.form.get("education_level", "").strip()
        is_pwd_val = request.form.get("is_pwd")
        loan_def_val = request.form.get("has_loan_default")

        # Validate that no required field was left unselected or blank
        if not age_str or not gender or not caste_category or not edu_str:
            return redirect(url_for("index", error="invalid_input"))
        if is_pwd_val is None or loan_def_val is None:
            return redirect(url_for("index", error="invalid_input"))

        user = {
            "age": int(age_str),
            "gender": gender,
            "caste_category": caste_category,
            "education_level": int(edu_str),
            "is_pwd": is_pwd_val == "Yes",
            "has_loan_default": loan_def_val == "Yes",
        }
    except (ValueError, TypeError):
        return redirect(url_for("index", error="invalid_input"))

    # Sanity range check for age
    if not (18 <= user["age"] <= 99):
        return redirect(url_for("index", error="age_out_of_range"))

    # Execute deterministic matching engine against scheme repository
    match_results = run_engine(user, SCHEMES)

    return render_template("results.html", user=user, results=match_results)


@app.route("/navigator", methods=["GET"])
def navigator():
    """Renders the EMI Calculator and Geo-Spatial Channel Partner Locator."""
    return render_template("navigator.html")


@app.route("/compare", methods=["GET"])
def compare():
    """Renders the Multi-Channel Lender Comparison table and filter tools."""
    return render_template("compare.html")


@app.route("/api/schemes", methods=["GET"])
def api_schemes():
    """JSON API endpoint exposing active government loan schemes."""
    return jsonify({"schemes": SCHEMES})


@app.route("/style.css", methods=["GET"])
def serve_root_css():
    """Fallback route to ensure style.css serves properly under any link reference."""
    static_dir = os.path.join(BASE_DIR, "static")
    if os.path.exists(os.path.join(static_dir, "style.css")):
        return send_from_directory(static_dir, "style.css", mimetype="text/css")
    return send_from_directory(BASE_DIR, "style.css", mimetype="text/css")


@app.route("/i18n.js", methods=["GET"])
def serve_root_i18n():
    """Fallback route to ensure i18n.js serves properly under any link reference."""
    static_dir = os.path.join(BASE_DIR, "static")
    if os.path.exists(os.path.join(static_dir, "i18n.js")):
        return send_from_directory(static_dir, "i18n.js", mimetype="application/javascript")
    return send_from_directory(BASE_DIR, "i18n.js", mimetype="application/javascript")


if __name__ == "__main__":
    print(" * Starting UDYAMSetu Concessional Finance Server...")
    print(f" * Loaded {len(SCHEMES)} government schemes from schemes.json")
    print(" * Accessible at http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
