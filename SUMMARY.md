# BigBell — Codebase Summary

> Grounded in the live repository (`/mnt/samurai/Primordial/AI Learnings/Creo`). "Built" = code exists and is wired into the running app. "Not built" = absent from the tree, with the exact missing file/symbol named. Two business problems come from the Biggbell brief supplied alongside this task; each maps to concrete code and concrete gaps.

---

## 1. What this codebase is

**BigBell v2.0.0** is a single `streamlit run app.py` application — the creator-success platform prototype for Biggbell. It is split into a Streamlit UI layer (`creo/ui/` + `app.py`) and a pure-Python core library (`creo/agents`, `creo/services`, `creo/storage`, `creo/rag`, `creo/models`, `creo/utils`) that has **zero Streamlit dependency** and is also exposed via an experimental FastAPI layer (`api/`).

### Run / test / lint
- App: `streamlit run app.py` (default provider = **mock**, fully functional without API keys)
- Tests: `.venv/bin/python -m pytest tests/ -v --cov=creo` → **82 passed, 83% covered on tested modules, 23% overall**
- Lint: `ruff` (not yet installed; `AGENTS.md` lists `pip install ruff`)
- Providers: `AI_PROVIDER` env or Settings page (`mock` / `openai` / `gemini`). Every AI agent follows the `_mock_*` (deterministic) / `_ai_*` (LLM) contract with transparent fallback (`creo/agents/base.py`).
- Embeddings: `ONNXMiniLM_L6_V2`, local CPU, no API key (`creo/rag/embeddings.py`).

### Architecture — one rule: data-source agnostic by design
`creo/storage/factories.py` exposes `get_creator_repo()`, `get_campaign_repo()`, `get_payment_repo()`, `get_follow_up_note_repo()`, `get_assignment_repo()`. Each dispatches on `DATA_SOURCE`:
- `"json"` (default) → `creo/storage/json/*`  (file persistence in `data/sample_data/`)
- `"db"` → `creo/storage/db/*` (SQLite via `data/creo.db`, 5 tables + migrations)
- `"api"` → `creo/storage/api/*` (live API adapters)

This is the single most important constraint for future work: **new sources plug in without touching services or UI**.

### Live data scale
| Entity | Sample (JSON) | DB table exists |
|---|---|---|
| Creators | 54 | yes |
| Campaigns | 22 | yes |
| Applications | 18 | yes (repo class dead code — see §6 tech-debt) |
| Assignments | 60 | yes |
| Payments | 15 | yes |
| Follow-up notes | 0 | yes |
| FAQs | 30 | — (Chroma vector store) |
| Chat threads | 7 | — (chat_history.json) |

---

## 2. The two business problems (as stated)

**Problem 1 — Demand Side (Brand Onboarding & Campaign Management):** Brand Success ops manually collect campaign requirements via calls/emails/WhatsApp/meetings, convert to briefs, find creators, chase brands for info/approvals/budget/timelines, manage status in spreadsheets, handle repetitive brand questions, coordinate stakeholders, manually build reports, and juggle multiple campaigns. Goal: automate every repetitive brand-lifecycle step.

**Problem 2 — Supply Side (Creator Onboarding & Creator Success):** Creator Success ops manually review applications, verify profiles/socials, check completeness/quality, categorize niches/languages, chase creators for missing info, answer repetitive creator queries, match creators to campaigns, chase deliverables, track participation, manage records, and handle payment info. Goal: free the team for relationship work.

---

## 3. What is BUILT (with code evidence)

