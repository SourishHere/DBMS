from flask import Flask, render_template, request, redirect, url_for, flash, abort
from pathlib import Path
from datetime import date, datetime
import os
import re
import sqlite3
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent
INSTANCE = ROOT / "instance"
INSTANCE.mkdir(exist_ok=True)
DB_BACKEND = "sqlite"
DB_PATH = Path(os.environ.get("VEHICLE_DB_PATH", INSTANCE / "vehicle_service.db"))

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "review3-local-demo-change-me")
app.config["DATABASE"] = str(DB_PATH)
app.config["DB_BACKEND"] = DB_BACKEND

DB_ERRORS = (sqlite3.Error,)


@contextmanager
def connect_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_tables(conn):
    rows = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()
    return [r["name"] for r in rows]


def valid_table(conn, table):
    return table.upper() in {name.upper() for name in get_tables(conn)}


def columns_for(conn, table):
    if not valid_table(conn, table):
        abort(404)
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    return [{
        "name": col["name"], "type": col["type"] or "TEXT",
        "notnull": col["notnull"], "pk": col["pk"],
        "dflt_value": col["dflt_value"],
        "identity": bool(col["pk"] and "INT" in (col["type"] or "").upper())
    } for col in rows]


def primary_key(columns):
    pks = [c for c in columns if c["pk"]]
    return pks[0]["name"] if len(pks) == 1 else None


def safe_identifier(name):
    return '"' + str(name).replace('"', '""') + '"'


def table_info(conn, table):
    cols = columns_for(conn, table)
    fks = conn.execute(f'PRAGMA foreign_key_list("{table}")').fetchall()
    fk_map = {fk["from"]: (fk["table"], fk["to"]) for fk in fks}
    return [{
        "name": col["name"], "type": (col["type"] or "TEXT").upper(),
        "notnull": bool(col["notnull"]), "pk": bool(col["pk"]),
        "identity": bool(col.get("identity", False)), "default": col["dflt_value"],
        "fk": fk_map.get(col["name"])
    } for col in cols]


def scalar(conn, sql):
    row = conn.execute(sql).fetchone()
    return row[0] if row else 0


def query_if_possible(conn, sql):
    try:
        return {"rows": conn.execute(sql).fetchall(), "error": None}
    except DB_ERRORS + (RuntimeError,) as exc:
        return {"rows": [], "error": str(exc)}


def foreign_key_issue_count(conn):
    return len(conn.execute("PRAGMA foreign_key_check").fetchall())


def form_value(value, col):
    return None if value == "" else value


