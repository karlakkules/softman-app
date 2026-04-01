#!/usr/bin/env python3
"""
fix_client_and_validation.py

Rješava tri zadatka:

1. Dodaje "Interno" opciju u dropdown Klijent/Partner:
   - u brzom unosu (orders.html quick modal)
   - u novom/edit nalogu (form.html)

2. U form.html mijenja polje Klijent/Partner iz slobodnog teksta (input+datalist)
   u select dropdown s klijentima + "Interno" opcija.

3. U form.html dodaje validaciju pri predaji (saveOrder('submitted')):
   - Destinacija, Datum polaska, Predviđeno trajanje, Svrha putovanja,
     Klijent/Partner, Vozilo (ako nije "ostali načini"), Polazak, Povratak,
     Izvješće s puta, Mjesto izvještaja

4. Dodaje u bazu vozila opcije "Ostali načini prijevoza" i "Prijevoz osiguran"
   kao vozila bez registarskih oznaka (ako već ne postoje).

Pokretanje:
    cd ~/Projects/Softman_app
    python3 fix_client_and_validation.py
"""

import shutil, os, re, sqlite3

BASE      = os.path.dirname(os.path.abspath(__file__))
FORM      = os.path.join(BASE, 'templates', 'form.html')
ORDERS    = os.path.join(BASE, 'templates', 'orders.html')
DB_PATH   = os.path.join(BASE, 'putni_nalog.db')

# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────
def read(p):
    with open(p, encoding='utf-8') as f: return f.read()

def write(p, c):
    with open(p, 'w', encoding='utf-8') as f: f.write(c)

def backup(p):
    shutil.copy2(p, p + '.bak_client_fix')

# ─────────────────────────────────────────────────────────────────────────────
# 1. BAZA — dodaj "Ostali načini prijevoza" i "Prijevoz osiguran"
# ─────────────────────────────────────────────────────────────────────────────
def patch_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        for name, reg in [('Ostali načini prijevoza', ''), ('Prijevoz osiguran', '')]:
            exists = conn.execute("SELECT id FROM vehicles WHERE name=?", (name,)).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO vehicles (name, reg_plate, vehicle_type) VALUES (?, ?, 'pool')",
                    (name, reg)
                )
                print(f"OK: Dodano vozilo '{name}' u bazu.")
            else:
                print(f"INFO: Vozilo '{name}' već postoji.")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"GREŠKA pri ažuriranju baze: {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────────
# 2. form.html — client_info: input+datalist → select dropdown
# ─────────────────────────────────────────────────────────────────────────────

OLD_CLIENT_INPUT = '''      <div class="form-group">
        <label class="form-label" data-hr="Klijent / Partner" data-en="Client / Partner">Klijent / Partner</label>
        <input type="text" class="form-control" id="client_info"
               list="client_list"
               value="{{ order.client_info if order else '' }}"
               placeholder="Upišite ili odaberite klijenta">
      <datalist id="client_list">
        {% for cl in clients %}
        <option value="{{ cl.name }}">
        {% endfor %}
      </datalist>
      </div>'''

NEW_CLIENT_SELECT = '''      <div class="form-group">
        <label class="form-label" data-hr="Klijent / Partner" data-en="Client / Partner">Klijent / Partner</label>
        <select class="form-control" id="client_info">
          <option value="">— odaberi —</option>
          <option value="interno" {% if order and order.client_info == 'interno' %}selected{% endif %}>Interno</option>
          {% for cl in clients %}
          <option value="{{ cl.name }}"
            {% if order and order.client_info == cl.name %}selected{% endif %}>{{ cl.name }}</option>
          {% endfor %}
        </select>
      </div>'''

def patch_form_client():
    content = read(FORM)
    if 'id="client_info"' in content and '<select' in content[content.find('id="client_info"')-50:content.find('id="client_info"')+10]:
        print("INFO: Klijent/Partner u form.html je već select — preskačem.")
        return True
    if OLD_CLIENT_INPUT not in content:
        # Pokušaj fleksibilniji match
        print("UPOZORENJE: Točan string za client_info input nije pronađen.")
        print("  Pokušavam fleksibilni regex zamjenu...")
        pattern = re.compile(
            r'<div class="form-group">\s*<label[^>]*>Klijent / Partner</label>\s*'
            r'<input[^>]*id="client_info"[^>]*>\s*'
            r'(?:<datalist[^>]*>.*?</datalist>\s*)?'
            r'</div>',
            re.DOTALL
        )
        if pattern.search(content):
            content = pattern.sub(NEW_CLIENT_SELECT, content, count=1)
            backup(FORM)
            write(FORM, content)
            print("OK: Klijent/Partner u form.html zamijenjen select dropdownom (regex).")
            return True
        else:
            print("GREŠKA: Ne mogu zamijeniti client_info polje u form.html.")
            return False
    content = content.replace(OLD_CLIENT_INPUT, NEW_CLIENT_SELECT, 1)
    backup(FORM)
    write(FORM, content)
    print("OK: Klijent/Partner u form.html zamijenjen select dropdownom.")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# 3. form.html — dodaj validaciju u saveOrder JS funkciju
