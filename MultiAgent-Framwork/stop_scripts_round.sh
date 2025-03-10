#!/bin/bash

echo "Stopping all related processes..."

# 1) Kill the infinite-loop script itself (restart_scripts_round.sh)
pkill -f restart_scripts_round.sh

# 2) Kill Python processes started by that script
pkill -f BhrLgcParallel_once.py
pkill -f CmtRpyLgcRunning.py
pkill -f Socket.py

# 3) (Optional) Kill ALL Python processes
# WARNING: This will terminate every Python process on the system,
# including unrelated ones (e.g., Jupyter notebooks, other Python apps).
# Uncomment if you really want to do this.
# pkill python

echo "All related processes have been stopped."