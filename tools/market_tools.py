"""
Tool definitions for the Financial Research Agent.

Each tool has two parts:
1. A SCHEMA — tells Claude what the tool does and what parameters it accepts
2. A HANDLER — the actual Python function that runs when Claude calls the tool

This is how Claude's "tool use" (function calling) works:
- You send Claude a message + a list of tool schemas
- Claude decides which tool(s) to call and with what arguments
- You execute the tool and send the result back to Claude
- Claude uses the result to continue reasoning

Think of it like giving Claude hands — the schemas are the instruction manual,
and the handlers are the actual muscles.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


# =============================================================================
# TOOL SCHEMAS — These are sent to Claude so it knows what tools are available
# =============================================================================

TOOL_SCHEMAS = [
    {
        "name": "get_stock_data",
        "description": (
            "Fetch historical stock price data for a given ticker symbol. "
            "Returns OHLCV data (Open, High, Low, Close, Volume) along with "
            "basic statistics like average price, volatility, and price change."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'SPY')"
                },
                "period": {
                    "type": "string",
                    "description": "Time period for data. Options: '1mo', '3mo', '6mo', '1y', '2y'",
                    "enum": ["1mo", "3mo", "6mo", "1y", "2y"]
                }
            },
            "required": ["ticker"]
        }
    },
    {
        "name": "get_company_info",
        "description": (
            "Fetch fundamental company information including sector, industry, "
            "market cap, P/E ratio, dividend yield, and a business summary."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., 'AAPL', 'MSFT')"
                }
            },
            "required": ["ticker"]
        }
    },
    {
        "name": "get_technical_indicators",
        "description": (
            "Calculate technical indicators for a stock: Simple Moving Averages "
            "(SMA 20, 50, 200), Relative Strength Index (RSI), MACD, and "
            "Bollinger Bands. Useful for trend and momentum analysis."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol"
                }
            },
            "required": ["ticker"]
        }
    },
]


# =============================================================================
# TOOL HANDLERS — The actual functions that execute when Claude calls a tool
# =============================================================================

def get_stock_data(ticker: str, period: str = "3mo") -> dict:
    """Fetch historical stock data and compute basic statistics."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty:
            return {"error": f"No data found for ticker '{ticker}'"}

        # Compute basic statistics
        latest = df.iloc[-1]
        first = df.iloc[0]
        price_change = ((latest["Close"] - first["Close"]) / first["Close"]) * 100
        volatility = df["Close"].pct_change().std() * (252 ** 0.5) * 100  # Annualized

        # Recent price history (last 10 trading days)
        recent = df.tail(10)[["Close", "Volume"]].copy()
        recent["Close"] = recent["Close"].round(2)
        recent.index = recent.index.strftime("%Y-%m-%d")

        return {
            "ticker": ticker.upper(),
            "period": period,
            "current_price": round(latest["Close"], 2),
            "period_high": round(df["High"].max(), 2),
            "period_low": round(df["Low"].min(), 2),
            "price_change_pct": round(price_change, 2),
            "annualized_volatility_pct": round(volatility, 2),
            "avg_daily_volume": int(df["Volume"].mean()),
            "recent_prices": recent.to_dict(),
            "data_points": len(df),
        }
    except Exception as e:
        return {"error": str(e)}


def get_company_info(ticker: str) -> dict:
    """Fetch fundamental company information."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Extract key fundamentals (with safe .get() to handle missing fields)
        return {
            "ticker": ticker.upper(),
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "avg_analyst_rating": info.get("recommendationKey", "N/A"),
            "business_summary": info.get("longBusinessSummary", "N/A")[:500],
        }
    except Exception as e:
        return {"error": str(e)}


def get_technical_indicators(ticker: str) -> dict:
    """Calculate technical indicators for trend and momentum analysis."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")

        if df.empty:
            return {"error": f"No data found for ticker '{ticker}'"}

        close = df["Close"]

        # Simple Moving Averages
        sma_20 = close.rolling(window=20).mean().iloc[-1]
        sma_50 = close.rolling(window=50).mean().iloc[-1]
        sma_200 = close.rolling(window=200).mean().iloc[-1]

        # RSI (14-day)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_value = rsi.iloc[-1]

        # MACD
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_histogram = macd_line - signal_line

        # Bollinger Bands (20-day)
        bb_middle = sma_20
        bb_std = close.rolling(window=20).std().iloc[-1]
        bb_upper = bb_middle + (2 * bb_std)
        bb_lower = bb_middle - (2 * bb_std)

        current_price = close.iloc[-1]

        # Determine trend signals
        trend_signals = []
        if current_price > sma_50 > sma_200:
            trend_signals.append("Bullish: Price above SMA50 and SMA200 (golden cross territory)")
        elif current_price < sma_50 < sma_200:
            trend_signals.append("Bearish: Price below SMA50 and SMA200 (death cross territory)")
        if rsi_value > 70:
            trend_signals.append("RSI overbought (>70): Potential pullback")
        elif rsi_value < 30:
            trend_signals.append("RSI oversold (<30): Potential bounce")
        if macd_histogram.iloc[-1] > 0 and macd_histogram.iloc[-2] <= 0:
            trend_signals.append("MACD bullish crossover (histogram turned positive)")
        elif macd_histogram.iloc[-1] < 0 and macd_histogram.iloc[-2] >= 0:
            trend_signals.append("MACD bearish crossover (histogram turned negative)")

        return {
            "ticker": ticker.upper(),
            "current_price": round(current_price, 2),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "sma_200": round(sma_200, 2),
            "rsi_14": round(rsi_value, 2),
            "macd": round(macd_line.iloc[-1], 2),
            "macd_signal": round(signal_line.iloc[-1], 2),
            "macd_histogram": round(macd_histogram.iloc[-1], 2),
            "bollinger_upper": round(bb_upper, 2),
            "bollinger_middle": round(bb_middle, 2),
            "bollinger_lower": round(bb_lower, 2),
            "trend_signals": trend_signals if trend_signals else ["Neutral / no strong signals"],
        }
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# TOOL DISPATCHER — Maps tool names to handler functions
# =============================================================================

TOOL_HANDLERS = {
    "get_stock_data": get_stock_data,
    "get_company_info": get_company_info,
    "get_technical_indicators": get_technical_indicators,
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Execute a tool by name with the given inputs.
    Returns the result as a JSON string (Claude expects string results).
    """
    import json

    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    result = handler(**tool_input)
    return json.dumps(result, indent=2, default=str)
