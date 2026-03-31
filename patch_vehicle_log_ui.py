#!/usr/bin/env python3
"""
Patch: vehicle_log.html i vehicle_log_form.html

vehicle_log.html:
  - Dodaj Status kolonu (Nacrt/Predano/Odobreno)
  - Makni stupce "Službeno km" i "Privatno km"

vehicle_log_form.html:
  - Approve gumb vidljiv za can_approve (ne samo is_admin)
"""

import shutil, re
from pathlib import Path

TLIST = Path('templates/vehicle_log.html')
TFORM = Path('templates/vehicle_log_form.html')

for f in [TLIST, TFORM]:
    if not f.exists():
        print(f'ERROR: {f} ne postoji!')
        exit(1)

shutil.copy(TLIST, TLIST.with_suffix('.html.bak'))
shutil.copy(TFORM, TFORM.with_suffix('.html.bak'))
print('✅ Backupi kreirani')

# ═══════════════════════════════════════════
# vehicle_log.html
# ═══════════════════════════════════════════
list_content = TLIST.read_text(encoding='utf-8')

# Fix 1: thead — makni Službeno km i Privatno km, dodaj Status
OLD_THEAD = """          <th class="sortable" onclick="sortLog(4)">Ukupno km <span class="sort-icon">↕</span></th>
          <th class="sortable" onclick="sortLog(5)">Službeno km <span class="sort-icon">↕</span></th>
          <th class="sortable" onclick="sortLog(6)">Privatno km <span class="sort-icon">↕</span></th>
          <th>PN nalozi</th>
          <th>Akcije</th>"""

NEW_THEAD = """          <th class="sortable" onclick="sortLog(4)">Ukupno km <span class="sort-icon">↕</span></th>
          <th>Status</th>
          <th>PN nalozi</th>
          <th>Akcije</th>"""

if OLD_THEAD in list_content:
    list_content = list_content.replace(OLD_THEAD, NEW_THEAD)
    print('✅ thead: Službeno/Privatno km maknuti, Status dodan')
else:
    print('❌ thead pattern nije pronađen')

# Fix 2: tbody red — makni td za official_km i private_km, dodaj Status td
OLD_TBODY_KMS = """          <td data-val="{{ log.total_km or 0 }}" style="font-weight:700;">{{ '%.2f'|format(log.total_km or 0) }} km</td>
          <td data-val="{{ log.official_km or 0 }}" style="color:#27ae60;">{{ '%.2f'|format(log.official_km or 0) }} km</td>
          <td data-val="{{ log.private_km or 0 }}" style="color:#e67e22;">{{ '%.2f'|format(log.private_km or 0) }} km</td>
          <td>
            <span class="pn-badges" data-log-id="{{ log.id }}" style="font-size:11px;color:var(--gray-400);">učitavam...</span>
          </td>"""

NEW_TBODY_KMS = """          <td data-val="{{ log.total_km or 0 }}" style="font-weight:700;">{{ '%.2f'|format(log.total_km or 0) }} km</td>
          <td>
            {% if log.is_approved %}
              <span style="background:#e8f8f5;color:#27ae60;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">✅ Odobreno</span>
            {% else %}
              <span style="background:#fef9e7;color:#e67e22;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">📝 Nacrt</span>
            {% endif %}
          </td>
          <td>
            <span class="pn-badges" data-log-id="{{ log.id }}" style="font-size:11px;color:var(--gray-400);">učitavam...</span>
          </td>"""

if OLD_TBODY_KMS in list_content:
    list_content = list_content.replace(OLD_TBODY_KMS, NEW_TBODY_KMS)
    print('✅ tbody: km stupci maknuti, Status badge dodan')
else:
    print('❌ tbody km pattern nije pronađen')

# Fix 3: colspan u praznom stanju (bio 9, sada je 7)
OLD_COLSPAN = 'colspan="9"'
NEW_COLSPAN = 'colspan="7"'
if OLD_COLSPAN in list_content:
    list_content = list_content.replace(OLD_COLSPAN, NEW_COLSPAN)
    print('✅ colspan ažuriran na 7')

# Fix 4: sortLog — PN kolona je sada col 5, Akcije col 6
# (korisnik ne sortira PN/Akcije pa je ok da indeksi ostanu, samo status je novi col 4)

TLIST.write_text(list_content, encoding='utf-8')
print('✅ vehicle_log.html ažuriran')

# ═══════════════════════════════════════════
# vehicle_log_form.html — approve gumb
# ═══════════════════════════════════════════
form_content = TFORM.read_text(encoding='utf-8')

# Approve gumb — trenutno: {% if can_edit and current_user.get('is_admin') %}
# Mijenjamo u: {% if can_approve %}
OLD_APPROVE_BTN = """{% if can_edit and current_user.get('is_admin') %}
{% if log.is_approved %}
<span class="btn btn-secondary" style="opacity:0.6;cursor:default;">✅ Odobreno</span>
{% else %}
<button class="btn btn-secondary" onclick="approveLog()" id="approve-btn" title="Odobri evidenciju — dodaje potpis direktora">✍️ Odobri</button>
{% endif %}
{% endif %}"""

NEW_APPROVE_BTN = """{% if can_approve %}
{% if log.is_approved %}
<span class="btn btn-secondary" style="opacity:0.6;cursor:default;">✅ Odobreno</span>
{% else %}
<button class="btn btn-secondary" onclick="approveLog()" id="approve-btn" title="Odobri evidenciju — dodaje potpis direktora">✍️ Odobri</button>
{% endif %}
{% endif %}"""

if OLD_APPROVE_BTN in form_content:
    form_content = form_content.replace(OLD_APPROVE_BTN, NEW_APPROVE_BTN)
    print('✅ vehicle_log_form.html: approve gumb koristi can_approve umjesto is_admin')
else:
    print('❌ approve gumb pattern nije pronađen u vehicle_log_form.html')

TFORM.write_text(form_content, encoding='utf-8')
print('✅ vehicle_log_form.html ažuriran')
print('\n✅ Svi UI patchi primijenjeni!')
