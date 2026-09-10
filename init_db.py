import pymysql
import re

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "root123456",
    "database": "mydb",
    "charset": "utf8mb4",
}

with open("b.sql", "r", encoding="utf-8") as f:
    content = f.read()

statements = []
current = ""
for line in content.split("\n"):
    stripped = line.strip()
    if stripped.startswith("--") or stripped == "":
        continue
    current += line + "\n"
    if stripped.endswith(";"):
        statements.append(current.strip())
        current = ""

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

for stmt in statements:
    stmt = stmt.strip()
    if not stmt:
        continue
    try:
        cursor.execute(stmt)
        print(f"OK: {stmt[:80]}...")
    except Exception as e:
        print(f"ERR: {str(e)[:100]} | SQL: {stmt[:80]}...")

conn.commit()
cursor.close()
conn.close()
print("\nDone!")