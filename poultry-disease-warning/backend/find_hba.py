import os
import subprocess

# Find the postgres data directory and pg_hba.conf
for root, dirs, files in os.walk("C:\\Program Files"):
    for f in files:
        if f in ("pg_hba.conf", "postgresql.conf"):
            print(os.path.join(root, f))