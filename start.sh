#!/bin/bash

# Start verticals in background
uvicorn proxy.verticals.internet.main:app --port 8801 &
uvicorn proxy.verticals.mobile.main:app --port 8802 &
uvicorn proxy.verticals.travel.main:app --port 8803 &

# Wait for verticals to start
sleep 2

# Start proxy
uvicorn proxy.main:app --host 0.0.0.0 --port 8787
