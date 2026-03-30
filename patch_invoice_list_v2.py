#!/usr/bin/env python3
"""
Patch v2 za templates/invoice_list.html:
  FIX 1: Prošireni filter gumbi (width na selectima)
  FIX 2: Stisni kolone Veza PN, Plaćeno, Likvidirano; šira kolona Partner
  FIX 3: U Veza PN td - makni ikonu i "PN " prefiks, ostavi samo broj (npr. 2026-13)

Pokreni: python3 patch_invoice_list_v2.py
"""
import shutil, os

TARGET = os.path.join('templates', 'invoice_list.html')
BACKUP = TARGET + '.bak_v2'

if not os.path.exists(TARGET):
    print(f"❌ Nije pronađen: {TARGET}"); exit(1)

shutil.copy2(TARGET, BACKUP)
print(f"✅ Backup: {BACKUP}")

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

# ═══════════════════════════════════════════════════════════════════════════
# FIX 1: Filter selecti — ukloni fiksnu width:130px/140px/160px
#        i postavi min-width da tekst stane
# ═══════════════════════════════════════════════════════════════════════════

OLD_PAID_SEL = '''      <select id="inv-paid" class="form-control" style="width:130px;" onchange="filterInv()">
        <option value="">Plaćenost: sve</option>'''
NEW_PAID_SEL = '''      <select id="inv-paid" class="form-control" style="min-width:140px;" onchange="filterInv()">
        <option value="">Plaćenost: sve</option>'''

if OLD_PAID_SEL in content:
    content = content.replace(OLD_PAID_SEL, NEW_PAID_SEL, 1)
    print("✅ FIX 1a: Plaćenost select proširen")
else:
    print("⚠️  FIX 1a: Plaćenost select pattern nije pronađen")

OLD_LIQ_SEL = '''      <select id="inv-liq" class="form-control" style="width:140px;" onchange="filterInv()">
        <option value="">Likvidacija: sve</option>'''
NEW_LIQ_SEL = '''      <select id="inv-liq" class="form-control" style="min-width:148px;" onchange="filterInv()">
        <option value="">Likvidacija: sve</option>'''

if OLD_LIQ_SEL in content:
    content = content.replace(OLD_LIQ_SEL, NEW_LIQ_SEL, 1)
    print("✅ FIX 1b: Likvidacija select proširen")
else:
    print("⚠️  FIX 1b: Likvidacija select pattern nije pronađen")

OLD_PAY_SEL = '''      <select id="inv-payment" class="form-control" style="width:160px;" onchange="filterInv()">
        <option value="">Način plaćanja: sve</option>'''
NEW_PAY_SEL = '''      <select id="inv-payment" class="form-control" style="min-width:172px;" onchange="filterInv()">
        <option value="">Način plaćanja: sve</option>'''

if OLD_PAY_SEL in content:
    content = content.replace(OLD_PAY_SEL, NEW_PAY_SEL, 1)
    print("✅ FIX 1c: Način plaćanja select proširen")
else:
    print("⚠️  FIX 1c: Način plaćanja select pattern nije pronađen")

# ═══════════════════════════════════════════════════════════════════════════
# FIX 2: Header kolona — širi Partner, stisni Veza PN, Plaćeno, Likvidirano
# ═══════════════════════════════════════════════════════════════════════════

OLD_TH_BLOCK = '''          <th style="width:120px;">Broj računa</th>
          <th>Partner</th>
          <th style="width:95px;">OIB</th>
          <th style="text-align:right;width:90px;">Iznos</th>
          <th style="width:88px;">Datum</th>
          <th style="width:88px;">Dospijeće</th>
          <th style="width:90px;white-space:nowrap;">Veza PN</th>
          <th style="text-align:center;width:72px;">Plaćeno</th>
          <th style="text-align:center;width:82px;">Likvidirano</th>'''

NEW_TH_BLOCK = '''          <th style="width:110px;">Broj računa</th>
          <th style="min-width:160px;">Partner</th>
          <th style="width:90px;">OIB</th>
          <th style="text-align:right;width:80px;">Iznos</th>
          <th style="width:84px;">Datum</th>
          <th style="width:84px;">Dospijeće</th>
          <th style="width:70px;text-align:center;">Veza PN</th>
          <th style="text-align:center;width:62px;">Plaćeno</th>
          <th style="text-align:center;width:72px;">Likvidirano</th>'''

if OLD_TH_BLOCK in content:
    content = content.replace(OLD_TH_BLOCK, NEW_TH_BLOCK, 1)
    print("✅ FIX 2: Header kolone resajzirane")
else:
    print("⚠️  FIX 2: Header block pattern nije pronađen — pokušavam parcijalno...")
    # Parcijalni fix samo za Veza PN th
    OLD_TH_PN = '          <th style="width:90px;white-space:nowrap;">Veza PN</th>'
    NEW_TH_PN = '          <th style="width:70px;text-align:center;">Veza PN</th>'
    if OLD_TH_PN in content:
        content = content.replace(OLD_TH_PN, NEW_TH_PN, 1)
        print("  ✅ Parcijalni fix Veza PN th")

# ═══════════════════════════════════════════════════════════════════════════
# FIX 3: Veza PN td — ukloni ikonu i "PN " prefiks, samo broj; stisnuti prikaz
# ═══════════════════════════════════════════════════════════════════════════

OLD_PN_TD = '''          <td style="font-size:12px;white-space:nowrap;">
            {% if inv.pn_auto_id %}
            <a href="/orders/{{ inv.pn_order_id }}/edit"
               style="color:var(--accent);font-weight:600;text-decoration:none;"
               title="Otvori putni nalog PN {{ inv.pn_auto_id }}"
               onclick="event.stopPropagation();">
              📋 PN {{ inv.pn_auto_id }}
            </a>
            {% else %}—{% endif %}
          </td>'''

NEW_PN_TD = '''          <td style="font-size:12px;white-space:nowrap;text-align:center;">
            {% if inv.pn_auto_id %}
            <a href="/orders/{{ inv.pn_order_id }}/edit"
               style="color:var(--accent);font-weight:600;text-decoration:none;"
               title="Otvori putni nalog PN {{ inv.pn_auto_id }}"
               onclick="event.stopPropagation();">
              {{ inv.pn_auto_id }}
            </a>
            {% else %}<span style="color:var(--gray-300);">—</span>{% endif %}
          </td>'''

if OLD_PN_TD in content:
    content = content.replace(OLD_PN_TD, NEW_PN_TD, 1)
    print("✅ FIX 3: Veza PN td — uklonjena ikona i PN prefiks")
else:
    print("⚠️  FIX 3: Veza PN td pattern nije pronađen")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🎉 Patch v2 završen!")
print("   cd ~/Projects/Softman_app && git add templates/invoice_list.html && git commit -m 'ui: filter selecti sirinai, stisni Veza PN/Placeno/Likvidirano kolone' && git push origin main")
