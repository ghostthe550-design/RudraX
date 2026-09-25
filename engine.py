"""
engine.py
Phase 2 — Core Rules Engine (Expert System)

Compares a User Profile against the Scheme Database (schemes.json)
and computes an eligibility compatibility score with plain-language
reasons for eligibility or rejection.

This is a DETERMINISTIC rules engine built with loops and if/else
logic only — no Machine Learning model is used, so every decision
is fully explainable to the applicant.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------
# STEP 1: Load the Scheme Database
# ---------------------------------------------------------------
def load_schemes(filepath="schemes.json"):
    """Reads schemes.json and returns the list of scheme dictionaries."""
    if not os.path.isabs(filepath):
        filepath = os.path.join(BASE_DIR, filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("schemes", [])


# ---------------------------------------------------------------
# STEP 2: Dummy User Profile (for standalone testing)
# ---------------------------------------------------------------
dummy_user = {
    "age": 26,
    "gender": "Female",
    "caste_category": "OBC",
    "education_level": 4,      # 4 = 12th Pass (see ordinal scale in schemes.json)
    "is_pwd": False,
    # New field: one of NO_PRIOR_LOANS | ACTIVE_ON_TIME | PAST_MINOR_DELAYS | CURRENT_DEFAULT_NPA
    "repayment_status": "NO_PRIOR_LOANS",
    "cibil_range": ""          # Optional; empty string means not provided
}


# ---------------------------------------------------------------
# STEP 3: The Core Matching Function
# Each core eligibility rule contributes toward the match score.
# Every pass/fail decision is logged in plain language so the user
# knows exactly why they qualify or what prevented qualification.
# ---------------------------------------------------------------
def evaluate_scheme(user, scheme):
    rules = scheme.get("eligibility_rules", {})
    reasons_pass = []
    reasons_fail = []

    total_checks = 5
    passed_checks = 0

    # --- Check 1: Age range ---
    min_age = rules.get("min_age", 18)
    max_age = rules.get("max_age", 99)
    if min_age <= user["age"] <= max_age:
        passed_checks += 1
        reasons_pass.append(
            f"Age {user['age']} is within the allowed range ({min_age}-{max_age} years)."
        )
    else:
        reasons_fail.append(
            f"Age {user['age']} is outside the allowed range ({min_age}-{max_age} years)."
        )

    # --- Special Case Check: Stand-Up India (SUI02) ---
    # Stand-Up India requires the applicant to be SC/ST OR Female.
    is_sui = scheme.get("scheme_id") == "SUI02"
    sui_eligible = (user["caste_category"] in ["SC", "ST"]) or (user["gender"] == "Female")

    # --- Check 2: Gender ---
    allowed_genders = rules.get("allowed_genders", ["Male", "Female", "Other"])
    if is_sui and not sui_eligible:
        reasons_fail.append(
            f"Gender '{user['gender']}' with caste '{user['caste_category']}' does not meet Stand-Up India requirement (must be SC/ST OR Female)."
        )
    elif user["gender"] in allowed_genders:
        passed_checks += 1
        reasons_pass.append(f"Gender '{user['gender']}' is eligible for this scheme.")
    else:
        reasons_fail.append(f"Gender '{user['gender']}' is not listed as eligible.")

    # --- Check 3: Caste category ---
    allowed_castes = rules.get("allowed_castes", ["General", "SC", "ST", "OBC"])
    if is_sui:
        if sui_eligible:
            passed_checks += 1
            reasons_pass.append(
                f"Meets Stand-Up India social category criteria ({user['caste_category']} / {user['gender']})."
            )
        else:
            reasons_fail.append(
                f"Caste '{user['caste_category']}' is not SC/ST (and applicant is not female), disqualifying for Stand-Up India."
            )
    elif user["caste_category"] in allowed_castes:
        passed_checks += 1
        reasons_pass.append(f"Caste category '{user['caste_category']}' is eligible.")
    else:
        reasons_fail.append(f"Caste category '{user['caste_category']}' is not eligible.")

    # --- Check 4: Minimum education level ---
    min_edu = rules.get("min_education_level", 0)
    edu_labels = {
        0: "No formal education",
        1: "Below 8th pass",
        2: "8th pass",
        3: "10th pass",
        4: "12th pass",
        5: "Graduate",
        6: "Post-graduate"
    }
    user_edu_label = edu_labels.get(user["education_level"], f"Level {user['education_level']}")
    min_edu_label = edu_labels.get(min_edu, f"Level {min_edu}")

    if user["education_level"] >= min_edu:
        passed_checks += 1
        reasons_pass.append(
            f"Education ({user_edu_label}) meets the minimum requirement ({min_edu_label})."
        )
    else:
        reasons_fail.append(
            f"Education ({user_edu_label}) is below the required minimum ({min_edu_label})."
        )

    # --- Check 5: Repayment track record (replaces binary has_loan_default) ---
    # CURRENT_DEFAULT_NPA is the only hard-disqualifying value.
    # PAST_MINOR_DELAYS is flagged with an advisory but does NOT disqualify.
    # NO_PRIOR_LOANS and ACTIVE_ON_TIME both pass cleanly.
    repayment_status = user.get("repayment_status", "NO_PRIOR_LOANS")
    allow_defaulters = rules.get("allow_defaulters", False)

    if repayment_status == "CURRENT_DEFAULT_NPA" and not allow_defaulters:
        reasons_fail.append(
            "Account is currently marked NPA / written off. You must regularise the account or "
            "obtain a No-Objection Certificate before a loan can be sanctioned."
        )
    else:
        passed_checks += 1
        if repayment_status == "NO_PRIOR_LOANS":
            reasons_pass.append("First-time borrower / no prior loans — clean credit slate.")
        elif repayment_status == "ACTIVE_ON_TIME":
            reasons_pass.append("Active loans with all EMIs paid on time — strong repayment record.")
        elif repayment_status == "PAST_MINOR_DELAYS":
            reasons_pass.append(
                "Past minor delays (1-30 days), now regularized — eligible to proceed. "
                "Bank may request a clarification letter."
            )
        else:
            reasons_pass.append("Repayment status accepted for this scheme.")

    # Derive backward-compat has_loan_default for score-cap logic
    has_loan_default = (repayment_status == "CURRENT_DEFAULT_NPA")

    # --- Additional Bonus: PwD (Divyang) Consideration ---
    if user.get("is_pwd"):
        if rules.get("pwd_eligible", True):
            reasons_pass.append(
                "Divyang (Person with Disability) applicants are eligible and may receive higher subsidy/priority quotas."
            )

    # --- Compute final percentage score ---
    # Stand-Up India strict restriction: if not SC/ST or Female, cap match score
    if is_sui and not sui_eligible:
        score_percent = min(round((passed_checks / total_checks) * 100), 40)
    else:
        score_percent = round((passed_checks / total_checks) * 100)

    # NPA hard cap: a bank loan cannot be sanctioned to a current defaulter
    if has_loan_default and not allow_defaulters:
        if score_percent > 60:
            score_percent = 60

    if score_percent == 100:
        status = "Eligible"
    elif score_percent >= 50:
        status = "Partially Eligible"
    else:
        status = "Not Eligible"

    return {
        "scheme_id": scheme["scheme_id"],
        "scheme_name": scheme["scheme_name"],
        "issuing_authority": scheme.get("issuing_authority", ""),
        "loan_category": scheme.get("loan_category", ""),
        "max_loan_amount": scheme.get("max_loan_amount", 0),
        "min_loan_amount": scheme.get("min_loan_amount", 0),
        "interest_rate_range": scheme.get("interest_rate_range", ""),
        "match_score": score_percent,
        "status": status,
        "reasons_pass": reasons_pass,
        "reasons_fail": reasons_fail,
        # Provide application steps for eligible & partially eligible (for awareness)
        "application_steps": scheme.get("application_steps", []) if score_percent >= 70 else [],
        "contact_and_apply": scheme.get("contact_and_apply", {})
    }


# ---------------------------------------------------------------
# STEP 4: Run the Engine Against Every Scheme in the Database
# ---------------------------------------------------------------
def run_engine(user, schemes):
    results = []
    for scheme in schemes:
        result = evaluate_scheme(user, scheme)
        results.append(result)

    # Sort best matches first
    results.sort(key=lambda r: r["match_score"], reverse=True)
    return results


# ---------------------------------------------------------------
# STEP 5: Demo Run — only executes when this file is run directly
# ---------------------------------------------------------------
if __name__ == "__main__":
    schemes = load_schemes("schemes.json")
    results = run_engine(dummy_user, schemes)

    print(f"\n=== Match Results for Dummy User ===")
    print(dummy_user, "\n")

    for r in results:
        print(f"{r['scheme_name']} ({r['scheme_id']}) -> {r['match_score']}% ({r['status']})")
        for reason in r["reasons_pass"]:
            print(f"   [PASS] {reason}")
        for reason in r["reasons_fail"]:
            print(f"   [FAIL] {reason}")
        print()
