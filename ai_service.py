import asyncio
import os
import sys

from google import genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def ask_async(question: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "GEMINI_API_KEY saknas."

    client = genai.Client(api_key=api_key)

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:

                await session.initialize()

                response = await client.aio.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=question,
                    config={
                        "tools": [session]
                    },
                )

                return response.text

    finally:
        await client.aio.aclose()


def ask(question: str) -> str:
    return asyncio.run(ask_async(question))