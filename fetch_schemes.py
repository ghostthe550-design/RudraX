"""
fetch_schemes.py
UDYAMSetu -- Live Scheme Data Pipeline (Fetch Stage)

Offline admin pipeline: searches official government portals via Gemini's
live web grounding capability to discover new scheme candidates, validates
each one against the full schemes.json schema, cross-checks against existing
schemes.json for duplicates, and writes accepted candidates to
pending_review.json for human review.

NEVER writes directly to schemes.json.

CLI usage:
  python fetch_schemes.py                           # fetch from default watchlist
  python fetch_schemes.py --query "agriculture loan scheme SC farmers"
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Mirror the exact dual-path Gemini SDK import pattern from app.py
# ---------------------------------------------------------------------------
try:
    from google import genai as google_genai
    _GENAI_AVAILABLE = True
    _GENAI_NEW_SDK = True
except ImportError:
    try:
        import google.generativeai as genai_legacy  # noqa: F401
        _GENAI_AVAILABLE = True
        _GENAI_NEW_SDK = False
    except ImportError:
        _GENAI_AVAILABLE = False
        _GENAI_NEW_SDK = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Auto-load .env file from BASE_DIR or current directory
for _p in [os.path.join(BASE_DIR, ".env"), os.path.join(os.path.dirname(BASE_DIR), ".env"), ".env"]:
    if os.path.exists(_p):
        with open(_p, "r", encoding="utf-8-sig") as _f:
            for _line in _f:
                _line = _line.strip().lstrip("\ufeff")
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    _k = _k.strip()
                    _v = _v.strip().strip('"').strip("'")
                    if _k and _k not in os.environ:
                        os.environ[_k] = _v

# ---------------------------------------------------------------------------
# File paths (all relative to the project root alongside app.py)
# ---------------------------------------------------------------------------
SCHEMES_FILE = os.path.join(BASE_DIR, "schemes.json")
PENDING_FILE = os.path.join(BASE_DIR, "pending_review.json")

# ---------------------------------------------------------------------------
# Default watchlist -- queries run when no --query flag is given
# ---------------------------------------------------------------------------
DEFAULT_WATCHLIST = [
    "SC ST welfare department concessional loan scheme India",
    "NSTFDC tribal finance loan scheme India",
    "PM SVANidhi street vendor micro loan scheme",
    "Startup India seed fund scheme DPIIT",
    "KVIC Khadi handloom artisan loan subsidy scheme",
    "NBCFDC OBC backward classes finance loan scheme",
    "NMDFC minority communities micro finance loan scheme",
    "WDC Mahila e-Haat women entrepreneur digital scheme",
    "agriculture allied activity SC ST loan scheme NABARD",
    "PwD handicapped entrepreneur loan scheme India",
]

# ---------------------------------------------------------------------------
# Required top-level fields in a valid scheme object
# ---------------------------------------------------------------------------
REQUIRED_TOP_LEVEL = [
    "scheme_id", "scheme_name", "issuing_authority", "loan_category",
    "max_loan_amount", "min_loan_amount", "interest_rate_range",
    "purpose", "eligibility_rules", "contact_and_apply", "application_steps",
]

# Required sub-keys inside eligibility_rules
REQUIRED_ELIGIBILITY_KEYS = [
    "min_age", "max_age", "allowed_genders", "allowed_castes",
    "min_education_level", "allow_defaulters", "pwd_eligible",
]

# Required sub-keys inside contact_and_apply
REQUIRED_CONTACT_KEYS = [
    "portal_url", "toll_free_helpline", "support_email",
    "designated_physical_office",
]


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------
def validate_scheme(obj):
    """
    Returns a list of validation error strings.
    An empty list means the object is valid.
    """
    errors = []

    # Top-level required fields
    for field in REQUIRED_TOP_LEVEL:
        if field not in obj or obj[field] is None:
            errors.append("Missing or null top-level field: '{}'".format(field))

    # eligibility_rules sub-keys
    rules = obj.get("eligibility_rules")
    if not isinstance(rules, dict):
        errors.append("'eligibility_rules' must be a JSON object")
    else:
        for key in REQUIRED_ELIGIBILITY_KEYS:
            if key not in rules or rules[key] is None:
                errors.append("Missing or null eligibility_rules.{}".format(key))
        if "min_age" in rules and not isinstance(rules["min_age"], (int, float)):
            errors.append("eligibility_rules.min_age must be a number")
        if "max_age" in rules and not isinstance(rules["max_age"], (int, float)):
            errors.append("eligibility_rules.max_age must be a number")
        if "allowed_genders" in rules and not isinstance(rules["allowed_genders"], list):
            errors.append("eligibility_rules.allowed_genders must be an array")
        if "allowed_castes" in rules and not isinstance(rules["allowed_castes"], list):
            errors.append("eligibility_rules.allowed_castes must be an array")
        if "min_education_level" in rules and not isinstance(rules["min_education_level"], (int, float)):
            errors.append("eligibility_rules.min_education_level must be a number")
        if "allow_defaulters" in rules and not isinstance(rules["allow_defaulters"], bool):
            errors.append("eligibility_rules.allow_defaulters must be a boolean")
        if "pwd_eligible" in rules and not isinstance(rules["pwd_eligible"], bool):
            errors.append("eligibility_rules.pwd_eligible must be a boolean")

    # contact_and_apply sub-keys
    contact = obj.get("contact_and_apply")
    if not isinstance(contact, dict):
        errors.append("'contact_and_apply' must be a JSON object")
    else:
        for key in REQUIRED_CONTACT_KEYS:
            if key not in contact or contact[key] is None:
                errors.append("Missing or null contact_and_apply.{}".format(key))

    # application_steps must be a non-empty list
    steps = obj.get("application_steps")
    if not isinstance(steps, list) or len(steps) == 0:
        errors.append("'application_steps' must be a non-empty array")

    # Numeric amount fields
    for amt_field in ("max_loan_amount", "min_loan_amount"):
        if amt_field in obj and not isinstance(obj[amt_field], (int, float)):
            errors.append("'{}' must be a number".format(amt_field))

    return errors


# ---------------------------------------------------------------------------
# Load existing schemes.json -> build lookup maps
# ---------------------------------------------------------------------------
def load_existing_schemes():
    """
    Returns:
      id_map   : { scheme_id -> scheme_name }
      name_map : { lowercase(scheme_name) -> scheme_id }
    """
    if not os.path.exists(SCHEMES_FILE):
        return {}, {}
    with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    schemes = data.get("schemes", [])
    id_map = {s["scheme_id"]: s.get("scheme_name", "") for s in schemes}
    name_map = {s.get("scheme_name", "").lower(): s["scheme_id"] for s in schemes}
    return id_map, name_map


# ---------------------------------------------------------------------------
# Load / save pending_review.json
# ---------------------------------------------------------------------------
def load_pending():
    if not os.path.exists(PENDING_FILE):
        return []
    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("pending", [])


def save_pending(pending):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump({"pending": pending}, f, indent=2, ensure_ascii=False)
    print("[INFO] Saved {} pending scheme(s) to {}".format(len(pending), PENDING_FILE))


# ---------------------------------------------------------------------------
# Strip markdown fences -- identical helper used in app.py
# ---------------------------------------------------------------------------
def strip_markdown_fences(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


# ---------------------------------------------------------------------------
# Gemini call -- mirrors get_live_schemes_gemini() in app.py exactly
# ---------------------------------------------------------------------------
def call_gemini(prompt):
    """
    Calls Gemini with web grounding enabled.
    Falls back to a call without tools= if the grounded call fails.
    Returns raw response text.
    Raises RuntimeError if Gemini is not available or no API key is set.
    """
    if not _GENAI_AVAILABLE:
        raise RuntimeError("Gemini SDK not installed. Run: pip install google-genai")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("No API key found. Set GEMINI_API_KEY or GOOGLE_API_KEY.")

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
                    response_mime_type="application/json",
                ),
            )
        except Exception as grounded_err:
            print("[WARN] Grounded call failed ({}). Retrying without tools=...".format(grounded_err))
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=google_genai.types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
        return response.text
    else:
        import google.generativeai as genai_legacy  # noqa: PLC0415
        genai_legacy.configure(api_key=api_key)
        model = genai_legacy.GenerativeModel(model_name=model_name)
        resp = model.generate_content(prompt)
        return resp.text


# ---------------------------------------------------------------------------
# Build the Gemini prompt
# ---------------------------------------------------------------------------
_PROMPT_TEMPLATE = """\
You are a government scheme data extraction AI for India.

