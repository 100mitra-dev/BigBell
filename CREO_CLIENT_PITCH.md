# BigBell — Creator Discovery & Campaign Messaging
## Client Presentation & Delivery Plan

> Grounded in the BigBell codebase (`app.py` · `creo/`). All "built" claims are live in the repo; all "proposed" items are additive and reuse existing conventions.

---

## Agenda
1. The two business problems (as you described them)
2. What BigBell already does well today (evidence)
3. The gaps — where your pain lives in the code
4. Solution A: Creator Discovery by criteria (region · niche · language · reach)
5. Solution B: Automated campaign messaging to creators
6. Implementation plan · timeline · value
7. Risks & mitigations
8. Client Q&A prep (cross-examination answers)
9. One-page summary

---

## 1. The two business problems

| # | Your words | What it really is |
|---|------------|-------------------|
| 1 | *"Get all creators based on criteria on Instagram like region/niche etc"* | On-demand creator **discovery + segmentation** by region, niche, language, and reach, sourced from Instagram (Meta ecosystem). |
| 2 | *"Automate the chatting/messaging the creators about the campaigns"* | **Proactive, lifecycle-triggered** outbound messaging (invoices, briefs, nudges) over WhatsApp/email/in-app — not just inbound auto-reply. |

---

## 2. What BigBell already does (no re-invention needed)

| Capability | Where | Status |
|------------|-------|--------|
| Creator data model: `name, email, platforms{handle,followers,verified}, primary_niche, secondary_niches, primary_language, secondary_languages, content_quality_score, avg_engagement_rate, tier` | `creo/models.py` · class `Creator` | LIVE |
| Niche / language / status / keyword search over the creator pool | `creo/services/creator_service.py` · `CreatorService` | LIVE |
| Niche-match scoring via **semantic embedding similarity** + heuristics | `creo/agents/matching.py` · `MatchingAgent` (weights in `creo/config.py`: `MATCH_NICHE_WEIGHT=0.30`, `MATCH_ENGAGEMENT_WEIGHT=0.15`, …) | LIVE |
| Campaign-campaign assignment workflow with a real **status machine** | `creo/services/assignment_service.py` · `AssignmentService` · `NEXT_STATUS` | LIVE |
| Inbox + auto-answer from an FAQ knowledge base (embedding similarity) + manual reply | `creo/services/helpdesk_service.py` · `HelpdeskService` | LIVE |
| Chat message model with channels `whatsapp \| email \| in_app` and kinds `incoming \| auto \| manual` | `creo/models.py` · class `ChatMessage` | LIVE |
| AI-provider switching: `_mock_*` (deterministic) + `_ai_*` (LLM) with transparent fallback | `creo/agents/base.py` · `BaseAgent.use_mock/use_openai/use_gemini` | LIVE |
| Storage abstraction: `CreatorRepository` with `json`, `db`, and `api` backends selected by `DATA_SOURCE` | `creo/storage/factories.py` · `get_creator_repo()` | LIVE |
| API-key configuration, persisted to `.env` | `creo/ui/pages/settings.py` · `persist_config()` | LIVE |

**Key architectural fact:** BigBell is *data-source agnostic by design*. `get_creator_repo()` already swaps between local JSON, a database, and a live API adapter. The YouTube live adapter (`YouTubeCreatorRepository`) already demonstrates the exact pattern we'd reuse for Instagram.

---

## 3. The gaps (your pain, mapped to code)

### Gap 1 — Instagram creators are not discoverable
- `get_creator_repo()` routes the `api` source **only to `YouTubeCreatorRepository`** → `creo/storage/api/youtube.py`. There is **no Instagram/Meta discovery adapter**.
- The Instagram file that *does* exist, `creo/storage/api/instagram.py`, is `InstagramCampaignRepository` — it reads the **brand's own media** via the Graph Instagram API; it is read-only and raises `NotImplementedError` on write. It does not discover *creators*.
- `Creator` has **no `region` field** → Instagram-region filtering cannot be expressed today.
- `.env` ships with `INSTAGRAM_API_KEY=''` (empty). Discovery is inert.

