#!/usr/bin/env python3
"""
fix_km_autofill.py
Dodaje automatsko punjenje Početna/Završna KM u putnom nalogu
iz evidencije službenog automobila (vehicle_log_days).

Logika:
- Početna KM = start_km prvog dana putovanja iz vehicle_log_days
- Završna KM  = end_km  zadnjeg dana putovanja iz vehicle_log_days
- Pokreće se samo ako su km polja prazna u travel_orders

Izmjene:
1. app.py   — novi API endpoint /api/orders/<id>/km-from-log
2. form.html — JS koji poziva endpoint pri učitavanju (samo za draft/rejected)

Pokreni iz korijena projekta:
    python fix_km_autofill.py
"""

import shutil
from pathlib import Path

APP_PATH = Path("app.py")
FORM_PATH = Path("templates/form.html")

for p in [APP_PATH, FORM_PATH]:
    if not p.exists():
        print(f"❌ Nije pronađeno: {p}")
        exit(1)

# ── Backup ────────────────────────────────────────────────────────────────────
shutil.copy2(APP_PATH, APP_PATH.with_suffix(".py.bak2"))
shutil.copy2(FORM_PATH, FORM_PATH.with_suffix(".html.bak2"))
print("✅ Backupi kreirani (.bak2)")

# ═══════════════════════════════════════════════════════════════════
# 1. app.py — dodaj API endpoint ispred @app.route('/api/calculate_dnevnice')
# ═══════════════════════════════════════════════════════════════════
app_content = APP_PATH.read_text(encoding="utf-8")

MARKER = "@app.route('/api/calculate_dnevnice', methods=['POST'])"

NEW_ENDPOINT = '''@app.route('/api/orders/<int:order_id>/km-from-log', methods=['GET'])
@login_required
def km_from_log(order_id):
    """
    Dohvaća Početna/Završna KM iz vehicle_log_days za dati putni nalog.
    Traži dane koji odgovaraju rasponu putovanja (departure_date → trip_end_datetime).
    Vraća start_km prvog i end_km zadnjeg dana.
    """
    conn = get_db()
    order = conn.execute(
        "SELECT vehicle_id, departure_date, trip_start_datetime, trip_end_datetime FROM travel_orders WHERE id=?",
        (order_id,)
    ).fetchone()

    if not order or not order['vehicle_id']:
        conn.close()
        return jsonify({'found': False, 'reason': 'no_vehicle'})

    vehicle_id = order['vehicle_id']

    # Odredi raspon datuma putovanja
    date_start = None
    date_end   = None

    if order['departure_date']:
        date_start = str(order['departure_date'])[:10]
    elif order['trip_start_datetime']:
        date_start = str(order['trip_start_datetime'])[:10]

    if order['trip_end_datetime']:
        date_end = str(order['trip_end_datetime'])[:10]
    elif date_start:
        date_end = date_start  # jednodnevno putovanje

    if not date_start:
        conn.close()
        return jsonify({'found': False, 'reason': 'no_dates'})

    # Pronađi log_id za to vozilo u odgovarajućem mjesecu
    # vehicle_log je organiziran po (vehicle_id, year, month)
    # Trebamo pokriti sve mjesece u rasponu putovanja
    import datetime as _dt

    try:
        d_start = _dt.date.fromisoformat(date_start)
        d_end   = _dt.date.fromisoformat(date_end)
    except:
        conn.close()
        return jsonify({'found': False, 'reason': 'bad_dates'})

    # Skupi sve log_id-ove za vozilo koji pokrivaju raspon
    months_needed = set()
    cur = d_start.replace(day=1)
    while cur <= d_end:
        months_needed.add((cur.year, cur.month))
        # Sljedeći mjesec
        if cur.month == 12:
            cur = cur.replace(year=cur.year+1, month=1)
        else:
            cur = cur.replace(month=cur.month+1)

    log_ids = []
    for (yr, mo) in months_needed:
        row = conn.execute(
            "SELECT id FROM vehicle_log WHERE vehicle_id=? AND year=? AND month=?",
            (vehicle_id, yr, mo)
        ).fetchone()
        if row:
            log_ids.append(row['id'])

    if not log_ids:
        conn.close()
        return jsonify({'found': False, 'reason': 'no_log'})

    # Dohvati sve dane u rasponu
    placeholders = ','.join('?' for _ in log_ids)
    days = conn.execute(
        f"""SELECT date, start_km, end_km
            FROM vehicle_log_days
            WHERE log_id IN ({placeholders})
              AND date >= ? AND date <= ?
              AND (official_km > 0 OR total_km > 0 OR start_km > 0 OR end_km > 0)
            ORDER BY date ASC""",
        log_ids + [date_start, date_end]
    ).fetchall()

    conn.close()

    if not days:
        return jsonify({'found': False, 'reason': 'no_days'})

    first_day = days[0]
    last_day  = days[-1]

    start_km = first_day['start_km'] if first_day['start_km'] else None
    end_km   = last_day['end_km']    if last_day['end_km']    else None

    if not start_km and not end_km:
        return jsonify({'found': False, 'reason': 'no_km_values'})

    return jsonify({
        'found': True,
        'start_km': start_km,
        'end_km': end_km,
        'date_start': date_start,
        'date_end': date_end,
        'days_count': len(days)
    })


'''

