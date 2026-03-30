#!/usr/bin/env python3
"""
Patch: app.py
_get_pn_for_month() — za PN naloge kojima nedostaje start_km/end_km,
pokuša popuniti km iz vehicle_log_days za odgovarajući datum i isti month/year log.
"""
import shutil, os, sys

APP = os.path.join(os.path.dirname(__file__), 'app.py')

if not os.path.exists(APP):
    print(f"❌ Nije pronađen: {APP}")
    sys.exit(1)

shutil.copy(APP, APP + '.bak2')
print("✅ Backup kreiran: app.py.bak2")

with open(APP, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''def _get_pn_for_month(conn, year, month):
    """Find PN nalozi whose departure_date falls in given year/month."""
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    date_from = f"{year}-{month:02d}-01"
    date_to = f"{year}-{month:02d}-{last_day:02d}"
    rows = conn.execute(\'\'\'
        SELECT to2.auto_id, to2.departure_date, to2.start_km, to2.end_km,
               to2.destination, e.name as employee_name
        FROM travel_orders to2
        LEFT JOIN employees e ON to2.employee_id = e.id
        WHERE (to2.is_deleted=0 OR to2.is_deleted IS NULL)
          AND to2.departure_date >= ? AND to2.departure_date <= ?
        ORDER BY to2.departure_date
    \'\'\', (date_from, date_to)).fetchall()
    return rows_to_dicts(rows)'''

NEW = '''def _get_pn_for_month(conn, year, month):
    """Find PN nalozi whose departure_date falls in given year/month.
    Za naloge bez start_km/end_km, pokuša popuniti iz vehicle_log_days."""
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    date_from = f"{year}-{month:02d}-01"
    date_to = f"{year}-{month:02d}-{last_day:02d}"
    rows = conn.execute(\'\'\'
        SELECT to2.id, to2.auto_id, to2.departure_date, to2.start_km, to2.end_km,
               to2.destination, e.name as employee_name
        FROM travel_orders to2
        LEFT JOIN employees e ON to2.employee_id = e.id
        WHERE (to2.is_deleted=0 OR to2.is_deleted IS NULL)
          AND to2.departure_date >= ? AND to2.departure_date <= ?
        ORDER BY to2.departure_date
    \'\'\', (date_from, date_to)).fetchall()
    result = rows_to_dicts(rows)

    # Za svaki PN bez km — pokušaj naći iz vehicle_log_days za isti datum
    # Dohvati sve log_id-ove za ovaj year/month
    log_ids = conn.execute(
        "SELECT id FROM vehicle_log WHERE year=? AND month=?", (year, month)
    ).fetchall()
    log_id_list = [r[\'id\'] for r in log_ids]

    if log_id_list:
        placeholders = \',\'.join(\'?\' * len(log_id_list))
        # Izgradi mapu: datum -> (start_km, end_km) iz vehicle_log_days
        day_km_map = {}
        day_rows = conn.execute(
            f"SELECT date, start_km, end_km FROM vehicle_log_days WHERE log_id IN ({placeholders}) ORDER BY log_id",
            log_id_list
        ).fetchall()
        for dr in day_rows:
            d = dr[\'date\']
            if d not in day_km_map:
                day_km_map[d] = (dr[\'start_km\'], dr[\'end_km\'])

        # Popuni km za PN-ove kojima nedostaju
        for pn in result:
            if not pn.get(\'start_km\') and not pn.get(\'end_km\'):
                dep = pn.get(\'departure_date\', \'\')
                if dep and dep in day_km_map:
                    pn[\'start_km\'] = day_km_map[dep][0]
                    pn[\'end_km\'] = day_km_map[dep][1]
                    pn[\'km_from_log\'] = True  # oznaka da km dolaze iz voznog dnevnika

    return result'''

if OLD not in src:
    print("⚠️  PATCH PRESKOČEN — pattern nije pronađen: _get_pn_for_month")
    print(f"   Tražim: {repr(OLD[:80])}")
    sys.exit(1)

src = src.replace(OLD, NEW, 1)
print("✅ Patch primijenjen: _get_pn_for_month")

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)

print("\n🎉 app.py uspješno ažuriran!")
print("   Reload stranice → 'Osvježi' u tablici PN naloga.")