Search ONLY these official portals for your information:
- myscheme.gov.in
- nsfdc.nic.in
- standupmitra.in
- kviconline.gov.in
- udyamimitra.in
- State SC/ST/OBC/Minority welfare department websites

QUERY: {query}

Find all active government loan / credit / subsidy schemes in India that match the query.
Return ONLY a JSON array (no markdown code fences, no extra text) where each element
matches this EXACT schema:

[
  {{
    "scheme_id": "Unique short uppercase ID (e.g. NSTFDC-TLS01). Invent a sensible ID.",
    "scheme_name": "Official full scheme name",
    "issuing_authority": "Ministry / Corporation name",
    "loan_category": "Type of loan or financial benefit",
    "max_loan_amount": 0,
    "min_loan_amount": 0,
    "interest_rate": 0.0,
    "interest_rate_range": "e.g. 5.0% - 8.0% p.a.",
    "moratorium_months": 0,
    "funding_pct": 90,
    "purpose": "micro | term | education | agriculture | other",
    "eligibility_rules": {{
      "min_age": 18,
      "max_age": 60,
      "allowed_genders": ["Male", "Female", "Other"],
      "allowed_castes": ["SC", "ST", "OBC", "General"],
      "min_education_level": 0,
      "allow_defaulters": false,
      "pwd_eligible": true,
      "special_conditions": ["Condition 1", "Condition 2"]
    }},
    "contact_and_apply": {{
      "portal_url": "example.gov.in",
      "toll_free_helpline": "1800-XXX-XXXX",
      "support_email": "email@gov.in",
      "designated_physical_office": "Office description"
    }},
    "application_steps": [
      "Step 1: ...",
      "Step 2: ...",
      "Step 3: ...",
      "Step 4: ...",
      "Step 5: ..."
    ],
    "_source_urls": ["https://actual.source.url1", "https://actual.source.url2"]
  }}
]

