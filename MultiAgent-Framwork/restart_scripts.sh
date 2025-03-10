#!/bin/bash

# Kill existing processes
pkill -f BhrLgcParallel.py
pkill -f CmtRpyLgcRunning.py
pkill -f Socket.py

# Restart scripts
cd /data/app/game/aitown/AIModule/satoshiLiveAI/BhrCtrl
nohup python3 ../BhrCtrl/BhrLgcParallel.py > ../BhrLgcParallel.log 2>&1 &

cd /data/app/game/aitown/AIModule/satoshiLiveAI/CmtRpyCtrl
nohup python3 ../CmtRpyCtrl/CmtRpyLgcRunning.py > ../CmtRpyLgcRunning.log 2>&1 &

cd /data/app/game/aitown/AIModule/satoshiLiveAI/NetworkSocket
nohup python3 ../NetworkSocket/Socket.py > ../Socket.log 2>&1 &