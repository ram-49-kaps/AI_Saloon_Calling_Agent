import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Test pooler without the project reference in the username
url = "postgresql+asyncpg://postgres:GANADHISHAY2026@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"

async def test():
    print("Testing pooler with just 'postgres'...")
    engine = create_async_engine(url, connect_args={"timeout": 5})
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"SUCCESS! Result: {result.scalar()}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__} - {e}")
    finally:
        await engine.dispose()

asyncio.run(test())
