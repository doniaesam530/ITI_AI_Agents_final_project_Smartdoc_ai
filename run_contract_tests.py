"""
Lab 6 - Automated contract verification for SmartDoc AI.

Usage:
    uvicorn main:app --reload      # in one terminal
    python run_contract_tests.py   # in another terminal

Notes:
- The /analyze test expects 200 only if a real GEMINI_API_KEY is set in
  .env. Without it, 502 is the CORRECT controlled behavior, not a bug.
- The /agent/ask test expects 200 either way (grounded answer needs a
  real key; without one it still returns 200 with a graceful message).
"""

import os
import tempfile

import requests

BASE_URL = "http://127.0.0.1:8000"
results = []


def record(method, path, case, expected, actual):
    status = "PASS" if expected == actual else "FAIL"
    results.append((f"{method} {path}", case, expected, actual, status))


def main():
    record("GET", "/health", "normal", 200, requests.get(f"{BASE_URL}/health").status_code)
    record("GET", "/documents", "normal", 200, requests.get(f"{BASE_URL}/documents").status_code)

    r = requests.post(
        f"{BASE_URL}/documents",
        json={"title": "Contract Doc", "content": "capstone content", "priority": 2},
    )
    record("POST", "/documents", "valid body", 201, r.status_code)
    doc_id = r.json().get("id") if r.status_code == 201 else None

    r = requests.post(f"{BASE_URL}/documents", json={"title": "Missing content"})
    record("POST", "/documents", "invalid body", 422, r.status_code)

    record(
        "GET", "/documents/999999", "missing", 404,
        requests.get(f"{BASE_URL}/documents/999999").status_code,
    )

    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("Uploaded via contract test.")
        txt_path = f.name
    with open(txt_path, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/documents/upload",
            files={"file": ("contract.txt", f, "text/plain")},
        )
    record("POST", "/documents/upload", "text/plain", 201, r.status_code)
    os.unlink(txt_path)

    with tempfile.NamedTemporaryFile(suffix=".pdf", mode="w", delete=False) as f:
        f.write("%PDF-1.4 fake")
        pdf_path = f.name
    with open(pdf_path, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/documents/upload",
            files={"file": ("contract.pdf", f, "application/pdf")},
        )
    record("POST", "/documents/upload", "unsupported type", 400, r.status_code)
    os.unlink(pdf_path)

    if doc_id is not None:
        r = requests.post(f"{BASE_URL}/documents/{doc_id}/analyze")
        record("POST", "/documents/{id}/analyze", "existing (needs real key for 200)", 200, r.status_code)

    r = requests.post(f"{BASE_URL}/documents/999999/analyze")
    record("POST", "/documents/{id}/analyze", "missing", 404, r.status_code)

    r = requests.post(f"{BASE_URL}/agent/ask", json={"message": "List the available documents"})
    record("POST", "/agent/ask", "document question", 200, r.status_code)

    header = "| Method / Path | Case | Expected | Actual | Pass/Fail |"
    sep = "|---|---|---|---|---|"
    lines = [header, sep]
    for path, case, expected, actual, status in results:
        lines.append(f"| {path} | {case} | {expected} | {actual} | {status} |")
    table = "\n".join(lines)
    print(table)

    with open("contract_matrix.md", "w") as f:
        f.write("# Contract Verification Matrix — Lab 6\n\n")
        f.write(table + "\n")
        f.write(
            "\n> A FAIL on `analyze` with actual=502 means no real "
            "GEMINI_API_KEY was configured — this is the documented, "
            "controlled behavior, not an application bug.\n"
        )
    print("\nSaved to contract_matrix.md")


if __name__ == "__main__":
    main()
