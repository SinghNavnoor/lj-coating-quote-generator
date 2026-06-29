# Painting Company Quote & Invoice Generator — Build Spec

## Overview

Build a web application for a commercial/residential painting business that allows field reps to enter property measurements on-site and automatically generate a branded PDF quote using company SOPs (pricing, paint specs, labor rates). Claude AI writes the scope of work and flags any issues.

**Stack:** Python · Streamlit · Claude API · ReportLab · PyYAML · Railway (hosting)

---

## Repository Structure

```
painting-quote-app/
├── app.py                  # Main Streamlit app
├── config/
│   └── sop.yaml            # All business rules and pricing (source of truth)
├── core/
│   ├── calculator.py       # Pricing logic (reads from sop.yaml)
│   ├── ai.py               # Claude API integration
│   └── pdf_generator.py    # PDF creation with branding
├── assets/
│   └── logo.png            # Company logo for PDF header
├── requirements.txt
├── .env.example
└── README.md
```

---

## Phase 1 — SOP Config File (`config/sop.yaml`)

This is the single source of truth for all business rules. The owner updates this file when pricing changes. The app reads it at runtime.

```yaml
company:
  name: "Apex Painting Co."
  phone: "(555) 000-0000"
  email: "quotes@apexpainting.com"
  website: "www.apexpainting.com"
  license: "LIC# CA-123456"
  logo_path: "assets/logo.png"

labor:
  rate_per_hour: 65.00          # USD per labor hour
  prep_time_percentage: 0.20    # 20% of paint time added for prep/masking

paint:
  default_brand: "Sherwin-Williams Duration"
  cost_per_gallon: 58.00
  coverage_sqft_per_gallon: 350
  default_coats: 2

surfaces:
  exterior_wall:
    label: "Exterior Wall"
    hours_per_100_sqft: 0.8
    coats: 2
  interior_wall:
    label: "Interior Wall"
    hours_per_100_sqft: 0.6
    coats: 2
  ceiling:
    label: "Ceiling"
    hours_per_100_sqft: 0.9
    coats: 1
  trim:
    label: "Trim / Baseboards"
    hours_per_linear_ft: 0.15
    coats: 2
  door:
    label: "Door (per unit)"
    hours_per_unit: 1.5
    coats: 2
  exterior_stucco:
    label: "Exterior Stucco"
    hours_per_100_sqft: 1.2
    coats: 2

markup:
  materials: 0.15              # 15% markup on paint/materials
  overhead: 0.10               # 10% overhead added to total

tax_rate: 0.095                 # 9.5% sales tax on materials only

payment_terms: "50% deposit required. Balance due upon completion."
validity_days: 30               # Quote valid for 30 days
```

---

## Phase 2 — Pricing Calculator (`core/calculator.py`)

Write a `QuoteCalculator` class that:

1. Loads `config/sop.yaml` on init
2. Accepts a list of line items, each with:
   - `surface_type` (key from `sop.yaml` surfaces)
   - `quantity` (sqft, linear ft, or unit count depending on surface type)
   - `notes` (optional string)
3. For each line item calculates:
   - Paint needed (gallons) based on sqft and coverage rate × coats
   - Paint cost with markup
   - Labor hours based on surface type rate
   - Labor cost at hourly rate
4. Rolls up to:
   - Subtotal (labor + materials)
   - Overhead
   - Tax (on materials only)
   - **Total**
5. Returns a structured dict that both the UI and PDF generator can consume

---

## Phase 3 — Streamlit App (`app.py`)

### Authentication
Use Streamlit `st.secrets` for a simple username/password check. Store credentials in `.streamlit/secrets.toml` (never committed to GitHub).

### UI Flow

**Step 1 — Client Info**
```
Client / Property Name    [text input]
Property Address          [text input]
Contact Name              [text input]
Contact Phone             [text input]
Contact Email             [text input]
Rep Name                  [selectbox — list of reps from sop.yaml]
Site Notes                [text area — condition, special instructions]
```

**Step 2 — Measurements**

Dynamic line item builder. User clicks "Add Surface" to add rows:
```
Surface Type     [selectbox — keys from sop.yaml surfaces]
Quantity         [number input — auto-labels unit (sqft / linear ft / units)]
Notes            [text input — e.g., "peeling paint", "two coats primer needed"]
[Remove]
```

Display a **live running estimate** (labor + materials subtotal) that updates as the user fills in measurements. This uses `calculator.py` directly — no API call needed.

**Step 3 — Review & Generate**