### A. Core data model — `creo/models.py`
| Model | Key fields | Status |
|---|---|---|
| `Creator` | id, name, email, phone, primary_niche, secondary_niches, primary_language, secondary_languages, `platforms: dict[str, PlatformInfo]` (handle/followers/verified), content_quality_score, profile_completeness, avg_engagement_rate, **8-tier `tier` property** (Rising/Growth/Pro/Elite), status, earnings, campaigns_completed, verified fields, suggested_tags | LIVE |
| `Campaign` | title, brand, description, requirements, budget, deadline, target_niches, target_languages, status, assigned_creators | LIVE |
| `Application` | creator_id, campaign_id, status, score, ai_notes, reviewer_notes, source, letter | LIVE (storage class exists but is **dead code** — see §6 tech-debt) |
| `Payment` | creator_id, campaign_id, amount, status, due_date, processed_at, notes | LIVE |
| `CampaignAssignment` | **8-state lifecycle enum** `AssignmentStatus` (matched→invited→accepted→brief_sent→content_received→approved→paid / rejected) | LIVE |
| `FollowUpNote` | campaign_id, note, created_at | LIVE |
| `ChatMessage` | creator_id, role (creator/agent), content, channel (whatsapp/email/in_app), kind (incoming/auto/manual), faq_id, confidence | LIVE |
| `FAQ` | question, answer, category | LIVE |

Status enums: `CreatorStatus` (pending/onboarding/active/inactive/rejected), `AssignmentStatus` (8 states, exhaustive).

### B. AI Agents — `creo/agents/` (all subclass `BaseAgent`, all use `_mock_*`/`_ai_*`)
| Agent | Method | What it does | File |
|---|---|---|---|
| `BaseAgent` | — | Provider switch (`use_mock`/`use_openai`/`use_gemini`), 10s LLM timeout, `_run_llm_chain`, `_stream_llm`, API debug logging | `base.py` |
| `MatchingAgent` | `match(creator, campaign)` | Semantic niche matching (ONNX embedding cosine similarity + heuristic fallbacks), language, reach, engagement, quality, completeness, budget-fit. Weights configurable in `config.py` (`MATCH_NICHE_WEIGHT=0.30`, `MATCH_ENGAGEMENT_WEIGHT=0.15`, …). Returns scored dict + `alignment_points` + `match_quality`. | `matching.py` |
| `ApplicationReviewerAgent` | `review(creator, campaign)` | Scores application (niche/quality/engagement/completeness/language), builds `risks` list, `feedback`, `recommendation`. `VERDICT_MIN_SCORE`/`VERDICT_APPROVE_THRESHOLD` from config. | `application_reviewer.py` |
| `CategorizationAgent` | `categorize(creator)` | Ranks creator against all niches/languages (embedding + heuristics), suggests tier + tags. | `categorization.py` |
| `VerificationAgent` | `verify(creator)` | Profile-completeness, platform verification, follower-growth sample, content-quality flags; `overall_score`; `verified = overall >= 60` (`VERIFY_MIN_SCORE`). | `verification.py` |
| `CreatorExtractionAgent` | `parse_text(raw)` / `extract_pdf_text` | Regex-first extraction of name/email/phone/niche/language/platforms (with `k`/`M` follower suffixes, handle-context platform detection, "verified"/"blue tick" flag), then LLM parse, with deterministic fallback. `missing_required_fields()` validator drives the UI gap-picker. | `extraction.py` |
| `QueryAgent` | `answer(q)` / `stream_answer(q)` | RAG FAQ retrieval → LLM answer with source citations; streaming. | `query.py` |

### C. Services (all extend `CachedRepositoryService[T]`)
| Service | Responsibilities | File |
|---|---|---|
| `CreatorService` | search (name/niche/language/email), filter_by_status/niche/language, tier & distribution stats, status + profile-completeness updates, pending/onboarding/active/inactive counts, `get_random_pending`. | `creator_service.py` |
| `CampaignService` | search, filter_by_status/niche, active count, total budget, budget range, active campaigns. | `campaign_service.py` |
| `AssignmentService` | The **8-state lifecycle**: `assign()`, `unassign()`, `update_status()`, `advance_status()`, `get_for_campaign/creator/campaign_creator`, `is_assigned`, `get_campaign_summary`. `NEXT_STATUS` map + `STATUS_COLORS`/`STATUS_LABELS`. | `assignment_service.py` |
| `PaymentService` | filter_by_status (pending/processed/paid/disputed), per-creator & per-campaign, totals, status updates. | `payment_service.py` |
| `FollowUpNoteService` | `get_for_campaign` notes. | `follow_up_service.py` |
| `HelpdeskService` | Thread store (per-creator), `receive_question` (auto-answer via FAQ embedding similarity + `AUTO_ANSWER_MAX_DIST=1.30` confidence gates), `suggest_replies` (KB + LLM), `send_reply`, `create_mock_creator` (dedup by name), `stats`, persistence to `chat_history.json`. | `helpdesk_service.py` |

