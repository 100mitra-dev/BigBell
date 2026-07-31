# Creo AI — Agent Instructions

## Run the app
```bash
streamlit run app.py
```

## Run tests
```bash
.venv/bin/python -m pytest tests/ -v --cov=creo
```

## Run linting
```bash
# ruff is not installed yet — install with:
.venv/bin/pip install ruff
ruff check creo/ tests/
ruff format --check creo/ tests/
```

## Project structure
- `app.py` — Streamlit entry point
- `creo/` — core package (models, services, agents, storage, UI)
- `tests/` — test suite
- `data/sample_data/` — JSON persistence files
- `api/` — FastAPI REST layer (experimental)

## Key conventions
- All AI agents have `_mock_*` (deterministic) and `_ai_*` (LLM) methods
- Switch provider in Settings or via `AI_PROVIDER` env var
- Use `get_*_repo()` factory from `creo/storage/factories.py` for data access
- Services extend `CachedRepositoryService[T]` from `creo/services/base.py`
- All Pydantic models in `creo/models.py`
- Embeddings use `ONNXMiniLM_L6_V2` (local, CPU-only, no API key)
