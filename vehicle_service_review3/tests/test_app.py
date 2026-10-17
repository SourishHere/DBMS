import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCHEMA = BASE / "schema.sql"
TEMP_DIR = tempfile.TemporaryDirectory(prefix="vehicle-service-tests-")
os.environ["VEHICLE_DB_PATH"] = str(Path(TEMP_DIR.name) / "test_vehicle_service.db")
sys.path.insert(0, str(BASE))

import app as app_module  # noqa: E402


class VehicleServiceAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app_module.app
        cls.app.config.update(TESTING=True)
        cls.client = cls.app.test_client()
        cls.db_path = Path(os.environ["VEHICLE_DB_PATH"])

    def setUp(self):
        if self.db_path.exists():
            self.db_path.unlink()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(SCHEMA.read_text(encoding="utf-8"))
            conn.commit()

    def db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def test_dashboard_loads_with_demo_counts(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<h1>Dashboard</h1>", response.data)
        self.assertIn(b"Meera Iyer", response.data)

    def test_tables_page_loads(self):
        response = self.client.get("/tables")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CUSTOMER", response.data)
        self.assertIn(b"SERVICE_PART", response.data)

    def test_every_database_table_page_loads(self):
        with self.db() as conn:
            tables = [
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            ]
        for table in tables:
            with self.subTest(table=table):
                response = self.client.get(f"/table/{table}")
                self.assertEqual(response.status_code, 200, table)

    def test_table_search(self):
        response = self.client.get("/table/CUSTOMER?q=Arun")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Arun Kumar", response.data)
        self.assertNotIn(b"Priya Sharma", response.data)

    def test_add_and_edit_customer(self):
        response = self.client.post(
            "/table/CUSTOMER/add",
            data={
                "Customer_Name": "Test Customer",
                "Phone": "9876500000",
                "Email": "test.customer@example.com",
                "Address": "Vellore",
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.db() as conn:
            row = conn.execute(
                "SELECT Customer_ID FROM CUSTOMER WHERE Email = ?",
                ("test.customer@example.com",),
            ).fetchone()
        self.assertIsNotNone(row)
        customer_id = row["Customer_ID"]

        response = self.client.post(
            f"/table/CUSTOMER/edit/{customer_id}",
            data={
                "Customer_Name": "Edited Customer",
                "Phone": "9876500001",
                "Email": "edited.customer@example.com",
                "Address": "Katpadi",
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.db() as conn:
            row = conn.execute(
                "SELECT Customer_Name, Phone FROM CUSTOMER WHERE Customer_ID = ?",
                (customer_id,),
            ).fetchone()
        self.assertEqual(row["Customer_Name"], "Edited Customer")
        self.assertEqual(row["Phone"], "9876500001")

    def test_duplicate_unique_value_is_rejected_without_crashing(self):
        response = self.client.post(
            "/table/CUSTOMER/add",
            data={
                "Customer_Name": "Duplicate Email",
                "Phone": "9876500002",
                "Email": "arun@gmail.com",
                "Address": "Vellore",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Could not add record", response.data)
        with self.db() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM CUSTOMER WHERE Email = 'arun@gmail.com'"
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_invalid_foreign_key_is_rejected(self):
        response = self.client.post(
            "/table/VEHICLE/add",
            data={
                "Registration_No": "TN99ZZ9999",
                "Customer_ID": "99999",
                "Model_ID": "201",
                "Manufacture_Year": "2024",
                "Mileage": "1000",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Could not add record", response.data)
        with self.db() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM VEHICLE WHERE Registration_No = 'TN99ZZ9999'"
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_check_constraint_is_enforced(self):
        response = self.client.post(
            "/table/FEEDBACK/add",
            data={
                "Service_ID": "801",
                "Customer_ID": "101",
                "Rating": "6",
                "Comments": "Invalid rating",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Could not add record", response.data)
        with self.db() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM FEEDBACK WHERE Rating = 6"
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_referenced_customer_cannot_be_deleted(self):
        response = self.client.post("/table/CUSTOMER/delete/101")
        self.assertEqual(response.status_code, 302)
        with self.db() as conn:
            row = conn.execute(
                "SELECT Customer_Name FROM CUSTOMER WHERE Customer_ID = 101"
            ).fetchone()
        self.assertEqual(row["Customer_Name"], "Arun Kumar")

    def test_composite_primary_key_table_is_read_only_for_generic_actions(self):
        response = self.client.get("/table/SERVICE_PART")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Add record", response.data)
        response = self.client.post("/table/SERVICE_PART/delete/1")
        self.assertEqual(response.status_code, 302)

    def test_reports_execute_without_schema_errors(self):
        response = self.client.get("/reports")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"JOIN", response.data)
        self.assertNotIn(b"Needs schema check", response.data)

    def test_health_reports_no_foreign_key_violations(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["backend"], "sqlite")
        self.assertEqual(data["foreign_key_violations"], 0)
        self.assertGreaterEqual(len(data["tables"]), 10)

    def test_unknown_table_and_record_return_404(self):
        self.assertEqual(self.client.get("/table/NO_SUCH_TABLE").status_code, 404)
        self.assertEqual(self.client.get("/table/CUSTOMER/edit/99999").status_code, 404)

    def test_delete_endpoint_rejects_get(self):
        self.assertEqual(self.client.get("/table/CUSTOMER/delete/1").status_code, 405)


    def test_email_field_uses_email_input_type(self):
        response = self.client.get("/table/CUSTOMER/add")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="Email" type="email"', response.data)
        self.assertNotIn(b'type="text" value="" required type="email"', response.data)

    def test_sqlite_date_columns_use_date_inputs(self):
        response = self.client.get("/table/APPOINTMENT/add")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="Appointment_Date" name="Appointment_Date" type="date"', response.data)


class DemoDatabaseSetupTests(unittest.TestCase):
    def test_setup_initializes_and_recreates_demo_db_safely(self):
        with tempfile.TemporaryDirectory(prefix="vehicle-setup-test-") as temp:
            root = Path(temp)
            shutil.copy2(BASE / "setup_demo_db.py", root / "setup_demo_db.py")
            (root / "scripts").mkdir()
            shutil.copy2(SCHEMA, root / "scripts" / "sqlite_schema.sql")
            db_path = root / "instance" / "vehicle_service.db"

            first = subprocess.run(
                [sys.executable, str(root / "setup_demo_db.py")],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertTrue(db_path.exists())
            with sqlite3.connect(db_path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM CUSTOMER").fetchone()[0], 10)
                conn.execute(
                    "INSERT INTO CUSTOMER (Customer_Name, Phone, Email) VALUES (?, ?, ?)",
                    ("Preserve Me", "9876500099", "preserve@example.com"),
                )

            refused = subprocess.run(
                [sys.executable, str(root / "setup_demo_db.py")],
                input="NO\n",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(refused.returncode, 0, refused.stdout + refused.stderr)
            self.assertIn("Cancelled", refused.stdout)
            with sqlite3.connect(db_path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM CUSTOMER").fetchone()[0], 11)

            recreated = subprocess.run(
                [sys.executable, str(root / "setup_demo_db.py")],
                input="YES\n",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(recreated.returncode, 0, recreated.stdout + recreated.stderr)
            with sqlite3.connect(db_path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM CUSTOMER").fetchone()[0], 10)
                self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
