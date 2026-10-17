# Vehicle Service & Maintenance Management System — Review 3

Flask web interface for the Vehicle Service & Maintenance Management System. The website runs on **SQLite**, so it can run in GitHub Codespaces without an Oracle account, wallet, cloud database, or database driver.

## Run the website in GitHub Codespaces

From this folder, run:

    python -m pip install -r requirements.txt
    python setup_demo_db.py
    python app.py

Open the forwarded port shown by Codespaces (Flask defaults to port 5000).

The setup script creates `instance/vehicle_service.db` using `scripts/sqlite_schema.sql`, including the tables, view, relationships, constraints, and demo records. If you already have a demo database, the script asks before replacing it.

## SQL*Plus coursework schema

The file `schema.sql` is intentionally kept as the **Oracle SQL*Plus version** for DBMS coursework. Run it in Oracle SQL*Plus or another Oracle SQL client:

    @schema.sql

It creates the Oracle tables, the `CustomerVehicleAppointment` view, and demo rows. It is not intended to be run against SQLite.

The website's separate `scripts/sqlite_schema.sql` contains the SQLite-compatible version used by the Flask application. Keeping these files separate allows the website to run without Oracle while preserving the SQL*Plus script for submission or demonstration.

## Website pages

- **Dashboard** — table counts and recent appointments.
- **Tables** — list of tables, columns, and row counts.
- **Manage table** — view/search up to 250 records and add, edit, or delete rows. Foreign-key fields offer existing related records where possible.
- **SQL reports** — JOIN, WHERE + ORDER BY, GROUP BY + HAVING, aggregates, a subquery, and the project view.
- **Health** — visit `/health` to see the SQLite database path, backend, table list, and foreign-key check count.

Tables with composite primary keys (such as `SERVICE_PART`) can be viewed and searched; generic edit/delete is disabled for safety.

## Automated regression tests

From this folder, run:

    python -m unittest discover -s tests -v

The test suite checks page rendering, every table page, searching, create/update/delete behavior, unique and foreign-key constraints, CHECK constraints, date/email form inputs, reports, health checks, and demo-database setup/recreation. GitHub Actions runs the suite on relevant pushes and pull requests.

## Troubleshooting

- **Flask missing:** run `python -m pip install -r requirements.txt`.
- **Database file missing:** run `python setup_demo_db.py`.
- **Existing database:** the setup script asks before replacing it; type `YES` only if you want to recreate the demo database and replace its contents.
- **Port 5000 in use:** run with `flask --app app run --port 5001`.
- This is an academic prototype. Keep Flask debug mode disabled unless actively debugging locally.
