#!/bin/bash
set -e

# Due to docker compose volume mounting, we need to reinstall all pip packages
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

