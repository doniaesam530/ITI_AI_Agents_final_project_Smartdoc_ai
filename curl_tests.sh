#!/usr/bin/env bash
# Lab 6 - SmartDoc AI full contract smoke test (bash)
# Run this while uvicorn is up: uvicorn main:app --reload

BASE_URL="http://127.0.0.1:8000"

echo "=== GET /health -> 200 ==="
curl -i "$BASE_URL/health"

echo -e "\n=== GET /documents -> 200 ==="
curl -i "$BASE_URL/documents"

echo -e "\n=== POST /documents valid -> 201 ==="
curl -i -X POST "$BASE_URL/documents" \
  -H "Content-Type: application/json" \
  -d '{"title":"SmartDoc Notes","content":"FastAPI with AI","priority":2}'

echo -e "\n=== POST /documents invalid -> 422 ==="
curl -i -X POST "$BASE_URL/documents" \
  -H "Content-Type: application/json" \
  -d '{"title":"Missing content field"}'

echo -e "\n=== GET /documents/999999 -> 404 ==="
curl -i "$BASE_URL/documents/999999"

echo -e "\n=== POST /documents/upload (.txt) -> 201 ==="
echo "Sample plain text content" > sample.txt
curl -i -X POST "$BASE_URL/documents/upload" -F "file=@sample.txt;type=text/plain"

echo -e "\n=== POST /documents/upload unsupported type -> 400 ==="
echo "fake pdf bytes" > sample.pdf
curl -i -X POST "$BASE_URL/documents/upload" -F "file=@sample.pdf;type=application/pdf"

echo -e "\n=== POST /documents/1/analyze (existing) -> 200 (needs real GEMINI_API_KEY) ==="
curl -i -X POST "$BASE_URL/documents/1/analyze"

echo -e "\n=== POST /documents/999999/analyze (missing) -> 404 ==="
curl -i -X POST "$BASE_URL/documents/999999/analyze"

echo -e "\n=== POST /agent/ask -> 200 (needs real GEMINI_API_KEY for a grounded answer) ==="
curl -i -X POST "$BASE_URL/agent/ask" \
  -H "Content-Type: application/json" \
  -d '{"message":"List the available documents"}'

echo -e "\nDone."
