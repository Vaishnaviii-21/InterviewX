import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
from database.connection import DATABASE_PATH

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Existing tables:", tables)
for t in tables:
    cursor.execute(f"PRAGMA table_info({t})")
    cols = [r[1] for r in cursor.fetchall()]
    print(f"  {t}: {cols}")
conn.close()
