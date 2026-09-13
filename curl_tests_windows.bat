@echo off
REM Lab 6 - SmartDoc AI full contract smoke test (Windows CMD)
REM Run this while uvicorn is up: uvicorn main:app --reload

echo === GET /health -> 200 ===
curl -i http://127.0.0.1:8000/health

echo.
echo === GET /documents -> 200 ===
curl -i http://127.0.0.1:8000/documents

echo.
echo === POST /documents valid -> 201 ===
curl -i -X POST http://127.0.0.1:8000/documents ^
 -H "Content-Type: application/json" ^
 -d "{\"title\":\"SmartDoc Notes\",\"content\":\"FastAPI with AI\",\"priority\":2}"

echo.
echo === POST /documents invalid -> 422 ===
curl -i -X POST http://127.0.0.1:8000/documents ^
 -H "Content-Type: application/json" ^
 -d "{\"title\":\"Missing content field\"}"

echo.
echo === GET /documents/999999 -> 404 ===
curl -i http://127.0.0.1:8000/documents/999999

echo.
echo === POST /documents/upload with a .txt file -> 201 ===
echo Sample plain text content> sample.txt
curl -i -X POST http://127.0.0.1:8000/documents/upload -F "file=@sample.txt;type=text/plain"

echo.
echo === POST /documents/upload with unsupported type -> 400 ===
echo fake pdf bytes> sample.pdf
curl -i -X POST http://127.0.0.1:8000/documents/upload -F "file=@sample.pdf;type=application/pdf"

echo.
echo === POST /documents/1/analyze (existing) -> 200 (needs real GEMINI_API_KEY) ===
curl -i -X POST http://127.0.0.1:8000/documents/1/analyze

echo.
echo === POST /documents/999999/analyze (missing) -> 404 ===
curl -i -X POST http://127.0.0.1:8000/documents/999999/analyze

echo.
echo === POST /agent/ask -> 200 (needs real GEMINI_API_KEY for a grounded answer) ===
curl -i -X POST http://127.0.0.1:8000/agent/ask ^
 -H "Content-Type: application/json" ^
 -d "{\"message\":\"List the available documents\"}"

echo.
echo Done.
pause
