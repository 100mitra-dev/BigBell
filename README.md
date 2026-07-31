# Creo — Creator Success AI Platform

AI-powered platform for creator onboarding, management, and campaign operations.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app launches in **mock mode** — fully functional with rule-based AI responses.

## AI providers

Configure via the **Settings** page in the app or set environment variables:

| Provider | Environment | Web UI |
|----------|-------------|--------|
| Mock | `AI_PROVIDER=mock` (default) | Fully functional |
| OpenAI | `AI_PROVIDER=openai` + `OPENAI_API_KEY` | Enter key in Settings |
| Gemini | `AI_PROVIDER=gemini` + `GEMINI_API_KEY` | Enter key in Settings |

For real semantic search (FAQ chatbot), install sentence-transformers:
```bash
pip install sentence-transformers
```

## Project structure

```
app.py                        # Streamlit entry point with navigation
creo/
    agents/                   # AI agents (base + review, verify, categorize, match, query)
    models.py                 # Pydantic data models
    rag/                      # RAG pipeline (embeddings, vector store, retrieval, FAQ KB)
    services/                 # Data services (creator, campaign, payment, assignment, follow-up, helpdesk)
        base.py               # CachedRepositoryService[T] base class
    storage/
        base.py               # Repository ABCs
        factories.py          # get_*_repo() factory functions
        json/                 # JSON-backed repositories
        db/                   # SQLite-backed repositories + migrations
        api/                  # Social API clients (YouTube, Instagram, WhatsApp)
        csv_handler.py
    ui/
        pages/                # Page modules (dashboard, creators, campaigns, deadlines, ...)
        components/           # Reusable UI building blocks (cards, layout, platforms)
    utils/
        json_io.py            # JSON load/save + typed entity loaders
        dates.py              # date helpers (today_str, days_until)
        debug_logging.py      # API log entries
        runtime_settings.py   # Runtime configuration (provider, keys)
api/                          # FastAPI REST layer (experimental)
data/
    sample_data/              # 52 creators, 22 campaigns, 18 applications, 15 payments
    vector_store/             # ChromaDB persistence (auto-created)
tests/                        # pytest suite
```

## Features

- **Applications** — AI review with scoring, risk flags, and recommendations
- **Verification** — Automated profile and social media verification
- **Categorization** — AI-driven niche and language classification
- **Campaign matching** — Multi-factor creator-campaign matchmaking
- **Creator queries** — RAG-based FAQ chatbot with source citations
- **Follow-ups** — Deadline tracking and deliverable management
- **Payments** — Payment status tracking and dispute resolution
- **Creator CRM** — Full creator record management with history
- **Settings** — Web-based AI provider configuration

## Architecture

```
creo/ui (streamlit UI)  →  creo/ui/pages/ (page modules)
                       →  creo/ui/components/ (reusable widgets)

creo/ (core library)   →  creo/agents/ (AI agents)
                       →  creo/rag/ (vector search)
                       →  creo/services/ (data layer)
                       →  creo/storage/ (repositories + factories)
                       →  creo/utils/ (helpers)
```

The `creo/` core layer (agents, services, storage, utils) has no Streamlit dependency — it can be used independently.
