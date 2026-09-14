# BigBell — Client Architecture Overview

> One view, two phases. **Phase 1 (blue) = Creator Discovery.** **Phase 2 (amber) = Lifecycle Messaging.** Everything teal is live today.

## Recommended approach
**Present the full architecture now, but gate delivery by phase.** Showing the complete vision up front builds confidence; tagging deliverables as Phase 1 vs Phase 2 manages scope and sets expectations. Creator Discovery is the right Phase 1 because it's self-contained (one new adapter + one model field + one filter + mock fallback) and de-risks the hardest dependency (Instagram/Meta API access).

```mermaid
flowchart TD
    classDef NEW1 fill:#1E88E5,color:#fff,stroke:#0D47A1,stroke-width:2px;
    classDef NEW2 fill:#FB8C00,color:#000,stroke:#E65100,stroke-width:2px;
    classDef core fill:#13B496,color:#fff,stroke:#00695C,stroke-width:2px;
    classDef data fill:#9C27B0,color:#fff,stroke:#4A148C,stroke-width:2px;
    classDef ext fill:#607D8B,color:#fff,stroke:#37474F,stroke-width:1px;

    subgraph legend["Legend"]
        L1["Phase 1 — Creator Discovery<br/>(new, blue)"]:::NEW1
        L2["Phase 2 — Lifecycle Messaging<br/>(new, amber)"]:::NEW2
        L3["Live today (teal)"]:::core
        L4["Data / storage"]:::data
        L5["External APIs"]:::ext
    end

    subgraph sources["Data & External Sources"]
        META["Meta Creator<br/>Marketplace API<br/>(INSTAGRAM_API_KEY)"]
        YT["YouTube Data API<br/>(YOUTUBE_API_KEY)"]
        LOCAL["Local JSON / CSV<br/>creators.json + upload"]
        DB["SQLite (creo.db)<br/>5 tables + migrations"]
        KB["FAQ Knowledge Base<br/>30 FAQs + PDFs<br/>Chroma vector store"]
    end

    subgraph repos["Storage — get_*_repo() dispatches on DATA_SOURCE"]
        INSTAREPO["InstagramCreatorRepository<br/>Meta fetch + _mock_creators fallback<br/>Phase 1 (NEW)"]
        YTREPO["YouTubeCreatorRepository<br/>existing pattern (blueprint)"]
        JSONREPO["Json* repositories<br/>creators / campaigns / payments<br/>applications / assignments / notes"]
        DBR["Db* repositories<br/>SQLite-backed mirror"]
        WAREPO["WhatsAppPaymentRepository<br/>(existing)"]
    end

    subgraph services["Domain Services (CachedRepositoryService)"]
        CRS["CreatorService<br/>search + filter_by_niche/language"]
        CRS_NEW["filter_by_region (Phase 1 NEW)"]
        CMS["CampaignService<br/>search + filter + budget"]
        AS["AssignmentService<br/>8-state lifecycle<br/>assign / advance_status / update_status"]
        PS["PaymentService<br/>status flow + disputes"]
        FUS["FollowUpNoteService<br/>deadlines + notes"]
        HS["HelpdeskService<br/>threads + auto-answer + send_reply<br/>+ suggest_replies (KB + LLM)"]
    end

    subgraph agents["AI Agents (BaseAgent — _mock_ / _ai_)"]
        MA["MatchingAgent<br/>niche embedding + 7-factor scoring"]
        AR["ApplicationReviewerAgent<br/>risk flags + recommendation"]
        CAT["CategorizationAgent<br/>niche / language / tier"]
        VER["VerificationAgent<br/>profile + social verification"]
        EXT["CreatorExtractionAgent<br/>text / WhatsApp / PDF"]
        QA["QueryAgent<br/>RAG FAQ w/ citations"]
        NOTIF["AssignmentNotifier (Phase 2 NEW)<br/>brief / invite / nudge<br/>per lifecycle transition"]
    end

    subgraph ui["Streamlit UI — app.py (10 pages)"]
        DASH["Dashboard"]
        CREATORS["All Creators<br/>search + filter toolbar"]
        CREATORS_NEW["+ Region filter dropdown (Phase 1 NEW)"]
        MATCH["Match Creators<br/>Find Creators + smart match<br/>+ assignment controls"]
        VAL["Review & Classify<br/>review / verify / classify"]
        HELP["AI Helpdesk<br/>Inbox threads + KB"]
        HELP_NEW["Outbound drafts<br/>(Phase 2 NEW)"]
        PAY["Payments"]
        DEAD["Deadlines & Notes"]
        SET["Settings<br/>provider + keys + DATA_SOURCE"]
        LOGS["API Logs"]
        ADD["Add Creator w/AI<br/>extraction + gap picker"]
    end

    subgraph api["REST API (FastAPI — experimental)"]
        APIM["/health"]
        APIF["/faq/ask"]
        APIC["/creators"]
    end

    subgraph chan["Channel Delivery (Phase 2 NEW)"]
        WA["WhatsApp Business"]
        SMTP["Email (SMTP)"]
        INAPP["In-app (always succeeds)"]
    end

    %% === Phase 1: discovery chain ===
    META -- "Phase 1" --> INSTAREPO
    YT --> YTREPO
    LOCAL --> JSONREPO
    DB --> DBR
    META -. "fallback" .-> YTREPO
    LOCAL -. "fallback" .-> JSONREPO
    INSTAREPO --> CRS
    YTREPO --> CRS
    JSONREPO --> CRS
    DBR --> CRS
    CRS <--> CREATORS
    CRS <--> MATCH
    CRS <--> VAL
    CRS_NEW --> CREATORS_NEW

    %% === Matching chain (live) ===
    MATCH --> MA
    VAL --> AR
    VAL --> VER
    VAL --> CAT
    ADD --> EXT
    HELP --> QA
    KB --> HS
    QA --> KB

    %% === Services → UI (demand side) ===
    CMS --> MATCH
    AS --> MATCH
    AS --> DEAD
    FUS --> DEAD
    PS --> PAY
    HS --> HELP
    HS <--> HELP_NEW

    %% === Phase 2: lifecycle messaging ===
    AS -- "on assign / advance_status<br/>(hooks NEXT_STATUS machine)" --> NOTIF
    NOTIF -- "draft ChatMessage<br/>(role=agent, kind=auto)<br/>related_assignment_id / related_campaign_id NEW" --> HS
    HS -- "send_reply" --> WA
    HS --> SMTP
    HS --> INAPP

    %% === API ===
    APIF --> QA
    APIC --> CRS

    %% === Settings wires all providers ===
    SET -- "AI_PROVIDER + keys" --> MA
    SET --> AR
    SET --> CAT
    SET --> VER
    SET --> EXT
    SET --> QA
    SET --> NOTIF
    SET -- "DATA_SOURCE" --> INSTAREPO
    SET --> YTREPO
    SET --> HS

    classDef sfill fill:#F5F5F5,stroke:#E0E0E0
    class INSTAREPO,CRS_NEW,CREATORS_NEW NEW1
    class NOTIF,HELP_NEW,WA,SMTP,INAPP NEW2
    class MA,AR,CAT,VER,EXT,QA,CRS,CMS,AS,PS,FUS,HS,DASH,CREATORS,MATCH,VAL,HELP,PAY,DEAD,SET,LOGS,ADD,APIM,APIF,APIC,YTREPO,JSONREPO,DBR,WAREPO,META,YT,LOCAL,DB,K B core
```


