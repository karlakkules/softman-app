#!/usr/bin/env python3
"""
Patch 1: app.py
  saveOrder() — total_expenses čita iz pn_expenses tablice (payment_method='private')
  umjesto iz manualnih redaka.

Patch 2: templates/orders.html
  Kolona "Ukupno" → "Za isplatu", prikazuje payout_amount.
"""
import shutil, os, sys

# ─── PATCH 1: app.py ──────────────────────────────────────────────────────────
APP = os.path.join(os.path.dirname(__file__), 'app.py')
if not os.path.exists(APP):
    print(f"❌ Nije pronađen: {APP}")
    sys.exit(1)

shutil.copy(APP, APP + '.bak4')
print("✅ Backup kreiran: app.py.bak4")

with open(APP, 'r', encoding='utf-8') as f:
    src = f.read()

OLD_CALC = """    # Calculate totals
    expenses = data.get('expenses', [])
    private_total = sum(float(e.get('amount', 0)) for e in expenses if e.get('paid_privately'))
    total_expenses = private_total
    daily_total = calc['total']
    total_amount = total_expenses + daily_total
    advance = float(data.get('advance_payment', 0))
    payout = total_amount - advance"""

NEW_CALC = """    # Calculate totals — čita iz pn_expenses (privatno plaćeni troškovi)
    order_id_for_calc = data.get('id') or None
    private_total = 0.0
    if order_id_for_calc:
        try:
            pn_exp_rows = conn.execute(
                "SELECT amount FROM pn_expenses WHERE travel_order_id=? AND payment_method='private'",
                (order_id_for_calc,)
            ).fetchall()
            private_total = sum(float(r['amount'] or 0) for r in pn_exp_rows)
        except:
            pass
    total_expenses = private_total
    daily_total = calc['total']
    total_amount = total_expenses + daily_total
    advance = float(data.get('advance_payment', 0))
    payout = total_amount - advance"""

if OLD_CALC in src:
    src = src.replace(OLD_CALC, NEW_CALC, 1)
    print("✅ Patch primijenjen: app.py - total_expenses iz pn_expenses")
else:
    print("⚠️  app.py PATCH PRESKOČEN — pattern nije pronađen")
    lines = src.splitlines()
    for i, line in enumerate(lines, 1):
        if 'private_total' in line or 'total_expenses' in line:
            print(f"  {i:5d}: {repr(line)}")

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)

# ─── PATCH 2: orders.html ─────────────────────────────────────────────────────
TEMPLATE = os.path.join(os.path.dirname(__file__), 'templates', 'orders.html')
if not os.path.exists(TEMPLATE):
    print(f"❌ Nije pronađen: {TEMPLATE}")
    sys.exit(1)

shutil.copy(TEMPLATE, TEMPLATE + '.bak')
print("✅ Backup kreiran: orders.html.bak")

with open(TEMPLATE, 'r', encoding='utf-8') as f:
    tsrc = f.read()

tpatches = [
    (
        "Header: Ukupno → Za isplatu",
        '<th class="sortable" style="width:90px;" data-col="6" onclick="sortTable(6)">Ukupno <span class="sort-icon">↕</span></th>',
        '<th class="sortable" style="width:90px;" data-col="6" onclick="sortTable(6)">Za isplatu <span class="sort-icon">↕</span></th>'
    ),
    (
        "Tbody: total_amount → payout_amount (single quotes)",
        '<td data-col="6" data-val="{{ o.total_amount or 0 }}"><strong>{{ \'%.2f\'|format(o.total_amount or 0) }} €</strong></td>',
        '<td data-col="6" data-val="{{ o.payout_amount or 0 }}"><strong>{{ \'%.2f\'|format(o.payout_amount or 0) }} €</strong></td>'
    ),
    (
        "Tbody: total_amount → payout_amount (double quotes)",
        '<td data-col="6" data-val="{{ o.total_amount or 0 }}"><strong>{{ "%.2f"|format(o.total_amount or 0) }} €</strong></td>',
        '<td data-col="6" data-val="{{ o.payout_amount or 0 }}"><strong>{{ "%.2f"|format(o.payout_amount or 0) }} €</strong></td>'
    ),
]

t_ok = 0
for label, old, new in tpatches:
    if old in tsrc:
        tsrc = tsrc.replace(old, new, 1)
        print(f"✅ Patch primijenjen: {label}")
        t_ok += 1
    else:
        print(f"   Preskočen: {label}")

if t_ok == 0:
    print("\n⚠️  orders.html — nijedan tbody patch nije primijenjen. Dijagnostika:")
    for i, line in enumerate(tsrc.splitlines(), 1):
        if 'total_amount' in line or 'data-col="6"' in line:
            print(f"  {i:5d}: {repr(line)}")
else:
    with open(TEMPLATE, 'w', encoding='utf-8') as f:
        f.write(tsrc)
    print("\n🎉 orders.html uspješno ažuriran!")

print("\n🎉 Gotovo!")
print("   Lista PN: kolona 'Za isplatu' = payout_amount")
print("   payout_amount = dnevnice + privatni troškovi (pn_expenses) − akontacija")
print("   Napomena: za postojeće nalog, iznos se ažurira tek pri sljedećem Spremi.")
