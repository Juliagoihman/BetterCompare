#!/bin/bash
set -e

echo "Starting vertical MCPs..."
cd /app
python verticals/internet/main.py &
python verticals/mobile/main.py &
python verticals/travel/main.py &
python verticals/insurance/main.py &

sleep 2

echo "Starting BetterCompare proxy..."
cd /app/proxy && python main.py