### D. RAG / Knowledge base — `creo/rag/`
- `embeddings.py` — `ONNXEmbeddings` (local CPU), `cosine_similarity`, `get_embeddings()` provider-fallback chain (openai → gemini → onnx).
- `vector_store.py` — `VectorStoreManager` singleton wrapping Chroma (persistent at `data/vector_store/`).
- `retrieval.py` — `FAQRetriever.search(query, k)` / `search_by_category`.
- `faq_kb.py` — `FAQKnowledgeBase`: seeds from `faq.json` + user-uploaded FAQs (`add_uploaded_faqs`), PDF FAQ ingestion (`parse_faq_pdf`), confidence-from-distance (`confidence_for_distance`: high ≤1.15, medium ≤1.45, auto-answer threshold 1.30), reindex.
- `document_loader.py` — `load_faq_documents()`.

### E. Storage backends
**JSON** (`creo/storage/json/`): creator, campaign, payment, application, assignment, note repos — each a thin CRUD over `data/sample_data/*.json`.

**SQLite** (`creo/storage/db/`): ORM models (`orm_models.py`), session factory, migrate (`migrate.py`), and 5 repos mirroring the JSON ones. Fully wired into `get_*_repo()` for `DATA_SOURCE="db"`.

**API** (`creo/storage/api/`):
| Adapter | Source | What it returns | Notes |
|---|---|---|---|
| `YouTubeCreatorRepository` | `youtube` | **Creators** (keyword search "creator") | `use_real_api` ↔ `YOUTUBE_API_KEY`; `_mock_creators()` 6 deterministic channels. **The pattern Solution A proposes to replicate.** |
| `InstagramCampaignRepository` | `instagram` | **Campaigns** from brand's own media (`graph.instagram.com/v12.0/me/media`) | Read-only; `add/delete/save_all` raise `NotImplementedError`. **NOT a creator-discovery adapter.** |
| `WhatsAppPaymentRepository` | `whatsapp` | **Payments** (mock only — `list_all` always returns `_mock_payments`) | No real WhatsApp fetch. |

### F. UI — `creo/ui/pages/` (10 pages, all Streamlit)
1. **Dashboard** (`dashboard.py`) — at-a-glance metrics: creators by status, campaigns by status, budget, payments, applications pipeline, recent assignments, overdue deliverables, hot links to each page.
2. **All Creators** (`creators.py`) — search bar + status/niche/language filters, add/import/export CSV, full creator cards (platforms, engagement, earnings, notes, assignments).
3. **Add Creator with AI** (`add_creator.py`) — text/WhatsApp/PDF paste → extraction → **preview with missing-field picker** (uses `missing_required_fields`) → creates creator via `HelpdeskService`-style flow.
4. **Review & Classify** (`creator_validation.py`) — three-stage pipeline: **Needs review** (ApplicationReviewerAgent on applications), **Needs verification** (VerificationAgent), **Needs classification** (CategorizationAgent → niche/language/tags). Mock recent-posts preview.
5. **Match Creators** (`campaigns.py`) — campaign CRUD + **Find Creators** panel (niche/language/min-followers filter) + **Run smart matching** (`MatchingAgent` over the pool, ranked) + assign individually or bulk + per-assignment **Advance / Reject / Unassign** buttons driving `AssignmentService`.
6. **Deadlines & Notes** (`deadlines.py`) — campaign deadlines (overdue / due-soon 7-day metric), pending deliverables by workflow status, campaign notes CRUD.
7. **Payments** (`payments.py`) — full payment CRUD (add/edit/delete dialogs), status tracking, disputes, per-creator payout table, CSV import/export.
8. **Configure** (`settings.py`) — AI provider + keys, model selection (OpenAI/Gemini fetched live), data-source selector, YouTube/Instagram/WhatsApp keys, debug logging toggle, persists to `.env`.
9. **API Logs** (`api_logs.py`) — LLM request/response/error inspector with duration timing.

