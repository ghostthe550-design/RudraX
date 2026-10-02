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
import requests
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

# Auto-load .env file from BASE_DIR if present
_env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8-sig") as _f:
        for _line in _f:
            _line = _line.strip().lstrip("\ufeff")
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _k = _k.strip()
                _v = _v.strip().strip('"').strip("'")
                if _k and _k not in os.environ:
                    os.environ[_k] = _v

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
def get_schemes():
    return load_schemes(SCHEMES_FILE)

SCHEMES = get_schemes()


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

    # Helper function for live AI search
    def get_live_schemes_gemini(user_profile):
        if not _GENAI_AVAILABLE:
            return []
        
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return []

        prompt = f"""
You are a government scheme discovery AI. You MUST search the live web (e.g., myscheme.gov.in, gov.in) to find the most relevant active government schemes in India for this applicant:
Age: {user_profile.get('age')}
Gender: {user_profile.get('gender')}
Caste: {user_profile.get('caste_category')}
Education Level (0-6): {user_profile.get('education_level')}
PwD (Divyang): {user_profile.get('is_pwd')}
Repayment Status: {user_profile.get('repayment_status')}
CIBIL Range: {user_profile.get('cibil_range')}

Return a JSON array of scheme objects. Ensure valid JSON.
Schema for each object:
[
  {{
    "scheme_id": "Unique string ID (e.g. LIVE-01)",
    "scheme_name": "Name of the Scheme (Live Search)",
    "issuing_authority": "Authority name + URL citation",
    "loan_category": "Type of loan or benefit",
    "max_loan_amount": 1000000,
    "min_loan_amount": 50000,
    "interest_rate_range": "e.g. 5% - 8%",
    "match_score": 95,
    "status": "Eligible",
    "reasons_pass": ["Why they pass based on live data"],
    "reasons_fail": [],
    "application_steps": ["Step 1..."],
    "contact_and_apply": {{
        "portal_url": "URL to apply",
        "toll_free_helpline": "Phone number",
        "support_email": "Email",
        "designated_physical_office": "Office details"
    }}
  }}
]
IMPORTANT: Return ONLY the JSON array. Do not wrap in markdown.
"""
        model_name = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
        
        if _GENAI_NEW_SDK:
            client = google_genai.Client(api_key=api_key)
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=google_genai.types.GenerateContentConfig(
                        tools=[{"google_search": {}}],
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
            except Exception:
                # Fallback if tools argument fails
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=google_genai.types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
            text = response.text
        else:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=api_key)
            model = genai_legacy.GenerativeModel(model_name=model_name)
            resp = model.generate_content(prompt)
            text = resp.text

        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        data = json.loads(text)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "schemes" in data:
            return data["schemes"]
        return []

    # Execute matching
    match_results = []
    
    # Try Live Gemini Search First
    try:
        live_results = get_live_schemes_gemini(user)
        if live_results and isinstance(live_results, list) and len(live_results) > 0:
            match_results = live_results
    except Exception as e:
        print(f"Live search failed: {e}")
        pass
        
    # Fallback to local DB
    if not match_results:
        print("Falling back to local static DB.")
        match_results = run_engine(user, get_schemes())

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
    return jsonify({"schemes": get_schemes()})