> Net: searching for creators by niche/region currently works only against the **local** JSON pool (`CreatorService` filters `cs.creators`), or a single hardcoded YouTube keyword search. There is no structured, criteria-based Instagram discovery.

### Gap 2 — Messaging is inbound-only
- `HelpdeskService` answers *incoming* creator questions from the FAQ KB and lets ops *manually* reply (`send_reply`). Excellent for support.
- The assignment lifecycle — `AssignmentService.assign()`, `update_status()`, `advance_status()` — has **no notification hook**. When an assignment moves `matched → invited → brief_sent`, **nothing messages the creator**.
- `ChatMessage` has no `related_campaign_id`/`related_assignment_id` → campaign-originated outbound messages are not traceable.

> Net: there is **no proactive campaign messaging**. Briefs, invitations, and status nudges are still sent manually or not at all.

---

## 4. Solution A — Creator Discovery by criteria

### Approach (no scraping)
We do **not** scrape Instagram's public web/GraphQL surface (ToS-violating, brittle, IP-ban risk, no structured niche/region). Instead we consume **official API endpoints** — the Meta Creator Marketplace discovery endpoint (and Instagram Graph API where creators authorized their accounts) — which return verified follower counts, business-category/niche, and location (region). This mirrors the proven `YouTubeCreatorRepository` pattern exactly.

### Architecture
```
            ┌────────────────────────────┐
            │  Creators page filters     │  (niche, language, region, min-followers)
            └─────────────┬──────────────┘
                          ▼
            ┌────────────────────────────┐
            │  CreatorService (cache)    │  filter_by_niche / _language / NEW filter_by_region
            └─────────────┬──────────────┘
                          ▼
            ┌────────────────────────────┐   source="api" ──┐
            │  get_creator_repo()         │ ───────────────► │ CompositeCreatorRepository
            └─────────────┬──────────────┘                  │  (merges Meta Marketplace + YouTube + local)
         source="json"│  "db"   │  "api"                   │
                      ▼        ▼        ▼                  │
            ┌─────────┐ ┌──────┐ ┌─────────────────────┐  │
            │ Json    │ │  Db   │ │ InstagramCreatorRepo │  │  ← NEW. _fetch_by_criteria(niche, region, …)
            │ Creator │ │Creat. │ │ + _mock_creators()    │  │      uses INSTAGRAM_API_KEY; falls back to mock
            └─────────┘ └──────┘ └─────────────────────┘  │
                                          ▲                │
                     (existing pattern)   │                │
                          ┌───────────────┴───────────────┘
                          │ YouTubeCreatorRepository  (existing; keep as secondary source)
                          └─────────────────────────────────┐
                                              fallback when
                                              marketplace key missing
```

### Reality check — why Instagram discovery is genuinely tough (and our path

This is worth being honest about, because it shapes scoping and budget:

1. **There is no public Instagram creator-discovery API.** The Instagram Graph API can list a *business account's own* media and basic profile — not "find creators by niche/region." The audience/creator-discovery endpoints (`ig_user/search`, Audience Discovery, the Meta Creator Marketplace directory) are restricted, require Facebook-App business verification, and are not generally accessible. This is *why* the repo today only has a YouTube adapter and an Instagram *campaign*-media adapter.
2. **The Meta Creator Marketplace API key is hard to get** — exactly as you reported. Access is gated on partner/approval, so it is unreliable as a sole dependency.
3. **Scraping Instagram's public surface is not a real option.** It violates ToS, triggers CAPTCHAs/rate-limits/IP bans within minutes, and Instagram changes its HTML/JSON layout regularly — a classic brittle scraper that spends more time broken than working. It also yields no structured `region` or vetted `niche`.

| Approach | Verdict | Fits BigBell? |
|----------|---------|------------|
| Web/GraphQL scraping | ToS violation, IP bans, brittle | **No** |
| Meta Creator Marketplace endpoint | Best data quality (verified followers, region, category) but gated by hard-to-get key | Yes — as **one** source |
| Instagram Graph API (own-account search) | Limited, not true discovery | Secondary signal only |
| YouTube Data API discovery | Works today, always-on | Yes — **existing** adapter |
| Local CSV / DB import | Creator self-onboarding or ops upload | Yes — **existing** |
| Creator pull-model (creator applies via "Add creator with AI") | Most reliable long-term | Yes — **existing** `add_creator.py` + `CreatorExtractionAgent` |

