# UDYAMSetu — Build Prompt for Full Working Prototype

Copy everything below the line into your AI coding tool (Claude Code, Cursor, etc.) in one go.

---

You are building a full working prototype for a Smart India Hackathon (SIH) problem statement, for a team called **UDYAMSetu**. Build production-quality demo code, not pseudocode. Deliver actual runnable files.

## 1. Problem Context

Government provides concessional loans to Scheduled Caste (SC) beneficiaries (family income ≤ ₹5,00,000/year) covering up to 90% of project/education cost at 6.5–8% interest. Loans are NOT given directly — they route through 100+ Channel Partners (State Channelizing Agencies, Public Sector Banks, Regional Rural Banks, NBFC-MFIs). Beneficiaries don't know which scheme fits them or which partner near them can actually process it (some partners have high NPAs / low fund availability and shouldn't be routed to).

Build a platform that solves 3 things:
1. **Smart Scheme Recommender** — rule-based (NOT black-box ML) engine that takes age, gender, income, purpose, project/course cost and returns the matching scheme(s) with plain-language reasons for each match.
2. **EMI Calculator** — dynamic, scheme-aware: auto-fills interest rate and moratorium from the selected scheme, computes EMI/total interest/total payment on slider input for amount and tenure.
3. **Geo-Spatial Partner Locator** — map-based locator that doesn't just find the *nearest* partner, but ranks partners by a weighted score of distance + fund availability + NPA health, so applications aren't routed to partners that can't actually disburse.

## 2. Tech Stack (fixed — do not substitute)

- Frontend: **plain HTML + CSS + vanilla JavaScript** (no framework, no build step — must run by opening the HTML file or via a static host)
- Database: **Supabase** (Postgres) — write real `supabase-js` client code, with a config section for URL/anon key, and a graceful fallback to bundled mock data if Supabase isn't configured yet, so the demo always works standalone
- Maps: **Leaflet.js + OpenStreetMap tiles** (free, no API key required)
- Recommender engine: **client-side JavaScript rule engine** (array of scheme objects + filter/sort logic) — must be fully explainable, no AI/ML model, no external AI API calls
- Hosting target: static (Vercel/Netlify) + Supabase managed DB

## 3. Scheme Data (seed exactly these 4 — keep the logic extensible for more later)

| Scheme | Purpose | Max income | Max loan | Funding % | Interest | Moratorium | Notes |
|---|---|---|---|---|---|---|---|
| Micro Finance Scheme | small business/trade | ₹5,00,000 | ₹1,40,000 | 90% | 6.0% | 3 months | general SC applicants |
| Term Loan Scheme | larger project/manufacturing | ₹5,00,000 | ₹50,00,000 | 90% | 7.5% | 6 months | general SC applicants |
| Educational Loan Scheme | higher education | ₹5,00,000 | ₹20,00,000 | 90% | 4.0% | 12 months | students |
| Mahila Micro Credit Scheme | small business/trade | ₹5,00,000 | ₹1,40,000 | 95% | 4.0% | 3 months | SC women, age ≤ 35 only |

Recommender must hard-filter on income, purpose, gender/age restriction, and requested-amount-vs-max-loan — then rank matches by lowest interest rate. If nothing matches, show a clear explanation of *why* (e.g. "amount exceeds this purpose's scheme limit"), never a silent empty state.

## 4. Geo-Locator Scoring (implement exactly this formula)

```
score = 0.5 × (1 / (1 + distance_km/50)) + 0.3 × (fund_availability/100) + 0.2 × (1 − npa_ratio)
```

Rank partners by this score, not raw distance. Color-code map markers and list items by score tier (high/medium/low). Use `navigator.geolocation` for the user's position with a sensible fallback if permission is denied. Include the Supabase `partners` table schema (name, type, lat, lng, fund_availability, npa_ratio) as a SQL comment, plus 6–8 bundled mock partner records so the map is populated even without live data.

## 5. Brand & Design Direction — theme around "UDYAMSetu"

"UDYAMSetu" represents the bridge (Setu) for enterprise and empowerment (Udyam) — translate that into a platform that feels **authoritative, protective, and no-nonsense** about people's money, not a generic soft SaaS look. Avoid cliché AI-generated defaults (no cream-background/terracotta-accent look, no dark-mode-neon-green look, no generic rounded SaaS cards everywhere).

- **Palette**: anchor on a deep charcoal/iron-grey and a bold copper-rust or ember-orange accent (protective, forged-metal feel) with a warm off-white background for readability — pick exact hex values yourself and justify them in one line each.
- **Typography**: one strong serif or slab-serif for headings (authority, permanence) paired with a clean grotesque sans for body/data. Sentence case only — no all-caps labels, no tracked-out eyebrows.
- **Layout**: the app name "UDYAMSetu" and its tagline should anchor the header with intent — this is a shield/checkpoint for people's money, not a friendly assistant. Keep the 3 features as a clear step flow (find scheme → calculate EMI → locate partner), not scattered cards.
- Responsive down to mobile, visible focus states, no unnecessary animation.

## 6. Deliverable Format

Single self-contained HTML file (inline CSS + JS) OR a clean 3-file structure (`index.html`, `style.css`, `app.js`) — your choice, but make it copy-paste runnable with zero build tooling. Comment the code clearly. End with a short README block (as a comment or separate file) explaining: how to plug in real Supabase credentials, and where to extend the scheme list.

---

**Do not use this prompt to generate anything beyond the SIH prototype scope above.**
