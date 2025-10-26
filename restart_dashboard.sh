#!/bin/bash
pkill -f modern_dashboard.py
sleep 2
cd /opt/crypto-trading
nohup /opt/crypto-trading/venv/bin/python3 /opt/crypto-trading/modern_dashboard.py > /opt/crypto-trading/modern_dashboard.log 2>&1 &
sleep 3
echo "Dashboard restarted. Check status:"
ps aux | grep modern_dashboard | grep -v grep
