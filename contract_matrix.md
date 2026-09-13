# Contract Verification Matrix — Lab 6

| Method / Path | Case | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| GET /health | normal | 200 | 200 | PASS |
| GET /documents | normal | 200 | 200 | PASS |
| POST /documents | valid body | 201 | 201 | PASS |
| POST /documents | invalid body | 422 | 422 | PASS |
| GET /documents/999999 | missing | 404 | 404 | PASS |
| POST /documents/upload | text/plain | 201 | 201 | PASS |
| POST /documents/upload | unsupported type | 400 | 400 | PASS |
| POST /documents/{id}/analyze | existing (needs real key for 200) | 200 | 502 | FAIL |
| POST /documents/{id}/analyze | missing | 404 | 404 | PASS |
| POST /agent/ask | document question | 200 | 200 | PASS |

> A FAIL on `analyze` with actual=502 means no real GEMINI_API_KEY was configured — this is the documented, controlled behavior, not an application bug.
