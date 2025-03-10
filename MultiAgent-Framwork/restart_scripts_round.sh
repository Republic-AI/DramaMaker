#!/bin/bash

LOG_DIR="/Users/jackhan/Desktop/AITown/satoshiLive/memelive/MultiAgent-Framwork"
BHR_DIR="$LOG_DIR/BhrCtrl"
CMT_DIR="$LOG_DIR/CmtRpyCtrl"
SOCKET_DIR="$LOG_DIR/NetworkSocket"

while true
do
    echo "========= New Round Started at $(date) ========="

    #
    # 1) Start a new instance of BhrLgcParallel_once.py
    #    (Do NOT kill the old one, in case it's still running)
    #
    echo "[1/3] Starting a new BhrLgcParallel_once.py..."
    cd "$BHR_DIR"
    nohup python3 ../BhrCtrl/BhrLgcParallel_once.py >> ../BhrLgcParallel_once.log 2>&1 &

    #
    # 2) Restart CmtRpyLgcRunning.py (kill old, then start new)
    #
    echo "[2/3] Killing old CmtRpyLgcRunning.py..."
    pkill -f CmtRpyLgcRunning.py

    echo "      Starting a new CmtRpyLgcRunning.py..."
    cd "$CMT_DIR"
    nohup python3 ../CmtRpyCtrl/CmtRpyLgcRunning.py >> ../CmtRpyLgcRunning.log 2>&1 &

    #
    # 3) Restart Socket.py (kill old, then start new)
    #
    echo "[3/3] Killing old Socket.py..."
    pkill -f Socket.py

    echo "      Starting a new Socket.py..."
    cd "$SOCKET_DIR"
    nohup python3 ../NetworkSocket/Socket.py >> ../Socket.log 2>&1 &

    #
    # Sleep 40 seconds until next round
    #
    echo "Sleeping 40 seconds before next round..."
    sleep 40
done