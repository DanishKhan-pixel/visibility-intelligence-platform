# AI Visibility - Project Documentation

## What this project is

`AI Visibility` is a Flask API application that helps a business discover search opportunities and generate content recommendations using a 3-agent AI pipeline.

The system lets you:

- create a business profile
- discover relevant user search queries

- score those queries by opportunity
- generate recommendation ideas for high-value gaps
- recheck scoring for individual queries later

## How the system works

### 1) Create profile

You create a profile with:

- business name
- domain
- industry
- competitors

Endpoint: `POST /api/v1/profiles`

### 2) Run pipeline

When `POST /api/v1/profiles/{profile_uuid}/run` is called, the orchestrator runs three agents in order:

1. `QueryDiscoveryAgent`
   - generates relevant user search-style queries
2. `VisibilityScoringAgent`
   - estimates volume and difficulty
   - checks if the domain is visible
   - calculates an opportunity score
3. `RecommendationAgent`
   - creates content ideas for high-opportunity queries where visibility is low

### 3) Retrieve outputs

- scored queries: `GET /api/v1/profiles/{profile_uuid}/queries`
- recommendations: `GET /api/v1/profiles/{profile_uuid}/recommendations`
- profile summary/stats: `GET /api/v1/profiles/{profile_uuid}`

### 4) Recheck one query

You can re-run scoring for a single query:

- `POST /api/v1/queries/{query_uuid}/recheck`

## Project structure

```text
app/
  api/                     # Route handlers and API response wrappers
  agents/                  # Multi-agent pipeline implementations
  models/                  # SQLAlchemy models
  services/                # Pipeline orchestrator and service logic
  utils/                   # LLM client, DataForSEO client, scoring/parser helpers
  __init__.py              # Flask app factory and blueprint registration

migrations/                # Flask-Migrate / Alembic migration files
tests/                     # API and utility tests
instance/                  # Runtime database/config artifacts
```

## Technologies used

### Backend framework

- Flask
- Flask-Migrate
- SQLAlchemy (Flask-SQLAlchemy)

### Database and migrations

- relational DB via SQLAlchemy models
- Alembic migrations through Flask-Migrate

### AI / external integrations

- OpenAI API (if `OPENAI_API_KEY` is configured)
- DataForSEO (if credentials are configured)
- strict provider mode: invalid/missing credentials cause request errors

### Testing

- pytest

## API response format

All routes use a consistent envelope:

- success response:
  - `{"success": true, "data": ..., "error": null}`
- error response:
  - `{"success": false, "data": null, "error": {"message": "...", "code": "..."}}`

## Run locally

From project root:

```bash
source venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app
flask run --port 5000
```

## Local URLs

- App root: `http://127.0.0.1:5000/`
- Swagger UI: `http://127.0.0.1:5000/docs`
- OpenAPI spec: `http://127.0.0.1:5000/openapi.json`

## Main endpoints

- `POST /api/v1/profiles`
- `GET /api/v1/profiles/{profile_uuid}`
- `POST /api/v1/profiles/{profile_uuid}/run`
- `GET /api/v1/profiles/{profile_uuid}/queries`
- `GET /api/v1/profiles/{profile_uuid}/recommendations`
- `POST /api/v1/queries/{query_uuid}/recheck`

## Environment variables

Common variables (via `.env`):

- `OPENAI_API_KEY` - enables real LLM calls
- DataForSEO credentials - enables real search metrics calls

If these are missing/invalid, provider-backed steps fail and the pipeline run returns an error.

## Notes for future improvements

