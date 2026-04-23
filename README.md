# AI Visibility (Flask + Multi-Agent Pipeline)

## Run locally

Create a virtualenv and install:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
export FLASK_APP=app
flask run
```

If you want migrations :

```bash
export FLASK_APP=app
flask db init
flask db migrate -m "init"
flask db upgrade
```


## Short summary (quick guide)

This backend API  flow:

register a business profile
run a 3.agent AI pipeline
view scored query opportunities
view content recommendations
recheck a single query score later

### Agents (easy step.by.step)

When you call `POST /api/v1/profiles/{profile_uuid}/run`, agents run in this order:

1. **Agent 1: Query Discovery**  
   Reads domain + industry + competitors and generates 10.20 user search questions.

2. **Agent 2: Visibility Scoring**  
   For each query, checks volume, estimates difficulty, checks visibility, and calculates opportunity score.

3. **Agent 3: Recommendation**  
   Takes high.opportunity queries where domain is not visible and creates actionable content ideas.

Final output gives:
. top opportunity queries
. recommendations
. pipeline status and counts

### Base URLs

. App: `http://127.0.0.1:5000`
. Swagger: `http://127.0.0.1:5000/docs`
. OpenAPI: `http://127.0.0.1:5000/openapi.json`

### API URLs

. `POST /api/v1/profiles`
. `GET /api/v1/profiles/{profile_uuid}`
. `POST /api/v1/profiles/{profile_uuid}/run`
. `GET /api/v1/profiles/{profile_uuid}/queries`
. `GET /api/v1/profiles/{profile_uuid}/recommendations`
. `POST /api/v1/queries/{query_uuid}/recheck`

### How to use (step.by.step)

1. Start server  
   `flask run ..port 5000`
2. Create profile  
   `POST /api/v1/profiles`
3. Copy `profile_uuid` from create response
4. Run pipeline  
   `POST /api/v1/profiles/{profile_uuid}/run`
5. View scored queries  
   `GET /api/v1/profiles/{profile_uuid}/queries`
6. View recommendations  
   `GET /api/v1/profiles/{profile_uuid}/recommendations`
7. Recheck one query later  
   `POST /api/v1/queries/{query_uuid}/recheck`

### LLM/API mode behavior

If `OPENAI_API_KEY` is set: real GPT.4o responses are used.
If key is missing/invalid: mock fallback still returns valid API responses.
If DataForSEO creds are missing/fail: deterministic mock volume is used.





## AI Tools Used

I used AI-assisted tools to support development, improve productivity, and refine system design.

### ChatGPT (OpenAI)
Used for system design, Flask architecture (app factory pattern), multi-agent pipeline design, SQLAlchemy schema structuring, debugging, and prompt engineering for structured LLM outputs.

### Antigravity AI Tool
Used for rapid prototyping, code exploration, boilerplate generation, and iterative refinement of API and service layer logic.
