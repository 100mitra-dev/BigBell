# Creo — Creator Success AI Platform

AI-powered platform for creator onboarding, management, and campaign operations.

## Quick start

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
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
streamlit_app.py              # Entry point with navigation
app_pages/                    # Page modules (operations, management, insights)
    dashboard.py
    applications.py
    verification.py
    categorization.py
    campaign_matching.py
    creator_queries.py
    follow_ups.py
    payments.py
    creator_crm.py
    settings.py               # Web-based configuration
app/components/               # Reusable UI building blocks
    cards.py
    layout.py
src/                          # Core library (no streamlit dependency)
    core/
        config.py             # Configuration constants
        models.py             # Pydantic data models
        runtime_config.py     # Runtime configuration (provider, keys)
        agents/               # AI agents (review, verify, categorize, match, query)
        rag/                  # RAG pipeline (embeddings, vector store, retrieval)
        services/             # Data services (creator, campaign, payment)
    utils/
        helpers.py            # JSON I/O, date helpers, search
data/
    sample_data/              # 50 creators, 22 campaigns, 30 FAQs, 15 payments
    vector_store/             # ChromaDB persistence (auto-created)
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
app/ (streamlit UI)  →  app/components/ (reusable widgets)
                     →  app_pages/ (page modules)

src/ (core library)  →  src/core/agents/ (AI agents)
                     →  src/core/rag/ (vector search)
                     →  src/core/services/ (data layer)
                     →  src/utils/ (helpers)
```

The `src/` layer has no Streamlit dependency — it can be used independently.
