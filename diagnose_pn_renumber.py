#!/usr/bin/env python3
"""
Dijagnostika: prikazuje sve PN-ove i njihove veze (troškovi, računi)
Pokreni: python3 diagnose_pn_renumber.py
"""
import sqlite3, os

DB = 'putni_nalog.db'
if not os.path.exists(DB):
    print("❌ Nije pronađen putni_nalog.db"); exit(1)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

print("=" * 70)
print("TRENUTNI PUTNI NALOZI (2026)")
print("=" * 70)
orders = conn.execute("""
    SELECT to2.id, to2.auto_id, to2.departure_date, to2.trip_start_datetime,
           to2.trip_end_datetime, to2.status, to2.is_deleted,
           e.name as employee_name
    FROM travel_orders to2
    LEFT JOIN employees e ON e.id = to2.employee_id
    WHERE to2.auto_id LIKE '2026-%'
    ORDER BY CAST(SUBSTR(to2.auto_id, 6) AS INTEGER) ASC
""").fetchall()

for o in orders:
    deleted = " [IZBRISAN]" if o['is_deleted'] else ""
    print(f"  ID={o['id']:3d}  auto_id={o['auto_id']:12s}  dep={o['departure_date'] or '?':12s}  "
          f"start={str(o['trip_start_datetime'] or '')[:10]:12s}  "
          f"status={o['status']:10s}{deleted}  {o['employee_name'] or ''}")

print()
print("=" * 70)
print("VEZE: pn_expenses → travel_orders")
print("=" * 70)
exps = conn.execute("""
    SELECT pe.id, pe.travel_order_id, to2.auto_id as pn_auto_id,
           pe.invoice_id, pe.doc_type, pe.amount, pe.partner_name
    FROM pn_expenses pe
    LEFT JOIN travel_orders to2 ON to2.id = pe.travel_order_id
    ORDER BY pe.travel_order_id, pe.id
""").fetchall()

for e in exps:
    inv = f"→ invoice_id={e['invoice_id']}" if e['invoice_id'] else ""
    print(f"  pn_exp.id={e['id']:3d}  travel_order_id={str(e['travel_order_id']):5s}  "
          f"pn={str(e['pn_auto_id']):12s}  {e['doc_type']:7s}  "
          f"{e['amount']:.2f}€  {e['partner_name'] or ''}  {inv}")

print()
print("=" * 70)
print("PROVJERA: Koji auto_id trebaju promjenu?")
print("(Nalozi sortirani po departure_date)")
print("=" * 70)
orders_by_date = conn.execute("""
    SELECT id, auto_id, departure_date, trip_start_datetime, is_deleted,
           e.name as employee_name
    FROM travel_orders to2
    LEFT JOIN employees e ON e.id = to2.employee_id
    WHERE auto_id LIKE '2026-%' AND (is_deleted=0 OR is_deleted IS NULL)
    ORDER BY COALESCE(trip_start_datetime, departure_date||'T00:00') ASC
""").fetchall()

print(f"  {'Redoslijed':^4}  {'auto_id':^12}  {'departure':^12}  {'trip_start':^12}  Zaposlenik")
print("  " + "-"*66)
for i, o in enumerate(orders_by_date, 1):
    expected = f"2026-{i}"
    marker = " ◄ RAZLIKA" if o['auto_id'] != expected else ""
    print(f"  {i:4d}.  {o['auto_id']:12s}  {o['departure_date'] or '':12s}  "
          f"{str(o['trip_start_datetime'] or '')[:10]:12s}  {o['employee_name'] or ''}{marker}")

conn.close()
print()
print("Pošalji ovaj ispis Claudeu!")