@app.template_filter("date_input")
def date_input(value):
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    text = str(value)
    return text[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", text) else text


@app.context_processor
def inject_global():
    try:
        with connect_db() as conn:
            tables = get_tables(conn)
    except (DB_ERRORS + (RuntimeError,)) as exc:
        app.logger.warning("Database navigation unavailable: %s", exc)
        tables = []
    return {"nav_tables": tables, "db_backend": DB_BACKEND}


@app.route("/")
def index():
    with connect_db() as conn:
        tables = get_tables(conn)
        counts = {}
        for table in tables:
            try:
                counts[table] = scalar(conn, f"SELECT COUNT(*) FROM {safe_identifier(table)}")
            except DB_ERRORS:
                counts[table] = 0
        customer_count = counts.get("CUSTOMER", 0)
        vehicle_count = counts.get("VEHICLE", 0)
        appointment_count = counts.get("APPOINTMENT", 0)
        completed = 0
        if "APPOINTMENT" in tables:
            cols = [c["name"].lower() for c in columns_for(conn, "APPOINTMENT")]
            if "status" in cols:
                completed = scalar(conn, "SELECT COUNT(*) FROM APPOINTMENT WHERE Status = 'Completed'")
        recent = query_if_possible(conn, """
            SELECT a.Appointment_ID, a.Appointment_Date, a.Status,
                   c.Customer_Name, v.Registration_No
            FROM APPOINTMENT a
            JOIN VEHICLE v ON a.Vehicle_ID = v.Vehicle_ID
            JOIN CUSTOMER c ON v.Customer_ID = c.Customer_ID
            ORDER BY a.Appointment_ID DESC LIMIT 6
        """) if {"APPOINTMENT", "VEHICLE", "CUSTOMER"}.issubset(set(tables)) else {"rows": [], "error": "Expected appointment tables are not present."}
    return render_template("index.html", counts=counts, customer_count=customer_count,
                           vehicle_count=vehicle_count, appointment_count=appointment_count,
                           completed=completed, recent=recent)


@app.route("/tables")
def tables_page():
    with connect_db() as conn:
        tables = get_tables(conn)
        items = []
        for table in tables:
            cols = columns_for(conn, table)
            items.append({"name": table, "columns": len(cols),
                          "rows": scalar(conn, f"SELECT COUNT(*) FROM {safe_identifier(table)}"),
                          "pk": primary_key(cols)})
    return render_template("tables.html", items=items)


@app.route("/table/<table>")
def table_page(table):
    search = request.args.get("q", "").strip()
    with connect_db() as conn:
        if not valid_table(conn, table):
            abort(404)
        cols = columns_for(conn, table)
        pk = primary_key(cols)
        colnames = [c["name"] for c in cols]
        if search:
            searchable = [c for c in cols if any(t in (c["type"] or "").upper() for t in ("CHAR", "TEXT", "CLOB", "INT", "REAL", "NUM", "DATE", "FLOAT"))]
            if searchable:
                where = " OR ".join(f"CAST({safe_identifier(c['name'])} AS TEXT) LIKE ?" for c in searchable)
                params = [f"%{search}%"] * len(searchable)
                rows = conn.execute(f"SELECT * FROM {safe_identifier(table)} WHERE {where} LIMIT 250", params).fetchall()
            else:
                rows = conn.execute(f"SELECT * FROM {safe_identifier(table)} LIMIT 250").fetchall()
        else:
            rows = conn.execute(f"SELECT * FROM {safe_identifier(table)} LIMIT 250").fetchall()
        fk_errors = foreign_key_issue_count(conn)
    return render_template("table.html", table=table, columns=colnames, rows=rows,
                           pk=pk, search=search, total=len(rows), fk_error_count=fk_errors)


def render_record_form(table, mode, record=None):
    with connect_db() as conn:
        if not valid_table(conn, table):
            abort(404)
        cols = table_info(conn, table)
        record = record or {}
        for col in cols:
            col["options"] = []
            if col["fk"]:
                ref_table, ref_col = col["fk"]
                try:
                    refcols = [x["name"] for x in columns_for(conn, ref_table)]
                    label_col = next((x for x in refcols if x.lower().endswith("name")), ref_col)
                    if label_col not in refcols:
                        label_col = ref_col
                    col["options"] = conn.execute(
                        f"SELECT {safe_identifier(ref_col)} AS value, {safe_identifier(label_col)} AS label "
                        f"FROM {safe_identifier(ref_table)} ORDER BY 2 LIMIT 500"
                    ).fetchall()
                except DB_ERRORS:
                    col["options"] = []
    return render_template("form.html", table=table, mode=mode, columns=cols, record=record)


@app.route("/table/<table>/add", methods=["GET", "POST"])
def add_record(table):
    if request.method == "GET":
        return render_record_form(table, "add")
    with connect_db() as conn:
        if not valid_table(conn, table):
            abort(404)
        cols = columns_for(conn, table)
        data = {}
        for col in cols:
            name = col["name"]
            raw_value = request.form.get(name, "").strip()
            if col.get("identity") and raw_value == "":
                continue
            if col["pk"] and "INT" in (col["type"] or "").upper() and raw_value == "":
                continue
            if raw_value == "" and col["dflt_value"] is not None:
                continue
            value = form_value(raw_value, col)
            if value is None and not col["notnull"] and not col["pk"]:
                data[name] = None
            else:
                data[name] = value
        if not data:
            flash("Please enter values for the record.", "error")
            return render_record_form(table, "add")
        try:
            names = list(data.keys())
            placeholders = ", ".join(["?"] * len(names))
            sql = f"INSERT INTO {safe_identifier(table)} ({', '.join(safe_identifier(n) for n in names)}) VALUES ({placeholders})"
            conn.execute(sql, [data[n] for n in names])
            conn.commit()
            flash(f"Record added to {table}.", "success")
            return redirect(url_for("table_page", table=table))
        except DB_ERRORS + (ValueError, RuntimeError) as exc:
            conn.rollback()
            flash(f"Could not add record: {exc}", "error")
            return render_record_form(table, "add", data)


@app.route("/table/<table>/edit/<path:key>", methods=["GET", "POST"])
def edit_record(table, key):
    with connect_db() as conn:
        if not valid_table(conn, table):
            abort(404)
        cols = columns_for(conn, table)
        pk = primary_key(cols)
        if not pk:
            flash("This table has a composite or missing primary key. Generic edit is disabled for safety.", "error")
            return redirect(url_for("table_page", table=table))
        record = conn.execute(f"SELECT * FROM {safe_identifier(table)} WHERE {safe_identifier(pk)} = ?", (key,)).fetchone()
        if not record:
            abort(404)
        if request.method == "GET":
            return render_record_form(table, "edit", dict(record))
        data = {}
        for col in cols:
            name = col["name"]
            if name.lower() == pk.lower():
                continue
            raw_value = request.form.get(name, "").strip()
            if raw_value == "" and not col["notnull"]:
                data[name] = None
            elif raw_value == "" and col["dflt_value"] is not None:
                continue
            else:
                data[name] = form_value(raw_value, col)
        try:
            if data:
                assignments = ", ".join(f"{safe_identifier(n)} = ?" for n in data)
                conn.execute(f"UPDATE {safe_identifier(table)} SET {assignments} WHERE {safe_identifier(pk)} = ?",
                             list(data.values()) + [key])
                conn.commit()
            flash(f"Record updated in {table}.", "success")
            return redirect(url_for("table_page", table=table))
        except DB_ERRORS + (ValueError, RuntimeError) as exc:
            conn.rollback()
            flash(f"Could not update record: {exc}", "error")
            updated = dict(record)
            updated.update(data)
            return render_record_form(table, "edit", updated)


@app.route("/table/<table>/delete/<path:key>", methods=["POST"])
def delete_record(table, key):
    with connect_db() as conn:
        if not valid_table(conn, table):
            abort(404)
        pk = primary_key(columns_for(conn, table))
        if not pk:
            flash("Delete is disabled for tables without a single-column primary key.", "error")
            return redirect(url_for("table_page", table=table))
        try:
            conn.execute(f"DELETE FROM {safe_identifier(table)} WHERE {safe_identifier(pk)} = ?", (key,))
            conn.commit()
            flash(f"Record deleted from {table}.", "success")
        except DB_ERRORS as exc:
            conn.rollback()
            flash(f"Could not delete record. It may be referenced by another record. Details: {exc}", "error")
        return redirect(url_for("table_page", table=table))


@app.route("/reports")
def reports():
    with connect_db() as conn:
        tables = set(get_tables(conn))
        reports_data = []
        definitions = [
            ("Appointment details (JOIN)", """
                SELECT a.Appointment_ID, a.Appointment_Date, a.Status,
                       c.Customer_Name, v.Registration_No, st.Service_Name,
                       m.Mechanic_Name
                FROM APPOINTMENT a
                JOIN VEHICLE v ON a.Vehicle_ID = v.Vehicle_ID
                JOIN CUSTOMER c ON v.Customer_ID = c.Customer_ID
                JOIN SERVICE_TYPE st ON a.Service_Type_ID = st.Service_Type_ID
                JOIN MECHANIC m ON a.Mechanic_ID = m.Mechanic_ID
                ORDER BY a.Appointment_Date DESC
            """, {"APPOINTMENT", "VEHICLE", "CUSTOMER", "SERVICE_TYPE", "MECHANIC"}),
            ("Appointments by status (WHERE + ORDER BY)", """
                SELECT Appointment_ID, Appointment_Date, Vehicle_ID, Status
                FROM APPOINTMENT
                WHERE Status = 'Completed'
                ORDER BY Appointment_Date DESC
            """, {"APPOINTMENT"}),
            ("Customers with more than one appointment (GROUP BY + HAVING)", """
                SELECT c.Customer_ID, c.Customer_Name, COUNT(a.Appointment_ID) AS Appointment_Count
                FROM CUSTOMER c
                JOIN VEHICLE v ON c.Customer_ID = v.Customer_ID
                JOIN APPOINTMENT a ON v.Vehicle_ID = a.Vehicle_ID
                GROUP BY c.Customer_ID, c.Customer_Name
                HAVING COUNT(a.Appointment_ID) > 1
                ORDER BY Appointment_Count DESC
            """, {"CUSTOMER", "VEHICLE", "APPOINTMENT"}),
            ("Service record aggregates (COUNT / SUM / AVG / MAX / MIN)", """
                SELECT COUNT(*) AS Service_Count,
                       COALESCE(SUM(Cost), 0) AS Total_Cost,
                       COALESCE(AVG(Cost), 0) AS Average_Cost,
                       COALESCE(MAX(Cost), 0) AS Highest_Cost,
                       COALESCE(MIN(Cost), 0) AS Lowest_Cost
                FROM SERVICE_RECORD
            """, {"SERVICE_RECORD"}),
            ("Vehicles with above-average mileage (subquery)", """
                SELECT Vehicle_ID, Registration_No, Mileage
                FROM VEHICLE
                WHERE Mileage > (SELECT AVG(Mileage) FROM VEHICLE)
                ORDER BY Mileage DESC
            """, {"VEHICLE"}),
            ("Customer-vehicle-appointment view", """
                SELECT * FROM CustomerVehicleAppointment
            """, set())
        ]
        for title, sql, required in definitions:
            missing = sorted(required - tables)
            if missing:
                reports_data.append({"title": title, "rows": [], "error": "Missing table(s): " + ", ".join(missing), "sql": sql.strip()})
                continue
            result = query_if_possible(conn, sql)
            reports_data.append({"title": title, "rows": result["rows"], "error": result["error"], "sql": sql.strip()})
    return render_template("reports.html", reports_data=reports_data)


@app.route("/health")
def health():
    with connect_db() as conn:
        return {"database": str(DB_PATH),
                "backend": "sqlite",
                "tables": get_tables(conn),
                "foreign_key_violations": foreign_key_issue_count(conn)}


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", title="Not found", message="That table or record was not found."), 404


@app.errorhandler(RuntimeError)
def database_configuration_error(error):
    return render_template("error.html", title="Database configuration error", message=str(error)), 500


if __name__ == "__main__":
    if not DB_PATH.exists():
        print("SQLite database file not found. Run: python setup_demo_db.py")
    print(f"Using SQLite database: {DB_PATH}")
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
