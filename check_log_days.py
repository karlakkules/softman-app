#!/usr/bin/env python3
"""
Dijagnostika: prikaži vehicle_log_days za najnoviju evidenciju
Pokreni iz root direktorija projekta: python3 check_log_days.py
"""
import sqlite3
from pathlib import Path

DB = Path('putni_nalog.db')
if not DB.exists():
    print('ERROR: putni_nalog.db nije pronađen!')
    exit(1)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Najnovija evidencija
log = conn.execute(
    "SELECT * FROM vehicle_log ORDER BY year DESC, month DESC, id DESC LIMIT 1"
).fetchone()

if not log:
    print('Nema evidencija!'); exit(1)

print(f"Evidencija: {log['year']}-{log['month']:02d}, vehicle_id={log['vehicle_id']}")
print(f"  start_km={log['start_km']}, end_km={log['end_km']}, total_km={log['total_km']}")
print()

days = conn.execute(
    "SELECT * FROM vehicle_log_days WHERE log_id=? ORDER BY date LIMIT 10",
    (log['id'],)
).fetchall()

print(f"Prvih 10 dana u vehicle_log_days (log_id={log['id']}):")
print(f"{'Datum':<12} {'start_km':>10} {'end_km':>10} {'total_km':>10} {'official':>10} {'private':>10}")
print("-" * 65)
for d in days:
    print(f"{d['date']:<12} {d['start_km']:>10.0f} {d['end_km']:>10.0f} {d['total_km']:>10.2f} {d['official_km']:>10.2f} {d['private_km']:>10.2f}")

conn.close()
