
#!/bin/bash
# Simple startup script for manual use

cd /opt/crypto-trading

# Start all agents
python3 agents/market_data_agent.py &
python3 agents/research_agent.py &
python3 agents/scalping_agent.py &
python3 agents/swing_agent.py &
python3 agents/portfolio_agent.py &
python3 agents/risk_manager_agent.py &
python3 agents/execution_agent.py &
python3 interactive_dashboard.py &

echo "All agents started!"