Plus `creo/ui/components/` — `layout.py` (init_app_state/sync_config/render_sidebar_stats), `cards.py` (creator avatar), `platforms.py` (platform icons/links/grid), `mock_content.py`.

### G. REST API — `api/` (experimental)
- `main.py` — FastAPI app, CORS, `/api/v1/health`, routes for `/faq` and `/creators`.
- `faq.py` — `GET /ask` (QueryAgent answer) + `/health`.
- `creators.py` — `GET /` (filterable list), `GET /{id}` (full creator dump).

---

## 4. What is NOT BUILT — gaps mapped to the two problems

> Verified by: searching the tree for the symbol; confirming absence; checking the pitch's proposed additions are not present.

### Problem 1 — Demand Side (Brand Onboarding & Campaign Management)

| # | Business task (from brief) | Status | Gap / missing code |
|---|---|---|---|
| 1 | **Convert brand calls/emails/WhatsApp → structured campaign briefs** | ❌ Not built | No `CampaignExtractionAgent`. The only extraction agent (`CreatorExtractionAgent`) targets *creator* profiles. The campaign add form (`campaigns.py` ~line 71) is manual text inputs only — no text/PDF/WhatsApp → brief parsing, no "missing brief fields" picker. |
| 2 | **Instagram creator discovery by region/niche/language/reach** | ❌ Not built | Confirmed gap. No `InstagramCreatorRepository` (only `InstagramCampaignRepository` for *brand media*). `Creator` has **no `region` field**. `.env` ships `INSTAGRAM_API_KEY=''`. |
| 3 | **Filter/sort creators by region** | ❌ Not built | `CreatorService` has `filter_by_niche` / `filter_by_language` but **no `filter_by_region`**. UI (`creators.py`, `campaigns.py`) filter toolbars have no Region dropdown. |
| 4 | **Brand status updates / automated campaign reporting** | ❌ Not built | Dashboard shows internal metrics only. No campaign-performance report generator, no branded report PDF, no scheduled status digests to brands. |
| 5 | **Automated brand follow-ups (missing info / approvals / budget / timelines)** | ❌ Not built | `FollowUpNoteService` is internal campaign notes only. No outbound message composer for brands, no reminder cadence. |
| 6 | **Brand-facing query handling / FAQ** | ❌ Not built | `HelpdeskService` is creator→support only (inbound auto-answer). No brand-side chatbot, no brand status portal. |
| 7 | **Multi-stakeholder coordination** | ⚠️ Partial | The 8-state assignment machine handles creator↔campaign handoff, but there is no stakeholder-role/approval workflow (no approval gates, no stakeholder routing, no brand-signoff step). |

**Built for demand side (the foundation):** campaign CRUD, creator search by niche/language/min-followers, smart matching (`MatchingAgent`), the 8-state assignment lifecycle, payments, deadlines. The demand pipeline exists end-to-end for *ops-driven* campaigns but lacks *brand self-service* and *proactive brand communication*.

### Problem 2 — Supply Side (Creator Onboarding & Creator Success)

