"""Seed the mock employee directory (SQLite). Run once.

Creates data/directory.db with an `employees` table + sample records. The records
are aligned with the sample emails (e.g. Rita's account shows as locked), so the
lookup tool corroborates what an email claims. In production this is Graph / AD.

Run from the repo root:  python scripts/seed_directory.py
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "directory.db"

# employee_id, name, email, department, job_title, manager, device, account_status, mfa_enrolled, location
EMPLOYEES = [
    ("4471", "Rita Fernandes",  "rita.fernandes@northwind.example", "Sales",      "Account Executive",    "Sarah Cole",     "MacBook Pro 14 (LT-4471)",   "locked",   1, "Dubai"),
    ("3820", "Tom Becker",      "tom.becker@northwind.example",     "Operations", "Logistics Coordinator","Mark Reyes",     "Dell Latitude 7440 (LT-3820)","active",  1, "Remote"),
    ("5102", "Priya Nair",      "priya.nair@northwind.example",     "Finance",    "Financial Analyst",    "Anil Rao",       "Dell Latitude 7440 (LT-5102)","active",  1, "Abu Dhabi"),
    ("6210", "Daniel Osei",     "daniel.osei@northwind.example",    "Marketing",  "Web Designer",         "Sarah Cole",     "MacBook Pro 16 (LT-6210)",   "active",   0, "Dubai"),
    ("6884", "Mei Lin",         "mei.lin@northwind.example",        "Marketing",  "Content Specialist",   "Sarah Cole",     "MacBook Air (LT-6884)",      "active",   1, "Dubai"),
    ("1002", "Sarah Cole",      "sarah.cole@northwind.example",     "Marketing",  "Marketing Director",   "Elena Vasquez",  "MacBook Pro 16 (LT-1002)",   "active",   1, "Dubai"),
    ("1005", "Anil Rao",        "anil.rao@northwind.example",       "Finance",    "Finance Director",     "Elena Vasquez",  "Dell Latitude 9440 (LT-1005)","active",  1, "Abu Dhabi"),
    ("1001", "Elena Vasquez",   "elena.vasquez@northwind.example",  "Executive",  "COO",                  "",               "MacBook Pro 16 (LT-1001)",   "active",   1, "Dubai"),
    ("7340", "Mark Reyes",      "mark.reyes@northwind.example",     "Operations", "Ops Manager",          "Elena Vasquez",  "Dell Latitude 7440 (LT-7340)","active",  1, "Dubai"),
    ("8150", "James Whitfield", "james.whitfield@northwind.example","IT",         "Service Desk Analyst", "Elena Vasquez",  "Dell Latitude 7440 (LT-8150)","active",  1, "Dubai"),
]

def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("DROP TABLE IF EXISTS employees")
    con.execute("""
        CREATE TABLE employees (
            employee_id    TEXT PRIMARY KEY,
            name           TEXT NOT NULL,
            email          TEXT UNIQUE NOT NULL,
            department     TEXT,
            job_title      TEXT,
            manager        TEXT,
            device         TEXT,
            account_status TEXT,
            mfa_enrolled   INTEGER,
            location       TEXT
        )
    """)
    con.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?,?,?,?,?)", EMPLOYEES)
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    con.close()
    print(f"Seeded {n} employees into {DB}")

if __name__ == "__main__":
    main()
