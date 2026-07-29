# Creo — Creator Success AI Platform

An AI-powered platform for creator onboarding, management, and campaign operations. Built with **Streamlit**, **LangChain**, and **Python**.

## Features

| Page | Description |
|------|-------------|
| **Dashboard** | Executive KPIs, niche distribution, status breakdown, trend charts |
| **Applications** | AI-powered application review with scoring, risk flags, and recommendations |
| **Verification** | Automated profile completeness and social media verification |
| **Categorization** | AI-driven niche and language classification with scoring |
| **Campaign Matching** | Semantic matching with explainable AI scores |
| **Creator Queries** | RAG-based chatbot answering FAQs with source citations |
| **Follow-Ups** | Deadline tracking, deliverable status, automated reminders |
| **Payments** | Payment status tracking, processing, and dispute resolution |
| **Creator CRM** | Full creator record management with filters and history |

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app launches in **mock mode** — fully functional with simulated AI responses.

## AI Providers

For real AI features, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add your keys:

- **OpenAI**: Set `OPENAI_API_KEY` and `AI_PROVIDER=openai`
- **Google Gemini**: Set `GEMINI_API_KEY` and `AI_PROVIDER=gemini`

## Project Structure

```
creo/
├── app.py                    # Streamlit entry point
├── pages/                    # 9 multi-page app views
│   ├── 01_Dashboard.py
│   ├── 02_Applications.py
│   └── ...
├── src/
│   ├── core/
│   │   ├── agents/           # LangChain AI agents
│   │   ├── rag/              # RAG pipeline (ChromaDB)
│   │   ├── services/         # Data services
│   │   ├── config.py         # Configuration
│   │   └── models.py         # Pydantic models
│   └── utils/                # UI components & helpers
├── data/
│   └── sample_data/          # Pre-seeded mock data
└── .streamlit/
    └── config.toml           # Theme configuration
```

## Tech Stack

- **Frontend**: Streamlit (multi-page, custom theme)
- **AI Orchestration**: LangChain (LCEL chains)
- **Vector Store**: ChromaDB (persisted FAQ knowledge base)
- **Models**: Pydantic v2
- **Visualization**: Plotly
- **Data**: JSON-based (no database required)
