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
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from jinja2 import ChoiceLoader, FileSystemLoader
from engine import load_schemes, run_engine

try:
    from google import genai as google_genai
    _GENAI_AVAILABLE = True
    _GENAI_NEW_SDK = True
except ImportError:
    try:
        import google.generativeai as genai_legacy
        _GENAI_AVAILABLE = True
        _GENAI_NEW_SDK = False
    except ImportError:
        _GENAI_AVAILABLE = False
        _GENAI_NEW_SDK = False


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
        repayment_status = request.form.get("repayment_status", "").strip()
        cibil_range = request.form.get("cibil_range", "").strip()  # Optional — never blocks

        # Validate all required fields; cibil_range is intentionally excluded
        if not age_str or not gender or not caste_category or not edu_str:
            return redirect(url_for("index", error="invalid_input"))
        if is_pwd_val is None or not repayment_status:
            return redirect(url_for("index", error="invalid_input"))

        user = {
            "age": int(age_str),
            "gender": gender,
            "caste_category": caste_category,
            "education_level": int(edu_str),
            "is_pwd": is_pwd_val == "Yes",
            "repayment_status": repayment_status,
            "cibil_range": cibil_range,  # passed through for display; engine ignores it for scoring
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


# ---------------------------------------------------------------------------
# AI Loan Assistant Chat API
# ---------------------------------------------------------------------------
_CHATBOT_SYSTEM_PROMPT = """You are UDYAMSetu AI — a knowledgeable, empathetic loan guidance assistant
specialised in Indian government concessional finance schemes. Answer only questions related to
loan eligibility, documentation, and scheme details. Be concise, warm, and use simple language.

KEY SCHEME FACTS YOU MUST APPLY ACCURATELY:

## Stand-Up India Scheme
- Administered by SIDBI / Lead district banks under RBI mandate.
- Target: SC, ST, or Women entrepreneurs setting up a GREENFIELD enterprise only.
- Loan range: ₹10 Lakh to ₹1 Crore (composite term loan + working capital).
- Collateral: Credit Guarantee Fund Trust for Micro & Small Enterprises (CGTMSE) covers.
- CRITICAL: Having an active home loan, vehicle loan, or personal loan does NOT disqualify.
  Only current NPA / loan write-off status disqualifies. Applicants with regular running loans
  (even home loans) are fully eligible.
- Moratorium: typically 18 months.
- Apply via: standupmitra.in or designated lead bank branch.

## NSFDC (National Scheduled Castes Finance & Development Corporation)
- Target: SC beneficiaries ONLY.
- Annual family income ceiling: Urban ≤ ₹3 Lakh; Rural ≤ ₹2 Lakh (poverty line × 3).
  (Many state SCAs use a combined ceiling of ≤ ₹5 Lakh — clarify with local SCA.)
- Loan range: micro-finance ₹20,000 – ₹1.4 Lakh (MFS) to term loans up to ₹50 Lakh (TLS).
- Interest: 5% – 8% p.a. channelled through State Channelising Agencies (SCAs).
- Clean repayment track record is required; minor past delays may be reviewed case-by-case.
- Current NPA disqualifies.

## GENERAL GUIDANCE
- Always reassure applicants that having standard running loans (home, auto, personal) does NOT
  prevent them from applying — only active NPA / write-off status does.
- Encourage applicants to provide accurate information; there is no penalty for disclosing
  legitimate existing loans.
- For CIBIL scores: a score of 700+ is ideal, but many concessional schemes are
  CIBIL-score-relaxed for SC/ST/Women under priority-sector lending mandates.
- If you don't know the answer, say so clearly and direct users to the relevant helpline or portal.

ALWAYS end your response with a reassuring, action-oriented closing sentence.
"""

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """AI loan assistant endpoint.
    Expects JSON: { "message": "user query", "history": [{"role": "user"|"model", "parts": ["..."]}, ...] }
    Returns JSON: { "reply": "...", "error": null }
    """
    if not _GENAI_AVAILABLE:
        return jsonify({"reply": None, "error": "AI assistant unavailable: google-genai not installed."}), 503

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return jsonify({"reply": None, "error": "API key not configured on server."}), 503

    try:
        body = request.get_json(force=True)
        user_message = (body.get("message") or "").strip()
        history = body.get("history") or []

        if not user_message:
            return jsonify({"reply": None, "error": "Empty message."}), 400

        if _GENAI_NEW_SDK:
            # ---- New google-genai SDK ----
            client = google_genai.Client(api_key=api_key)
            # Build contents list: system turn + history + current user message
            contents = []
            for h in history:
                if h.get("role") in ("user", "model") and h.get("parts"):
                    contents.append({"role": h["role"], "parts": [{"text": h["parts"][0]}]})
            contents.append({"role": "user", "parts": [{"text": user_message}]})

            gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            response = client.models.generate_content(
                model=gemini_model,
                contents=contents,
                config=google_genai.types.GenerateContentConfig(
                    system_instruction=_CHATBOT_SYSTEM_PROMPT,
                    temperature=0.5,
                    max_output_tokens=600,
                )
            )
            reply_text = response.text
        else:
            # ---- Legacy google.generativeai SDK (fallback) ----
            import google.generativeai as genai_legacy  # noqa: PLC0415
            import warnings
            genai_legacy.configure(api_key=api_key)
            gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            model = genai_legacy.GenerativeModel(
                model_name=gemini_model,
                system_instruction=_CHATBOT_SYSTEM_PROMPT
            )
            chat = model.start_chat(history=[
                {"role": h["role"], "parts": [h["parts"][0]]}
                for h in history
                if h.get("role") in ("user", "model") and h.get("parts")
            ])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                resp = chat.send_message(user_message)
            reply_text = resp.text

        return jsonify({"reply": reply_text, "error": None})

    except Exception as exc:  # noqa: BLE001
        return jsonify({"reply": None, "error": str(exc)}), 500



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


@app.route("/chatbot.js", methods=["GET"])
def serve_chatbot_js():
    """Serves the floating AI loan assistant widget script."""
    static_dir = os.path.join(BASE_DIR, "static")
    return send_from_directory(static_dir, "chatbot.js", mimetype="application/javascript")


if __name__ == "__main__":
    print(" * Starting UDYAMSetu Concessional Finance Server...")
    print(f" * Loaded {len(SCHEMES)} government schemes from schemes.json")
    print(" * Accessible at http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
