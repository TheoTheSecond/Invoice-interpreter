import os
import sys
from contextlib import AsyncExitStack

from google import genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


client = None
mcp_session = None
exit_stack = None


async def startup():
    global client, mcp_session, exit_stack

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY saknas.")

    client = genai.Client(api_key=api_key)

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
    )

    exit_stack = AsyncExitStack()

    read, write = await exit_stack.enter_async_context(
        stdio_client(server_params)
    )

    mcp_session = await exit_stack.enter_async_context(
        ClientSession(read, write)
    )

    await mcp_session.initialize()


async def shutdown():
    global client, mcp_session, exit_stack

    if exit_stack:
        await exit_stack.aclose()

    if client:
        await client.aio.aclose()

    mcp_session = None
    client = None
    exit_stack = None


async def ask(question: str) -> str:
    if client is None or mcp_session is None:
        raise RuntimeError("AI service är inte startad.")

    response = await client.aio.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=question,
        config={
            "tools": [mcp_session]
        },
    )

    return response.text