- add authentication and per-user access control
- add background job queue for long-running pipeline runs
- add richer dashboard UI and analytics charts
- add CI checks for lint + tests
























   # AI Visibility - Interview Prep Guide

   ## 1) Project Purpose

   `AI Visibility` is an API-first system that helps businesses improve discoverability in AI/search experiences.

   It solves a practical problem:

   - businesses do not know which user questions matter most
   - they do not know where they are weak in visibility
   - they need prioritized, actionable content recommendations

   The project takes a business domain and turns it into prioritized opportunities and content actions.

   ## 2) What the project does (high-level flow)

   1. Create a business profile (`name`, `domain`, `industry`, `competitors`)
   2. Run a 3-agent pipeline
   3. Get scored query opportunities
   4. Get recommendations for high-opportunity gaps
   5. Recheck individual queries over time

   ## 3) System design (architecture)

   ### Core layers

   - `api` layer: Flask routes and request/response contracts
   - `service` layer: pipeline orchestration and workflow sequencing
   - `agent` layer: specialized AI/business logic units
   - `model` layer: SQLAlchemy persistence
   - `utils` layer: provider clients (OpenAI, DataForSEO), parsing, scoring helpers

   ### Why this design works

   - clear separation of concerns
   - each agent can evolve independently
   - easier testing (mock/fallback behavior in clients)
   - straightforward extension for async/background processing later

   ## 4) Agent pipeline setup and behavior

   Pipeline entrypoint:

   - `POST /api/v1/profiles/{profile_uuid}/run`
   - orchestrated by `PipelineOrchestrator` in `app/services/pipeline_orchestrator.py`

   ### Agent 1: Query Discovery

   File: `app/agents/discovery_agent.py`

   Input:

   - domain
   - industry
   - competitors

   Output:

   - list of 10-20 realistic search/assistant-style queries

   Behavior:

   - uses LLM prompt for structured JSON
   - if LLM output fails/unusable, uses deterministic fallback query list

   ### Agent 2: Visibility Scoring

   File: `app/agents/scoring_agent.py`

   Input:

   - query text
   - target domain

   Output per query:

   - estimated search volume
   - competitive difficulty (0-100)
   - domain visibility (visible/not visible)
   - visibility position
   - opportunity score

   Behavior:

   - tries DataForSEO for volume
   - tries LLM for difficulty estimate
   - uses deterministic fallback when APIs are missing/fail
   - calculates final score via shared scoring utility

   ### Agent 3: Recommendation

   File: `app/agents/recommendation_agent.py`

   Input:

   - target domain
   - top not-visible queries

   Output:

   - 3-5 recommendations with title, content type, priority, rationale, keywords

   Behavior:

   - uses LLM for recommendation generation
   - deterministic fallback recommendations if provider fails

   ### Persistence + output

   The orchestrator writes:

   - pipeline run metadata (`PipelineRun`)
   - scored queries (`DiscoveredQuery`)
   - recommendations (`Recommendation`)

   Then API returns:

   - status
   - discovered/scored counts
   - top queries
   - recommendations

   ## 5) Technology stack

   ### Backend

   - Python
   - Flask
   - Flask-SQLAlchemy
   - Flask-Migrate (Alembic)

   ### Integrations

   - OpenAI API (LLM generation)
   - DataForSEO API (search volume metrics)
   - requests (HTTP integration)

   ### Database

   - SQLAlchemy-backed DB
   - SQLite fallback for local/demo
   - PostgreSQL supported via env configuration

   ### Testing & tooling

   - pytest
   - python-dotenv

   ## 6) API design and contract

   Base response envelope:

   - success: `{"success": true, "data": ..., "error": null}`
   - error: `{"success": false, "data": null, "error": {"message": "...", "code": "..."}}`

   Main endpoints:

   - `POST /api/v1/profiles`
   - `GET /api/v1/profiles/{profile_uuid}`
   - `POST /api/v1/profiles/{profile_uuid}/run`
   - `GET /api/v1/profiles/{profile_uuid}/queries`
   - `GET /api/v1/profiles/{profile_uuid}/recommendations`
   - `POST /api/v1/queries/{query_uuid}/recheck`

   ## 7) How to run for demo/interview

   From project root:

   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   export FLASK_APP=app
   flask run --port 5000
   ```

   Demo URLs:

   - App/UI root: `http://127.0.0.1:5000/`
   - Swagger docs: `http://127.0.0.1:5000/docs`
   - OpenAPI spec: `http://127.0.0.1:5000/openapi.json`

   ## 8) Current API-key status (checked today)

   Live connectivity check result:

   - OpenAI key variable is present, but provider returned `401 invalid_api_key`
   - DataForSEO credentials are present, but provider returned `401 unauthorized`

   Meaning:

   - pipeline still runs because code has deterministic fallback behavior
   - external provider responses are currently mock/fallback, not real-provider output

   ## 9) How to fix API keys quickly

   1. Replace credentials in `.env` with active provider keys
   2. Restart Flask server so new env values are loaded
   3. Re-run a quick live probe:
      - OpenAI test completion should return `200`
      - DataForSEO endpoint should return API status `20000`
   4. Run one pipeline call and verify output quality improves (less fallback-like)

   ## 10) Interview talking points (ready script)

   Use this simple narrative:

   1. "I designed this as a modular, API-first intelligence pipeline."
   2. "Each agent has one responsibility: discover -> score -> recommend."
   3. "I added robust fallback behavior so the system still works even if providers fail."
   4. "The orchestrator persists every stage so results are auditable and re-runnable."
   5. "This architecture can scale by moving agent execution to background workers."

   ## 11) Future improvements (professional roadmap)

   ### Short term

   - add auth and multi-user access control
   - add async queue (Celery/RQ) for long-running pipelines
   - improve observability: structured logs, metrics, run tracing

   ### Medium term

   - replace simulated visibility with real SERP/AI answer-grounded visibility checks
   - improve recommendation relevance with historical performance feedback
   - optimize query/recommendation matching logic (better targeting than first not-visible query)

   ### Long term

   - add campaign tracking loop (recommendation -> publish -> measure -> re-score)
   - introduce model/provider routing and cost control policies
   - build richer dashboard analytics and executive reporting views

   ## 12) Risks and trade-offs to mention honestly

   - current visibility check is simulated (deterministic), not live SERP ingestion
   - pagination/filtering currently done in-memory for simplicity
   - provider failures currently degrade to fallback instead of job retry queue

   These are acceptable for assessment scope and are clear extension points for production hardening.


