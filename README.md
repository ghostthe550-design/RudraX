# UDYAMSetu — Concessional Finance Navigator & Eligibility Shield

> Smart India Hackathon (SIH) — Team UDYAMSetu

A deterministic, fully explainable government concessional loan scheme eligibility platform built for SC/ST and general beneficiaries and channel partners.

---

## What It Does

**3 core tools in one platform:**

1. **Scheme Matcher** — Rule-based expert system that evaluates your profile (age, gender, caste, education, disability, credit history) against 8+ government concessional loan schemes and returns a compatibility score with plain-language reasons for every pass/fail.

2. **Compare Lenders** — Side-by-side comparison table covering all 3 funding routes: Central Govt Concessional Schemes, Channel Partner Banks/NBFCs/RRBs, and Block-Level Direct Desks. Sortable by interest rate, disbursal speed, and NPA safety.

3. **EMI Calculator & Geo-Spatial Partner Locator** — Scheme-aware EMI simulator with moratorium handling, plus a Leaflet.js map that ranks nearby channel partners by a weighted formula (distance + fund availability + NPA ratio), not distance alone.

---

## Schemes Covered

| Scheme | Category | Max Loan | Rate |
|---|---|---|---|
| PM MUDRA Yojana | Central Govt | ₹10,00,000 | 8.5% |
| Stand-Up India Scheme | Central Govt | ₹1,00,00,000 | 9.5% |
| PMEGP (KVIC/DIC) | Central Govt | ₹50,00,000 | 10.5% |
| NSFDC Micro Finance Scheme | SC Concessional | ₹1,40,000 | 6.0% |
| NSFDC Term Loan Scheme | SC Concessional | ₹50,00,000 | 7.5% |
| NSFDC Educational Loan Scheme | SC Concessional | ₹20,00,000 | 4.0% |
| Mahila Micro Credit Scheme (MMCS) | SC Women | ₹1,40,000 | 4.0% |
| Bihar Student Credit Card Scheme (BSCC) | Higher Education | ₹4,00,000 | 4.0% (1.0% Women/PwD) |

---

## Tech Stack

- **Backend**: Python 3 + Flask (deterministic rules engine — no ML, fully explainable)
- **Frontend**: Vanilla HTML + CSS + JavaScript (no build step, no framework)
- **Maps**: Leaflet.js + OpenStreetMap tiles (free, no API key)
- **Database (optional)**: Supabase (Postgres) — bundled mock data works offline
- **Hosting target**: Vercel / Netlify (static) + Supabase managed DB

---

## Quick Start (Local)

```bash
# 1. Clone the repository
git clone https://github.com/ghostthe550-design/udyamsetu.git
cd udyamsetu

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the Flask server
python app.py

# 4. Open in browser
# http://127.0.0.1:5000
```

---

## Project Structure

```
udyamsetu/
├── app.py              # Flask backend — routes, validation, engine call
├── engine.py           # Deterministic eligibility rules engine (no ML)
├── schemes.json        # Government scheme database (loan rules & contacts)
├── requirements.txt    # Python dependencies (Flask only)
├── templates/
│   ├── index.html      # Applicant profile input form
│   ├── results.html    # Eligibility match dashboard
│   ├── navigator.html  # EMI calculator & geo-spatial partner locator
│   └── compare.html    # Multi-channel lender comparison table
└── static/
    └── style.css       # Unified design system (iron-charcoal + ember-copper)
```

---

## How to Extend

### Add a new scheme
Open `schemes.json` and add a new object to the `"schemes"` array following the existing schema. The rules engine picks it up automatically on restart — no code changes needed.

### Connect Supabase (live partner data)
In `templates/navigator.html`, replace the placeholders:
```javascript
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';
```

Run the schema in your Supabase SQL editor:
```sql
create table lenders (
  id serial primary key,
  name text, type text,
  interest_rate float8, max_loan numeric,
  processing_days int, funding_pct float8,
  moratorium_months int,
  address text, phone text,
  lat float8, lng float8,
  fund_availability int, npa_ratio float8
);
```

---

## Partner Locator Scoring Formula (SIH Spec)

```
Score = 0.5 × (1 / (1 + distance_km / 50))
      + 0.3 × (fund_availability / 100)
      + 0.2 × (1 − npa_ratio)
```

Partners are ranked by this composite score, ensuring beneficiaries are routed to branches with active fund headroom and low NPA risk — not just the nearest branch.

---

## License

MIT License — Built for Smart India Hackathon (SIH), Team UDYAMSetu.