if MARKER in app_content:
    if 'km-from-log' in app_content:
        print("ℹ️  API endpoint km-from-log već postoji u app.py.")
    else:
        app_content = app_content.replace(MARKER, NEW_ENDPOINT + MARKER)
        APP_PATH.write_text(app_content, encoding="utf-8")
        print("✅ app.py: Dodan endpoint /api/orders/<id>/km-from-log")
else:
    print("⚠️  Nije pronađen marker u app.py — dodaj endpoint ručno.")

# ═══════════════════════════════════════════════════════════════════
# 2. form.html — dodaj JS koji puni km polja pri učitavanju
# ═══════════════════════════════════════════════════════════════════
form_content = FORM_PATH.read_text(encoding="utf-8")

# Tražimo kraj DOMContentLoaded gdje ćemo dodati km autofill poziv
# Specifičan marker: kraj bloka koji računa dnevnice pri inicijalizaciji
OLD_INIT_END = '''  // Calculate dnevnice if we have dates
  const start = document.getElementById('trip_start_datetime').value;
  const end = document.getElementById('trip_end_datetime').value;
  if (start && end) {
    calcDnevnice();
  } else {
    updateTotals();
  }'''

NEW_INIT_END = '''  // Calculate dnevnice if we have dates
  const start = document.getElementById('trip_start_datetime').value;
  const end = document.getElementById('trip_end_datetime').value;
  if (start && end) {
    calcDnevnice();
  } else {
    updateTotals();
  }

  // ── Auto-fill KM iz evidencije vozila ────────────────────────────
  // Samo za nalog koji se uređuje i nije zaključan
  autoFillKmFromVehicleLog();'''

KM_JS_FUNCTION = '''
// ── KM auto-fill iz vehicle_log_days ─────────────────────────────────────
async function autoFillKmFromVehicleLog() {
  const orderId = document.getElementById('order-id')?.value;
  if (!orderId) return; // novi nalog — nema što dohvaćati

  // Provjeri jesu li km polja već popunjena
  const startKmEl = document.getElementById('start_km');
  const endKmEl   = document.getElementById('end_km');
  if (!startKmEl || !endKmEl) return;

  const hasStartKm = startKmEl.value && parseFloat(startKmEl.value) > 0;
  const hasEndKm   = endKmEl.value   && parseFloat(endKmEl.value) > 0;

  // Ako su oba već popunjena, ne diraj
  if (hasStartKm && hasEndKm) return;

  try {
    const res = await fetch(`/api/orders/${orderId}/km-from-log`);
    if (!res.ok) return;
    const d = await res.json();

    if (!d.found) return;

    let filled = [];

    if (!hasStartKm && d.start_km) {
      startKmEl.value = Math.round(d.start_km);
      filled.push('početna KM');
    }
    if (!hasEndKm && d.end_km) {
      endKmEl.value = Math.round(d.end_km);
      filled.push('završna KM');
    }

    if (filled.length > 0) {
      // Prikaži info badge ispod vozilo sekcije
      const vehicleSection = startKmEl.closest('.card');
      if (vehicleSection && !document.getElementById('km-autofill-badge')) {
        const badge = document.createElement('div');
        badge.id = 'km-autofill-badge';
        badge.style.cssText = 'background:#e8f4fd;border:1px solid #aac4db;border-radius:6px;padding:7px 12px;margin-top:8px;font-size:12px;color:#1a6b9a;display:flex;align-items:center;gap:6px;';
        badge.innerHTML = `<span>📍</span><span>Kilometraža automatski preuzeta iz evidencije vozila (${filled.join(', ')}). Možeš je ručno ispraviti.</span>`;
        vehicleSection.querySelector('.card-body').appendChild(badge);
      }
    }
  } catch(e) {
    // Tiho — ne prikazuj grešku korisniku
  }
}
'''

if 'autoFillKmFromVehicleLog' in form_content:
    print("ℹ️  form.html: autoFillKmFromVehicleLog već postoji.")
else:
    # Dodaj poziv u DOMContentLoaded
    if OLD_INIT_END in form_content:
        form_content = form_content.replace(OLD_INIT_END, NEW_INIT_END)
        print("✅ form.html: Dodan poziv autoFillKmFromVehicleLog() u DOMContentLoaded")
    else:
        print("⚠️  form.html: Nije pronađen točan init blok — poziv dodan ispred </script>")
        form_content = form_content.replace('</script>\n{% endblock %}',
            '\n  autoFillKmFromVehicleLog();\n</script>\n{% endblock %}')

    # Dodaj JS funkciju ispred zatvaranja </script>
    form_content = form_content.replace(
        '</script>\n{% endblock %}',
        KM_JS_FUNCTION + '</script>\n{% endblock %}'
    )
    print("✅ form.html: Dodana funkcija autoFillKmFromVehicleLog()")

FORM_PATH.write_text(form_content, encoding="utf-8")

print("""
✅ Gotovo!

Što je implementirano:
- API /api/orders/<id>/km-from-log traži vehicle_log_days za raspon datuma putovanja
- Početna KM = start_km prvog dana, Završna KM = end_km zadnjeg dana
- Puni se samo ako su polja PRAZNA (ne briše ručno unesene vrijednosti)
- Prikazuje plavi info badge ispod sekcije vozila kad se km popuni

Restart aplikacije:
  Ctrl+C pa python app.py
""")