# ─────────────────────────────────────────────────────────────────────────────

VALIDATION_JS = """
  // ── Validacija pri predaji ────────────────────────────────────────────
  if (newStatus === 'submitted') {
    const errors = [];
    const destination = document.getElementById('destination')?.value?.trim();
    const departure_date = document.getElementById('departure_date')?.value?.trim();
    const expected_duration = document.getElementById('expected_duration')?.value?.trim();
    const purpose = document.getElementById('purpose')?.value?.trim();
    const client_info = document.getElementById('client_info')?.value?.trim();
    const vehicle_id = document.getElementById('vehicle_id')?.value?.trim();
    const vehicle_name = document.getElementById('vehicle_id')?.options[document.getElementById('vehicle_id')?.selectedIndex]?.text || '';
    const start_km = document.getElementById('start_km')?.value?.trim();
    const end_km = document.getElementById('end_km')?.value?.trim();
    const trip_start = document.getElementById('trip_start_datetime')?.value?.trim();
    const trip_end = document.getElementById('trip_end_datetime')?.value?.trim();
    const report_text = document.getElementById('report_text')?.value?.trim();
    const place_of_report = document.getElementById('place_of_report')?.value?.trim();

    if (!destination) errors.push('Destinacija');
    if (!departure_date) errors.push('Datum polaska');
    if (!expected_duration) errors.push('Predviđeno trajanje (dana)');
    if (!purpose) errors.push('Svrha putovanja');
    if (!client_info) errors.push('Klijent / Partner');
    if (!vehicle_id) {
      errors.push('Vozilo');
    } else {
      const noKmTypes = ['ostali načini prijevoza', 'prijevoz osiguran'];
      const isNoKm = noKmTypes.some(t => vehicle_name.toLowerCase().includes(t));
      if (!isNoKm) {
        if (!start_km) errors.push('Početna kilometraža');
        if (!end_km) errors.push('Završna kilometraža');
      }
    }
    if (!trip_start) errors.push('Polazak (datum i vrijeme)');
    if (!trip_end) errors.push('Povratak (datum i vrijeme)');
    if (!report_text) errors.push('Izvješće s puta');
    if (!place_of_report) errors.push('Mjesto izvještaja');

    if (errors.length > 0) {
      toast('Molimo ispunite obavezna polja:\\n• ' + errors.join('\\n• '), 'error');
      return;
    }
  }
  // ── Kraj validacije ───────────────────────────────────────────────────
"""

def patch_form_validation():
    content = read(FORM)
    if '// ── Validacija pri predaji' in content:
        print("INFO: Validacija već postoji u form.html — preskačem.")
        return True

    # Nađi saveOrder funkciju i umetni validaciju na početak tijela,
    # nakon deklaracije newStatus
    # Tražimo: async function saveOrder(newStatus) { ili function saveOrder(newStatus) {
    pattern = re.compile(
        r'((?:async\s+)?function saveOrder\s*\(newStatus\)\s*\{)',
        re.MULTILINE
    )
    match = pattern.search(content)
    if not match:
        print("GREŠKA: Ne mogu pronaći saveOrder funkciju u form.html.")
        return False

    insert_pos = match.end()
    content = content[:insert_pos] + VALIDATION_JS + content[insert_pos:]
    write(FORM, content)
    print("OK: Validacija pri predaji dodana u saveOrder() u form.html.")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# 4. orders.html — dodaj "Interno" na vrh klijent dropdown liste
# ─────────────────────────────────────────────────────────────────────────────