| # | Business task (from brief) | Status | Gap / missing code |
|---|---|---|---|
| 1 | **Review creator applications & profiles** | ✅ Built | `ApplicationReviewerAgent.review()` + `creator_validation.py` "Needs review" stage. |
| 2 | **Verify creator info & social accounts** | ✅ Built | `VerificationAgent.verify()` + "Needs verification" stage. |
| 3 | **Check profile completeness & content quality** | ✅ Built | VerificationAgent emits completeness + content-quality flags + overall_score (≥60 = verified). |
| 4 | **Categorize creators (niche & language)** | ✅ Built | `CategorizationAgent.categorize()` + "Needs classification" stage. |
| 5 | **Collect missing information from creators** | ⚠️ Partial / not systematic | `CreatorExtractionAgent` + `missing_required_fields()` let *ops* enter a creator and pick what's missing, but there is no **outbound collection workflow** — no auto-triggered "please provide X" message to the creator, no response capture-and-refill loop. |
| 6 | **Answer repetitive creator queries** | ✅ Built | `HelpdeskService.receive_question` auto-answers from FAQ KB (embedding similarity); `suggest_replies` (KB + LLM); manual fallback. Full inbox UI (`helpdesk.py`). |
| 7 | **Match creators to campaigns** | ✅ Built | `MatchingAgent.match()` with configurable weights, ranked results, assign in `campaigns.py`. |
| 8 | **Follow up on deliverables & deadlines** | ✅ Built | `deadlines.py` + `FollowUpNoteService` + `AssignmentStatus.CONTENT_RECEIVED` state. |
| 9 | **Track creator participation across campaigns** | ✅ Built | `AssignmentService.get_for_creator(creator_id)`, `CampaignAssignment`, payment linking. |
| 10 | **Manage creator records across systems** | ⚠️ Single source only | One persistence source (JSON/DB) selected by `DATA_SOURCE`. No sync to external CRMs/social suites. |
| 11 | **Proactive lifecycle messaging to creators** | ❌ Not built | Confirmed gap (pitch Solution B). `AssignmentService.assign()`/`advance_status()`/`update_status()` have **no notification hook**. When `MATCHED→INVITED`, nothing messages the creator. `ChatMessage` has **no `related_campaign_id` / `related_assignment_id`** fields. Briefs/invites/nudges are sent manually (or not at all) via the helpdesk reply box. |

### Cross-cutting gaps (affect both sides)

| Gap | Evidence |
|---|---|
| **No `MessagingOptOut` model** for compliance | Absent from `models.py`. The pitch proposes it; it does not exist. |
| **No `AssignmentNotifier` agent** | Absent from `creo/agents/`. No notifier file; `agents/__init__.py` is empty. |
| **No composite repository** | `get_creator_repo()` returns a single repo per source. No `CompositeCreatorRepository` merging Meta + YouTube + local (pitch proposes it). |
| **No `BaseApiRepository` reuse** | `creo/storage/api/base_api.py` defines `BaseApiRepository` with `use_real_api`/`_check_key`/`_mock_data`, but **nothing subclasses it** — `YouTubeCreatorRepository` reimplements `use_real_api` directly. Dead code. |
| **`JsonApplicationRepository` is dead code** | `creo/storage/json/application_repo.py` defines a class wrapping `load_applications`/`save_applications`, but it is **never imported anywhere**; there is no `ApplicationRepository` ABC in `base.py`, no `get_application_repo()` in `factories.py`. `creator_validation.py` and `dashboard.py` call `load_applications()`/`save_applications()` from `json_io` directly, bypassing the repo pattern. |
| **No `ChannelDispatcher` / WhatsApp Business send** | `WhatsAppPaymentRepository` is read-only mock. `HelpdeskService.send_reply` only *stores* a `ChatMessage`; it does not actually transmit over WhatsApp/Email. Channels are a model field, not a send path. |

---

## 5. Build quality & current engineering status

### Test suite
- **Command:** `.venv/bin/python -m pytest tests/ -v --cov=creo`
- **Result:** 82 passed, 0 failed (after installing `reportlab` + `pypdf` — see §5 dependency drift).
- **Coverage: 23% overall.** Hotspots:
  - `models.py` 100%, `mock_content.py` 100%, `storage/base.py` 100%.
  - `helpdesk_service.py` 85%, `config.py` 81%, `json_io.py` 75%.
  - `matching.py` ~partial (mock scored, AI fallback tested), `verification.py` 67% (mock path), `application_reviewer.py` partial, `categorization.py` ~partial.
  - **Zero coverage:** `campaign_service.py` (0%), `payment_service.py` (0%), `follow_up_service.py` (0%), `assignment_service.py` (35% — only `NEXT_STATUS`/`STATUS_LABELS` transition tables), all DB repos (0%), `storage/api/*` (0%), `storage/factories.py` (26%), `rag/vector_store.py` (0%), `rag/retrieval.py` (0%), `rag/document_loader.py` (0%), `rag/embeddings.py` (58%), full `query.py` (0%), **all UI pages (0%)**, **all API routes (0%)**.
- Coverage tests are **mock-mode deterministic** (no live LLM/api calls). `BaseAgentTimeout.test_llm_timeout_constant_is_10_seconds` locks the timeout.

