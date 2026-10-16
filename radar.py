"""Outbreak Radar storage (SQLite, free, local). Only disease + taluka + time are stored: no names, no GPS."""
import sqlite3, time, random

DB = "kisansaathi.db"
# approximate taluka centres (Kolhapur district) used only to place map circles
TALUKAS = {
    "Karveer": (16.70, 74.24), "Panhala": (16.81, 74.11), "Shahuwadi": (16.93, 73.93),
    "Kagal": (16.58, 74.31), "Hatkanangale": (16.69, 74.44), "Shirol": (16.74, 74.60),
    "Radhanagari": (16.40, 73.99), "Gaganbawada": (16.55, 73.84), "Bhudargad": (16.37, 74.13),
    "Gadhinglaj": (16.23, 74.35), "Chandgad": (15.95, 74.17), "Ajra": (16.12, 74.22),
}

def _conn():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY, ts INTEGER, disease TEXT, taluka TEXT, demo INTEGER DEFAULT 0)")
    return c

def add_report(disease, taluka, demo=0, ts=None):
    with _conn() as c:
        c.execute("INSERT INTO reports(ts,disease,taluka,demo) VALUES(?,?,?,?)", (ts or int(time.time()), disease, taluka, demo))

def summary(days=14, alert_at=3):
    since = int(time.time()) - days * 86400
    with _conn() as c:
        rows = c.execute("SELECT taluka, disease, COUNT(*), MAX(demo) FROM reports WHERE ts>=? GROUP BY taluka, disease", (since,)).fetchall()
    reports = [{"taluka": t, "lat": TALUKAS[t][0], "lon": TALUKAS[t][1], "disease": d, "count": n}
               for t, d, n, _ in rows if t in TALUKAS]
    alerts = sorted([{"taluka": r["taluka"], "disease": r["disease"], "count": r["count"]}
                     for r in reports if r["count"] >= alert_at], key=lambda a: -a["count"])
    return {"reports": reports, "alerts": alerts, "total": sum(r["count"] for r in reports),
            "has_demo": any(r[3] for r in rows)}

def seed_demo():
    clear_demo()
    sample = [("Hatkanangale", "Tomato___Late_blight", 6), ("Shirol", "Tomato___Late_blight", 3),
              ("Karveer", "Potato___Early_blight", 2), ("Kagal", "Corn_(maize)___Common_rust_", 4),
              ("Hatkanangale", "Grape___Black_rot", 2), ("Panhala", "Apple___Apple_scab", 1),
              ("Radhanagari", "Tomato___Bacterial_spot", 3)]
    now = int(time.time())
    for t, d, n in sample:
        for _ in range(n):
            add_report(d, t, demo=1, ts=now - random.randint(0, 10 * 86400))

def clear_demo():
    with _conn() as c:
        c.execute("DELETE FROM reports WHERE demo=1")