# Tražimo filterQClientDropdown funkciju i dodajemo "Interno" kao fiksnu opciju
OLD_FILTER_CLIENTS = '''function filterQClientDropdown() {
  const q = (document.getElementById('q-client').value || '').toLowerCase();
  const list = document.getElementById('q-client-dropdown');
  if (!list) return;
  const filtered = _qClients.filter(c => !q || c.name.toLowerCase().includes(q) || (c.oib && c.oib.includes(q)) || (c.address && c.address.toLowerCase().includes(q)));
  if (!filtered.length) {
    list.innerHTML = '<div style="padding:10px 14px;color:var(--gray-400);font-size:13px;">Nema rezultata</div>';
  } else {
    list.innerHTML = filtered.map(c => `
      <div style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);"
        onmousedown="selectQClient(${c.id}, ${JSON.stringify(c.name)})"
        onmouseover="this.style.background='var(--accent-light)'" onmouseout="this.style.background=''">
        <div style="font-weight:600;color:var(--navy);">${c.name}</div>
        ${c.oib ? `<div style="font-size:11px;color:var(--gray-400);">OIB: ${c.oib}${c.address ? ' · '+c.address : ''}</div>` : ''}
      </div>`).join('');
  }
  list.style.display = 'block';
}
function selectQClient(id, name) { document.getElementById('q-client-id').value = id; document.getElementById('q-client').value = name; hideQClientDropdown(); }'''

NEW_FILTER_CLIENTS = '''function filterQClientDropdown() {
  const q = (document.getElementById('q-client').value || '').toLowerCase();
  const list = document.getElementById('q-client-dropdown');
  if (!list) return;
  const filtered = _qClients.filter(c => !q || c.name.toLowerCase().includes(q) || (c.oib && c.oib.includes(q)) || (c.address && c.address.toLowerCase().includes(q)));
  const internoMatch = !q || 'interno'.includes(q);
  let html = '';
  if (internoMatch) {
    html += `<div style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);background:#f5f9ff;"
      onmousedown="selectQClient(0, 'interno')"
      onmouseover="this.style.background='var(--accent-light)'" onmouseout="this.style.background='#f5f9ff'">
      <div style="font-weight:700;color:var(--navy);">Interno</div>
    </div>`;
  }
  if (!filtered.length && !internoMatch) {
    list.innerHTML = '<div style="padding:10px 14px;color:var(--gray-400);font-size:13px;">Nema rezultata</div>';
    list.style.display = 'block'; return;
  }
  html += filtered.map(c => `
    <div style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);"
      onmousedown="selectQClient(${c.id}, ${JSON.stringify(c.name)})"
      onmouseover="this.style.background='var(--accent-light)'" onmouseout="this.style.background=''">
      <div style="font-weight:600;color:var(--navy);">${c.name}</div>
      ${c.oib ? `<div style="font-size:11px;color:var(--gray-400);">OIB: ${c.oib}${c.address ? ' · '+c.address : ''}</div>` : ''}
    </div>`).join('');
  list.innerHTML = html;
  list.style.display = 'block';
}
function selectQClient(id, name) { document.getElementById('q-client-id').value = id; document.getElementById('q-client').value = name; hideQClientDropdown(); }'''

def patch_orders_client():
    content = read(ORDERS)
    if "'interno'" in content and 'selectQClient' in content:
        print("INFO: 'Interno' opcija u orders.html quick modal već postoji — preskačem.")
        return True
    if OLD_FILTER_CLIENTS not in content:
        print("UPOZORENJE: Točan string filterQClientDropdown nije pronađen u orders.html.")
        print("  Pokušavam regex zamjenu...")
        pattern = re.compile(
            r'function filterQClientDropdown\(\)\s*\{.*?\}\s*\n'
            r'function selectQClient\([^)]*\)\s*\{[^}]*\}',
            re.DOTALL
        )
        if pattern.search(content):
            content = pattern.sub(NEW_FILTER_CLIENTS, content, count=1)
            backup(ORDERS)
            write(ORDERS, content)
            print("OK: 'Interno' dodano u quick modal klijent dropdown (regex).")
            return True
        print("GREŠKA: Ne mogu patchati orders.html klijent dropdown.")
        return False
    content = content.replace(OLD_FILTER_CLIENTS, NEW_FILTER_CLIENTS, 1)
    backup(ORDERS)
    write(ORDERS, content)
    print("OK: 'Interno' dodano u quick modal klijent dropdown u orders.html.")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("fix_client_and_validation.py")
    print("=" * 60)

    r1 = patch_db()
    r2 = patch_form_client()
    r3 = patch_form_validation()
    r4 = patch_orders_client()

    print()
    if all([r1, r2, r3, r4]):
        print("✅ Sve promjene primijenjene. Restartaj Flask pa testiraj.")
    else:
        print("⚠️  Neke promjene nisu primijenjene — provjeri poruke gore.")
    print()
    print("Napomena: form.html — polje 'Klijent/Partner' je sada select.")
    print("  Ako neke stare narudžbe imaju free-text koji nije na listi,")
    print("  vrijednost neće biti odabrana — uredit ćeš ih ručno.")
