#!/bin/bash

cd /app/proxy

uvicorn verticals.internet.main:app --port 8801 &
uvicorn verticals.mobile.main:app --port 8802 &
uvicorn verticals.travel.main:app --port 8803 &
uvicorn verticals.insurance.main:app --port 8804 &

sleep 2

uvicorn main:app --host 0.0.0.0 --port 8787