# ---------------------------------------------------------------------------
# AI Loan Assistant Chat API
# ---------------------------------------------------------------------------
_CHATBOT_SYSTEM_PROMPT = """You are UDYAMSetu AI — a knowledgeable, empathetic loan and scheme guidance assistant
specialised in ALL Indian government schemes (Central and State level). Answer questions related to
scheme eligibility, documentation, subsidies, and benefits for citizens and businesses. Be concise, warm, and use simple language.

KEY GUIDANCE YOU MUST APPLY:
- You possess broad knowledge of ALL government schemes in India (e.g., PM-EGP, PM-SVANidhi, Stand-Up India, Mudra Yojana, PM Kisan, Ayushman Bharat, Startup India, NSFDC, etc.).
- Help users navigate through the vast landscape of schemes by asking clarifying questions about their profile if needed.
- Reassure applicants that there are schemes available for all sectors, genders, and social categories.
- Encourage applicants to provide accurate information.
- If you don't know the exact details of a niche or newly announced scheme, provide the best available general guidance and direct users to official portals like myscheme.gov.in or india.gov.in.

ALWAYS end your response with a reassuring, action-oriented closing sentence.
"""

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """AI loan assistant endpoint with fallbacks.
    Expects JSON: { "message": "user query", "history": [{"role": "user"|"model", "parts": ["..."]}, ...] }
    Returns JSON: { "reply": "...", "error": null }
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    groq_api_key = os.environ.get("GROQ_API_KEY")
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")

    if not any([api_key, groq_api_key, openrouter_api_key]):
        return jsonify({"reply": None, "error": "No AI API keys configured on server."}), 503

    try:
        body = request.get_json(force=True)
        user_message = (body.get("message") or "").strip()
        history = body.get("history") or []

        if not user_message:
            return jsonify({"reply": None, "error": "Empty message."}), 400

        # Models ordered by priority (fallback mechanism)
        models_to_try = [
            {"provider": "gemini", "model": "gemini-3.8-flash"},
            {"provider": "gemini", "model": "gemini-3.6-flash"},
            {"provider": "gemini", "model": "gemini-3.5-flash"},
            {"provider": "groq", "model": "llama-3.3-70b-versatile"}, # Assuming this as GPT-OSS equivalent
            {"provider": "openrouter", "model": "openrouter/auto"}
        ]

        reply_text = None
        last_error = None

        for m in models_to_try:
            provider = m["provider"]
            model_name = m["model"]
            try:
                if provider == "gemini":
                    if not _GENAI_AVAILABLE or not api_key:
                        continue
                    
                    if _GENAI_NEW_SDK:
                        client = google_genai.Client(api_key=api_key)
                        contents = []
                        for h in history:
                            if h.get("role") in ("user", "model") and h.get("parts"):
                                contents.append({"role": h["role"], "parts": [{"text": h["parts"][0]}]})
                        contents.append({"role": "user", "parts": [{"text": user_message}]})
                        
                        response = client.models.generate_content(
                            model=model_name,
                            contents=contents,
                            config=google_genai.types.GenerateContentConfig(
                                system_instruction=_CHATBOT_SYSTEM_PROMPT,
                                temperature=0.5,
                                max_output_tokens=600,
                            )
                        )
                        reply_text = response.text
                        break
                    else:
                        import google.generativeai as genai_legacy  # noqa: PLC0415
                        import warnings
                        genai_legacy.configure(api_key=api_key)
                        model = genai_legacy.GenerativeModel(
                            model_name=model_name,
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
                        break

                elif provider in ["groq", "openrouter"]:
                    current_key = groq_api_key if provider == "groq" else openrouter_api_key
                    if not current_key:
                        continue
                        
                    url = "https://api.groq.com/openai/v1/chat/completions" if provider == "groq" else "https://openrouter.ai/api/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {current_key}",
                        "Content-Type": "application/json"
                    }
                    if provider == "openrouter":
                        headers["HTTP-Referer"] = "http://localhost:5000"
                        headers["X-Title"] = "UDYAMSetu"
                        
                    messages = [{"role": "system", "content": _CHATBOT_SYSTEM_PROMPT}]
                    for h in history:
                        if h.get("role") in ("user", "model") and h.get("parts"):
                            role = "assistant" if h["role"] == "model" else "user"
                            messages.append({"role": role, "content": h["parts"][0]})
                    messages.append({"role": "user", "content": user_message})
                    
                    payload = {
                        "model": model_name,
                        "messages": messages,
                        "temperature": 0.5,
                        "max_tokens": 600
                    }
                    
                    response = requests.post(url, headers=headers, json=payload, timeout=15)
                    response.raise_for_status()
                    reply_text = response.json()["choices"][0]["message"]["content"]
                    break

            except Exception as e:
                last_error = str(e)
                print(f"Fallback warning: {provider} {model_name} failed - {e}")
                continue

        if reply_text:
            return jsonify({"reply": reply_text, "error": None})
        else:
            return jsonify({"reply": None, "error": f"All AI models failed. Last error: {last_error}"}), 503

    except Exception as exc:  # noqa: BLE001
        return jsonify({"reply": None, "error": str(exc)}), 500



# ---------------------------------------------------------------------------
# AI Natural Language Scheme Search API
# ---------------------------------------------------------------------------
@app.route("/api/ai-search", methods=["POST"])
def api_ai_search():
    """
    Accepts a free-text query (e.g. 'schemes for women entrepreneurs in SC category')
    and returns matched schemes from the local DB, ranked by AI relevance.

    Expects JSON: { "query": "natural language search query" }
    Returns JSON: { "results": [...], "query_interpretation": "...", "error": null }
    """
    try:
        body = request.get_json(force=True)
        query = (body.get("query") or "").strip()

        if not query:
            return jsonify({"results": [], "query_interpretation": "", "error": "Empty query."}), 400

        # Build a compact scheme catalogue for the prompt (scheme_id + name + key fields)
        active_schemes = get_schemes()
        scheme_catalogue = []
        for s in active_schemes:
            rules = s.get("eligibility_rules", {})
            scheme_catalogue.append({
                "scheme_id": s.get("scheme_id"),
                "scheme_name": s.get("scheme_name"),
                "loan_category": s.get("loan_category"),
                "issuing_authority": s.get("issuing_authority"),
                "max_loan_amount": s.get("max_loan_amount"),
                "min_loan_amount": s.get("min_loan_amount"),
                "interest_rate_range": s.get("interest_rate_range"),
                "purpose": s.get("purpose"),
                "allowed_genders": rules.get("allowed_genders", []),
                "allowed_castes": rules.get("allowed_castes", []),
                "min_age": rules.get("min_age"),
                "max_age": rules.get("max_age"),
                "pwd_eligible": rules.get("pwd_eligible"),
                "special_conditions": rules.get("special_conditions", []),
            })

        prompt = f"""You are a government scheme matching AI for India.
