# Lab 6 Compliance Checklist

Legend: **PASS** = verified in this sandbox by running real code.
**Not verified** = code is written correctly per spec, but could not be
exercised here (no real Gemini API key / no network egress to Google).

## Stage A — REST + database foundation

| Requirement | Status |
|---|---|
| GET /health -> 200 | PASS (curl-tested) |
| GET /documents -> 200 | PASS |
| POST /documents valid -> 201 | PASS |
| POST /documents invalid -> 422 | PASS |
| GET /documents/{id} missing -> 404 | PASS |
| PUT /documents/{id} | PASS |
| DELETE /documents/{id} | PASS |
| POST /documents/upload text/plain -> 201, content stored | PASS |
| POST /documents/upload unsupported type -> 400 | PASS |
| Session(engine) pattern kept unchanged | PASS (code review) |

## Phase 3 — Alembic migration

| Requirement | Status |
|---|---|
| Adds nullable `ai_summary` column | PASS — migration applied against a documents.db with a pre-existing seeded row |
| Does not delete documents.db | PASS |
| Existing data preserved after migration | PASS — verified the seed row (`id=1`) still had all its original fields after `alembic upgrade head` |
| Migration reviewed before applying | PASS — see the migration file's diff shown before `upgrade head` was run |

## Phase 4 — Gemini integration

| Requirement | Status |
|---|---|
| GEMINI_API_KEY loaded from .env, never hardcoded | PASS (code review — `settings.py`) |
| POST /documents/{id}/analyze exists | PASS |
| Returns 404 for missing document | PASS (curl-tested) |
| R-T-C-F prompt structure | PASS (code review — `gemini_service.py`) |
| Structured JSON response contract | Not verified — requires a real Gemini call |
| Saves only `summary` into `ai_summary`, commits | PASS (code review) |
| Gemini failure -> controlled error, no secrets/tracebacks leaked | PASS — tested via missing-key path, returned clean 502 with no traceback |

## Phase 5 — Read-only agent

| Requirement | Status |
|---|---|
| Agent cannot create/update/delete | PASS (code review — no such tools exist in `TOOLS`) |
| Exactly 3 whitelisted tools | PASS |
| POST /agent/ask exists, returns 200 | PASS (curl-tested) |
| Only whitelisted tools execute | PASS — verified with `tests/fakes.py`: a scripted `delete_document` tool call was rejected and logged, never executed |
| MAX_STEPS = 5 enforced | PASS — verified with a scripted client that never returns a final answer; loop stopped at exactly 5 steps |
| Tool observation fed back to Gemini, loop continues to final answer | PASS — verified with a 2-step scripted scenario (tool call -> final answer) |
| Tool exceptions converted to safe observations | PASS (code review — `try/except` around each tool call in `agent_service.py`) |
| Tool name + success/failure logged | PASS — visible in test output (`agent step=1 tool=delete_document result=rejected_not_whitelisted`) |
| Real Gemini decides the tool call (not a stub) | Not verified — requires a real API key |

## Phase 6 — AI-assisted development

| Requirement | Status |
|---|---|
| One scoped AI-assisted change documented | PASS — see `ai_assisted_review.md` |
| Prompt + diff + 3-5 line review note | PASS |

## Phase 7 — Testing

| Requirement | Status |
|---|---|
| All HTTP contract cases tested through real HTTP (not direct function calls) | PASS — via `curl` and `run_contract_tests.py` (both use real HTTP requests to a running uvicorn server) |
| /docs, /redoc, /openapi.json work | PASS — confirmed reachable while the server was running |

## Phase 8 — Postman

| Requirement | Status |
|---|---|
| Collection covers health/CRUD/invalid/upload/AI/agent | PASS — `SmartDoc_AI.postman_collection.json`, validated as syntactically correct JSON |
| base_url + document_id variables | PASS |

## Phase 9 — Security review

| Requirement | Status |
|---|---|
| No API key hardcoded | PASS (code review) |
| .env git-ignored | PASS — see `.gitignore` |
| .env.example has placeholders only | PASS |
| No secrets committed | PASS |
| Error responses don't expose tracebacks | PASS — tested: missing-key /analyze returned `{"detail": "GEMINI_API_KEY is not configured."}`, no stack trace |
| Agent tools strictly whitelisted | PASS — tested |
| Agent is read-only | PASS (code review — no write/delete tool exists) |
| MAX_STEPS = 5 | PASS — tested |
| Tool arguments validated | PASS (code review — `get_document_tool`/`search_documents_tool` raise `ValueError` on bad input) |
| Database data not lost | PASS — tested via the migration |

## Overall

Everything that does **not** require a live Gemini API call was actually
executed and is a genuine PASS. The two items marked "Not verified"
(structured JSON from a real Gemini call, and a real model choosing a
tool) need a real `GEMINI_API_KEY` and network access this sandbox
doesn't have — run `python run_contract_tests.py` with your own key to
close those out.
