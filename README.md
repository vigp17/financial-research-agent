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
# 1. Clone/navigate to the project
cd financial-research-agent

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your API key
cp .env.example .env
# Edit .env and add your Anthropic API key
# Get one at: https://console.anthropic.com/settings/keys

# 5. Run the agent
python agent.py
```

## Example Usage

```
You: Analyze NVDA

🔧 Tool call [1]: get_company_info({"ticker": "NVDA"})
✓ Got result (450 chars)
🔧 Tool call [2]: get_stock_data({"ticker": "NVDA", "period": "3mo"})
✓ Got result (820 chars)
🔧 Tool call [3]: get_technical_indicators({"ticker": "NVDA"})
✓ Got result (380 chars)

📊 Analysis
┌─────────────────────────────────────────────┐
│ ## NVIDIA (NVDA) — Research Summary          │
│                                              │
│ **Executive Summary**                        │
│ NVIDIA continues to dominate the AI chip     │
│ market with strong momentum...               │
│                                              │
│ **Key Metrics**                              │
│ ...                                          │
└─────────────────────────────────────────────┘
```

## Project Structure

```
financial-research-agent/
├── agent.py              # Core agent loop — the brain
├── tools/
│   ├── __init__.py
│   └── market_tools.py   # Tool schemas + handler functions
├── requirements.txt
├── .env.example
└── README.md
```

## Key Concepts

### Tool Use (Function Calling)
Claude's tool use lets you define functions that Claude can call. You provide:
- **Schemas**: JSON descriptions of available tools (name, description, parameters)
- **Handlers**: Python functions that execute when Claude calls a tool

Claude decides *when* and *which* tools to call based on the user's question.

### The Agent Loop
```
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
