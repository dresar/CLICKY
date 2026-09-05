@echo off
title CLICKY_Traffic_Simulator
cd /d "c:\Users\NCN0C\Downloads\CLICKY"
echo [%date% %time%] Starting CLICKY Traffic Simulator for 1 Hour (19:00 - 20:00)... >> schedule_run.log
py gas.py --duration 3600 --visits 100000 >> schedule_run.log 2>&1
echo [%date% %time%] Task finished or timed out. >> schedule_run.log
