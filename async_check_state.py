import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="poultry_disease",
    )
    rows = await conn.fetch("SELECT datname FROM pg_database")
    for r in rows:
        print(r)
    await conn.close()

asyncio.run(main())