### Linting
- `AGENTS.md` says install `ruff` then run `ruff check creo/ tests/` + `ruff format --check`. **Not yet installed** in the environment; no `ruff` config in `pyproject.toml` beyond defaults.

### Environment / dependency drift (real, blocking issues found)
1. **Dead `.venv`.** The committed `.venv` Python was a symlink to a uv-managed CPython 3.14 (`/home/doc/snap/code/.../cpython-3.14.5...`) that **does not exist** on this machine. `.venv/bin/python` was broken → pytest could not run. Recreated with `uv venv --clear --python 3.13` + `uv pip install -e ".[dev]"`. Now green.
2. **`reportlab` / `pypdf` not in `pyproject.toml`.** They are in `requirements.txt` (lines 13–14) and `extraction.py`/`faq_kb.py` import them, but `pyproject.toml` `[project].dependencies` omits both. `uv pip install -e ".[dev]"` (the modern path) leaves them out → **2 tests fail immediately** (`test_parse_pdf_and_extract`, `test_pdf_round_trip`). Fix: add `pypdf>=5.0.0` and `reportlab>=4.0.0` to `pyproject.toml` dependencies (or a `pdf` extra). This is the cause of the two initial failures, not a code defect.
3. **Secrets in repo.** `.env` is tracked and contains a real `GEMINI_API_KEY='AQ.Ab8...'` and `DEBUG_LOGGING='true'`. Should be gitignored + key rotated.
4. **`config.py` `EMBEDDING_MODEL` unused for the local path.** Defaults to `"text-embedding-3-small"` but `get_local_embeddings()` always uses ONNX; the OpenAI embedding path in `rag/embeddings.py:get_embeddings` reads it. Consistent only if `provider=openai`. Not a bug, but a latent config mismatch.
5. **`AGENTS.md` is stale on linting.** Says "ruff is not installed yet — install with: `.venv/bin/pip install ruff`" but recommends `.venv/bin/python -m pytest`. The venv has no `pip` (uv-managed). Should be `uv pip install ruff`.

### Application smoke test
- `import app` / `import creo` → **OK** (clean import; streamlit warnings about missing `ScriptRunContext` are expected when importing headless — irrelevant at runtime).

---

## 6. Future work — prioritized roadmap

The existing `CREO_CLIENT_PITCH.md` already documents a 5-phase plan. Below, I fold the pitch's two solutions **plus** the supply-side gaps my audit uncovered, each with the exact file(s) to touch.

### Phase A — Supply-side completion (Problem 2)
| Task | Files | Est. |
|---|---|---|
| **A-proactive-messaging:** add `AssignmentNotifier` agent (`_mock_*`/`_ai_*`); hook `AssignmentService.assign`/`advance_status`/`update_status`; add `related_campaign_id` + `related_assignment_id` to `ChatMessage`; Draft-first + per-creator `MessagingOptOut` model; `AssignmentService` already owns the lifecycle so this is an injection, not a rewrite. | `creo/agents/notifier.py` (new), `creo/services/assignment_service.py`, `creo/models.py` | 2 dev + 1 test |
| **A-collection-loop:** when VerificationAgent flags missing profile fields, queue an outbound "please provide X" message to the creator and re-run extraction on their reply. | `creo/services/creator_service.py`, `creo/services/helpdesk_service.py` | 1.5 dev + 1 test |
| **A-channel-dispatch:** real WhatsApp Business API send + SMTP email send in `HelpdeskService.send_reply` (today it only stores). In-app is already the guaranteed fallback. | `creo/services/helpdesk_service.py`, `creo/storage/api/whatsapp.py`, `creo/utils/runtime_settings.py` | 1.5 dev + 1 test |

