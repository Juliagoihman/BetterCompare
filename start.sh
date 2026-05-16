#!/bin/bash
set -e

echo "Starting vertical MCPs..."
python verticals/internet/main.py &
python verticals/mobile/main.py &
python verticals/travel/main.py &
python verticals/insurance/main.py &

sleep 2

echo "Starting BetterCompare proxy..."
python proxy/main.py
