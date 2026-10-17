from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "instance" / "vehicle_service.db"

APPOINTMENTS = [
    (716, 601, 302, 403, "2026-10-16", "Completed"),
    (717, 602, 303, 404, "2026-10-16", "Completed"),
    (718, 603, 304, 405, "2026-10-16", "Completed"),
    (719, 604, 305, 406, "2026-10-16", "Completed"),
    (720, 605, 306, 407, "2026-10-16", "Completed"),
]

def main():
    if not DB_PATH.exists():
        raise SystemExit(
            f"Database not found: {DB_PATH}\n"
            "Run this script from the project after creating the demo database."
        )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        missing = []
        for appointment_id, vehicle_id, mechanic_id, service_type_id, _, _ in APPOINTMENTS:
            checks = [
                ("VEHICLE", "Vehicle_ID", vehicle_id),
                ("MECHANIC", "Mechanic_ID", mechanic_id),
                ("SERVICE_TYPE", "Service_Type_ID", service_type_id),
            ]
            for table, column, value in checks:
                if conn.execute(
                    f"SELECT 1 FROM {table} WHERE {column} = ?", (value,)
                ).fetchone() is None:
                    missing.append(f"{table}.{column}={value}")

        if missing:
            raise SystemExit(
                "No data was changed. Required referenced records are missing: "
                + ", ".join(missing)
            )

        before = conn.execute(
            "SELECT COUNT(*) FROM APPOINTMENT WHERE Appointment_ID BETWEEN 716 AND 720"
        ).fetchone()[0]

        conn.executemany(
            """INSERT OR IGNORE INTO APPOINTMENT
            (Appointment_ID, Vehicle_ID, Mechanic_ID, Service_Type_ID, Appointment_Date, Status)
            VALUES (?, ?, ?, ?, ?, ?)""",
            APPOINTMENTS,
        )

        after = conn.execute(
            "SELECT COUNT(*) FROM APPOINTMENT WHERE Appointment_ID BETWEEN 716 AND 720"
        ).fetchone()[0]

        print(f"Appointments 716-720 present: {after}/5")
        print(f"New appointments inserted: {after - before}")
        print("Existing database records were preserved.")

        results = conn.execute(
            """SELECT c.Customer_ID, c.Customer_Name, COUNT(a.Appointment_ID) AS appointment_count
            FROM CUSTOMER c
            JOIN VEHICLE v ON v.Customer_ID = c.Customer_ID
            JOIN APPOINTMENT a ON a.Vehicle_ID = v.Vehicle_ID
            GROUP BY c.Customer_ID, c.Customer_Name
            HAVING COUNT(a.Appointment_ID) > 1
            ORDER BY appointment_count DESC, c.Customer_ID"""
        ).fetchall()

        print("\nGROUP BY + HAVING results:")
        for row in results:
            print(f"Customer {row[0]} | {row[1]} | Appointments: {row[2]}")

if __name__ == "__main__":
    main()
