import ast, sys, pathlib

root = pathlib.Path(__file__).parent
results = []
for p in sorted(root.rglob("*.py")):
    try:
        src = p.read_text(encoding="utf-8")
        ast.parse(src, filename=str(p))
        results.append((str(p), "OK"))
    except SyntaxError as e:
        results.append((str(p), f"SYNTAX ERROR line {e.lineno}: {e.msg}"))
for path, msg in results:
    print(f"{path}: {msg}")