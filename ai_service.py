import asyncio
import json
import os
import sys
from typing import Any

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


MAX_TOOL_ROUNDS = 10


def mcp_result_to_text(result: Any) -> str:
    """Convert an MCP CallToolResult into text Claude can read."""
    parts: list[str] = []

    for content in result.content:
        text = getattr(content, "text", None)

        if text is not None:
            parts.append(text)
            continue

        if hasattr(content, "model_dump"):
            parts.append(
                json.dumps(
                    content.model_dump(mode="json"),
                    ensure_ascii=False,
                )
            )
        else:
            parts.append(str(content))

    if parts:
        return "\n".join(parts)

    if hasattr(result, "model_dump"):
        return json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
        )

    return str(result)


def get_text_response(response: Any) -> str:
    """Extract normal text blocks from an Anthropic response."""
    text_parts = [
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text"
    ]

    return "\n".join(text_parts).strip()


async def ask_async(question: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return "ANTHROPIC_API_KEY saknas."

    anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            mcp_tools_result = await session.list_tools()

            anthropic_tools = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.input_schema,
                }
                for tool in mcp_tools_result.tools
            ]

            messages: list[dict[str, Any]] = [
                {
                    "role": "user",
                    "content": question,
                }
            ]

            for _ in range(MAX_TOOL_ROUNDS):
                response = await anthropic_client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    system=(
                        "You are an invoice assistant. "
                        "Answer in Swedish. "
                        "Use the available invoice tools when the answer "
                        "requires invoice data. "
                        "Use analytics tools for comparisons, totals, counts, "
                        "earliest dates, and latest dates. "
                        "Do not repeatedly call the same tool with the same "
                        "arguments."
                    ),
                    tools=anthropic_tools,
                    messages=messages,
                )

                if response.stop_reason != "tool_use":
                    return get_text_response(response)

                assistant_content = [
                    block.model_dump()
                    for block in response.content
                ]

                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_content,
                    }
                )

                tool_results: list[dict[str, Any]] = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    try:
                        result = await session.call_tool(
                            block.name,
                            arguments=block.input,
                        )

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": mcp_result_to_text(result),
                                "is_error": bool(
                                    getattr(result, "isError", False)
                                ),
                            }
                        )
                    except Exception as exc:
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Tool error: {exc}",
                                "is_error": True,
                            }
                        )

                if not tool_results:
                    return get_text_response(response)

                messages.append(
                    {
                        "role": "user",
                        "content": tool_results,
                    }
                )

            return (
                "Jag kunde inte slutföra frågan inom det tillåtna antalet "
                "verktygsanrop."
            )


def ask(question: str) -> str:
    return asyncio.run(ask_async(question))
