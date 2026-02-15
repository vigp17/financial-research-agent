# 🏦 Financial Research Agent

An AI-powered financial research assistant built with Claude's tool use (function calling) capability. The agent autonomously gathers market data, computes technical indicators, detects market regimes using a Hidden Markov Model, and synthesizes everything into clear research analysis.

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
┌──────────────────────────────────────────┐
│             Tools Layer                  │
│  ┌───────────┐ ┌───────────────────────┐ │
│  │Stock Data │ │   Company Info        │ │
│  └───────────┘ └───────────────────────┘ │
│  ┌───────────┐ ┌───────────────────────┐ │
│  │Technicals │ │ HMM Regime Detection  │ │
│  └───────────┘ └───────────────────────┘ │
└──────────────────────────────────────────┘
       │                    │
       ▼                    ▼
  Yahoo Finance    Pre-trained HMM Model
                   (market-regime-detection)
```

**The Agentic Loop**: Claude doesn't just answer in one shot. It can make multiple tool calls in sequence — fetching company info, price data, technical indicators, and market regime — before synthesizing everything into a final analysis. This multi-step reasoning is what makes it an "agent."

**HMM Integration**: The agent connects to a [separately trained Hidden Markov Model](https://github.com/vigp17/market-regime-detection) that identifies 5 market regimes (Strong Bull, Calm Bull, Neutral, Bear/High Vol, Crisis) from 20 years of S&P 500 data. This gives every analysis real macro context.

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/vigp17/financial-research-agent.git
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

> **Note**: For HMM regime detection, you also need the [market-regime-detection](https://github.com/vigp17/market-regime-detection) project set up locally. Update the `HMM_PROJECT_PATH` in `tools/regime_tool.py` to point to your local copy. The agent works without it, but regime context won't be available.

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
🔧 Tool call [1]: detect_market_regime({"ticker": "SPY"})
✓ Got result (1475 chars)
🔄 Sending tool results back to Claude...
```

The agent autonomously called **all 4 tools** — including the HMM regime detector — then synthesized the results:

```
📊 Analysis
┌──────────────────────────────────────────────────────────────────────┐
│                    Apple Inc. (AAPL) Analysis                        │
│                                                                      │
│  Executive Summary                                                   │
│  Apple is showing mixed technical signals in the current             │
│  "Calm Bull" market environment. While the stock has gained 5%       │
│  over the past year and remains above its 200-day moving average,    │
│  recent price action suggests some near-term weakness.               │
│                                                                      │
│  Key Fundamentals                                                    │
│  • Market Cap: $3.76 trillion                                        │
│  • P/E Ratio: 32.4 | Forward P/E: 27.5                              │
│  • Dividend Yield: 0.41%                                             │
│  • 52-Week Range: $169.21 - $288.62                                  │
│  • Analyst Consensus: Buy                                            │
│                                                                      │
│  Technical Analysis                                                  │
│  • Below SMA-20 ($262.09): Short-term weakness                       │
│  • Below SMA-50 ($267.25): Medium-term weakness                      │
│  • Above SMA-200 ($239.60): Long-term uptrend intact                 │
│  • RSI: 50.56 (neutral)                                              │
│  • MACD: Bearish crossover — short-term caution                      │
│                                                                      │
│  Market Regime Context (HMM Model)                                   │
│  The broader market is in a "Calm Bull" regime:                      │
│  • 100% model confidence                                             │
│  • 10/10 days stable in current regime                               │
│  • 97% probability of remaining in Calm Bull                         │
│  • 0% crisis probability                                             │
│                                                                      │
│  This supportive macro backdrop suggests any Apple weakness          │
│  may be company-specific rather than systemic.                       │
│                                                                      │
│  Balanced Assessment                                                 │
│  Apple appears to be in a healthy consolidation phase within a       │
│  longer-term uptrend. The recent pullback may present a better       │
│  entry point, though short-term traders should watch for a break     │
│  back above $262 (20-day SMA) for confirmation.                      │
└──────────────────────────────────────────────────────────────────────┘
```

> The agent decided which tools to call, in what order, without any hardcoded logic — and wove the HMM regime context directly into its investment analysis.

## Project Structure

```
financial-research-agent/
├── agent.py              # Core agent loop — the brain
├── tools/
│   ├── __init__.py       # Tool registry
│   ├── market_tools.py   # Stock data, company info, technicals
│   └── regime_tool.py    # HMM regime detection integration
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

### HMM Regime Detection
The agent integrates a [pre-trained Hidden Markov Model](https://github.com/vigp17/market-regime-detection) that classifies market conditions into 5 regimes:

| Regime | Characteristics |
|--------|----------------|
| Strong Bull | High returns, moderate vol, RSI ~68 |
| Calm Bull | Steady gains, low vol, RSI ~61 |
| Neutral | Mixed signals, moderate vol |
| Bear / High Vol | Negative returns, high vol, RSI ~46 |
| Crisis | Sharp declines, extreme vol |

The model was trained on 20 years of S&P 500 data using features: log returns, rolling volatility, volatility ratio, RSI, and moving average distance.

### Conversation Memory
The agent maintains conversation history, so you can ask follow-up questions:
```
You: Analyze AAPL
Agent: [detailed analysis with regime context]
You: How does its P/E compare to the sector average?
Agent: [contextual follow-up using previous data]
```

## Available Tools

| Tool | Description | Data Source |
|------|-------------|------------|
| `get_stock_data` | Historical OHLCV data, returns, volatility | Yahoo Finance |
| `get_company_info` | Fundamentals: P/E, market cap, sector, summary | Yahoo Finance |
| `get_technical_indicators` | SMA, RSI, MACD, Bollinger Bands, trend signals | Computed from price data |
| `detect_market_regime` | Current market regime, confidence, stability, transitions | Pre-trained HMM model |

## Next Steps (Planned Enhancements)

- [x] ~~**HMM Integration**: Connect market regime detection model as a tool~~
- [ ] **News Tool**: Fetch recent news articles for sentiment context
- [ ] **Comparison Tool**: Side-by-side stock comparison
- [ ] **Output Export**: Save analyses as PDF/Markdown reports
- [ ] **Streaming**: Stream Claude's response in real-time

## Tech Stack

- **LLM**: Claude (Anthropic API) with tool use
- **ML**: Hidden Markov Model via `hmmlearn` ([separate project](https://github.com/vigp17/market-regime-detection))
- **Data**: Yahoo Finance via `yfinance`
- **UI**: Rich (terminal formatting)
- **Language**: Python 3.10+

## Author

**Vignesh Pai**