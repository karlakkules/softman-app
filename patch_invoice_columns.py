#!/usr/bin/env python3
"""
Patch skripta za invoice_list.html - kompaktnost tablice
1. Broj računa uvijek u jednom redu (min-width + white-space:nowrap)
2. Ukloni suvišne razmake između kolona: OIB→Iznos, VezaPN→Plaćeno,
   Plaćeno→Likvidirano, Likvidirano→Komentar
"""

import shutil, sys
from pathlib import Path

TEMPLATE = Path("templates/invoice_list.html")

if not TEMPLATE.exists():
    print(f"GREŠKA: {TEMPLATE} nije pronađen!")
    sys.exit(1)

shutil.copy(TEMPLATE, TEMPLATE.with_suffix(".html.bak2"))
print(f"✅ Backup: {TEMPLATE.with_suffix('.html.bak2')}")

html = TEMPLATE.read_text(encoding="utf-8")

changes = []

# ─── TH (header) kolone ──────────────────────────────────────────────────────

# Redni broj (prva th - prazna)
old = '<th style="width:32px;"></th>'
new = '<th style="width:20px;padding:0 2px;"></th>'
if old in html: html = html.replace(old, new, 1); changes.append("th: redni broj uži")

# Broj računa - nowrap + min-width da stane u jedan red
old = '<th style="width:120px;">Broj računa</th>'
new = '<th style="min-width:110px;white-space:nowrap;">Broj računa</th>'
if old in html: html = html.replace(old, new); changes.append("th: Broj računa nowrap")

# OIB - malo uži
old = '<th style="width:95px;">OIB</th>'
new = '<th style="width:88px;">OIB</th>'
if old in html: html = html.replace(old, new); changes.append("th: OIB uži")

# Iznos - smanji desni padding
old = '<th style="text-align:right;min-width:105px;white-space:nowrap;">Iznos</th>'
new = '<th style="text-align:right;min-width:95px;white-space:nowrap;padding-right:6px;">Iznos</th>'
if old in html:
    html = html.replace(old, new); changes.append("th: Iznos padding manji")
else:
    # fallback ako prethodna patch nije promijenila
    old2 = '<th style="text-align:right;width:90px;">Iznos</th>'
    new2 = '<th style="text-align:right;min-width:95px;white-space:nowrap;padding-right:6px;">Iznos</th>'
    if old2 in html: html = html.replace(old2, new2); changes.append("th: Iznos (fallback)")

# Datum
old = '<th style="width:88px;">Datum</th>'
new = '<th style="width:82px;">Datum</th>'
if old in html: html = html.replace(old, new); changes.append("th: Datum uži")

# Dospijeće
old = '<th style="width:88px;">Dospijeće</th>'
new = '<th style="width:82px;">Dospijeće</th>'
if old in html: html = html.replace(old, new); changes.append("th: Dospijeće uži")

# Veza PN - smanji padding
old = '<th style="text-align:center;width:72px;">Plaćeno</th>'
new = '<th style="text-align:center;width:64px;padding-left:4px;padding-right:4px;">Plaćeno</th>'
if old in html: html = html.replace(old, new); changes.append("th: Plaćeno uži")

old = '<th style="text-align:center;width:82px;">Likvidirano</th>'
new = '<th style="text-align:center;width:74px;padding-left:4px;padding-right:4px;">Likvidirano</th>'
if old in html: html = html.replace(old, new); changes.append("th: Likvidirano uži")

# Komentar (ikona 💬)
old = '<th style="width:32px;text-align:center;" title="Napomena">💬</th>'
new = '<th style="width:24px;text-align:center;padding-left:2px;padding-right:2px;" title="Napomena">💬</th>'
if old in html: html = html.replace(old, new); changes.append("th: Komentar uži")

# Korisnik - sakrij ili uži (zamijenjeno je u prošloj sesiji s Veza PN)
old = '<th style="width:75px;">Korisnik</th>'
new = '<th style="width:60px;">Korisnik</th>'
if old in html: html = html.replace(old, new); changes.append("th: Korisnik uži")

# Akcije - malo uže
old = '<th style="width:100px;">Akcije</th>'
new = '<th style="width:90px;">Akcije</th>'
if old in html: html = html.replace(old, new); changes.append("th: Akcije uži")

# ─── TD (data) kolone ─────────────────────────────────────────────────────────

# Redni broj td
old = '<td style="text-align:center;color:var(--gray-500);font-size:12px;">{{ loop.index }}</td>'
new = '<td style="text-align:center;color:var(--gray-500);font-size:11px;padding:0 2px;">{{ loop.index }}</td>'
if old in html: html = html.replace(old, new); changes.append("td: redni broj uži")