RULES:
- Include ONLY schemes you can verify from the official portals listed above.
- Do NOT invent scheme details -- use only information from the live sources.
- Return ONLY the JSON array. No markdown, no explanation, no preamble.
- If you find zero matching schemes, return an empty JSON array: []
"""


# ---------------------------------------------------------------------------
# Fetch one query
# ---------------------------------------------------------------------------
def fetch_query(query, existing_id_map, existing_name_map, pending_id_set):
    """
    Calls Gemini for query, parses + validates the response,
    deduplicates against existing schemes and in-session pending set,
    and returns the list of newly accepted candidates (with audit metadata).
    """
    print("\n" + "=" * 60)
    print("[FETCH] Query: {}".format(query))
    print("=" * 60)

    prompt = _PROMPT_TEMPLATE.format(query=query)

    try:
        raw = call_gemini(prompt)
    except RuntimeError as exc:
        print("[ERROR] Gemini unavailable: {}".format(exc))
        return []
    except Exception as exc:
        print("[ERROR] Gemini call failed: {}".format(exc))
        return []

    raw_clean = strip_markdown_fences(raw)

    try:
        parsed = json.loads(raw_clean)
    except json.JSONDecodeError as exc:
        print("[ERROR] JSON parse failed: {}".format(exc))
        print("[DEBUG] Raw response (first 500 chars): {}".format(raw_clean[:500]))
        return []

    # Accept both a bare array and {"schemes": [...]} wrapper
    if isinstance(parsed, dict) and "schemes" in parsed:
        parsed = parsed["schemes"]
    if not isinstance(parsed, list):
        print("[ERROR] Expected JSON array, got: {}".format(type(parsed).__name__))
        return []

    print("[INFO] Model returned {} scheme candidate(s)".format(len(parsed)))

    accepted = []
    fetched_at = datetime.now(timezone.utc).isoformat()

    for idx, obj in enumerate(parsed):
        if not isinstance(obj, dict):
            print("  [SKIP] Item {} is not a JSON object".format(idx))
            continue

        scheme_id = obj.get("scheme_id", "UNKNOWN-{}".format(idx))
        scheme_name = obj.get("scheme_name", "<no name>")

        print("\n  --- Candidate: {} | {}".format(scheme_id, scheme_name))

        # Validate schema
        errors = validate_scheme(obj)
        if errors:
            print("  [REJECTED -- schema errors]")
            for err in errors:
                print("      * {}".format(err))
            continue

        # Duplicate: exact scheme_id match
        if scheme_id in existing_id_map:
            print("  [SKIP -- duplicate ID] '{}' already exists in schemes.json as '{}'".format(
                scheme_id, existing_id_map[scheme_id]))
            continue

        # Duplicate: already queued in this run
        if scheme_id in pending_id_set:
            print("  [SKIP -- already pending] '{}' is already in pending_review.json".format(scheme_id))
            continue

        # Possible duplicate: same name, different ID
        name_key = scheme_name.lower()
        if name_key in existing_name_map:
            existing_id = existing_name_map[name_key]
            print("  [FLAG -- possible duplicate] Same name found in schemes.json under a different ID: '{}'."
                  " Adding with _possible_duplicate flag for human review.".format(existing_id))
            obj["_possible_duplicate"] = {
                "reason": "Same scheme_name found in schemes.json under a different scheme_id",
                "existing_scheme_id": existing_id,
            }

        # Enrich with fetch metadata
        source_urls = obj.pop("_source_urls", [])
        obj["_source_urls"] = source_urls if isinstance(source_urls, list) else []
        obj["_fetched_at"] = fetched_at
        obj["_fetch_query"] = query

        accepted.append(obj)
        pending_id_set.add(scheme_id)
        print("  [ACCEPTED] '{}' added to pending_review.json candidates".format(scheme_id))

    return accepted


def direct_merge_to_schemes(candidates):
    """
    Directly merges validated candidates into schemes.json with backup and smoke test,
    bypassing the need for manual human review.
    """
    if not candidates:
        return

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = "{}.bak.{}".format(SCHEMES_FILE, ts)
    if os.path.exists(SCHEMES_FILE):
        shutil.copy2(SCHEMES_FILE, backup_path)
        print("[BACKUP] Created backup of schemes.json at {}".format(backup_path))

    if os.path.exists(SCHEMES_FILE):
        with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        schemes = data.get("schemes", [])
    else:
        schemes = []

    existing_map = {s["scheme_id"]: idx for idx, s in enumerate(schemes)}
    added = 0
    updated = 0

    for c in candidates:
        clean = {k: v for k, v in c.items() if not k.startswith("_")}
        sid = clean.get("scheme_id")
        if sid in existing_map:
            schemes[existing_map[sid]] = clean
            updated += 1
            print("  [AUTO-MERGE] Updated existing scheme: {} - {}".format(sid, clean.get("scheme_name")))
        else:
            schemes.append(clean)
            existing_map[sid] = len(schemes) - 1
            added += 1
            print("  [AUTO-MERGE] Added new scheme directly to schemes.json: {} - {}".format(sid, clean.get("scheme_name")))

    tmp_path = SCHEMES_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump({"schemes": schemes}, f, indent=2, ensure_ascii=False)

    try:
        from engine import load_schemes
        loaded = load_schemes(tmp_path)
        print("[SMOKE TEST] Engine successfully verified {} total schemes.".format(len(loaded)))
        shutil.move(tmp_path, SCHEMES_FILE)
        print("[SUCCESS] schemes.json directly updated with {} new & {} updated scheme(s)!".format(added, updated))
    except Exception as exc:
        print("[ERROR] Smoke test failed: {}. Rolling back.".format(exc))
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, SCHEMES_FILE)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="UDYAMSetu -- Fetch new schemes from official government portals via Gemini."
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Ad-hoc search query. If omitted, runs the default watchlist.",
    )
    parser.add_argument(
        "--stage-only",
        action="store_true",
        help="If set, writes to pending_review.json instead of directly uploading to schemes.json.",
    )
    args = parser.parse_args()

    if not _GENAI_AVAILABLE:
        print("[FATAL] Gemini SDK is not installed. Run: pip install google-genai\nAborting.")
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("[FATAL] No Gemini API key found. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.\nAborting.")
        sys.exit(1)

    # Load reference data
    existing_id_map, existing_name_map = load_existing_schemes()
    print("[INFO] Loaded {} existing scheme(s) from schemes.json".format(len(existing_id_map)))

    existing_pending = load_pending()
    pending_id_set = {p.get("scheme_id", "") for p in existing_pending}

    queries = [args.query] if args.query else DEFAULT_WATCHLIST

    all_new_candidates = []
    for query in queries:
        candidates = fetch_query(query, existing_id_map, existing_name_map, pending_id_set)
        all_new_candidates.extend(candidates)

    print("\n" + "=" * 60)
    print("[SUMMARY] {} new candidate(s) accepted this run".format(len(all_new_candidates)))

    if all_new_candidates:
        if args.stage_only:
            merged_pending = existing_pending + all_new_candidates
            save_pending(merged_pending)
            print("[DONE] pending_review.json now contains {} item(s).".format(len(merged_pending)))
            print("[NEXT] Run: python review.py  -- to approve/reject candidates.")
        else:
            # DIRECT MERGE INTO schemes.json
            print("[ACTION] Directly uploading validated scheme(s) to schemes.json...")
            direct_merge_to_schemes(all_new_candidates)
    else:
        print("[DONE] No new candidates were accepted. schemes.json unchanged.")


if __name__ == "__main__":
    main()
