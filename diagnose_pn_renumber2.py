#!/usr/bin/env python3
import sqlite3, os

DB = 'putni_nalog.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

print("=" * 70)
print("PROVJERA: Nalozi sortirani po departure_date")
print("=" * 70)
orders_by_date = conn.execute("""
    SELECT to2.id, to2.auto_id, to2.departure_date, to2.trip_start_datetime,
           e.name as employee_name
    FROM travel_orders to2
    LEFT JOIN employees e ON e.id = to2.employee_id
    WHERE to2.auto_id LIKE '2026-%'
      AND (to2.auto_id NOT LIKE '%-I')
      AND (to2.is_deleted=0 OR to2.is_deleted IS NULL)
    ORDER BY COALESCE(to2.departure_date, SUBSTR(to2.trip_start_datetime,1,10)) ASC,
             to2.id ASC
""").fetchall()

print(f"  {'Redni':^5}  {'auto_id':^12}  {'departure':^12}  {'trip_start':^12}  Zaposlenik")
print("  " + "-"*68)
for i, o in enumerate(orders_by_date, 1):
    expected = f"2026-{i}"
    marker = " ◄ RAZLIKA" if o['auto_id'] != expected else ""
    print(f"  {i:5d}.  {o['auto_id']:12s}  {o['departure_date'] or '':12s}  "
          f"{str(o['trip_start_datetime'] or '')[:10]:12s}  "
          f"{o['employee_name'] or ''}{marker}")

conn.close()
