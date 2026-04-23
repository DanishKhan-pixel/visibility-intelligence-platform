# AI Visibility (Flask + Multi-Agent Pipeline)

Backend service that helps a business discover AI-related search queries, score them for opportunity, and generate recommendations when the business is not visible.

## High-level flow

API → Orchestrator → Agent 1 (Discovery) → Agent 2 (Scoring) → Agent 3 (Recommendations) → SQLite → Response

## Why these choices

- **Flask (not FastAPI)**: small surface area, easy to read in an interview, minimal framework magic.
- **SQLite + SQLAlchemy**: zero setup, deterministic local evaluation, plenty for the assignment.
- **OpenAI GPT-4o (`openai` python package)**: strong structured JSON, stable, easy debugging.
- **No LangChain**: simplicity and clarity beat over-engineering.

## Opportunity score

We use an explainable scoring function:

\[
score = 0.5 \cdot \min(\frac{volume}{2000}, 1) + 0.3 \cdot (1 - \frac{difficulty}{100}) + 0.2 \cdot (1 \text{ if not visible else } 0.3)
\]

Returned as a value in \([0, 1]\) rounded to 2 decimals.

## Hybrid mocking strategy (required)

- Uses **real OpenAI / DataForSEO** if credentials are present
- **Always** falls back to deterministic mocks on any error

This ensures the pipeline can always run in a clean evaluator environment.

## Endpoints

- **POST** `/profiles` create a business profile
- **POST** `/profiles/{id}/run` run pipeline and persist results
- **GET** `/profiles/{id}/queries` list discovered+scored queries
- **GET** `/profiles/{id}/recommendations` list recommendations

All responses use a consistent envelope:

```json
{ "success": true, "data": {}, "error": null }
```

## Run locally

Create a virtualenv (optional if you already have one) and install:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
export FLASK_APP=app
flask run
```

If you want migrations (recommended for the assessment):

```bash
export FLASK_APP=app
flask db init
flask db migrate -m "init"
flask db upgrade
```

Optional env vars:

- `OPENAI_API_KEY` to use real GPT-4o calls (otherwise mock fallback)
- `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` to use real DataForSEO (otherwise mock fallback)
- `DATABASE_URL` (default: `sqlite:///ai_visibility.db`)

## Tests

```bash
pytest -q
```

## Tradeoffs (kept intentionally simple)

- Single-process SQLite is enough for evaluation; production would use Postgres.
- Mocks are deterministic to make tests repeatable.
- Prompts enforce strict JSON; parser is resilient to imperfect model output.
