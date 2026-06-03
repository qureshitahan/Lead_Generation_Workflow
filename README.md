# Lead Generation Workflow

A recruiting outreach automation platform (MVP). It helps a staffing/recruiting
team find fresh job openings, decide whether each opening is from a **direct
employer** (vs another recruiting/staffing firm), enrich company/contact data,
match available candidates to openings, and prepare **personalized email and
voice outreach** — all with a human in the loop.

> **Safety first:** nothing is emailed or called automatically. Every job,
> contact, email, and call requires explicit human approval. The default
> integration providers are *stubs* that never transmit anything.

---

## Architecture

```
Lead_Generation_Workflow/
├── backend/          FastAPI + SQLAlchemy (Python) REST API
│   ├── app/
│   │   ├── core/         config (env vars)
│   │   ├── db/           engine, session, base
│   │   ├── models/       SQLAlchemy data model (the schema)
│   │   ├── schemas/      Pydantic request/response models
│   │   ├── services/     business logic (see below)
│   │   └── api/routes/   HTTP endpoints
│   ├── scripts/seed.py   end-to-end smoke test + demo data
│   └── sample_data/      example Bright Data export
└── frontend/         React + Vite + TypeScript + Tailwind dashboard
    └── src/
        ├── api/          typed API client
        ├── components/   layout + UI primitives
        └── pages/        Dashboard, Jobs, Companies, Contacts, Candidates,
                          Matches, Email Drafts, Call Queue, Import
```

### Service layer (modular, swappable)

| Concern | Module | Notes |
|---|---|---|
| Job ingestion | `services/ingestion/` | One adapter per source (Bright Data, Apify, manual). Add a source = add one adapter. |
| Normalization / dedup | `services/normalization.py` | Cleans fields; dedups by `job_posting_id`, else by fingerprint. |
| Relevance scoring | `services/classification/relevance.py` | 0–100 score + reason, driven by `role_profiles.py`. |
| Direct-employer detection | `services/classification/direct_employer.py` | Red-flag phrases (“our client is seeking”, “staffing”, …). |
| Company enrichment | `services/enrichment/` | `stub` / `apollo` / `zoominfo` behind one interface. |
| Contact discovery + ranking | `services/contacts.py` | Ranks target titles by usefulness + company size. |
| Candidate parsing | `services/candidates.py` | Heuristic resume → structured profile. |
| Matching | `services/matching.py` | 0–100 match score, matched/missing skills, pitch. |
| Email drafting | `services/email_generation.py` | Concise personalized first-touch email. |
| Email sending | `services/email_providers/` | `stub` (no send) → Postmark/SendGrid later. |
| Voice scripts | `services/voice.py` | Transparent AI-disclosure script. |
| Voice calling | `services/voice_providers/` | `stub` (no dial) → Twilio/ElevenLabs later. |
| Audit log | `services/audit.py` | Every decision + human action is recorded. |

---

## Quick start

### 1. Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # optional; defaults work out of the box

# (optional) load demo data + run an end-to-end smoke test:
python -m scripts.seed

# start the API
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173  (it proxies `/api` to the backend on :8000)

---

## First workflow (Milestone 1)

1. Go to **Import Jobs**, choose **Bright Data**, and upload
   `backend/sample_data/brightdata_sample.json` (or paste JSON/CSV).
2. The system stores the raw record, normalizes it, deduplicates, and runs the
   **relevance** + **direct-employer** classifiers.
3. Go to **Jobs** to see scores and classifications. Approve/reject jobs.
4. Open a job to see the full classification reasoning and matched candidates.

### Milestone 2 (candidates, matching, emails)
- Add a candidate under **Candidates** (paste a resume; skills/roles/experience
  are parsed automatically).
- Open an approved job → **Match candidates** → review scores + pitches.
- From **Matches**, generate an **email draft**; edit and approve it under
  **Email Drafts**.

### Milestone 3 (enrichment + contacts)
- On **Companies**, click **Enrich** to fetch firmographics and discover ranked
  contacts (stub data until `ENRICHMENT_PROVIDER=apollo|zoominfo` + an API key).
- Approve a contact for outreach under **Contacts**.

### Milestone 4 (sending + voice) — wiring points are in place
- Set `EMAIL_PROVIDER` / `VOICE_PROVIDER` and the relevant keys in `.env`, then
  implement the provider skeletons in `services/email_providers/` and
  `services/voice_providers/`.

---

## Configuration

All config is environment-driven — see `backend/.env.example`. Everything runs
on stub providers with no keys. Add keys incrementally:

- `BRIGHTDATA_API_KEY`, `APIFY_API_TOKEN` — job sources
- `ENRICHMENT_PROVIDER` + `APOLLO_API_KEY` / `ZOOMINFO_API_KEY` — enrichment
- `EMAIL_PROVIDER` + `POSTMARK_SERVER_TOKEN` / `SENDGRID_API_KEY` — sending
- `VOICE_PROVIDER` + `TWILIO_*` / `ELEVENLABS_API_KEY` — voice calls
- `TARGET_ROLES` — roles that drive relevance scoring

## Compliance & safety

- Do-not-contact flags at company and contact level (`Suppression`).
- Outreach history for cooldowns / rate limits (`OutreachHistory`).
- Audit log of every classification, draft, approval, send, and call.
- No mass-blasting: per-step human approval is required by design.

## Notes

- MVP uses SQLite and `create_all` on startup. For production, switch
  `DATABASE_URL` to Postgres and introduce Alembic migrations.
- Classifiers are rule-based (transparent, free, fast). Interfaces are designed
  so an LLM backend can be added later without changing callers.
