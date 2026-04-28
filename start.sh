#!/bin/bash

# Start verticals in background
cd /app/proxy
uvicorn verticals.internet.main:app --port 8801 &
uvicorn verticals.mobile.main:app --port 8802 &
uvicorn verticals.travel.main:app --port 8803 &

# Wait for verticals to start
sleep 2

# Start proxy
uvicorn main:app --host 0.0.0.0 --port 8787
