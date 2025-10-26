
#!/usr/bin/env python3
"""
LLM Tools Module - Function Calling for GPT-4o
Provides database query functions that the LLM can call to access trading data
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

class TradingDataTools:
    """Tools for querying trading database that LLM can call"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
    
    def query_trades(
        self, 
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        exchange: Optional[str] = None,
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Query trades from database with filters
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            exchange: 'binance' or 'kraken'
            limit: Maximum number of trades to return
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
        
        Returns:
            List of trade records
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
            
            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)
            
            if side:
                query += " AND side = %s"
                params.append(side.lower())
            
            if exchange:
                query += " AND exchange = %s"
                params.append(exchange.lower())
            
            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            trades = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Convert datetime objects to strings for JSON serialization
            for trade in trades:
                if isinstance(trade.get('timestamp'), datetime):
                    trade['timestamp'] = trade['timestamp'].isoformat()
            
            return trades
        except Exception as e:
            return [{"error": f"Failed to query trades: {str(e)}"}]
    
    def get_agent_decisions(
        self,
        agent: Optional[str] = None,
        executed: Optional[bool] = None,
        min_confidence: Optional[float] = None,
        limit: int = 20,
        hours_back: int = 24
    ) -> List[Dict]:
        """
        Get agent decisions with full reasoning
        
        Args:
            agent: Specific agent name (e.g., 'research_agent', 'scalping_agent')
            executed: Filter by execution status
            min_confidence: Minimum confidence level (0-100)
            limit: Maximum number of decisions to return
            hours_back: How many hours back to look
        
        Returns:
            List of agent decision records with full reasoning
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM agent_decisions WHERE timestamp >= %s"
            params = [datetime.now() - timedelta(hours=hours_back)]
            
            if agent:
                query += " AND agent = %s"
                params.append(agent)
            
            if executed is not None:
                query += " AND executed = %s"
                params.append(executed)
            
            if min_confidence:
                query += " AND confidence >= %s"
                params.append(min_confidence)
            
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            decisions = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Convert datetime objects to strings
            for decision in decisions:
                if isinstance(decision.get('timestamp'), datetime):
                    decision['timestamp'] = decision['timestamp'].isoformat()
            
            return decisions
        except Exception as e:
            return [{"error": f"Failed to query agent decisions: {str(e)}"}]
    
    def get_portfolio_metrics(self) -> Dict:
        """
        Get current portfolio metrics and statistics
        
        Returns:
            Portfolio metrics including capital, PnL, risk metrics
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get latest risk metrics
            cursor.execute("""
                SELECT * FROM risk_metrics 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            latest_metrics = cursor.fetchone()
            
            # Calculate trade statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    AVG(pnl) as avg_pnl,
                    SUM(pnl) as total_pnl
                FROM trades
                WHERE timestamp >= NOW() - INTERVAL '7 days'
            """)
            trade_stats = cursor.fetchone()
            
            # Get open positions count
            cursor.execute("""
                SELECT COUNT(*) as open_positions
                FROM positions
                WHERE status = 'open'
            """)
            positions = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            result = {
                "latest_metrics": dict(latest_metrics) if latest_metrics else {},
                "trade_statistics": dict(trade_stats) if trade_stats else {},
                "open_positions_count": positions['open_positions'] if positions else 0
            }
            
            # Convert datetime objects to strings
            if result['latest_metrics'].get('timestamp'):
                result['latest_metrics']['timestamp'] = result['latest_metrics']['timestamp'].isoformat()
            
            return result
        except Exception as e:
            return {"error": f"Failed to get portfolio metrics: {str(e)}"}
    
    def get_market_data(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100
    ) -> List[Dict]:
        """
        Get historical market data (OHLCV)
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1h', '4h', '1d')
            limit: Number of candles to return
        
        Returns:
            List of OHLCV data
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM market_data
                WHERE symbol = %s AND timeframe = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (symbol, timeframe, limit))
            
            market_data = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Convert datetime objects to strings
            for candle in market_data:
                if isinstance(candle.get('timestamp'), datetime):
                    candle['timestamp'] = candle['timestamp'].isoformat()
            
            return list(reversed(market_data))  # Return in chronological order
        except Exception as e:
            return [{"error": f"Failed to get market data: {str(e)}"}]
    
    def get_risk_analysis(self, days: int = 7) -> Dict:
        """
        Get detailed risk analysis over specified period
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Risk analysis including drawdown, volatility, Sharpe ratio
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM risk_metrics
                WHERE timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """, (days,))
            
            metrics = cursor.fetchall()
            
            if not metrics:
                return {"error": "No risk data available"}
            
            # Calculate statistics
            pnls = [float(m['daily_pnl']) for m in metrics if m.get('daily_pnl')]
            max_drawdowns = [float(m['max_drawdown']) for m in metrics if m.get('max_drawdown')]
            
            cursor.close()
            conn.close()
            
            return {
                "period_days": days,
                "avg_daily_pnl": sum(pnls) / len(pnls) if pnls else 0,
                "max_daily_gain": max(pnls) if pnls else 0,
                "max_daily_loss": min(pnls) if pnls else 0,
                "worst_drawdown": min(max_drawdowns) if max_drawdowns else 0,
                "current_sharpe_ratio": float(metrics[-1]['sharpe_ratio']) if metrics[-1].get('sharpe_ratio') else None,
                "current_win_rate": float(metrics[-1]['win_rate']) if metrics[-1].get('win_rate') else None,
                "data_points": len(metrics)
            }
        except Exception as e:
            return {"error": f"Failed to analyze risk: {str(e)}"}
    
    def get_agent_performance(self, days: int = 7) -> List[Dict]:
        """
        Get performance metrics for each trading agent
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Performance metrics per agent
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    agent,
                    COUNT(*) as total_decisions,
                    SUM(CASE WHEN executed THEN 1 ELSE 0 END) as executed_decisions,
                    AVG(confidence) as avg_confidence,
                    MAX(confidence) as max_confidence,
                    MIN(confidence) as min_confidence
                FROM agent_decisions
                WHERE timestamp >= NOW() - INTERVAL '%s days'
                GROUP BY agent
                ORDER BY total_decisions DESC
            """, (days,))
            
            agent_stats = cursor.fetchall()
            
            # Get trade outcomes by agent (if agent field exists in trades table)
            cursor.execute("""
                SELECT 
                    p.agent,
                    COUNT(*) as trades,
                    SUM(CASE WHEN p.realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    AVG(p.realized_pnl) as avg_pnl,
                    SUM(p.realized_pnl) as total_pnl
                FROM positions p
                WHERE p.status = 'closed' 
                AND p.agent IS NOT NULL
                GROUP BY p.agent
            """)
            
            trade_stats = {row['agent']: dict(row) for row in cursor.fetchall()}
            
            cursor.close()
            conn.close()
            
            # Combine stats
            results = []
            for agent_stat in agent_stats:
                agent_name = agent_stat['agent']
                result = dict(agent_stat)
                
                if agent_name in trade_stats:
                    result.update({
                        'trades': trade_stats[agent_name]['trades'],
                        'winning_trades': trade_stats[agent_name]['winning_trades'],
                        'win_rate': (trade_stats[agent_name]['winning_trades'] / trade_stats[agent_name]['trades'] * 100) if trade_stats[agent_name]['trades'] > 0 else 0,
                        'avg_pnl': float(trade_stats[agent_name]['avg_pnl']) if trade_stats[agent_name]['avg_pnl'] else 0,
                        'total_pnl': float(trade_stats[agent_name]['total_pnl']) if trade_stats[agent_name]['total_pnl'] else 0
                    })
                
                results.append(result)
            
            return results
        except Exception as e:
            return [{"error": f"Failed to get agent performance: {str(e)}"}]
    
    def get_orchestrator_state(self) -> Dict:
        """
        Get current state of the orchestrator and decision queue
        
        Returns:
            Orchestrator state including pending decisions and priorities
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get recent pending decisions
            cursor.execute("""
                SELECT agent, decision, reasoning, confidence, timestamp
                FROM agent_decisions
                WHERE executed = FALSE
                AND timestamp >= NOW() - INTERVAL '1 hour'
                ORDER BY confidence DESC, timestamp DESC
                LIMIT 10
            """)
            pending_decisions = cursor.fetchall()
            
            # Get agent activity in last hour
            cursor.execute("""
                SELECT 
                    agent,
                    COUNT(*) as decisions_last_hour,
                    AVG(confidence) as avg_confidence
                FROM agent_decisions
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
                GROUP BY agent
                ORDER BY decisions_last_hour DESC
            """)
            agent_activity = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convert datetime objects
            for decision in pending_decisions:
                if isinstance(decision.get('timestamp'), datetime):
                    decision['timestamp'] = decision['timestamp'].isoformat()
            
            return {
                "pending_decisions": [dict(d) for d in pending_decisions],
                "agent_activity": [dict(a) for a in agent_activity],
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to get orchestrator state: {str(e)}"}


# Function definitions for OpenAI function calling
FUNCTION_DEFINITIONS = [
    {
        "name": "query_trades",
        "description": "Query trades from the database with various filters. Use this to analyze trading history, patterns, and performance.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USDT')"
                },
                "side": {
                    "type": "string",
                    "enum": ["buy", "sell"],
                    "description": "Trade side: 'buy' or 'sell'"
                },
                "exchange": {
                    "type": "string",
                    "enum": ["binance", "kraken"],
                    "description": "Exchange name: 'binance' or 'kraken'"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of trades to return (default: 50)",
                    "default": 50
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO format (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO format (YYYY-MM-DD)"
                }
            }
        }
    },
    {
        "name": "get_agent_decisions",
        "description": "Get agent decisions with full reasoning and context. Use this to understand why agents made specific decisions.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Specific agent name (e.g., 'research_agent', 'scalping_agent', 'swing_agent')"
                },
                "executed": {
                    "type": "boolean",
                    "description": "Filter by execution status (true for executed, false for pending)"
                },
                "min_confidence": {
                    "type": "number",
                    "description": "Minimum confidence level (0-100)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of decisions to return (default: 20)",
                    "default": 20
                },
                "hours_back": {
                    "type": "integer",
                    "description": "How many hours back to look (default: 24)",
                    "default": 24
                }
            }
        }
    },
    {
        "name": "get_portfolio_metrics",
        "description": "Get current portfolio metrics including capital, P&L, and risk statistics. Use this for portfolio overview.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_market_data",
        "description": "Get historical market data (OHLCV candles) for technical analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Trading pair symbol (e.g., 'BTC/USDT')"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
                    "description": "Timeframe for candles (default: '1h')",
                    "default": "1h"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of candles to return (default: 100)",
                    "default": 100
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_risk_analysis",
        "description": "Get detailed risk analysis including drawdown, volatility, and Sharpe ratio over a specified period.",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 7)",
                    "default": 7
                }
            }
        }
    },
    {
        "name": "get_agent_performance",
        "description": "Get performance metrics for each trading agent including decision accuracy and trade outcomes.",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 7)",
                    "default": 7
                }
            }
        }
    },
    {
        "name": "get_orchestrator_state",
        "description": "Get current state of the orchestrator including pending decisions and agent activity. Use this to understand decision prioritization.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]


def execute_function(function_name: str, arguments: Dict, tools: TradingDataTools) -> str:
    """Execute a function call and return the result as JSON string"""
    try:
        if function_name == "query_trades":
            result = tools.query_trades(**arguments)
        elif function_name == "get_agent_decisions":
            result = tools.get_agent_decisions(**arguments)
        elif function_name == "get_portfolio_metrics":
            result = tools.get_portfolio_metrics()
        elif function_name == "get_market_data":
            result = tools.get_market_data(**arguments)
        elif function_name == "get_risk_analysis":
            result = tools.get_risk_analysis(**arguments)
        elif function_name == "get_agent_performance":
            result = tools.get_agent_performance(**arguments)
        elif function_name == "get_orchestrator_state":
            result = tools.get_orchestrator_state()
        else:
            result = {"error": f"Unknown function: {function_name}"}
        
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": f"Function execution error: {str(e)}"})