### Phase B — Demand-side completion (Problem 1)
| Task | Files | Est. |
|---|---|---|
| **B-campaign-extraction:** `CampaignExtractionAgent` (mirror `CreatorExtractionAgent`) — parse brand call/email/WhatsApp/PDF → structured `Campaign` brief + missing-fields picker. | `creo/agents/extraction.py` (extend), new campaign form in `campaigns.py` | 1 dev + 1 test |
| **B-instagram-discovery:** add `region: Optional[str]` to `Creator`; `InstagramCreatorRepository` (Meta Creator Marketplace discovery fetch + `_mock_creators`, subclassing `CreatorRepository` + reusing `BaseApiRepository`); route in `factories.get_creator_repo()` for `source="api"`; `CreatorService.filter_by_region` + UI Region filter. Multi-source fallback: Meta ∪ YouTube ∪ local CSV. | `creo/models.py`, `creo/storage/api/instagram.py`, `creo/storage/factories.py`, `creo/services/creator_service.py`, `creo/ui/pages/creators.py`, `creo/ui/pages/campaigns.py` | 2 dev + 1 test |
| **B-brand-reports:** generate campaign performance reports (PDF) + scheduled brand status digests. | new `creo/services/report_service.py`, `creo/rag/faq_kb.py` (report templates) | 2 dev + 1 test |
| **B-brand-portal:** brand-facing query bot (reuse `QueryAgent` against a brand FAQ KB) + campaign status view. | `creo/ui/pages/` (new page), `creo/rag/` | 1.5 dev + 1 test |

### Tech-debt / hygiene (do first — unblocks reliability)
| Task | Why | Est. |
|---|---|---|
| Sync `pyproject.toml` deps with `requirements.txt` (add `pypdf`, `reportlab`). | Today `uv pip install -e ".[dev]"` produces a failing test run. | 0.25 |
| Add `ruff` config to `pyproject.toml` + CI; fix `AGENTS.md` pip→uv. | Linting is documented but not wired. | 0.5 |
| Delete dead `creo/storage/api/base_api.py` or actually use it. | Dead code; `YouTubeCreatorRepository` reimplements it. | 0.25 |
| Add `region` to `orm_models.py` DB mapper too (parallel to JSON repo). | Consistency when DB source is selected. | 0.5 |
| Git-ignore `.env`; rotate the leaked Gemini key. | Security. | 0.25 |
| Add a `CompositeCreatorRepository` so multi-source discovery is clean, not ad-hoc. | Pitch proposes it; makes Phase B scalable. | 1 dev |
| Either wire `JsonApplicationRepository` into `get_application_repo()` (and add the ABC + factory entry) or delete it. | Currently dead code; applications are read/written via `json_io` directly, breaking the repo abstraction. | 0.25 |

### Test-coverage targets (stretch, high-ROI)
- `CampaignService`, `PaymentService`, `AssignmentService.advance_status` (behavioral, not just the `NEXT_STATUS` table).
- DB repo round-trips (SQLite).
- API routes (`api/routes/*`) via `TestClient`.
- `AssignmentNotifier` end-to-end (status transition → ChatMessage created in thread).

---

## 7. One-paragraph status

BigBell is a **complete, runnable creator-success prototype** with both Problem-2 supply-side ops (extraction → review → verify → categorize → match → helpdesk → deadlines → payments) and the Problem-1 demand-side core (campaign CRUD → find creators → smart match → 8-state assignment lifecycle → payments), all behind a clean data-source abstraction (`get_*_repo()`) and a deterministic `_mock_*`/`_ai_*` AI switch. **What it ships without** is proactive *outbound* messaging on both sides: there is no `AssignmentNotifier` to message creators when an assignment advances (`ChatMessage` lacks the foreign keys), no Instagram *creator* discovery adapter (only an Instagram *campaign-media* adapter; `Creator` has no `region`), and no campaign-brief extraction from brand text. The pitch doc (`CREO_CLIENT_PITCH.md`) already plans these as additive phases (A1→A2, B1→B3) that reuse existing patterns — the work is real, bounded, and low-risk because `AssignmentService` owns the lifecycle and `HelpdeskService` + `ChatMessage` are the natural injection points.

---

## Appendix — file map (truth table of what was read)

