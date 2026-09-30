"""
review.py
UDYAMSetu -- Scheme Review Stage (Terminal UI)

Loads pending_review.json, shows one scheme at a time in a readable summary,
and lets a human reviewer take one of four actions:
  [a] approve  -- move scheme to approved_schemes.json
  [r] reject   -- remove from pending, log reason to review_log.txt
  [e] edit     -- open raw JSON in $EDITOR for quick fixes before approving
  [s] skip     -- leave in pending, come back later

NEVER modifies schemes.json directly -- that is merge.py''s responsibility.

CLI usage:
  python review.py
"""

import json
import os
import sys
import subprocess
import tempfile
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PENDING_FILE = os.path.join(BASE_DIR, "pending_review.json")
APPROVED_FILE = os.path.join(BASE_DIR, "approved_schemes.json")
REVIEW_LOG = os.path.join(BASE_DIR, "review_log.txt")

# ---------------------------------------------------------------------------
# Console colours (gracefully degrade if the terminal doesn''t support ANSI)
# ---------------------------------------------------------------------------
try:
    import colorama
    colorama.init(autoreset=True)
    _GREEN  = colorama.Fore.GREEN
    _RED    = colorama.Fore.RED
    _YELLOW = colorama.Fore.YELLOW
    _CYAN   = colorama.Fore.CYAN
    _BOLD   = colorama.Style.BRIGHT
    _RESET  = colorama.Style.RESET_ALL
    _HAS_COLOR = True
except ImportError:
    _GREEN = _RED = _YELLOW = _CYAN = _BOLD = _RESET = ""
    _HAS_COLOR = False


def c(text, colour):
    """Wrap text in an ANSI colour code if colour is supported."""
    return "{}{}{}".format(colour, text, _RESET) if colour else text


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------
def load_json_list(filepath, key):
    """Load a JSON file and return the list stored under *key*."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(key, [])


def save_json_list(filepath, key, items):
    """Overwrite *filepath* with { key: items }."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({key: items}, f, indent=2, ensure_ascii=False)


def append_review_log(scheme_id, scheme_name, action, reason=""):
    """Append a one-line audit entry to review_log.txt."""
    timestamp = datetime.now(timezone.utc).isoformat()
    line = "[{}] {} | {} | {} | {}\n".format(timestamp, action.upper(), scheme_id, scheme_name, reason)
    with open(REVIEW_LOG, "a", encoding="utf-8") as f:
        f.write(line)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------
def _fmt_amount(amount):
    """Format an integer rupee amount as a human-readable string."""
    if not isinstance(amount, (int, float)):
        return str(amount)
    if amount >= 10_000_000:
        return "Rs {:.1f} Cr".format(amount / 10_000_000)
    elif amount >= 100_000:
        return "Rs {:.1f} L".format(amount / 100_000)
    elif amount >= 1000:
        return "Rs {:.1f} K".format(amount / 1000)
    return "Rs {}".format(int(amount))


def display_scheme(scheme, index, total):
    """Print a human-readable summary of a single pending scheme."""
    sep = "=" * 70
    print("\n" + c(sep, _CYAN))
    print(c("  Scheme {}/{}: {}".format(index, total, scheme.get("scheme_name", "N/A")), _BOLD))
    print(c(sep, _CYAN))

    # Core identity
    print("  ID               : {}".format(c(scheme.get("scheme_id", "N/A"), _YELLOW)))
    print("  Authority        : {}".format(scheme.get("issuing_authority", "N/A")))
    print("  Category         : {}".format(scheme.get("loan_category", "N/A")))
    print("  Purpose          : {}".format(scheme.get("purpose", "N/A")))

    # Loan financials
    min_amt = _fmt_amount(scheme.get("min_loan_amount", 0))
    max_amt = _fmt_amount(scheme.get("max_loan_amount", 0))
    print("  Loan Range       : {} -- {}".format(min_amt, max_amt))
    print("  Interest Range   : {}".format(scheme.get("interest_rate_range", "N/A")))
    moratorium = scheme.get("moratorium_months")
    if moratorium is not None:
        print("  Moratorium       : {} month(s)".format(moratorium))

    # Eligibility rules summary
    rules = scheme.get("eligibility_rules", {})
    print("\n  --- Eligibility Rules ---")
    print("  Age              : {} - {}".format(rules.get("min_age", "?"), rules.get("max_age", "?")))
    print("  Genders          : {}".format(", ".join(rules.get("allowed_genders", []))))
    print("  Castes           : {}".format(", ".join(rules.get("allowed_castes", []))))
    print("  Min Education    : {}".format(rules.get("min_education_level", 0)))
    print("  Allow Defaulters : {}".format(rules.get("allow_defaulters", False)))
    print("  PwD Eligible     : {}".format(rules.get("pwd_eligible", True)))
    special = rules.get("special_conditions", [])
    if special:
        print("  Special Conds    :")
        for cond in special:
            print("    * {}".format(cond))

    # Contact
    contact = scheme.get("contact_and_apply", {})
    print("\n  --- Contact & Apply ---")
    print("  Portal           : {}".format(contact.get("portal_url", "N/A")))
    print("  Helpline         : {}".format(contact.get("toll_free_helpline", "N/A")))
    print("  Email            : {}".format(contact.get("support_email", "N/A")))
    print("  Office           : {}".format(contact.get("designated_physical_office", "N/A")))

    # Application steps (abbreviated)
    steps = scheme.get("application_steps", [])
    print("\n  --- Application Steps ---")
    for step in steps:
        print("    {}".format(step))

    # Fetch metadata
    print("\n  --- Fetch Metadata ---")
    print("  Fetched At       : {}".format(scheme.get("_fetched_at", "N/A")))
    print("  Fetch Query      : {}".format(scheme.get("_fetch_query", "N/A")))
    source_urls = scheme.get("_source_urls", [])
    if source_urls:
        print("  Source URLs      :")
        for url in source_urls:
            print("    * {}".format(url))
    else:
        print("  Source URLs      : (none provided)")

    # Possible duplicate warning
    dup = scheme.get("_possible_duplicate")
    if dup:
        print("\n  " + c("[!] POSSIBLE DUPLICATE: {}".format(dup.get("reason", "")), _RED))
        print("      Existing ID  : {}".format(dup.get("existing_scheme_id", "?")))

    print(c(sep, _CYAN))


