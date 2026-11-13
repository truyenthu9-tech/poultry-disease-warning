import os, sys
sys.stdout.reconfigure(encoding="utf-8")
import asyncio
import asyncpg

root = r"C:\Users\Admin\OneDrive - Trường Đại học Công nghiệp Hà Nội\Documents\deepseek-harness\default-workspace\poultry-disease-warning\backend"
for pw in ["postgres", "password", "poultry", "devpassword", "trust"]:
    try:
        conn = asyncpg.connect(user="postgres", password=pw, host="localhost", port=5432, database="poultry_disease")
        rows = await conn.fetch("select current_user, current_database(), version()")
        print("CONNECTED:", pw, rows[0])
        await conn.close()
        break
    except Exception as e:
        print("failed:", pw, str(e)[:100])
print("done")