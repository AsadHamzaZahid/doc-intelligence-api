import asyncio
from sqlalchemy import select
from app.database import Async_Sessionmaker   # you have database.py, not db.py
# adjust to the exact model file inside app/models/
from app.models import Chunk
from app.services.embeddings import get_embedding


async def reembed_all_chunks():
    async with Async_Sessionmaker() as session:
        result = await session.execute(select(Chunk))
        chunks = result.scalars().all()

        print(f"Re-embedding {len(chunks)} chunks...")
        for chunk in chunks:
            new_vector = await asyncio.to_thread(get_embedding, chunk.content)
            chunk.embedding = new_vector
            print(f"  done: chunk {chunk.id}")

        await session.commit()
        print("All chunks re-embedded and committed.")


if __name__ == "__main__":
    asyncio.run(reembed_all_chunks())
