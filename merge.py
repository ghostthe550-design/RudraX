"""
merge.py
UDYAMSetu -- Scheme Merge Stage (Admin)

Merges approved_schemes.json into the live schemes.json database.

Safety guarantees:
  1. Validates every approved scheme against the full schema BEFORE touching
     schemes.json -- aborts with a clear error on any malformed entry.
  2. Creates a timestamped backup (schemes.json.bak.<ISO8601>) before writing.
  3. After writing, runs engine.load_schemes() as a smoke test -- rolls back
     to the backup if it raises.
  4. Clears merged entries out of approved_schemes.json on success.

CLI usage:
  python merge.py
"""

import json
import os
import shutil
import sys
from datetime import datetime, timezone

# Import the live engine for smoke-test -- no Flask context needed
from engine import load_schemes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCHEMES_FILE    = os.path.join(BASE_DIR, "schemes.json")
APPROVED_FILE   = os.path.join(BASE_DIR, "approved_schemes.json")
MERGE_LOG       = os.path.join(BASE_DIR, "review_log.txt")

# ---------------------------------------------------------------------------
# Required field sets (same as fetch_schemes.py -- kept DRY here intentionally
# so merge.py has zero dependency on fetch_schemes.py at runtime)
# ---------------------------------------------------------------------------
REQUIRED_TOP_LEVEL = [
    "scheme_id", "scheme_name", "issuing_authority", "loan_category",
    "max_loan_amount", "min_loan_amount", "interest_rate_range",
    "purpose", "eligibility_rules", "contact_and_apply", "application_steps",
]

REQUIRED_ELIGIBILITY_KEYS = [
    "min_age", "max_age", "allowed_genders", "allowed_castes",
    "min_education_level", "allow_defaulters", "pwd_eligible",
]

REQUIRED_CONTACT_KEYS = [
    "portal_url", "toll_free_helpline", "support_email",
    "designated_physical_office",
]


# ---------------------------------------------------------------------------
# Schema validation (identical contract to fetch_schemes.validate_scheme)
# ---------------------------------------------------------------------------
def validate_scheme(obj):
    """
    Returns a list of validation error strings.
    An empty list means the object is valid.
    """
    errors = []

    for field in REQUIRED_TOP_LEVEL:
        if field not in obj or obj[field] is None:
            errors.append("Missing or null top-level field: '{}'".format(field))

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

    contact = obj.get("contact_and_apply")
    if not isinstance(contact, dict):
        errors.append("'contact_and_apply' must be a JSON object")
    else:
        for key in REQUIRED_CONTACT_KEYS:
            if key not in contact or contact[key] is None:
                errors.append("Missing or null contact_and_apply.{}".format(key))

    steps = obj.get("application_steps")
    if not isinstance(steps, list) or len(steps) == 0:
        errors.append("'application_steps' must be a non-empty array")

    for amt_field in ("max_loan_amount", "min_loan_amount"):
        if amt_field in obj and not isinstance(obj[amt_field], (int, float)):
            errors.append("'{}' must be a number".format(amt_field))

    return errors


# ---------------------------------------------------------------------------
# Audit log helper
# ---------------------------------------------------------------------------
def append_merge_log(line):
    """Append a line to review_log.txt (shared audit log)."""
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(MERGE_LOG, "a", encoding="utf-8") as f:
        f.write("[{}] MERGE | {}\n".format(timestamp, line))


