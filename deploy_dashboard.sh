#!/bin/bash

echo "=========================================="
echo "🚀 Deploying Modern Crypto Dashboard"
echo "=========================================="

cd /opt/crypto-trading

# Stop current dashboard
echo "⏹️  Stopping current dashboard..."
pkill -f "enhanced_dashboard.py" || true
pkill -f "dashboard.py" || true

# Install/Update dependencies
echo "📦 Installing dependencies..."
/opt/crypto-trading/venv/bin/pip install -q dash==2.14.2 dash-auth==2.0.0 plotly==5.18.0 pandas==2.1.4 numpy==1.26.2

# Check database schema
echo "🔍 Checking database schema..."
/opt/crypto-trading/venv/bin/python3 << 'EOF'
import psycopg2
import json

with open('/opt/crypto-trading/config.json', 'r') as f:
    config = json.load(f)

try:
    conn = psycopg2.connect(**config['database'])
    cursor = conn.cursor()
    
    # Check if agent_decisions table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'agent_decisions'
        );
    """)
    
    if not cursor.fetchone()[0]:
        print("Creating agent_decisions table...")
        cursor.execute("""
            CREATE TABLE agent_decisions (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                agent VARCHAR(50),
                decision TEXT,
                reasoning TEXT,
                confidence DECIMAL(5, 2),
                executed BOOLEAN DEFAULT FALSE
            )
        """)
        cursor.execute("""
            CREATE INDEX idx_agent_decisions_timestamp ON agent_decisions(timestamp)
        """)
        conn.commit()
        print("✓ Table created successfully")
    else:
        print("✓ Table already exists")
    
    cursor.close()
    conn.close()
    print("✓ Database ready")
except Exception as e:
    print(f"❌ Database error: {e}")
EOF

# Make dashboard executable
chmod +x /opt/crypto-trading/modern_dashboard.py

# Start new dashboard
echo "🚀 Starting modern dashboard..."
nohup /opt/crypto-trading/venv/bin/python3 /opt/crypto-trading/modern_dashboard.py > /opt/crypto-trading/modern_dashboard.log 2>&1 &

# Wait a moment
sleep 3

# Check if it's running
if pgrep -f "modern_dashboard.py" > /dev/null; then
    echo "✓ Dashboard started successfully!"
    echo "📍 Access at: http://192.34.59.191:3000"
    echo "🔐 Username: admin"
    echo "🔑 Password: CryptoTrader2024!"
else
    echo "❌ Dashboard failed to start. Check logs:"
    tail -30 /opt/crypto-trading/modern_dashboard.log
    exit 1
fi

echo "=========================================="
echo "✨ Deployment Complete!"
echo "=========================================="
