#!/bin/bash
set -e

echo "Starting vertical MCPs..."
cd /app
python verticals/internet/main.py &
python verticals/mobile/main.py &
python verticals/travel/main.py &
python verticals/insurance/main.py &

sleep 2

echo "Starting admin API on port 8788..."
cd /app/proxy && uvicorn admin_app:app --host 0.0.0.0 --port 8788 &

echo "Starting MCP proxy on port 8787..."
cd /app/proxy && python main.py
