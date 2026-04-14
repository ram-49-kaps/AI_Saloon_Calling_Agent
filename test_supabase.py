"""Quick test — verify Supabase PostgreSQL connection."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://postgres:GANADHISHAY2026@db.qqvkuxjwmwehfnlkgkxa.supabase.co:5432/postgres"

async def test():
    print("Connecting to Supabase...")
    engine = create_async_engine(DB_URL, echo=False)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"SUCCESS! Connection works. Result: {result.scalar()}")
    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        await engine.dispose()

asyncio.run(test())
