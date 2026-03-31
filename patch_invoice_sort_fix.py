#!/usr/bin/env python3
"""
Patch za pouzdani sort po datumu računa.
Problem: tekstualni sadržaj datuma je nekonzistentan (fmt_date filtar,
različite točke, razmaci). Rješenje: dodaj data-date="YYYY-MM-DD" atribut
direktno na <tr> red, pa JS sortira po njemu.
"""

import shutil, sys
from pathlib import Path

TEMPLATE = Path("templates/invoice_list.html")

if not TEMPLATE.exists():
    print(f"GREŠKA: {TEMPLATE} nije pronađen!")
    sys.exit(1)

shutil.copy(TEMPLATE, TEMPLATE.with_suffix(".html.bak3"))
print(f"✅ Backup: {TEMPLATE.with_suffix('.html.bak3')}")

html = TEMPLATE.read_text(encoding="utf-8")

# ─── 1. Dodaj data-date na <tr> ──────────────────────────────────────────────
# Tražimo postojeći <tr data-id=...> i dodajemo data-date atribut
OLD_TR = '''        <tr data-id="{{ inv.id }}"
            data-paid="{{ inv.is_paid }}"
            data-liq="{{ inv.is_liquidated }}"
            data-search="{{ inv.partner_name }} {{ inv.invoice_number }} {{ inv.partner_oib }}"
            data-payment="{{ inv.paid_card_last4 or '' }}"'''

NEW_TR = '''        <tr data-id="{{ inv.id }}"
            data-paid="{{ inv.is_paid }}"
            data-liq="{{ inv.is_liquidated }}"
            data-search="{{ inv.partner_name }} {{ inv.invoice_number }} {{ inv.partner_oib }}"
            data-payment="{{ inv.paid_card_last4 or '' }}"
            data-date="{{ inv.invoice_date or '' }}"'''

if OLD_TR in html:
    html = html.replace(OLD_TR, NEW_TR)
    print("✅ data-date atribut dodan na <tr>")
else:
    print("⚠️  <tr> marker nije pronađen!")
    sys.exit(1)

# ─── 2. Zamijeni JS sort funkciju ─────────────────────────────────────────────
# Stara verzija koja čita textContent
OLD_SORT = """// ── Defaultni sort po datumu (najnoviji prvo) ────────────────────────────────
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
document.addEventListener('DOMContentLoaded', sortInvByDate);"""

NEW_SORT = """// ── Defaultni sort po datumu (najnoviji prvo) ────────────────────────────────
function sortInvByDate() {
  const tbody = document.getElementById('inv-tbody');
  if (!tbody) return;
  const rows = Array.from(tbody.querySelectorAll('tr[data-id]'));
  rows.sort((a, b) => {
    // Čitamo iz data-date atributa (ISO format YYYY-MM-DD iz baze)
    const da = a.dataset.date || '';
    const db = b.dataset.date || '';
    // Leksikografska usporedba ISO datuma je ispravna za sort
    if (db > da) return 1;
    if (db < da) return -1;
    return 0;
  });
  rows.forEach(r => tbody.appendChild(r));
}

// Pokretanje odmah po učitavanju stranice
document.addEventListener('DOMContentLoaded', sortInvByDate);"""

if OLD_SORT in html:
    html = html.replace(OLD_SORT, NEW_SORT)
    print("✅ sortInvByDate() - nova verzija s data-date atributom")
else:
    # Stara sort funkcija možda nije bila patchana - dodaj novu
    print("⚠️  Stara sort funkcija nije pronađena, tražim fallback marker...")
    FALLBACK_MARKER = "// ── Filter ──────────────────────────────────────────────────────────────────"
    if FALLBACK_MARKER in html:
        html = html.replace(FALLBACK_MARKER, NEW_SORT + "\n\n" + FALLBACK_MARKER)
        print("✅ sortInvByDate() ubačena ispred Filter bloka")
    else:
        print("⚠️  Ni fallback marker nije pronađen - sort nije dodan!")

# ─── SPREMI ──────────────────────────────────────────────────────────────────
TEMPLATE.write_text(html, encoding="utf-8")
print(f"\n✅ Patch primijenjen na {TEMPLATE}")
print("\nProvjerite: računi sortirani od najnovijeg prema najstarijem po datumu računa.")
