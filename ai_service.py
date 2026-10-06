import os

from google import genai


def ask(question: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "API_KEY saknas"

    client = genai.Client(
        api_key = api_key
    )
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite", contents = question
    )

    return response.text