# Broj računa td - nowrap da ne prelazi u novi red
old = '<td><strong style="font-size:13px;">{{ inv.invoice_number or \'—\' }}</strong></td>'
new = '<td style="white-space:nowrap;"><strong style="font-size:13px;">{{ inv.invoice_number or \'—\' }}</strong></td>'
if old in html: html = html.replace(old, new); changes.append("td: Broj računa nowrap")

# OIB td - smanji font i padding
old = '<td style="font-size:11px;color:var(--gray-500);">{{ inv.partner_oib or \'—\' }}</td>'
new = '<td style="font-size:11px;color:var(--gray-500);padding-right:4px;">{{ inv.partner_oib or \'—\' }}</td>'
if old in html: html = html.replace(old, new); changes.append("td: OIB padding manji")

# Iznos td - smanji left padding
old = '<td style="text-align:right;font-weight:600;white-space:nowrap;min-width:105px;">'
new = '<td style="text-align:right;font-weight:600;white-space:nowrap;min-width:88px;padding-left:4px;padding-right:6px;">'
if old in html:
    html = html.replace(old, new); changes.append("td: Iznos padding manji")
else:
    old2 = '<td style="text-align:right;font-weight:600;">'
    new2 = '<td style="text-align:right;font-weight:600;white-space:nowrap;min-width:88px;padding-left:4px;padding-right:6px;">'
    if old2 in html: html = html.replace(old2, new2); changes.append("td: Iznos (fallback)")

# Plaćeno td - smanji padding
old = '<td style="text-align:center;">'
# Ima ih više — zamijeni samo onu oko Plaćeno (koja je ispred is_paid bloka)
# Koristimo specifičniji kontekst
old_paid_block = '''          <td style="text-align:center;">
            {% if inv.is_paid %}'''
new_paid_block = '''          <td style="text-align:center;padding-left:4px;padding-right:4px;">
            {% if inv.is_paid %}'''
if old_paid_block in html: html = html.replace(old_paid_block, new_paid_block); changes.append("td: Plaćeno padding manji")

# Likvidirano td - smanji padding
old_liq_block = '''          <td style="text-align:center;">
            {% if inv.is_liquidated %}'''
new_liq_block = '''          <td style="text-align:center;padding-left:4px;padding-right:4px;">
            {% if inv.is_liquidated %}'''
if old_liq_block in html: html = html.replace(old_liq_block, new_liq_block); changes.append("td: Likvidirano padding manji")

# Komentar td - smanji padding
old_note = '<td style="text-align:center;padding:0 4px;">'
new_note = '<td style="text-align:center;padding:0 2px;">'
if old_note in html: html = html.replace(old_note, new_note); changes.append("td: Komentar padding manji")

# ─── Global table cell padding override ──────────────────────────────────────
# Dodaj style tag u <style> ili inline da tablica ima manji cell padding
STYLE_INJECT = """
<style>
/* Kompaktna tablica računa */
#inv-tbody td, #inv-tbody th {
  padding-top: 7px !important;
  padding-bottom: 7px !important;
}
</style>
"""

# Ubaci style tag neposredno ispred </div><!-- Filters --> taga
# Nalazimo prvu <div class="card" u template-u
MARKER = '<!-- Filters -->\n<div class="card"'
if MARKER in html:
    html = html.replace(MARKER, STYLE_INJECT + '\n' + MARKER)
    changes.append("style: kompaktni row padding")
else:
    # Fallback — ubaci ispred {% block content %}
    MARKER2 = '{% block content %}\n\n<!-- Filters -->'
    if MARKER2 in html:
        html = html.replace(MARKER2, '{% block content %}\n' + STYLE_INJECT + '\n<!-- Filters -->')
        changes.append("style: kompaktni row padding (fallback)")
    else:
        MARKER3 = '{% block content %}'
        if MARKER3 in html:
            html = html.replace(MARKER3, '{% block content %}\n' + STYLE_INJECT, 1)
            changes.append("style: kompaktni row padding (fallback2)")

# ─── SPREMI ──────────────────────────────────────────────────────────────────
TEMPLATE.write_text(html, encoding="utf-8")
print(f"\nPromijenjeno:")
for c in changes:
    print(f"  ✅ {c}")
print(f"\n✅ Sve promjene primijenjene na {TEMPLATE}")
print("\nProvjerite:")
print("  1. Broj računa u jednom redu (97994-S373-1 ne prelazi)")
print("  2. Nema suvišnih razmaka između OIB/Iznos, VezaPN/Plaćeno, Plaćeno/Likvidirano, Likvidirano/💬")
