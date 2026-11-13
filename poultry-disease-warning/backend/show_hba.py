lines = open(r"C:\Program Files\PostgreSQL\18\data\pg_hba.conf", encoding="utf-8").readlines()
for i, line in enumerate(lines):
    if line.startswith(("local", "host")):
        print(f"--- line {i+1} ---")
        print(line.rstrip())
        if i+1 < len(lines):
            print(lines[i+1].rstrip())
        if i+2 < len(lines):
            print(lines[i+2].rstrip())
        print()