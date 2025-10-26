#!/bin/bash
pkill -f professional_dashboard.py
sleep 2
cd /opt/crypto-trading
nohup python3 /opt/crypto-trading/professional_dashboard.py > /opt/crypto-trading/professional_dashboard.log 2>&1 &
sleep 3
echo "Professional Dashboard restarted on port 3000"
ps aux | grep professional_dashboard | grep -v grep
