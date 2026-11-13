lines = open(r"C:\Program Files\PostgreSQL\18\data\pg_hba.conf", encoding="utf-8").readlines()
out = []
for line in lines:
    if line.startswith("local   all"):
        line = "local   all             all                                     trust\n"
    if line.startswith("host    all"):
        line = "host    all             all             127.0.0.1/32            trust\n"
    out.append(line)
open(r"C:\Program Files\PostgreSQL\18\data\pg_hba.conf", "w", encoding="utf-8").writelines(out)
print("done")