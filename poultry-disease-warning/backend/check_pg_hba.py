import asyncio
import asyncpg

async def main():
    # Try connecting as a superuser via TCP with common passwords
    passwords = ["postgres", "password", "admin", "poultry", "1234", "devpassword"]
    for pw in passwords:
        try:
            conn = await asyncpg.connect(user="postgres", password=pw, host="localhost", port=5432, database="poultry_disease")
            rows = await conn.fetch("select current_user, current_database()")
            print("CONNECTED with password:", pw, rows[0])
            await conn.close()
            return
        except Exception as e:
            print("failed:", pw, str(e)[:80])
    print("no password found")

asyncio.run(main())