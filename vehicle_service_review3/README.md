# Vehicle Service & Maintenance Management System — Review 3

Flask web interface for the Oracle database schema in schema.sql. The existing dashboard, table browser, search, CRUD forms, and SQL report pages are retained.

## Oracle setup (recommended)

The Oracle schema uses Oracle SQL syntax and should be run in Oracle SQL*Plus or another Oracle SQL client. From the folder containing schema.sql, run:

    @schema.sql

The script creates the tables, the CustomerVehicleAppointment view, and demo rows. It uses MERGE for repeatable seed records and ends with COMMIT.

Install dependencies:

    python -m pip install -r requirements.txt

Set these environment variables in the terminal where Flask will run. Do not put real passwords in source files or commit them to Git.

    export DB_BACKEND=oracle
    export ORACLE_USER='your_schema_username'
    export ORACLE_PASSWORD='your_schema_password'
    export ORACLE_DSN='hostname:1521/service_name'
    export FLASK_SECRET_KEY='a-long-random-secret'
    python app.py

ORACLE_DSN must point to an Oracle database that the Codespace can reach. localhost means the Codespace itself, not your personal computer. If Oracle runs only on your laptop or a college LAN that Codespaces cannot reach, use an approved reachable Oracle instance or network connection.

For persistent configuration in GitHub Codespaces, add ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN, DB_BACKEND, and FLASK_SECRET_KEY as Codespaces secrets/environment variables. Never commit .env or credentials.

Open the forwarded Flask port shown by Codespaces. The /health endpoint reports the selected backend and accessible table list.

## Database backend modes

- DB_BACKEND=oracle — uses python-oracledb and the Oracle schema.
- DB_BACKEND=sqlite (default) — keeps compatibility with an existing local instance/vehicle_service.db database.

The Oracle mode reads tables and column/foreign-key metadata from Oracle's USER_* data dictionary views. CRUD statements use bound parameters; Oracle identity columns are omitted on insert when blank; HTML date inputs are converted to Python date values before Oracle binding. Database constraints remain responsible for enforcing uniqueness, required fields, CHECK constraints, and foreign keys.

## Website pages

- Dashboard — live table counts and recent appointments.
- Tables — list of tables and their columns/row counts.
- Manage table — view/search up to 250 records, add/edit/delete rows. Foreign-key fields offer existing related records where possible.
- SQL reports — JOIN, WHERE + ORDER BY, GROUP BY + HAVING, aggregates, a subquery, and the project view.

Tables with composite primary keys (such as SERVICE_PART) are viewable/searchable; generic edit/delete is disabled for safety.

## Local SQLite fallback

The SQLite backend uses instance/vehicle_service.db by default, or the path in VEHICLE_DB_PATH. schema.sql is Oracle SQL and is not a SQLite schema; do not run the Oracle file through a SQLite setup script. The SQLite database is local and ignored by Git.

## Troubleshooting

- Oracle driver missing: run python -m pip install -r requirements.txt.
- Missing Oracle configuration: confirm DB_BACKEND, ORACLE_USER, ORACLE_PASSWORD, and ORACLE_DSN are set in the same terminal/session running Flask.
- Connection refused / timeout: confirm the DSN is reachable from Codespaces and the database listener allows that connection.
- Foreign-key/unique/check error: choose an existing related row or correct the value; Oracle is enforcing the schema constraints.
- Port 5000 in use: use flask run --port 5001 or change the app's run port.
- This is an academic prototype. Keep Flask debug mode disabled unless actively debugging locally.
