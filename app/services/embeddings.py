from mistralai.client import Mistral
from app.config import settings

client = Mistral(api_key=settings.mistral_api_key)


def get_embedding(text: str) -> list[float]:

    response = client.embeddings.create(
        model="mistral-embed",
        inputs=[text],
    )
    return response.data[0].embedding


async def stream_answer(question: str, content_chunks=list[str]):
    numbered_content = "\n \n" .join(
        f"[{i+1}] {chunk}" for i, chunk in enumerate(content_chunks))

    system_promt = ("You are a helping assistant if you don't "
                    "know the answer jus tsay I don't know it or out of my limits don'T ANSWER WRONG OR GUESS BLINDLY"
                    " ASNWER THE questions precisely and accurately")

    user_prompt = f"Content:{numbered_content} question:{question}"

    stream = client.chat.stream(model="mistral-small-latest", messages=[{"role": "system", "content": system_promt},

                                                                        {"role": "user", "content": user_prompt}])

    for chunk in stream:
        if chunk.data.choices[0].delta.content:
            yield chunk.data.choices[0].delta.content
