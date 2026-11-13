import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

root = r"C:\Users\Admin\OneDrive - Trường Đại học Công nghiệp Hà Nội\Documents\deepseek-harness\default-workspace\poultry-disease-warning\backend\app\models"
for fname in ("farm.py", "outbreak.py", "alert.py"):
    print(f"===== {fname} =====")
    for line in open(os.path.join(root, fname), encoding="utf-8"):
        print(line.rstrip())
    print()