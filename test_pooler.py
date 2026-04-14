import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

url = "postgresql+asyncpg://postgres:GANADHISHAY2026@db.qqvkuxjwmwehfnlkgkxa.supabase.co:5432/postgres?ssl=require"

async def test():
    print("Testing pooler connection with ssl=require...")
    engine = create_async_engine(url, echo=False)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"SUCCESS! Result: {result.scalar()}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__} - {e}")
    finally:
        await engine.dispose()

asyncio.run(test())
