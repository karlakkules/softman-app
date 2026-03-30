#!/usr/bin/env python3
"""
Patch za templates/invoice_list.html:
  FIX 1: Dodaje kolonu "Veza PN" u tablicu ulaznih računa
  FIX 2: Formatira datume iz YYYY-MM-DD u DD.MM.YYYY. format (samo prikaz)

VAŽNO: Datumi se u bazi čuvaju kao YYYY-MM-DD — mijenjamo SAMO prikaz u HTML-u.
       Input polja za unos/edit ostaju text (DD.MM.YYYY.) jer ih backend već tako čeka.

Pokreni: python3 patch_invoice_list.py
"""
import shutil, os

TARGET = os.path.join('templates', 'invoice_list.html')
BACKUP = TARGET + '.bak'

if not os.path.exists(TARGET):
    print(f"❌ Nije pronađen: {TARGET}"); exit(1)

shutil.copy2(TARGET, BACKUP)
print(f"✅ Backup: {BACKUP}")

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

# ═══════════════════════════════════════════════════════════════════════════
# FIX 1a: Dodaj th "Veza PN" u header tablice (iza "Dospijeće")
# ═══════════════════════════════════════════════════════════════════════════

OLD_TH = '''          <th style="width:88px;">Dospijeće</th>
          <th style="text-align:center;width:72px;">Plaćeno</th>'''

NEW_TH = '''          <th style="width:88px;">Dospijeće</th>
          <th style="width:90px;white-space:nowrap;">Veza PN</th>
          <th style="text-align:center;width:72px;">Plaćeno</th>'''

if OLD_TH in content:
    content = content.replace(OLD_TH, NEW_TH, 1)
    print("✅ FIX 1a: Dodan <th> Veza PN")
else:
    print("❌ FIX 1a: th pattern nije pronađen!")

# ═══════════════════════════════════════════════════════════════════════════
# FIX 1b: Dodaj td "Veza PN" u redove tablice (iza td Dospijeće)
# ═══════════════════════════════════════════════════════════════════════════

OLD_TD_DUE = '''          <td style="font-size:12px;white-space:nowrap;">{{ inv.due_date or '—' }}</td>
          <td style="text-align:center;">'''

NEW_TD_DUE = '''          <td style="font-size:12px;white-space:nowrap;">{{ inv.due_date or '—' }}</td>
          <td style="font-size:12px;white-space:nowrap;">
            {% if inv.pn_auto_id %}
            <a href="/orders/{{ inv.pn_auto_id.split('-')[1] if '-' in inv.pn_auto_id else '' }}/edit"
               style="color:var(--accent);font-weight:600;text-decoration:none;"
               title="Otvori putni nalog PN {{ inv.pn_auto_id }}"
               onclick="event.stopPropagation();">
              📋 PN {{ inv.pn_auto_id }}
            </a>
            {% else %}—{% endif %}
          </td>
          <td style="text-align:center;">'''

if OLD_TD_DUE in content:
    content = content.replace(OLD_TD_DUE, NEW_TD_DUE, 1)
    print("✅ FIX 1b: Dodan <td> Veza PN")
else:
    print("❌ FIX 1b: td pattern nije pronađen!")

# ═══════════════════════════════════════════════════════════════════════════
# FIX 1c: colspan u "Nema računa" row — povećaj s 12 na 13
# ═══════════════════════════════════════════════════════════════════════════

OLD_COLSPAN = 'colspan="12"'
NEW_COLSPAN = 'colspan="13"'

if OLD_COLSPAN in content:
    content = content.replace(OLD_COLSPAN, NEW_COLSPAN, 1)
    print("✅ FIX 1c: colspan povećan na 13")

# ═══════════════════════════════════════════════════════════════════════════
# FIX 2: Formatiraj datume u prikazu (YYYY-MM-DD → DD.MM.YYYY.)
# Dodajemo Jinja2 filter fmt_date koji već postoji u app.py
# ═══════════════════════════════════════════════════════════════════════════

# FIX 2a: invoice_date u tablici
OLD_DATE_TD = "          <td style=\"font-size:12px;white-space:nowrap;\">{{ inv.invoice_date or '—' }}</td>"
NEW_DATE_TD = "          <td style=\"font-size:12px;white-space:nowrap;\">{{ inv.invoice_date|fmt_date or '—' }}</td>"

if OLD_DATE_TD in content:
    content = content.replace(OLD_DATE_TD, NEW_DATE_TD, 1)
    print("✅ FIX 2a: invoice_date formatiran s fmt_date")
else:
    print("⚠️  FIX 2a: invoice_date pattern nije pronađen")

# FIX 2b: due_date u tablici (prva pojava - u tbody redu, ne u th)
OLD_DUE_TD = "          <td style=\"font-size:12px;white-space:nowrap;\">{{ inv.due_date or '—' }}</td>"
NEW_DUE_TD = "          <td style=\"font-size:12px;white-space:nowrap;\">{{ inv.due_date|fmt_date or '—' }}</td>"

if OLD_DUE_TD in content:
    content = content.replace(OLD_DUE_TD, NEW_DUE_TD, 1)
    print("✅ FIX 2b: due_date formatiran s fmt_date")
else:
    print("⚠️  FIX 2b: due_date pattern nije pronađen")

# FIX 2c: paid_at u title atributu (tooltip)
# Tooltip prikazuje inv.paid_at — formatiramo i njega
OLD_PAID_TITLE = 'title="{{ inv.paid_at }}{% if inv.paid_card_last4 %} · {{ inv.paid_card_last4 }}{% endif %}"'
NEW_PAID_TITLE = 'title="{{ inv.paid_at|fmt_date }}{% if inv.paid_card_last4 %} · {{ inv.paid_card_last4 }}{% endif %}"'

count = content.count(OLD_PAID_TITLE)
if count > 0:
    content = content.replace(OLD_PAID_TITLE, NEW_PAID_TITLE)
    print(f"✅ FIX 2c: paid_at tooltip formatiran ({count}x)")
else:
    print("⚠️  FIX 2c: paid_at tooltip pattern nije pronađen")

# ═══════════════════════════════════════════════════════════════════════════
# FIX 3: Link na PN — popravak href-a
# Veza PN treba ići na /orders/{order_id}/edit, ne na auto_id split
# Dodajemo pn_order_id u backend query, a ovdje koristimo Jinja uvjet
# ═══════════════════════════════════════════════════════════════════════════
# Zamijeni href koji koristi split s direktnim linkom (backend treba poslati id)
OLD_PN_LINK = '''            <a href="/orders/{{ inv.pn_auto_id.split('-')[1] if '-' in inv.pn_auto_id else '' }}/edit"'''
NEW_PN_LINK = '''            <a href="/orders/{{ inv.pn_order_id }}/edit"'''

if OLD_PN_LINK in content:
    content = content.replace(OLD_PN_LINK, NEW_PN_LINK, 1)
    print("✅ FIX 3: PN link popravljen na pn_order_id")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🎉 invoice_list.html patch završen!")
print("   Sada pokreni: python3 patch_invoices_pn_link.py (za app.py)")
print("   pa: cd ~/Projects/Softman_app && git add templates/invoice_list.html app.py && git commit -m 'feat: Veza PN kolona i format datuma u Ulaznim racunima' && git push origin main")
