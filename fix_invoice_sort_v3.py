#!/usr/bin/env python3
"""
fix_invoice_sort_v3.py
JS za sort već postoji u datoteci — samo dodaje onclick i data-col
na <th> elemente u thead.

Pokreni iz korijena projekta:
    python fix_invoice_sort_v3.py
"""

import shutil
from pathlib import Path

INVOICE_PATH = Path("templates/invoice_list.html")

if not INVOICE_PATH.exists():
    print(f"❌ Nije pronađeno: {INVOICE_PATH}")
    exit(1)

shutil.copy2(INVOICE_PATH, INVOICE_PATH.with_suffix(".html.bak_sortv3"))
print("✅ Backup kreiran")

invoice = INVOICE_PATH.read_text(encoding="utf-8")

# Provjeri je li onclick već dodan
if "onclick=\"invSort('broj')" in invoice:
    print("ℹ️  Sort onclick već postoji u thead-u.")
    exit(0)

# Točni stringovi iz lokalne datoteke (kopirani iz view outputa)
OLD_TH_BROJ     = '<th style="width:110px;">Broj računa</th>'
OLD_TH_PARTNER  = '<th style="min-width:160px;">Partner</th>'
OLD_TH_OIB      = '<th style="width:90px;">OIB</th>'
OLD_TH_IZNOS    = '<th style="text-align:right;width:80px;">Iznos</th>'
OLD_TH_DATUM    = '<th style="width:84px;">Datum</th>'
OLD_TH_DOSP     = '<th style="width:84px;">Dospijeće</th>'
OLD_TH_PLACENO  = '<th style="text-align:center;width:62px;">Plaćeno</th>'
OLD_TH_LIQ      = '<th style="text-align:center;width:72px;">Likvidirano</th>'

NEW_TH_BROJ     = '<th class="inv-sortable" data-col="broj" style="width:110px;cursor:pointer;user-select:none;" onclick="invSort(\'broj\')">Broj računa <span class="inv-si" id="inv-si-broj">↕</span></th>'
NEW_TH_PARTNER  = '<th class="inv-sortable" data-col="partner" style="min-width:160px;cursor:pointer;user-select:none;" onclick="invSort(\'partner\')">Partner <span class="inv-si" id="inv-si-partner">↕</span></th>'
NEW_TH_OIB      = '<th class="inv-sortable" data-col="oib" style="width:90px;cursor:pointer;user-select:none;" onclick="invSort(\'oib\')">OIB <span class="inv-si" id="inv-si-oib">↕</span></th>'
NEW_TH_IZNOS    = '<th class="inv-sortable" data-col="iznos" style="text-align:right;width:80px;cursor:pointer;user-select:none;" onclick="invSort(\'iznos\')">Iznos <span class="inv-si" id="inv-si-iznos">↕</span></th>'
NEW_TH_DATUM    = '<th class="inv-sortable" data-col="datum" style="width:84px;cursor:pointer;user-select:none;" onclick="invSort(\'datum\')">Datum <span class="inv-si" id="inv-si-datum">↕</span></th>'
NEW_TH_DOSP     = '<th class="inv-sortable" data-col="dospijece" style="width:84px;cursor:pointer;user-select:none;" onclick="invSort(\'dospijece\')">Dospijeće <span class="inv-si" id="inv-si-dospijece">↕</span></th>'
NEW_TH_PLACENO  = '<th class="inv-sortable" data-col="placeno" style="text-align:center;width:62px;cursor:pointer;user-select:none;" onclick="invSort(\'placeno\')">Plaćeno <span class="inv-si" id="inv-si-placeno">↕</span></th>'
NEW_TH_LIQ      = '<th class="inv-sortable" data-col="likvidirano" style="text-align:center;width:72px;cursor:pointer;user-select:none;" onclick="invSort(\'likvidirano\')">Likvidirano <span class="inv-si" id="inv-si-likvidirano">↕</span></th>'

replacements = [
    (OLD_TH_BROJ,    NEW_TH_BROJ),
    (OLD_TH_PARTNER, NEW_TH_PARTNER),
    (OLD_TH_OIB,     NEW_TH_OIB),
    (OLD_TH_IZNOS,   NEW_TH_IZNOS),
    (OLD_TH_DATUM,   NEW_TH_DATUM),
    (OLD_TH_DOSP,    NEW_TH_DOSP),
    (OLD_TH_PLACENO, NEW_TH_PLACENO),
    (OLD_TH_LIQ,     NEW_TH_LIQ),
]

# Dodaj data-iznos i data-placeno i data-likvidirano na <tr> ako nedostaju
OLD_TR_DATA = 'data-datum="{{ inv.invoice_date or \'\' }}"'
NEW_TR_DATA = '''data-datum="{{ inv.invoice_date or '' }}"
            data-iznos="{{ inv.amount_total or 0 }}"
            data-placeno="{{ inv.is_paid or 0 }}"
            data-likvidirano="{{ inv.is_liquidated or 0 }}"'''

# Dodaj CSS za sortable ako nedostaje
CSS = """<style>
.inv-sortable { cursor:pointer; user-select:none; }
.inv-sortable:hover { background:var(--gray-100); }
.inv-si { font-size:10px; color:var(--gray-400); margin-left:2px; }
.inv-sort-asc .inv-si, .inv-sort-desc .inv-si { color:var(--accent); font-weight:700; }
</style>
"""

fixed = 0
for old, new in replacements:
    if old in invoice:
        invoice = invoice.replace(old, new)
        fixed += 1
    else:
        print(f"⚠️  Nije pronađen: {old[:50]}...")

print(f"✅ {fixed}/8 th elemenata ažurirano")

# Dodaj data-iznos/placeno/likvidirano na <tr> ako nedostaju
if OLD_TR_DATA in invoice and 'data-iznos' not in invoice:
    invoice = invoice.replace(OLD_TR_DATA, NEW_TR_DATA)
    print("✅ Dodani data-iznos, data-placeno, data-likvidirano na <tr>")
elif 'data-iznos' in invoice:
    print("ℹ️  data-iznos već postoji")

# Dodaj CSS ispred </style> bloka koji ima invSort
if '.inv-sortable' not in invoice:
    # Umetni CSS ispred prvog <script> u datoteci
    first_script = invoice.find('<script>')
    if first_script >= 0:
        invoice = invoice[:first_script] + CSS + invoice[first_script:]
        print("✅ CSS za .inv-sortable dodan")

INVOICE_PATH.write_text(invoice, encoding="utf-8")
print(f"\n✅ Gotovo! Refresh stranice (bez restarta app.py)")