```
app.py                              # Streamlit entry + 10-page navigation
AGENTS.md                           # repo run/test/lint instructions
README.md                           # feature overview + architecture
CREO_CLIENT_PITCH.md               # client-facing solution plan (Solutions A & B)

creo/
├── models.py                        # 8 Pydantic models + 2 enums          [100% cov]
├── config.py                        # weights, thresholds, niche/lang lists       [81%]
├── agents/
│   ├── base.py                     # BaseAgent: provider switch, LLM, logging
│   ├── matching.py                  # MatchingAgent (scored match dict)
│   ├── application_reviewer.py      # ApplicationReviewerAgent
│   ├── categorization.py            # CategorizationAgent
│   ├── verification.py              # VerificationAgent                         [67%]
│   ├── extraction.py                # CreatorExtractionAgent (text + PDF)
│   ├── query.py                     # QueryAgent (RAG FAQ answer)               [0%]
│   └── __init__.py                  # EMPTY — no exports
├── services/
│   ├── base.py                      # CachedRepositoryService[T]
│   ├── creator_service.py           # CreatorService                           [62%]
│   ├── campaign_service.py          # CampaignService                          [0%]
│   ├── assignment_service.py        # AssignmentService + NEXT_STATUS machine  [35%]
│   ├── payment_service.py           # PaymentService                           [0%]
│   ├── follow_up_service.py         # FollowUpNoteService                      [0%]
│   └── helpdesk_service.py          # HelpdeskService                          [85%]
├── storage/
│   ├── base.py                      # ABCs (Creator/Campaign/Payment/...)     [100%]
│   ├── factories.py                 # get_*_repo() source dispatch            [26%]
│   ├── csv_handler.py               # CSV export/import                          [0%]
│   ├── json/                        # JSON repos (creator, campaign, payment,
│   │                               #   application, assignment, note)
│   ├── db/                          # SQLite: orm_models + migrate + 5 repos     [0%]
│   └── api/
│       ├── base_api.py              # DEAD CODE (BaseApiRepository, unused)
│       ├── youtube.py               # YouTubeCreatorRepository (pattern template)
│       ├── instagram.py             # InstagramCampaignRepository (brand media, read-only)
│       └── whatsapp.py              # WhatsAppPaymentRepository (mock only)
├── rag/
│   ├── embeddings.py                # ONNXMiniLM_L6_V2 local + fallback        [58%]
│   ├── vector_store.py              # VectorStoreManager (Chroma singleton)     [0%]
│   ├── retrieval.py                 # FAQRetriever                              [0%]
│   ├── faq_kb.py                    # FAQKnowledgeBase                          [61%]
│   └── document_loader.py           # load_faq_documents                         [0%]
├── ui/
│   ├── components/                  # layout, cards, platforms, mock_content
│   └── pages/                       # dashboard, creators, add_creator,
│                                    # creator_validation, campaigns, deadlines,
│                                    # payments, settings, helpdesk, api_logs
└── utils/
    ├── json_io.py                   # typed JSON load/save                       [75%]
    ├── dates.py                     # today_str, days_until                    [33%]
    ├── runtime_settings.py          # provider/keys/data_source in-memory        [48%]
    ├── debug_logging.py             # APILogEntry + add_log/clear_logs          [69%]
    └── mock_content.py              # deterministic mock posts                 [100%]

api/
├── main.py                          # FastAPI app, CORS, /health
└── routes/
    ├── faq.py                       # GET /ask (QueryAgent)
    └── creators.py                  # GET / + GET /{id}

tests/
├── conftest.py                      # sample_creator, sample_campaign, minimal_creator, ...
├── test_models.py                   # tiers, properties, enum values, defaults
├── test_services.py                 # NEXT_STATUS transitions, CreatorService filters
├── test_agents.py                   # Matching/Categorization/Review/Verification mock scores,
│                                    # extraction (incl. PDF), extraction timeout
└── test_helpdesk.py                 # FAQ parsing, PDF round-trip, confidence, HelpdeskService
                                     # (auto-answer, no-match, persistence, suggestions,
                                      # create_mock_creator dedupe, stats, independent threads)

data/
├── sample_data/                     # 54 creators, 22 campaigns, 60 assignments,
│                                    #   18 applications, 15 payments, 30 FAQs, 7 chat msgs
├── creo.db                          # SQLite (5 tables, seeded)
└── vector_store/                    # ChromaDB persistence (auto-created)
```

### Legend
- `[NN%]` = pytest-cov line coverage for that module.
- **Bold** items = the file(s) a proposed task would touch first.