# ---------------------------------------------------------------------------
# Editor helper
# ---------------------------------------------------------------------------
def open_in_editor(scheme):
    """
    Serialise scheme to a temp file, open it in $EDITOR (default: notepad on
    Windows, nano on Unix), then re-parse on save.
    Returns the (possibly edited) scheme dict, or None if the user aborted.
    """
    editor = os.environ.get("EDITOR") or ("notepad" if os.name == "nt" else "nano")
    raw = json.dumps(scheme, indent=2, ensure_ascii=False)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name

    try:
        subprocess.call([editor, tmp_path])
    except FileNotFoundError:
        print(c("[ERROR] Editor '{}' not found. Set $EDITOR to a valid editor.".format(editor), _RED))
        os.unlink(tmp_path)
        return None

    try:
        with open(tmp_path, "r", encoding="utf-8") as f:
            edited = json.load(f)
        print(c("[OK] Edited JSON parsed successfully.", _GREEN))
        return edited
    except json.JSONDecodeError as exc:
        print(c("[ERROR] Edited file is not valid JSON: {}. Changes discarded.".format(exc), _RED))
        return None
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Interactive review loop
# ---------------------------------------------------------------------------
def review_loop():
    pending = load_json_list(PENDING_FILE, "pending")
    if not pending:
        print(c("[INFO] pending_review.json is empty or does not exist. Nothing to review.", _YELLOW))
        print("       Run: python fetch_schemes.py  -- to populate it first.")
        return

    approved = load_json_list(APPROVED_FILE, "approved")
    approved_id_set = {s.get("scheme_id") for s in approved}

    total = len(pending)
    print(c("\nUDYAMSetu Scheme Reviewer", _BOLD))
    print("Loaded {} pending scheme(s). Type your choice for each.\n".format(total))

    remaining_pending = []
    index = 0

    for scheme in pending:
        index += 1
        scheme_id = scheme.get("scheme_id", "UNKNOWN")
        scheme_name = scheme.get("scheme_name", "N/A")

        # Skip schemes already approved in a previous run
        if scheme_id in approved_id_set:
            print("[SKIP -- already approved] {} was previously approved.".format(scheme_id))
            continue

        display_scheme(scheme, index, total)

        while True:
            prompt_text = (
                "\n  Action: "
                + c("[a]", _GREEN) + "pprove  "
                + c("[r]", _RED) + "eject  "
                + c("[e]", _YELLOW) + "dit  "
                + c("[s]", _CYAN) + "kip"
                + "  > "
            )
            try:
                choice = input(prompt_text).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n[INFO] Reviewer interrupted. Saving progress...")
                remaining_pending.append(scheme)
                # Save any remaining un-processed schemes back to pending
                remaining_pending.extend(pending[index:])
                save_json_list(PENDING_FILE, "pending", remaining_pending)
                save_json_list(APPROVED_FILE, "approved", approved)
                print("[INFO] Progress saved. Exiting.")
                return

            if choice == "a":
                # Strip internal fetch metadata before approving
                clean = {k: v for k, v in scheme.items() if not k.startswith("_")}
                approved.append(clean)
                approved_id_set.add(scheme_id)
                append_review_log(scheme_id, scheme_name, "APPROVED")
                print(c("  [APPROVED] '{}' moved to approved_schemes.json.".format(scheme_id), _GREEN))
                break

            elif choice == "r":
                try:
                    reason = input("  Rejection reason (press Enter to skip): ").strip()
                except EOFError:
                    reason = ""
                append_review_log(scheme_id, scheme_name, "REJECTED", reason)
                print(c("  [REJECTED] '{}' removed from pending.".format(scheme_id), _RED))
                break

            elif choice == "e":
                edited = open_in_editor(scheme)
                if edited is not None:
                    scheme = edited
                    # Show the updated scheme before prompting again
                    display_scheme(scheme, index, total)
                # Loop back to re-prompt with the (possibly edited) scheme

            elif choice == "s":
                remaining_pending.append(scheme)
                append_review_log(scheme_id, scheme_name, "SKIPPED")
                print(c("  [SKIPPED] '{}' remains in pending_review.json.".format(scheme_id), _CYAN))
                break

            else:
                print("  Invalid choice. Please type a, r, e, or s.")

    # Save final state
    save_json_list(PENDING_FILE, "pending", remaining_pending)
    save_json_list(APPROVED_FILE, "approved", approved)

    print("\n" + c("=" * 60, _CYAN))
    print(c("Review session complete.", _BOLD))
    print("  Approved : {}".format(len(approved)))
    print("  Remaining: {}".format(len(remaining_pending)))
    print("  Log      : {}".format(REVIEW_LOG))
    if approved:
        print("\n[NEXT] Run: python merge.py  -- to merge approved schemes into schemes.json.")
    print(c("=" * 60, _CYAN))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    review_loop()
