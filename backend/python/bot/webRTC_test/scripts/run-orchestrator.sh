#!/bin/bash
export $(grep -v '^#' ../.env | xargs)  # Load env vars from .env (assumes run from scripts/)

echo "Starting orchestrator API on http://localhost:8000 ..."
uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --reload


