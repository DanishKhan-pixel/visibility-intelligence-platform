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

- **POST** `/api/v1/profiles` create a business profile
- **GET** `/api/v1/profiles/{profile_uuid}` get profile + summary stats
- **POST** `/api/v1/profiles/{profile_uuid}/run` run pipeline and persist results
- **GET** `/api/v1/profiles/{profile_uuid}/queries` list discovered+scored queries
- **GET** `/api/v1/profiles/{profile_uuid}/recommendations` list recommendations
- **POST** `/api/v1/queries/{query_uuid}/recheck` re-run scoring for one query

## API documentation (Swagger)

- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`

After starting the server, open:

- `http://127.0.0.1:5000/docs`

All responses use a consistent envelope:

```json
{ "success": true, "data": {}, "error": null }
```

## Step-by-step API test (curl)

Assuming the server is running on `http://127.0.0.1:5000`.

### 1) Create a business profile

```bash
curl -s -X POST "http://127.0.0.1:5000/api/v1/profiles" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Surfer SEO",
    "domain": "surferseo.com",
    "industry": "SEO Software",
    "description": "AI-powered SEO content optimization tool",
    "competitors": ["clearscope.io", "marketmuse.com", "frase.io"]
  }'
```

Copy `profile_uuid` from the response and export it:

```bash
export PROFILE_UUID="paste-profile-uuid-here"
```

### 2) Get profile + summary stats

```bash
curl -s "http://127.0.0.1:5000/api/v1/profiles/$PROFILE_UUID"
```

### 3) Run the full pipeline (Agent 1 → 2 → 3)

```bash
curl -s -X POST "http://127.0.0.1:5000/api/v1/profiles/$PROFILE_UUID/run"
```

This returns:
- `pipeline_id`
- `queries_discovered`, `queries_scored`
- `top_queries` (top 3 by opportunity)
- `recommendations`

### 4) List all queries (sorted by opportunity score desc)

```bash
curl -s "http://127.0.0.1:5000/api/v1/profiles/$PROFILE_UUID/queries"
```

#### Filters + pagination

```bash
# minimum opportunity score
curl -s "http://127.0.0.1:5000/api/v1/profiles/$PROFILE_UUID/queries?min_score=0.7"

# visibility filter: visible | not_visible
curl -s "http://127.0.0.1:5000/api/v1/profiles/$PROFILE_UUID/queries?status=not_visible"

# pagination
curl -s "http://127.0.0.1:5000/api/v1/profiles/$PROFILE_UUID/queries?page=1&per_page=20"
```

### 5) List recommendations

```bash
curl -s "http://127.0.0.1:5000/api/v1/profiles/$PROFILE_UUID/recommendations"
```

### 6) Recheck a single query (Agent 2)

First, grab a `query_uuid` from the queries list response, then:

```bash
export QUERY_UUID="paste-query-uuid-here"
curl -s -X POST "http://127.0.0.1:5000/api/v1/queries/$QUERY_UUID/recheck"
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
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` (alternative to `DATABASE_URL`)

### PostgreSQL setup example

For your case:
- database: `ai_visibility_db`
- password: `root`

Use either one of these:

```bash
# Option A: single URL
export DATABASE_URL="postgresql+psycopg2://postgres:root@localhost:5432/ai_visibility_db"
```

```bash
# Option B: split vars
export POSTGRES_DB="ai_visibility_db"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="root"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
```

## Tests

```bash
pytest -q
```

## Tradeoffs (kept intentionally simple)

- Single-process SQLite is enough for evaluation; production would use Postgres.
- Mocks are deterministic to make tests repeatable.
- Prompts enforce strict JSON; parser is resilient to imperfect model output.
