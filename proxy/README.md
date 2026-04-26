# BetterCompare

BetterCompare is a ChatGPT-facing proxy for multiple comparison verticals.

## Run locally

```bash
pip install -r requirements.txt
uvicorn proxy.main:app --reload --port 8000
