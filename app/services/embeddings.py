from google import genai
from google.genai import types
from app.config import settings

import asyncio

client = genai.Client(api_key=settings.gemini_api_key)


def get_embedding(text: str) -> list[float]:
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=1024)
    )
    return response.embeddings[0].values


async def stream_answer(question: str, content_chunks: list[str]):
    numbered_content = "\n\n".join(
        f"[{i+1}] {chunk}" for i, chunk in enumerate(content_chunks)
    )

    system_prompt = (
        "You are a helpful assistant. If you don't know the answer, "
        "say 'I don't know' or 'that's outside what I can answer' — "
        "do not guess or answer incorrectly. Answer precisely and accurately."
    )

    user_prompt = f"Content:\n{numbered_content}\n\nQuestion: {question}"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            stream = await client.aio.models.generate_content_stream(
                model="gemini-3.5-flash-lite",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
            )
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
            return
        except Exception as e:
            err = str(e)
            if ("429" in err or "RESOURCE_EXHAUSTED" in err or "rate" in err.lower()) and attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            yield f"\n[Error: {err}]"
            return