# ---------------------------------------------------------------------------
# Main merge logic
# ---------------------------------------------------------------------------
def main():
    # ------------------------------------------------------------------
    # 1. Load approved schemes
    # ------------------------------------------------------------------
    if not os.path.exists(APPROVED_FILE):
        print("[INFO] approved_schemes.json not found. Nothing to merge.")
        sys.exit(0)

    with open(APPROVED_FILE, "r", encoding="utf-8") as f:
        approved_data = json.load(f)

    approved = approved_data.get("approved", [])
    if not approved:
        print("[INFO] approved_schemes.json contains no approved schemes. Nothing to merge.")
        sys.exit(0)

    print("[INFO] Found {} approved scheme(s) to merge.".format(len(approved)))

    # ------------------------------------------------------------------
    # 2. Validate every approved scheme before touching schemes.json
    # ------------------------------------------------------------------
    all_valid = True
    for scheme in approved:
        scheme_id = scheme.get("scheme_id", "<no id>")
        errors = validate_scheme(scheme)
        if errors:
            all_valid = False
            print("\n[VALIDATION ERROR] Scheme '{}' is malformed:".format(scheme_id))
            for err in errors:
                print("  * {}".format(err))

    if not all_valid:
        print("\n[ABORT] One or more approved schemes failed validation. "
              "Fix the errors in approved_schemes.json and re-run merge.py.")
        sys.exit(1)

    print("[OK] All {} approved scheme(s) passed schema validation.".format(len(approved)))

    # ------------------------------------------------------------------
    # 3. Load current schemes.json
    # ------------------------------------------------------------------
    if not os.path.exists(SCHEMES_FILE):
        print("[WARN] schemes.json not found. Starting with an empty database.")
        existing_schemes = []
    else:
        with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        existing_schemes = existing_data.get("schemes", [])

    print("[INFO] Current schemes.json contains {} scheme(s).".format(len(existing_schemes)))

    # ------------------------------------------------------------------
    # 4. Create a timestamped backup before any write
    # ------------------------------------------------------------------
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = "{}.bak.{}".format(SCHEMES_FILE, ts)

    if os.path.exists(SCHEMES_FILE):
        shutil.copy2(SCHEMES_FILE, backup_path)
        print("[INFO] Backup created: {}".format(backup_path))

    # ------------------------------------------------------------------
    # 5. Merge: append new IDs, update existing IDs in place
    # ------------------------------------------------------------------
    existing_id_map = {s["scheme_id"]: idx for idx, s in enumerate(existing_schemes)}
    new_count = 0
    updated_count = 0
    merged_ids = []

    for scheme in approved:
        scheme_id = scheme.get("scheme_id")
        # Strip any leftover internal fetch metadata keys
        clean = {k: v for k, v in scheme.items() if not k.startswith("_")}

        if scheme_id in existing_id_map:
            idx = existing_id_map[scheme_id]
            existing_schemes[idx] = clean
            updated_count += 1
            print("[UPDATE] '{}' updated in place.".format(scheme_id))
            append_merge_log("UPDATED scheme_id={}".format(scheme_id))
        else:
            existing_schemes.append(clean)
            existing_id_map[scheme_id] = len(existing_schemes) - 1
            new_count += 1
            print("[NEW]    '{}' appended.".format(scheme_id))
            append_merge_log("ADDED scheme_id={}".format(scheme_id))

        merged_ids.append(scheme_id)

    merged_data = {"schemes": existing_schemes}

    # ------------------------------------------------------------------
    # 6. Write the new schemes.json atomically (temp file -> rename)
    # ------------------------------------------------------------------
    tmp_path = SCHEMES_FILE + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        print("[ERROR] Failed to write temp file: {}".format(exc))
        os.unlink(tmp_path) if os.path.exists(tmp_path) else None
        sys.exit(1)

    # ------------------------------------------------------------------
    # 7. Smoke test: run engine.load_schemes() against the new file
    # ------------------------------------------------------------------
    print("[SMOKE TEST] Running engine.load_schemes() against the new schemes.json...")
    try:
        loaded = load_schemes(tmp_path)
        print("[SMOKE TEST] OK -- {} scheme(s) loaded cleanly.".format(len(loaded)))
    except Exception as exc:
        print("\n[SMOKE TEST FAILED] engine.load_schemes() raised: {}".format(exc))
        print("[ROLLBACK] Restoring backup from {} ...".format(backup_path))
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, SCHEMES_FILE)
            print("[ROLLBACK] schemes.json restored successfully. No changes were committed.")
        else:
            print("[ROLLBACK] No backup found to restore. schemes.json may be in an inconsistent state.")
        os.unlink(tmp_path) if os.path.exists(tmp_path) else None
        sys.exit(1)

    # ------------------------------------------------------------------
    # 8. Commit: replace schemes.json with the validated temp file
    # ------------------------------------------------------------------
    shutil.move(tmp_path, SCHEMES_FILE)
    print("[COMMITTED] schemes.json updated successfully.")

    # ------------------------------------------------------------------
    # 9. Clear merged entries from approved_schemes.json
    # ------------------------------------------------------------------
    merged_id_set = set(merged_ids)
    remaining_approved = [s for s in approved if s.get("scheme_id") not in merged_id_set]

    with open(APPROVED_FILE, "w", encoding="utf-8") as f:
        json.dump({"approved": remaining_approved}, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # 10. Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Merge complete.")
    print("  New schemes added   : {}".format(new_count))
    print("  Existing updated    : {}".format(updated_count))
    print("  Total in database   : {}".format(len(existing_schemes)))
    print("  Backup saved at     : {}".format(backup_path))
    print("  Audit log           : {}".format(MERGE_LOG))
    print("=" * 60)


if __name__ == "__main__":
    main()