**Our path:** official Meta endpoint as the *preferred* source, with three fallbacks so the product is never blocked — (a) the deterministic `_mock_*` path (same pattern as `YouTubeCreatorRepository`), (b) YouTube discovery (already live), and (c) the existing "Add creator with AI" pull-model page. The client gets Instagram discovery *when the key is available*, and a working product *always*.


### Data-model change (minimal, non-breaking)
`creo/models.py` · class `Creator`:
```python
region: Optional[str] = None          # NEW — for Instagram/region filtering
```
`CreatorService` gains `filter_by_region(region)` — consistent with the existing `filter_by_niche`/`filter_by_language` signatures.

### Fallback guarantee (the "key is hard to get" hedge)
- **Key present** → live Meta Marketplace query by niche/region/language; verified follower counts.
- **Key absent** → `InstagramCreatorRepository._mock_creators()` returns deterministic sample creators (exactly how `YouTubeCreatorRepository` already behaves). The UI is fully functional for demos and the match pipeline runs end-to-end.
- **No single-key blocker**: even without the marketplace key, YouTube discovery + local CSV/DB import remain live sources. The system degrades gracefully, never breaks.

### What the client sees
- A **Creator Discovery** panel (extends the existing "All Creators" filter toolbar) with a new `Region` dropdown populated from discovered data.
- Results ranked by the existing `MatchingAgent` score, so "best creators for this niche/region" are surfaced first — not just raw API order.

> Follows the existing pattern: `BaseApiRepository.use_real_api` → real fetch, else `_mock_*`. Zero new conventions.

---

## 5. Solution B — Automated campaign messaging

