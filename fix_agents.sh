#!/bin/bash
echo "=== Crypto Trading System Fix Script ==="
echo "Fixing database connection issues..."

# Backup original agents
mkdir -p /opt/crypto-trading/agents/backup
cp /opt/crypto-trading/agents/*.py /opt/crypto-trading/agents/backup/

# Fix 1: Add connection pooling to all agents
echo "Adding connection pool support..."

# Replace the scalping agent
cp /opt/crypto-trading/agents/scalping_agent_fixed.py /opt/crypto-trading/agents/scalping_agent.py

# Fix 2: Restart PostgreSQL to clear stale connections
echo "Restarting PostgreSQL..."
systemctl restart postgresql
sleep 5

# Fix 3: Clear Redis cache
echo "Clearing Redis cache..."
redis-cli FLUSHALL

# Fix 4: Stop all agents
echo "Stopping all crypto agents..."
systemctl stop crypto-*

# Wait for clean shutdown
sleep 5

# Fix 5: Start agents one by one
echo "Starting agents..."
systemctl start crypto-data-collector
sleep 3
systemctl start crypto-signal-generator
sleep 3
systemctl start crypto-risk-manager
sleep 3
systemctl start crypto-order-executor
sleep 3
systemctl start crypto-market-analyzer
sleep 3
systemctl start crypto-portfolio-manager
sleep 3
systemctl start crypto-performance-tracker
sleep 3

echo "=== Fix Complete ==="
echo "Checking status..."
systemctl status crypto-* --no-pager | grep -E "Active:|crypto-"
