"""
Financial Research Agent — Core Agent Loop
==========================================

This is the brain of the agent. Here's how the agentic loop works:

    ┌─────────────────────────────────────────┐
    │  1. User asks a question                │
    │  2. Send question + tool schemas → Claude│
    │  3. Claude decides:                      │
    │     a) Use a tool → execute it, send     │
    │        result back to Claude (go to 3)   │
    │     b) Respond to user → done            │
    └─────────────────────────────────────────┘

The key insight: Claude doesn't just answer in one shot. It can make
MULTIPLE tool calls in sequence, building up information before giving
a final answer. This is what makes it an "agent" rather than just a chatbot.

For example, if you ask "Analyze AAPL", Claude might:
  1. Call get_company_info("AAPL") → learn about the company
  2. Call get_stock_data("AAPL") → get recent price data
  3. Call get_technical_indicators("AAPL") → check momentum/trend
  4. Synthesize everything into a research memo
"""

import os
import json
import anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from tools import TOOL_SCHEMAS, execute_tool

# Load API key from .env file
load_dotenv()

# Initialize the Anthropic client and Rich console for pretty output
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment
console = Console()

# The system prompt defines the agent's personality and behavior
SYSTEM_PROMPT = """You are a financial research analyst agent. Your job is to help users 
understand stocks, markets, and financial data by using your available tools.

When a user asks about a stock or financial topic:
1. Think about what information you need to answer well
2. Use your tools to gather relevant data (you can call multiple tools)
3. Synthesize the data into a clear, insightful analysis

Your analysis style:
- Start with a brief executive summary
- Present key metrics and what they mean
- Identify notable trends or signals
- End with a balanced assessment (not investment advice)
- Use clear language — avoid unnecessary jargon
- When presenting numbers, provide context (e.g., "P/E of 25, above sector average of 18")

Important: You are an analysis tool, NOT a financial advisor. Always clarify that your 
output is informational and not investment advice.

If the user's request is vague, use your judgment to provide the most useful analysis.
For example, "tell me about AAPL" should trigger a comprehensive overview using 
multiple tools, not just one data point.
"""

# Maximum number of tool-use loops to prevent infinite loops
MAX_ITERATIONS = 10


def run_agent(user_message: str, conversation_history: list = None) -> str:
    """
    Run the agent loop for a single user message.
    
    This is the core agentic loop:
    1. Send message + tools to Claude
    2. If Claude wants to use a tool → execute it, add result, repeat
    3. If Claude gives a text response → return it
    
    Args:
        user_message: The user's question or request
        conversation_history: Optional list of previous messages for context
    
    Returns:
        Claude's final text response after all tool use is complete
    """
    # Build the messages list
    if conversation_history is None:
        conversation_history = []

    messages = conversation_history + [
        {"role": "user", "content": user_message}
    ]

    console.print(f"\n[dim]🔄 Sending request to Claude...[/dim]")

    # === THE AGENTIC LOOP ===
    for iteration in range(MAX_ITERATIONS):

        # Call Claude with our tools
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        # Check the stop reason to decide what to do next
        if response.stop_reason == "tool_use":
            # Claude wants to use one or more tools
            # The response content can contain both text AND tool_use blocks
            
            # Add Claude's response (with tool calls) to conversation
            messages.append({"role": "assistant", "content": response.content})

            # Process each tool call
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    console.print(
                        f"[yellow]🔧 Tool call [{iteration+1}]: "
                        f"{tool_name}({json.dumps(tool_input)})[/yellow]"
                    )

                    # Execute the tool
                    result = execute_tool(tool_name, tool_input)

                    console.print(f"[green]✓ Got result ({len(result)} chars)[/green]")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Send tool results back to Claude
            messages.append({"role": "user", "content": tool_results})

            console.print(f"[dim]🔄 Sending tool results back to Claude...[/dim]")

        elif response.stop_reason == "end_turn":
            # Claude is done — extract the text response
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            # Update conversation history for future turns
            messages.append({"role": "assistant", "content": response.content})

            return final_text, messages

        else:
            # Unexpected stop reason
            return f"Agent stopped unexpectedly: {response.stop_reason}", messages

    return "Agent reached maximum iterations without completing.", messages


def main():
    """Interactive chat loop with the financial research agent."""
    console.print(
        Panel(
            "[bold green]Financial Research Agent[/bold green]\n"
            "Ask me about any stock, market trend, or financial topic.\n"
            "I'll gather data and provide analysis using real market data.\n\n"
            "[dim]Examples:[/dim]\n"
            "  • Analyze AAPL\n"
            "  • Compare MSFT and GOOGL\n"
            "  • What's the technical outlook for NVDA?\n"
            "  • Give me an overview of the semiconductor sector (NVDA, AMD, INTC)\n\n"
            "[dim]Type 'quit' to exit, 'clear' to reset conversation[/dim]",
            title="🏦 Welcome",
            border_style="green",
        )
    )

    conversation_history = []

    while True:
        console.print()
        user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye! 👋[/dim]")
            break
        if user_input.lower() == "clear":
            conversation_history = []
            console.print("[dim]Conversation cleared.[/dim]")
            continue

        try:
            response_text, conversation_history = run_agent(
                user_input, conversation_history
            )
            console.print()
            console.print(Panel(Markdown(response_text), title="📊 Analysis", border_style="blue"))

        except anthropic.APIError as e:
            console.print(f"[red]API Error: {e}[/red]")
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Type 'quit' to exit.[/dim]")


if __name__ == "__main__":
    main()
