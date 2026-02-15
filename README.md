# 🏦 Financial Research Agent

An AI-powered financial research assistant built with Claude's tool use (function calling) capability. The agent autonomously gathers market data, computes technical indicators, and synthesizes everything into clear research analysis.

## Architecture

```
User Question
     │
     ▼
┌─────────────┐     ┌──────────────────┐
│  Agent Loop  │◄───►│   Claude API     │
│  (agent.py)  │     │  (tool use)      │
└──────┬──────┘     └──────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│          Tools Layer            │
│  ┌───────────┐ ┌─────────────┐ │
│  │Stock Data │ │Company Info │ │
│  └───────────┘ └─────────────┘ │
│  ┌───────────────────────────┐ │
│  │  Technical Indicators     │ │
│  └───────────────────────────┘ │
└─────────────────────────────────┘
       │
       ▼
  Yahoo Finance API
```

**The Agentic Loop**: Claude doesn't just answer in one shot. It can make multiple tool calls in sequence — first fetching company info, then price data, then technical indicators — before synthesizing everything into a final analysis. This multi-step reasoning is what makes it an "agent."

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/financial-research-agent.git
cd financial-research-agent

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env
# Get your key at: https://console.anthropic.com/settings/keys

# 5. Run the agent
python agent.py
```

## Example: Analyzing AAPL

```
You: Analyze AAPL

🔄 Sending request to Claude...
🔧 Tool call [1]: get_company_info({"ticker": "AAPL"})
✓ Got result (827 chars)
🔧 Tool call [1]: get_stock_data({"ticker": "AAPL", "period": "1y"})
✓ Got result (883 chars)
🔧 Tool call [1]: get_technical_indicators({"ticker": "AAPL"})
✓ Got result (364 chars)
🔄 Sending tool results back to Claude...
```

The agent autonomously decided to call **all 3 tools**, then synthesized the results:

```
📊 Analysis
┌──────────────────────────────────────────────────────────────────────┐
│                    Apple Inc. (AAPL) Analysis                        │
│                                                                      │
│  Executive Summary                                                   │
│  Apple maintains its position as one of the world's most valuable    │
│  companies with a market cap of $3.76 trillion. Currently trading    │
│  at $255.78, the stock is showing mixed technical signals but        │
│  remains above its long-term trend line.                             │
│                                                                      │
│  Key Fundamental Metrics                                             │
│  • Market Cap: $3.76 trillion                                        │
│  • P/E Ratio: 32.4                                                   │
│  • Forward P/E: 27.5                                                 │
│  • Dividend Yield: 0.41%                                             │
│  • 52-Week Range: $169.21 - $288.62                                  │
│                                                                      │
│  Technical Analysis                                                  │
│  • Below SMA-20 ($262.09): Short-term bearish pressure               │
│  • Below SMA-50 ($267.25): Medium-term weakness                      │
│  • Above SMA-200 ($239.60): Long-term uptrend intact                 │
│  • RSI: 50.6 (neutral territory)                                     │
│  • MACD: Bearish crossover — potential short-term weakness            │
│                                                                      │
│  Balanced Assessment                                                 │
│  AAPL appears to be in a consolidation phase after significant       │
│  gains. While short-term technicals suggest caution, the company's   │
│  fundamental strength and position above the 200-day moving average  │
│  support a longer-term positive outlook.                             │
└──────────────────────────────────────────────────────────────────────┘
```

> The agent decided which tools to call, in what order, without any hardcoded logic — this is the power of agentic tool use.

## Project Structure

```
financial-research-agent/
├── agent.py              # Core agent loop — the brain
├── tools/
│   ├── __init__.py
│   └── market_tools.py   # Tool schemas + handler functions
├── requirements.txt
└── README.md
```

## Key Concepts

### Tool Use (Function Calling)
Claude's tool use lets you define functions that Claude can call. You provide:
- **Schemas**: JSON descriptions of available tools (name, description, parameters)
- **Handlers**: Python functions that execute when Claude calls a tool

Claude decides *when* and *which* tools to call based on the user's question.

### The Agent Loop
```python
while not done:
    response = claude.create(messages, tools)
    if response.wants_tool:
        result = execute_tool(response.tool_call)
        messages.append(result)  # send result back
    else:
        return response.text  # final answer
```

### Conversation Memory
The agent maintains conversation history, so you can ask follow-up questions:
```
You: Analyze AAPL
Agent: [detailed analysis]
You: How does its P/E compare to the sector average?
Agent: [contextual follow-up using previous data]
```

## Available Tools

| Tool | Description | Data Source |
|------|-------------|------------|
| `get_stock_data` | Historical OHLCV data, returns, volatility | Yahoo Finance |
| `get_company_info` | Fundamentals: P/E, market cap, sector, summary | Yahoo Finance |
| `get_technical_indicators` | SMA, RSI, MACD, Bollinger Bands, trend signals | Computed from price data |

## Next Steps (Planned Enhancements)

- [ ] **News Tool**: Fetch recent news articles for sentiment context
- [ ] **Comparison Tool**: Side-by-side stock comparison
- [ ] **HMM Integration**: Connect market regime detection model as a tool
- [ ] **Output Export**: Save analyses as PDF/Markdown reports
- [ ] **Streaming**: Stream Claude's response in real-time

## Tech Stack

- **LLM**: Claude (Anthropic API) with tool use
- **Data**: Yahoo Finance via `yfinance`
- **UI**: Rich (terminal formatting)
- **Language**: Python 3.10+