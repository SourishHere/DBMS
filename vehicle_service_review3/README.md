# Vehicle Service & Maintenance Management System — Review 3

A local Flask + SQLite web application for demonstrating database connectivity, CRUD operations, search, input validation, and SQL reports.

## Included

- `app.py` — Flask backend; reads and writes to SQLite.
- `schema.sql` — optional demo schema for the 15 project tables and a view.
- `setup_demo_db.py` — creates a demo database after asking before replacing an existing demo DB.
- `templates/` and `static/` — website interface.
- `instance/vehicle_service.db` — demo database is generated locally by the setup script.

## Important: use your existing database

The app defaults to `instance/vehicle_service.db`. To use your own SQLite file, either:
1. Make a backup, then place a copy of your database at `instance/vehicle_service.db`, or
2. Set the environment variable `VEHICLE_DB_PATH` to the full path of your existing `.db` file.

Example on Windows Command Prompt:

```bat
set VEHICLE_DB_PATH=C:\path\to\your\existing_database.db
python app.py
```

Do not run `setup_demo_db.py` on top of your only copy of your real database. The setup script only recreates the demo database in this project folder and asks for confirmation first.

## Run on Windows

1. Install Python 3.10 or newer.
2. Extract this ZIP into a folder.
3. Open Command Prompt in that folder.
4. Create a virtual environment (recommended):

```bat
py -m venv .venv
.venv\Scripts\activate
```

5. Install Flask:

```bat
pip install -r requirements.txt
```

6. If you want to test the included demo schema, run:

```bat
python setup_demo_db.py
```

Type `YES` only if you intend to create/replace the demo DB in this project folder.
7. Start the app:

```bat
python app.py
```

8. Open `http://127.0.0.1:5000` in your browser.

## Website pages

- **Dashboard** — counts and recent appointments.
- **Tables** — list of tables in the connected database.
- **Manage table** — view/search records, add/edit/delete rows. Foreign-key fields show choices when possible. Database constraints are enforced by SQLite.
- **SQL reports** — JOIN, WHERE + ORDER BY, GROUP BY + HAVING, aggregates, a subquery, and the project view.

The generic table manager supports single-column primary keys. Tables with composite primary keys (such as `SERVICE_PART`) are viewable/searchable; generic edit/delete is disabled for safety.

## SQL report schema assumptions

The reports use column names shown in the project materials, including `CUSTOMER.Customer_Name`, `VEHICLE.Registration_No`, `VEHICLE.Mileage`, `APPOINTMENT.Status`, `APPOINTMENT.Appointment_Date`, `SERVICE_RECORD.Cost`, and foreign-key names such as `Vehicle_ID` and `Service_Type_ID`. If your actual SQLite database uses different column names, the affected report will show an error rather than fake results. Update the query in `app.py` to match your exact schema.

## Review 3 demo flow

1. Open Dashboard and point out live counts from SQLite.
2. Open `CUSTOMER`, add a test customer, then search for the name.
3. Edit a record and demonstrate a constraint (e.g., duplicate email, if UNIQUE is configured).
4. Open `APPOINTMENT` and change a status.
5. Open SQL Reports; explain JOIN, WHERE/ORDER BY, GROUP BY/HAVING, aggregates, and the average-mileage subquery.
6. Try deleting a parent row referenced by another table to show foreign-key protection.
7. Mention that the backend uses parameterized SQL values to reduce SQL injection risk.

## Troubleshooting

- **No database file:** run `python setup_demo_db.py` to make a demo database, or set `VEHICLE_DB_PATH`.
- **A report shows missing tables/columns:** the connected database schema differs from the assumed column names; use your actual schema and adjust the SQL report.
- **Foreign key errors:** choose an existing parent record in foreign-key fields.
- **Port 5000 in use:** change the last line to `app.run(debug=True, port=5001)` and open `http://127.0.0.1:5001`.
- This is a local academic prototype, not a production-deployed or security-audited system. Keep debug mode local only.
