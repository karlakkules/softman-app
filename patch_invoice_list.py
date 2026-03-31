#!/usr/bin/env python3
"""
Patch skripta za invoice_list.html
Tri izmjene:
1. Defaultni sort po datumu računa (najnoviji prvo) - sortiranje u JS
2. Sticky header (filter bar + thead) pri scrollu tablice
3. Šira kolona iznosa (min-width) da EUR ne prelazi u novi red
"""

import shutil, re, sys
from pathlib import Path

TEMPLATE = Path("templates/invoice_list.html")

if not TEMPLATE.exists():
    print(f"GREŠKA: {TEMPLATE} nije pronađen!")
    sys.exit(1)

shutil.copy(TEMPLATE, TEMPLATE.with_suffix(".html.bak"))
print(f"✅ Backup: {TEMPLATE.with_suffix('.html.bak')}")

html = TEMPLATE.read_text(encoding="utf-8")

# ─── 1. STICKY HEADER ────────────────────────────────────────────────────────
# Omotaj tablicu u container s overflow:auto i max-height
# + card-header sticky + thead sticky

# Zamijeni .card stil — dodaj position:sticky na .card-header
OLD_CARD_HEADER = '<div class="card-header" style="flex-wrap:wrap;gap:8px;">'
NEW_CARD_HEADER = '<div class="card-header" style="flex-wrap:wrap;gap:8px;position:sticky;top:0;z-index:10;background:var(--surface);border-radius:8px 8px 0 0;">'

if OLD_CARD_HEADER in html:
    html = html.replace(OLD_CARD_HEADER, NEW_CARD_HEADER)
    print("✅ Sticky card-header dodan")
else:
    print("⚠️  card-header marker nije pronađen, preskačem")

# Zamijeni .table-wrap da ima max-height i overflow-y scroll
OLD_TABLE_WRAP = '<div class="table-wrap">'
NEW_TABLE_WRAP = '<div class="table-wrap" id="inv-table-wrap" style="overflow-y:auto;max-height:calc(100vh - 200px);">'

if OLD_TABLE_WRAP in html:
    html = html.replace(OLD_TABLE_WRAP, NEW_TABLE_WRAP, 1)  # samo prva pojava (tablica računa)
    print("✅ table-wrap scroll container dodan")
else:
    print("⚠️  table-wrap marker nije pronađen, preskačem")

# Sticky thead
OLD_THEAD = '<thead>\n        <tr>'
NEW_THEAD = '<thead style="position:sticky;top:0;z-index:5;">\n        <tr>'

if OLD_THEAD in html:
    html = html.replace(OLD_THEAD, NEW_THEAD)
    print("✅ Sticky thead dodan")
else:
    print("⚠️  thead marker nije pronađen, preskačem")

# ─── 2. IZNOS KOLONA ŠIRA ────────────────────────────────────────────────────
# Zamijeni width:90px s min-width:105px za kolonu iznosa (header i podaci)
OLD_TH_IZNOS = '<th style="text-align:right;width:90px;">Iznos</th>'
NEW_TH_IZNOS = '<th style="text-align:right;min-width:105px;white-space:nowrap;">Iznos</th>'

if OLD_TH_IZNOS in html:
    html = html.replace(OLD_TH_IZNOS, NEW_TH_IZNOS)
    print("✅ Iznos th header proširen")
else:
    print("⚠️  Iznos th header nije pronađen, preskačem")

# Dodaj white-space:nowrap na td iznosa da '25.000,00 €' ostane u jednom redu
OLD_TD_IZNOS = '<td style="text-align:right;font-weight:600;">'
NEW_TD_IZNOS = '<td style="text-align:right;font-weight:600;white-space:nowrap;min-width:105px;">'

if OLD_TD_IZNOS in html:
    html = html.replace(OLD_TD_IZNOS, NEW_TD_IZNOS)
    print("✅ Iznos td cell proširen")
else:
    print("⚠️  Iznos td cell nije pronađen, preskačem")

# ─── 3. DEFAULTNI SORT PO DATUMU (JS) ────────────────────────────────────────
# Dodaj sortByDateDesc() poziv na kraju JS bloka, nakon filterInv funkcije
SORT_JS = """
// ── Defaultni sort po datumu (najnoviji prvo) ────────────────────────────────
function parseDateHR(s) {
  if (!s) return 0;
  s = s.trim().replace(/\\.+$/, '');  // ukloni trailing točke
  // DD.MM.YYYY ili YYYY-MM-DD
  const m1 = s.match(/^(\\d{1,2})\\.(\\d{1,2})\\.(\\d{4})$/);
  if (m1) return new Date(m1[3], m1[2]-1, m1[1]).getTime();
  const m2 = s.match(/^(\\d{4})-(\\d{2})-(\\d{2})$/);
  if (m2) return new Date(m2[1], m2[2]-1, m2[3]).getTime();
  return 0;
}

function sortInvByDate() {
  const tbody = document.getElementById('inv-tbody');
  if (!tbody) return;
  const rows = Array.from(tbody.querySelectorAll('tr[data-id]'));
  rows.sort((a, b) => {
    // Datum je u 6. td-u (index 5, jer prva td je redni broj)
    const tdsA = a.querySelectorAll('td');
    const tdsB = b.querySelectorAll('td');
    const da = tdsA[5] ? parseDateHR(tdsA[5].textContent) : 0;
    const db = tdsB[5] ? parseDateHR(tdsB[5].textContent) : 0;
    return db - da;  // DESC (najnoviji prvo)
  });
  rows.forEach(r => tbody.appendChild(r));
}

// Pokretanje odmah po učitavanju stranice
document.addEventListener('DOMContentLoaded', sortInvByDate);
"""

# Dodaj sort JS kod neposredno ispred prvog </script> taga u glavnom JS bloku
# (prvom, koji sadrži filterInv)
MARKER = "// ── Filter ──────────────────────────────────────────────────────────────────"

if MARKER in html:
    html = html.replace(MARKER, SORT_JS + "\n" + MARKER)
    print("✅ sortInvByDate() JS dodan")
else:
    print("⚠️  JS filter marker nije pronađen, preskačem sort JS")

# ─── SPREMI ──────────────────────────────────────────────────────────────────
TEMPLATE.write_text(html, encoding="utf-8")
print(f"\n✅ Sve promjene primijenjene na {TEMPLATE}")
print("\nPokrenite aplikaciju i provjerite:")
print("  1. Računi sortirani po datumu (najnoviji na vrhu)")
print("  2. Scroll tablice — header i filteri ostaju vidljivi")
print("  3. Iznos se prikazuje u jednom redu (npr. 2.500,00 €)")