A user has typed this search query: "{query}"

Here is the catalogue of available schemes as JSON:
{json.dumps(scheme_catalogue, indent=2)}

TASK:
1. Interpret the user's query to understand what kind of scheme they are looking for.
2. Select the most relevant schemes (up to 6) from the catalogue above that match the query.
3. For each selected scheme, assign a relevance match_score (0-100) based on how well it fits.
4. Provide a short, friendly human-readable interpretation of the query (1 sentence).

Return a JSON object with this exact schema:
{{
  "query_interpretation": "Brief 1-sentence interpretation of what the user is looking for",
  "matched_ids": [
    {{
      "scheme_id": "ID from catalogue",
      "match_score": 85,
      "reasons": ["Reason 1 why this scheme matches", "Reason 2"]
    }}
  ]
}}

IMPORTANT:
- Only include scheme_ids that exist in the catalogue above.
- matched_ids must be sorted by match_score descending.
- Return ONLY the JSON object. No markdown fences.
"""

        query_interpretation = f'Showing results for: "{query}"'
        matched_ids = []

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        if _GENAI_AVAILABLE and api_key:
            model_name = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
            try:
                if _GENAI_NEW_SDK:
                    client = google_genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=google_genai.types.GenerateContentConfig(
                            temperature=0.2,
                            response_mime_type="application/json"
                        )
                    )
                    raw = response.text
                else:
                    import google.generativeai as genai_legacy
                    genai_legacy.configure(api_key=api_key)
                    model_obj = genai_legacy.GenerativeModel(model_name=model_name)
                    resp = model_obj.generate_content(prompt)
                    raw = resp.text

                raw = raw.strip()
                if raw.startswith("```json"):
                    raw = raw[7:]
                if raw.startswith("```"):
                    raw = raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

                ai_result = json.loads(raw)
                query_interpretation = ai_result.get("query_interpretation", query_interpretation)
                matched_ids = ai_result.get("matched_ids", [])

            except Exception as e:
                print(f"AI search Gemini error: {e}")
                # Fall through to keyword fallback

        # If AI returned nothing or failed, keyword fallback
        if not matched_ids:
            q_lower = query.lower()
            q_words = [w for w in q_lower.split() if len(w) > 3]
            scored_matches = []
            for s in active_schemes:
                searchable = " ".join([
                    s.get("scheme_name", ""),
                    s.get("loan_category", ""),
                    s.get("issuing_authority", ""),
                    s.get("purpose", ""),
                    " ".join(s.get("eligibility_rules", {}).get("special_conditions", []))
                ]).lower()
                overlap = sum(1 for word in q_words if word in searchable)
                if overlap > 0:
                    scored_matches.append({
                        "scheme_id": s["scheme_id"],
                        "match_score": min(95, 60 + overlap * 10),
                        "overlap": overlap,
                        "reasons": ["Keyword match with your search query"]
                    })
            scored_matches.sort(key=lambda x: x["overlap"], reverse=True)
            matched_ids = scored_matches[:6]

        # Build full scheme objects for the matched IDs
        scheme_map = {s["scheme_id"]: s for s in active_schemes}
        results = []
        for match in matched_ids:
            sid = match.get("scheme_id")
            scheme = scheme_map.get(sid)
            if scheme:
                enriched = dict(scheme)
                enriched["match_score"] = match.get("match_score", 70)
                enriched["reasons_pass"] = match.get("reasons", [])
                enriched["status"] = "Eligible"
                results.append(enriched)

        return jsonify({
            "results": results,
            "query_interpretation": query_interpretation,
            "error": None
        })

    except Exception as exc:
        return jsonify({"results": [], "query_interpretation": "", "error": str(exc)}), 500


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
