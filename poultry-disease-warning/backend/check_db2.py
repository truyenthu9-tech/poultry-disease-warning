import asyncio
import asyncpg

async def main():
    for pw in ["postgres", "password", "poultry", "devpassword"]:
        try:
            conn = await asyncpg.connect(user="postgres", password=pw, host="localhost", port=5432, database="poultry_disease")
            rows = await conn.fetch("select current_user, current_database(), version()")
            print("CONNECTED:", pw, rows[0])
            await conn.close()
            return
        except Exception as e:
            print("failed:", pw, str(e)[:80])
    print("no password found")

asyncio.run(main())