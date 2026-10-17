from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent
db_path = ROOT / "instance" / "vehicle_service.db"
schema_path = ROOT / "scripts" / "sqlite_schema.sql"
db_path.parent.mkdir(exist_ok=True)

if db_path.exists():
    answer = input(f"{db_path} already exists. Recreate the demo database? This replaces its contents. Type YES to continue: ")
    if answer != "YES":
        print("Cancelled. Existing database was not changed.")
        raise SystemExit(0)
    db_path.unlink()

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript(schema_path.read_text(encoding="utf-8"))
conn.commit()
conn.close()
print(f"Demo database created at: {db_path}")
print("Run the website with: python app.py")
