import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        user="postgres", password="postgres", host="localhost",
        port=5432, database="poultry_disease"
    )
    rows = await conn.fetch("select version()")
    print("version:", rows[0]["version"])
    try:
        rows2 = await conn.fetch("select extname from pg_extension")
        print("extensions:", [r["extname"] for r in rows2])
    except Exception as e:
        print("ext check failed:", e)
    await conn.close()

asyncio.run(main())