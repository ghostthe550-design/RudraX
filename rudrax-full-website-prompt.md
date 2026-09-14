# RudraX — Build Prompt for Full Working Website (v2)

Copy everything below the line into your AI coding tool (Claude Code, Cursor, etc.) in one go. This supersedes any earlier prototype — this time build a complete, judge-ready website with multiple pages, not a single demo screen.

---

You are building a full working website for a Smart India Hackathon (SIH) problem statement, for team **RudraX**. This must be a polished, deployable website — not pseudocode, not a single demo screen. Deliver actual runnable files with a proper multi-page structure and navigation.

## 1. Problem Context

Government gives concessional loans to Scheduled Caste (SC) beneficiaries (family income ≤ ₹5,00,000/year), covering up to 90% of project/education cost at 6.5–8% interest. But direct applications aren't accepted — funds route through 100+ Channel Partners: State Channelizing Agencies (SCAs), Public Sector Banks (PSBs), Regional Rural Banks (RRBs), and NBFC-MFIs. Beneficiaries don't know which scheme fits them, which lender/partner offers the best terms, or which nearby partner can actually process the loan (some have high NPAs or exhausted fund limits and shouldn't be routed to). Loans may also come from ordinary banks on regular terms or through block-level government schemes — the site must cover **all three routes**: government concessional schemes, channel partner banks/NBFCs, and block/local-level schemes — not government schemes alone.

## 2. Tech Stack (fixed)

- Frontend: **HTML + CSS + vanilla JavaScript**, multi-page (`index.html`, `recommender.html`, `compare.html`, `calculator.html`, `locator.html`, shared `style.css` and `app.js`) — no framework, no build step, deployable as static files
- Database: **Supabase (Postgres)** — real `supabase-js` client code for all lender/partner data, with config section for URL/anon key, and bundled mock/seed data fallback so the site works fully even before Supabase is connected
- Maps: **Leaflet.js + OpenStreetMap tiles** (free, no API key)
- Recommendation & comparison logic: **client-side rule engine** (JS objects + filter/sort) — explainable, no black-box ML, no external AI API calls
- Hosting target: static hosting (Vercel/Netlify) + Supabase managed DB

## 3. Pages & Site Structure

1. **Home** — what the platform does, 3-step visual (find scheme → compare lenders → apply at nearest partner), trust-building copy for a first-time rural/low-literacy visitor
2. **Find My Scheme** (recommender) — step-by-step wizard: age, gender, income, purpose, amount → matches against government schemes, returns explainable reasons per match
3. **Compare Lenders** (NEW — build this in full) — side-by-side comparison table/cards of every eligible option for the user's inputs: government concessional schemes, channel partner banks/NBFC-MFIs at their actual lending terms, and block-level government schemes. Sort by effective interest rate by default, with a toggle to sort by fastest disbursal / lowest NPA-risk partner instead. Each row must show: lender/scheme name, type (Govt Scheme / Bank / Block Scheme / NBFC-MFI), interest rate, max loan, moratorium, and a "Best rate" / "Fastest processing" badge where applicable.
4. **EMI Calculator** — scheme/lender-aware: auto-fills interest rate + moratorium from whichever option the user picked on the Compare page, sliders for amount/tenure, shows EMI, total interest, total payment
5. **Nearest Partner / Locator** — map + ranked list of nearby partners (banks, SCAs, NBFC-MFIs, block offices), each list card and map popup must show **full address and a contact phone number**, ranked by: `0.5 × (1/(1+distance_km/50)) + 0.3 × (fund_availability/100) + 0.2 × (1 − npa_ratio)`

Shared header/nav across all pages, shared footer with a short disclaimer ("rates shown are indicative, confirm with the lender") and RudraX credit line.

## 4. Data to Seed (extend all of this — do not leave it thin)

### A. Government Schemes (rule engine input, keep from earlier version)
| Scheme | Purpose | Max income | Max loan | Funding % | Interest | Moratorium |
|---|---|---|---|---|---|---|
| Micro Finance Scheme | small business/trade | ₹5,00,000 | ₹1,40,000 | 90% | 6.0% | 3 months |
| Term Loan Scheme | larger project/manufacturing | ₹5,00,000 | ₹50,00,000 | 90% | 7.5% | 6 months |
| Educational Loan Scheme | higher education | ₹5,00,000 | ₹20,00,000 | 90% | 4.0% | 12 months |
| Mahila Micro Credit Scheme | small business/trade (women ≤35) | ₹5,00,000 | ₹1,40,000 | 95% | 4.0% | 3 months |

### B. Bank / NBFC-MFI Lender Records (for the Compare page — seed at least 6-8 realistic entries)
Each record needs: `name, type (PSB/RRB/NBFC-MFI/Block Scheme), interest_rate, max_loan, processing_days, address, phone, lat, lng, fund_availability, npa_ratio`. Mix in a couple of **regular bank loan products** (non-concessional, higher rate, for users who don't qualify for the SC scheme) so the comparison is genuinely useful, not just a duplicate of the government scheme list. Also seed 1-2 **block-level scheme** entries (district/block office administered, lower documentation, smaller ticket size) to represent the third route explicitly.

### C. Supabase Schema (write as SQL comment)
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

## 5. Compare Logic (implement exactly)

Given the user's purpose + amount + income from the recommender step, filter `lenders` to those that can serve that purpose and amount, then:
- Default sort: ascending `interest_rate`
- Alternate sort toggle: descending computed score `0.6*(1-npa_ratio) + 0.4*(1/(1+processing_days/10))` (fastest + safest)
- Flag the top interest-rate result "Best rate" and the top alternate-sort result "Fastest & safest" — a lender can hold both badges

## 6. Brand & Design — RudraX theme

"Rudra" = strength, protection, decisive force. Design should feel authoritative and protective of people's money — not a soft generic SaaS site. Avoid default AI-generated looks (no cream+terracotta, no dark+neon, no identical rounded cards with soft grey shadows everywhere).

- Palette: deep charcoal/iron-grey base, bold copper-rust/ember-orange accent, warm off-white for content areas — pick your own exact hex values and justify each in one line
- Typography: one strong serif/slab-serif for headings, clean grotesque sans for body/data, sentence case only, no all-caps eyebrows
- The Compare page is the visual centerpiece — treat the comparison table/cards as the hero of that page, not an afterthought
- Fully responsive to mobile, visible focus states, minimal but purposeful motion

## 7. Deliverable

Complete static multi-page site (`index.html`, `recommender.html`, `compare.html`, `calculator.html`, `locator.html`, `style.css`, `app.js`), fully cross-linked navigation, comments in code, and a short README block covering how to connect real Supabase data and where to add more lenders/schemes.

---

**Do not use this prompt to generate anything beyond the SIH website scope above.**
