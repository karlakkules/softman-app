#!/usr/bin/env python3
"""
Patch: app.py — sinkronizacija start_km/end_km na putnim nalozima (status=draft)
pri svakom spremanju evidencije vozila.
"""

import shutil
from pathlib import Path

APP = Path('app.py')

if not APP.exists():
    print('ERROR: app.py nije pronađen! Pokreni iz root direktorija projekta.')
    exit(1)

shutil.copy(APP, APP.with_suffix('.py.bak'))
print('✅ Backup kreiran: app.py.bak')

content = APP.read_text(encoding='utf-8')

if 'sync_pn_km_from_log_days' in content:
    print('ℹ️  Patch već primijenjen.')
    exit(0)

# ─── 1. Helper funkcija ───────────────────────────────────────────────────────
HELPER = '''
def sync_pn_km_from_log_days(conn, vehicle_id, year, month):
    """
    Nakon spremanja vehicle_log_days, ažuriraj start_km/end_km na putnim nalozima
    koji su u statusu 'draft' i podudaraju se s vozilom i departure_date.
    Ne dira naloge u statusu submitted/approved/knjizeno.
    """
    if not vehicle_id:
        return 0
    days = conn.execute("""
        SELECT vld.date, vld.start_km, vld.end_km
        FROM vehicle_log_days vld
        JOIN vehicle_log vl ON vl.id = vld.log_id
        WHERE vl.vehicle_id = ? AND vl.year = ? AND vl.month = ?
        ORDER BY vld.date
    """, (vehicle_id, year, month)).fetchall()
    updated = 0
    for day in days:
        result = conn.execute("""
            UPDATE travel_orders
            SET start_km = ?,
                end_km = ?,
                updated_at = datetime('now')
            WHERE vehicle_id = ?
              AND departure_date = ?
              AND status = 'draft'
              AND (is_deleted = 0 OR is_deleted IS NULL)
        """, (round(day['start_km']), round(day['end_km']), vehicle_id, day['date']))
        updated += result.rowcount
    return updated

'''

ROUTE_MARKER = "@app.route('/api/vehicle-log', methods=['POST'])"
if ROUTE_MARKER not in content:
    print(f'❌ Marker nije pronađen: {ROUTE_MARKER}')
    exit(1)

content = content.replace(ROUTE_MARKER, HELPER + ROUTE_MARKER)
print('✅ Helper funkcija dodana')

# ─── 2. Poziv u save_vehicle_log() ───────────────────────────────────────────
OLD_BLOCK = """    conn.commit()
    conn.close()
    audit('create' if not data.get('id') else 'edit', module='sluzbeni_automobil', entity='vehicle_log', entity_id=log_id)
    return jsonify({'success': True, 'id': log_id})"""

NEW_BLOCK = """    # Sinkroniziraj km na putnim nalozima u statusu 'draft'
    _pn_updated = sync_pn_km_from_log_days(conn, fields.get('vehicle_id'), fields.get('year'), fields.get('month'))
    conn.commit()
    conn.close()
    audit('create' if not data.get('id') else 'edit', module='sluzbeni_automobil', entity='vehicle_log', entity_id=log_id,
          detail=f'Sinkronizirano {_pn_updated} PN naloga')
    return jsonify({'success': True, 'id': log_id, 'pn_updated': _pn_updated})"""

if OLD_BLOCK not in content:
    print('❌ Pattern za ubacivanje poziva nije pronađen!')
    exit(1)

content = content.replace(OLD_BLOCK, NEW_BLOCK)
print('✅ Poziv sync_pn_km_from_log_days() dodan')

APP.write_text(content, encoding='utf-8')
print('\n✅ Patch uspješno primijenjen!')
print('Testiraj: spremi evidenciju za ožujak → provjeri PN 2026-13 km vrijednosti.')