A brand launches a campaign → ops opens **Match Creators** → filters by niche, language, **region** (new), min-followers → the **MatchingAgent** ranks every candidate by niche-semantic similarity + reach + engagement + quality + budget fit. Behind the scenes, `get_creator_repo()` now returns the new **InstagramCreatorRepository** when `INSTAGRAM_API_KEY` is present, or its `_mock_creators()` fallback when it isn't — so the product works in demo today and Instagram discovery lights up the moment the Meta key lands. YouTube + local CSV are always-live fallbacks, so discovery is **never blocked on one credential**.

### Phase 2 — Lifecycle Messaging (follow-up)
Once creators are assigned, the **8-state machine** drives everything: each transition (`MATCHED→INVITED`, `INVITED→ACCEPTED`, `BRIEF_SENT→CONTENT_RECEIVED`, `APPROVED→PAID`, …) fires the new **AssignmentNotifier**, which **drafts** a brief/invite/nudge into the existing Helpdesk thread as a `ChatMessage(role=agent, kind=auto, related_assignment_id, related_campaign_id)` — **draft-first**, ops clicks Send (or toggles "auto-send trusted"). Messages dispatch WhatsApp → email → in-app, with in-app as the guaranteed fallback. A per-creator `MessagingOptOut` is checked before any send.

## Why this ships fast and safely
- **Reuses patterns, doesn't invent them.** AssignmentNotifier follows `BaseAgent`'s `_mock_*`/`_ai_*` switch; the Instagram adapter mirrors the existing `YouTubeCreatorRepository`; messaging reuses `HelpdeskService` + `ChatMessage`.
- **No single-key blocker.** Mock fallback + multi-source means Phase 1 is demo-ready without the Meta key; Phase 2 works in-app without WhatsApp/SMTP credentials.
- **Data model stays clean.** `region` is an additive `Optional[str]` on `Creator`; two optional FK fields on `ChatMessage` — no migration of existing records.