### Approach
A small **Assignment Notifier** agent (mirrors `MatchingAgent`'s `_mock_*`/`_ai_*` contract from `creo/agents/base.py`) that fires on assignment-lifecycle transitions and composes a campaign brief/invite/nudge. Messages are stored via the **existing** `ChatMessage` model and rendered in the **existing** Helpdesk inbox — so no new UI surface is required to be useful.

### Architecture
```
            AssignmentService.advance_status() / assign()
                           │  (hook)
                           ▼
            ┌──────────────────────────────────────┐
            │  AssignmentNotifier  (new agent)      │
            │   _mock_brief_message(...)  deterministic template
            │   _ai_brief_message(...)    LLM-personalized per creator
            │   (selects via BaseAgent.use_* — same switch as everywhere)
            └──────────────┬───────────────────────┘
                           │  produces ChatMessage(role="agent", kind="auto")
                           ▼
            ┌──────────────────────────────────────┐   links to:
            │  HelpdeskService.send_reply(...)      │   related_assignment_id / related_campaign_id
            │  (existing)                           │   (new optional fields on ChatMessage)
            └──────────────┬──────────────────────┘
                           │
              ┌────────────┼─────────────┐
              ▼            ▼             ▼
   WhatsApp Business   Email (SMTP)   In-app (stored)
   (uses WHATSAPP_API_ exists)          (always works)
   KEY if present; if   (SMTP creds    (fallback when
   absent → queued &    in Settings)   channel keys missing)
   shown in-app thread  — reusable    — never blocks)
```

### Data-model changes (minimal)
`creo/models.py` · class `ChatMessage`:
```python
related_campaign_id: Optional[str] = None   # NEW
related_assignment_id: Optional[str] = None  # NEW
```
`ChatMessage` already has `role`, `kind`, `channel`, `faq_id`, `confidence` — the outbound flow slots in without reshaping the model.

### Lifecycle triggers (from the existing `NEXT_STATUS` machine)
`creo/services/assignment_service.py`:
```
MATCHED    → INVITED      : "You've been invited to <Campaign> (<brand>). Brief + budget inside."
INVITED    → ACCEPTED      : "Thanks for accepting. Here's the full brief + deadline."
BRIEF_SENT → CONTENT_RECEIVED : "We're waiting on your deliverable. Deadline: <date>."
CONTENT_RECEIVED → APPROVED : "Content reviewed — approved. Payment queued."
APPROVED   → PAID          : "Payment processed. See you next campaign."
```
Each transition → `AssignmentNotifier` → `HelpdeskService.send_reply` → channel dispatch.

### End-to-end workflow (what ops and creators actually do)

Here is the exact sequence, step by step, mapped to the files involved:

1. **Brand launches a campaign.** Ops creates it via the existing Campaign CRUD (`campaigns.py` add-campaign form). Target niches/languages/budget/deadline are stored on `Campaign`.
2. **Find creators.** Ops picks the campaign → "Find Creators" panel → filters by niche / language / region / min-followers over the discovery pool (Instagram Meta Marketplace ∪ YouTube ∪ local).
3. **Smart match.** Ops clicks **Run smart matching** → `MatchingAgent.match(creator, campaign)` scores every candidate (niche embedding similarity + language + reach + engagement + quality + budget fit, weights in `creo/config.py`) → ranked list.
4. **Assign.** Ops assigns a creator → `AssignmentService.assign(campaign_id, creator_id, score)` creates a `CampaignAssignment`, status = `MATCHED`. This call now also **hooks the notifier**.
5. **Invite fires automatically.** On `MATCHED → INVITED`, `AssignmentNotifier` composes the message (`_mock_brief_message` by default, `_ai_brief_message` if an LLM key is set) using the creator's niche + the campaign budget/deadline. `HelpdeskService.send_reply` stores it as `ChatMessage(role=agent, kind=auto, channel=…, related_assignment_id, related_campaign_id)` = **DRAFT**.
6. **Ops reviews.** The draft appears (a) inline under the creator in the assignment panel and (b) in the Helpdesk → Inbox → that creator's thread. Ops clicks **Send** (or it auto-sends if "auto-send trusted" is on).
7. **Deliver.** Channel dispatch: WhatsApp Business API if `WHATSAPP_API_KEY` is set → email via SMTP if configured → otherwise the message is delivered **in-app** (creator sees it in BigBell) and ops can copy the text to send manually. Failure on one channel falls through to the next; in-app always succeeds.
8. **Creator responds.** Their reply lands as an inbound `ChatMessage(role=creator, kind=incoming)` → the existing helpdesk auto-answer resolves it from the FAQ knowledge base (or queues it for ops).
9. **Lifecycle continues.** As the creator completes each stage, ops (or the creator) advances the assignment again (`CONTENT_RECEIVED → APPROVED → PAID`); each transition auto-composes and drafts the next message. The thread becomes a full audit trail.

**Result for ops:** one click to assign, and the invite + brief + status nudge are composed, linked to the assignment, and ready to send — no tab-switching between WhatsApp, email, and a spreadsheet.
**Result for creators:** they're looped into the campaign flow automatically, with every message citing the campaign name, brand, budget, and deadline, and every outbound message traceable to `related_assignment_id`.


### Ops control (no blind spamming)
- Messages default to **draft** in the assignment panel → ops click **Send** (the existing assignment UI in `campaigns.py` already has action buttons per assignment, so this is a one-button addition).
- A **"Auto-send trusted"** toggle (per campaign or global) for brands that opt into hands-off delivery.
- **Opt-out tracking**: a `MessagingOptOut` record (per creator) — if unset, no campaign messaging is attempted. Respects Do Not Disturb windows.
- Every outbound message is linked to its assignment/campaign (new FK fields), so compliance and traceability are built in.

> Follows the existing pattern: `AssignmentService` already owns the lifecycle; we **hook** into `advance_status`/`assign` rather than reimplementing state. Messaging reuses `HelpdeskService` + `ChatMessage`.

---

## 6. Implementation plan · timeline · value

| Phase | Scope | Effort | What the client gets |
|-------|-------|--------|----------------------|
| **A1** | Add `region` to `Creator`; `InstagramCreatorRepository` (Meta Marketplace fetch + `_mock_creators`); route in `get_creator_repo()` | 2 dev-days + 1 test day | Instagram creators discoverable by niche · region · language · reach, with mock fallback |
| **A2** | `CreatorService.filter_by_region` + UI Region filter on "All Creators" + matching re-rank | 1 dev-day + 0.5 test | Client sees ranked, segmented creator lists |
| **B1** | `AssignmentNotifier` agent (`_mock_*`/`_ai_*`); hook into `AssignmentService.advance_status`/`assign`; add FK fields to `ChatMessage` | 1.5 dev-days + 1 test | Campaign invites/briefs auto-composed on lifecycle events |
| **B2** | Render outbound messages in Helpdesk inbox thread; **Send / Draft** toggle + opt-out record | 1 dev-day + 0.5 test | Ops review before send; channels WhatsApp/email/in-app; compliance traceable |
| **B3** | Settings: WhatsApp/SMTP credential persistence already exists; add "auto-send trusted" toggle | 0.5 dev-day | End-to-end automated flow, client-controlled |

**Total:** ~5 dev-days + 3 test days → **~1 person-week (parallelizable across 2)** to production-ready.

### Value (your KPIs)
- **Creators:** time-to-find-the-right-creator drops from "manual outreach on Instagram" to a filtered, scored list in <2s.
- **Ops team:** assignment handoffs from "matched" to "invited/briefed" become a single click — no copy/paste across WhatsApp/email.
- **Brands:** visibility into the creator shortlist + automated status nudges = fewer "where is my creator?" queries.

---

## 7. Risks & mitigations

| Risk | Mitigation (already in the plan) |
|------|----------------------------------|
| Instagram/Meta API key hard to obtain | Mock fallback keeps the product live; multi-source (YouTube + local CSV) ensures discovery still works; key persisted via existing Settings → `.env`. |
| "Messaging" reads as spam to creators | Only lifecycle events trigger messages; Draft-first + opt-out per creator + compliance link on every message. |
| LLM personalization costs / failure | `_ai_*` used only when a key is present; `_mock_*` is the always-on deterministic path; fallback identical to `MatchingAgent`'s existing fallback. |
| Channel delivery fails (WhatsApp/Email) | In-app delivery is the guaranteed channel (stored in `ChatMessage`); failed channel sends stay queued in-app for manual reshare. |
| Scope creep into full Instagram CRM | Hard scope: discovery + segmentation + lifecycle messaging only. No scraping, no follower-history graphs, no content analysis. |

---

## 8. Client Q&A prep

> How to answer if they push back. Every answer is tied to a concrete code pattern they can ask to see.

**Q1. "Why don't you just scrape Instagram? It's free."**
> We deliberately don't. Instagram's public surface (web + GraphQL) has no official creator-discovery API, changes layout constantly, rate-limits/bans IPs, and violates ToS — a support and legal liability at scale. Instead we use the **Meta Creator Marketplace discovery endpoint** (official), which returns *verified* follower counts, business category, and region in structured form. This is the same official-API-first approach the repo already takes for YouTube (`YouTubeCreatorRepository`).

**Q2. "The Meta marketplace API key is hard to get. What then?"**
> Two safety nets. (a) The `BaseApiRepository` pattern (`use_real_api` → real fetch, else `_mock_*`) means the product works end-to-end in demo without any key — deterministic sample creators flow through the *real* matching/scoring pipeline. (b) Multi-source: YouTube discovery + local CSV import are always live. No single credential is a hard blocker; the key unlocks *Instagram* discovery, not the whole product.

**Q3. "How is this different from the auto-answer in the helpdesk?"**
> Sharp distinction. The current helpdesk **auto-answers inbound** creator questions from the FAQ knowledge base (`HelpdeskService.receive_question` → FAQ embedding similarity). **Solution B is proactive outbound**: triggered by the assignment *status machine* (`AssignmentService.advance_status`), it *sends* briefs/invites/nudges the creator didn't ask for. Same `ChatMessage` model, different direction.

**Q4. "Aren't you going to spam creators with these messages?"**
> No. (1) Messages fire only on real lifecycle transitions — `matched→invited`, `brief_sent→content_received`, `approved→paid` — not on a timer. (2) Draft-first by default; an ops person clicks Send. (3) Opt-out is recorded per creator and checked before any send. (4) Every message is linked to its assignment + campaign (`related_assignment_id`) for traceability. That's the opposite of spam.

**Q5. "How do you personalize the message without an LLM for every creator?"**
> Same switch the whole app uses (`creo/agents/base.py`): `_ai_*` (LLM-personalized) when an API key is configured, `_mock_*` (deterministic template) otherwise. Templates merge real fields — creator niche, campaign budget, deadline — so personalization is real even in mock mode. And the fallback is identical to `MatchingAgent`'s existing fallback: proven, not invented.

**Q6. "If WhatsApp delivery fails, do creators just miss the campaign?"**
> No. WhatsApp/Email require keys (`WHATSAPP_API_KEY`, SMTP creds) — both are **optional**. If absent or failing, the message is still stored in-app via the existing `ChatMessage` thread and rendered in the Helpdesk inbox. An ops person can resend or copy it out. Failure never loses the message.

**Q7. "Adding `region` — does that break the existing data?"**
> No. `region: Optional[str] = None` is purely additive; existing creators remain valid Pydantic instances. The JSON/DBC creators simply lack the field until populated. Reads of `region` are guarded with `Optional` semantics.

**Q8. "What's the smallest thing you can ship first?"**
> Solution A1 alone: Instagram discovery adapter + mock fallback + the Region filter. The client gets "find Instagram creators by niche/region" without touching the live API. Then B1/B2 deliver messaging. Each phase is independently valuable and shippable.

**Q9. "Can I see this is real and not just slides?"**
> Yes — ask me to show you `creo/agents/matching.py` (the scoring weights), `creo/services/assignment_service.py` (the `NEXT_STATUS` machine), `creo/storage/api/youtube.py` (the exact pattern we replicate for Instagram), and `creo/agents/base.py` (the `_mock_*`/`_ai_*` switch). This proposal extends, not replaces, those files.

**Q10. "Where does the 'meta creator marketplace' actually get queried?"**
> In `creo/storage/api/instagram.py` we add `InstagramCreatorRepository`, subclassing the existing `CreatorRepository` ABC (`creo/storage/base.py`) and the `BaseApiRepository` pattern (`use_real_api`/`_mock_*`). The Meta Marketplace discovery endpoint is hit in `_fetch_by_criteria(niche, region, language, min_followers)`; identical `use_real_api` guard keeps the mock fallback. Selected by `get_creator_repo()` at `source == "api"` in `creo/storage/factories.py`.

---

## 9. One-page summary

**Problems**
1. Creator discovery is local-only; there is no Instagram/Meta adapter and no `region` field — so "find creators by region/niche on Instagram" is impossible today.
2. Messaging is inbound-only; the assignment lifecycle (`matched→invited→accepted→brief_sent→content_received→approved→paid`) sends nothing to creators — briefs/invites are manual or missed.

**Solutions**
1. Add `InstagramCreatorRepository` (Meta Marketplace discovery + `_mock_*` fallback) wired into the existing `get_creator_repo()` factory; add `Creator.region` + `filter_by_region`. No scraping; official API first; graceful degradation.
2. Add `AssignmentNotifier` agent (`_mock_*`/`_ai_*`) hooking `AssignmentService.advance_status`/`assign`; reuse `HelpdeskService` + `ChatMessage` (add `related_campaign_id`/`related_assignment_id`); Draft-first + opt-out + WhatsApp/Email/In-app dispatch.

**Evidence it fits** — reuses, verbatim, the patterns clients already trust in this codebase: `CachedRepositoryService`, the `CreatorRepository` ABC, `BaseApiRepository.use_real_api`/`_mock_*`, `BaseAgent.use_mock`/`_ai_*`, the `NEXT_STATUS` machine, and the `ChatMessage` channel model. No new abstractions, no scraping, no single-key blocker.

**Timeline**: ~1 person-week (2 devs, parallelizable) to production-ready, shipped in two independently valuable phases (Discovery → Messaging).