Show a full itemized breakdown table:
```
Surface          Qty     Paint (gal)   Paint Cost   Labor Hrs   Labor Cost
Exterior Wall    1200    6.9 gal       $399          9.6 hrs     $624
Interior Wall    800     4.6 gal       $266          4.8 hrs     $312
...
                                       Materials     Labor       
Subtotal                               $xxx          $xxx        $xxx
Overhead (10%)                                                   $xxx
Materials Tax (9.5%)                                             $xxx
TOTAL                                                            $xxx
```

Two buttons:
- **"Generate Scope with AI"** — calls Claude API (see Phase 4)
- **"Generate PDF Quote"** — calls `pdf_generator.py` (see below)

---

## Phase 4 — Claude AI Integration (`core/ai.py`)

### Function: `generate_scope_of_work(client_info, line_items, sop_config, site_notes)`

**What it does:**
Sends the job details to Claude and gets back:
1. A professional scope of work paragraph (ready to drop into the PDF)
2. A list of flags/warnings (anomalies, upsell opportunities, questions for the client)

**Prompt structure:**
```
System:
You are an expert estimator for a professional painting company. 
Your job is to write clear, professional scope of work descriptions 
for painting quotes and flag any unusual aspects of a job.

Always respond in valid JSON with this structure:
{
  "scope_of_work": "...",
  "flags": ["...", "..."]
}

User:
Company SOPs:
{sop_config as YAML string}

Client: {client_name} at {address}
Site notes: {site_notes}

Line items:
{line_items as formatted list}

Generate a professional scope of work paragraph and flag any issues or upsell opportunities.
```

**Display in Streamlit:**
- Scope text appears in an editable `st.text_area` so the rep can tweak it before PDF generation
- Flags appear as `st.warning()` callouts in yellow

---

## Phase 5 — PDF Generator (`core/pdf_generator.py`)

Use **ReportLab** to generate a branded PDF.

### PDF Layout

```
[LOGO]                          [Company Name]
                                [Phone | Email | Website | License]
────────────────────────────────────────────────────────────────────
PAINTING QUOTE                  Quote #: Q-2026-0042
                                Date: June 29, 2026
                                Valid Until: July 29, 2026

PREPARED FOR:                   PREPARED BY:
Client Name                     Rep Name
Address                         Apex Painting Co.
Phone | Email

────────────────────────────────────────────────────────────────────
SCOPE OF WORK

{scope_of_work text paragraph}

────────────────────────────────────────────────────────────────────
ITEMIZED ESTIMATE

Surface         Qty      Paint Cost   Labor Cost   Line Total
Exterior Wall   1200 sf  $399         $624         $1,023
...

                         Materials Subtotal:        $xxx
                         Labor Subtotal:            $xxx
                         Overhead (10%):            $xxx
                         Materials Tax (9.5%):      $xxx
                         ─────────────────────────────
                         TOTAL:                     $xxx

────────────────────────────────────────────────────────────────────
TERMS

{payment_terms from sop.yaml}
This quote is valid for {validity_days} days from the date above.

────────────────────────────────────────────────────────────────────
ACCEPTANCE

By signing below, you authorize Apex Painting Co. to proceed
with the scope of work described above at the quoted price.

Client Signature: ____________________  Date: ____________

Print Name:      ____________________
```

**Quote numbering:** Auto-increment using a simple `quotes_counter.txt` file stored locally (or a lightweight SQLite db if you want history).

---

## Phase 6 — Environment & Deployment

### `.env.example`
```
ANTHROPIC_API_KEY=your_key_here
```

### `.streamlit/secrets.toml` (never commit this)
```toml
[auth]
username = "fieldRep"
password = "yourpassword"

[anthropic]
api_key = "your_key_here"
```

### `requirements.txt`
```
streamlit
anthropic
reportlab
pyyaml
python-dotenv
```

### Railway Deployment
- Connect GitHub repo to Railway
- Set `ANTHROPIC_API_KEY` as a Railway environment variable
- Set start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- Auto-deploys on every push to `main`

---

## Build Order

1. `config/sop.yaml` — write the full config first, everything reads from this
2. `core/calculator.py` — pure Python, no dependencies, test with unit tests
3. `app.py` — Streamlit form with live estimate preview using calculator only
4. `core/pdf_generator.py` — branded PDF output, test with hardcoded sample data
5. `core/ai.py` — Claude integration for scope generation and flagging
6. Wire everything together in `app.py` — AI button → editable scope → PDF
7. Add auth, deploy to Railway

---

## Key Rules

- `sop.yaml` is the **only** place pricing or business rules live — never hardcode values in Python
- The app must work **without** clicking "Generate Scope with AI" — AI is an enhancement, not a dependency
- PDF must be download-ready instantly from the browser (use `st.download_button`)
- All monetary values rounded to 2 decimal places throughout
- Quote numbers must never repeat — use a persistent counter