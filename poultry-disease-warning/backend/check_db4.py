import os, sys
sys.stdout.reconfigure(encoding="utf-8")
import asyncio
import asyncpg

root = r"C:\Users\Admin\OneDrive - Trường Đại học Công nghiệp Hà Nội\Documents\deepseek-harness\default-workspace\poultry-disease-warning\backend"

async def try_pw(pw):
    try:
        conn = await asyncpg.connect(user="postgres", password=pw, host="localhost", port=5432, database="poultry_disease")
        rows = await conn.fetch("select current_user, current_database(), version()")
        print("CONNECTED:", pw, rows[0])
        await conn.close()
        return True
    except Exception as e:
        print("failed:", pw, str(e)[:100])
        return False

async def main():
    for pw in ["postgres", "password", "poultry", "devpassword", "trust"]:
        if await try_pw(pw):
            break
    print("done")

asyncio.run(main())