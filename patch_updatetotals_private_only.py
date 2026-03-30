#!/usr/bin/env python3
"""
Patch: templates/form.html
updateTotals() — filtrira samo payment_method === 'private' (privatna kartica/gotovina)
Isključuje 'card' (poslovne kartice tvrtke) iz izračuna Za isplatu.
"""
import shutil, os, sys

TEMPLATE = os.path.join(os.path.dirname(__file__), 'templates', 'form.html')

if not os.path.exists(TEMPLATE):
    print(f"❌ Nije pronađen: {TEMPLATE}")
    sys.exit(1)

shutil.copy(TEMPLATE, TEMPLATE + '.bak3')
print("✅ Backup kreiran: form.html.bak3")

with open(TEMPLATE, 'r', encoding='utf-8') as f:
    src = f.read()

# Patch: updateTotals - ispravi filter payment_method
# Stara verzija (iz prethodnog patcha) filtrira 'private' || 'card'
OLD = """function updateTotals() {
  // Zbroji troškove s dokumentima gdje je payment_method = 'private' ili 'card'
  const pnExps = window._pnExpensesData || [];
  const expTotal = pnExps
    .filter(e => e.payment_method === 'private' || e.payment_method === 'card')
    .reduce((s, e) => s + (parseFloat(e.amount) || 0), 0);"""

NEW = """function updateTotals() {
  // Zbroji SAMO troškove plaćene privatno (gotovina/privatna kartica)
  // 'card' = poslovna kartica tvrtke — NE ulazi u isplatu zaposleniku
  const pnExps = window._pnExpensesData || [];
  const expTotal = pnExps
    .filter(e => e.payment_method === 'private')
    .reduce((s, e) => s + (parseFloat(e.amount) || 0), 0);"""

# Ako prethodni patch nije bio primijenjen, tražimo originalnu verziju
OLD_ORIGINAL = """function updateTotals() {
  const exps = getExpenses();
  const expTotal = exps.filter(e => e.paid_privately).reduce((s, e) => s + (e.amount || 0), 0);
  const advance = parseFloat(document.getElementById('advance_payment').value || 0);
  const dnevTotal = dnevniceData.total || 0;
  const total = expTotal + dnevTotal;
  const payout = total - advance;

  const fmt = v => v.toFixed(2).replace('.', ',') + ' €';
  document.getElementById('expenses-total').textContent = fmt(expTotal);
  document.getElementById('summary-dnevnice').textContent = fmt(dnevTotal);
  document.getElementById('summary-expenses').textContent = fmt(expTotal);
  document.getElementById('summary-advance').textContent = fmt(advance);
  document.getElementById('summary-payout').textContent = fmt(payout);
}"""

NEW_FROM_ORIGINAL = """function updateTotals() {
  // Zbroji SAMO troškove plaćene privatno (gotovina/privatna kartica)
  // 'card' = poslovna kartica tvrtke — NE ulazi u isplatu zaposleniku
  const pnExps = window._pnExpensesData || [];
  const expTotal = pnExps
    .filter(e => e.payment_method === 'private')
    .reduce((s, e) => s + (parseFloat(e.amount) || 0), 0);

  const advance = parseFloat(document.getElementById('advance_payment').value || 0);
  const dnevTotal = dnevniceData.total || 0;
  const payout = dnevTotal + expTotal - advance;

  const fmt = v => v.toFixed(2).replace('.', ',') + ' €';
  document.getElementById('summary-dnevnice').textContent = fmt(dnevTotal);
  document.getElementById('summary-expenses').textContent = fmt(expTotal);
  document.getElementById('summary-advance').textContent = fmt(advance);
  document.getElementById('summary-payout').textContent = fmt(payout);
}"""

# Probaj novi patch (ako je prethodni bio primijenjen)
if OLD in src:
    src = src.replace(OLD, NEW, 1)
    print("✅ Patch primijenjen: updateTotals() filter 'private' only (iz patchane verzije)")
    applied = True
# Probaj original (ako prethodni patch nije bio primijenjen)
elif OLD_ORIGINAL in src:
    src = src.replace(OLD_ORIGINAL, NEW_FROM_ORIGINAL, 1)
    print("✅ Patch primijenjen: updateTotals() + fetch pnExpenses (iz originalne verzije)")
    # Patch init blok za učitavanje _pnExpensesData
    OLD_INIT = """  // Load existing expenses if editing
  if (EXISTING_EXPENSES.length > 0) {
    EXISTING_EXPENSES.forEach(e => addExpenseRow(e));
  } else if (!LOCKED) {
    addExpenseRow(); // start with one blank row only when editable
  }
  // Lock form AFTER expenses are rendered so static inputs also get locked
  lockForm();"""

    NEW_INIT = """  // Load existing expenses if editing
  if (EXISTING_EXPENSES.length > 0) {
    EXISTING_EXPENSES.forEach(e => addExpenseRow(e));
  } else if (!LOCKED) {
    addExpenseRow(); // start with one blank row only when editable
  }
  // Lock form AFTER expenses are rendered so static inputs also get locked
  lockForm();

  // Učitaj pn_expenses za rekapitulaciju (samo privatno plaćeni)
  window._pnExpensesData = [];
  const _orderId = document.getElementById('order-id')?.value;
  if (_orderId) {
    fetch(`/api/pn-expenses/by-order/${_orderId}`)
      .then(r => r.json())
      .then(data => {
        window._pnExpensesData = Array.isArray(data) ? data : (data.expenses || []);
        updateTotals();
      })
      .catch(() => {});
  }"""

    if OLD_INIT in src:
        src = src.replace(OLD_INIT, NEW_INIT, 1)
        print("✅ Patch primijenjen: init - dodano učitavanje pn_expenses")
    else:
        print("⚠️  Init patch preskočen — pattern nije pronađen (nije kritično)")
    applied = True
else:
    print("❌ PATCH PRESKOČEN — nije pronađena ni jedna verzija updateTotals()")
    print("   Pokreni dijagnostiku: grep -n 'updateTotals' templates/form.html")
    sys.exit(1)

with open(TEMPLATE, 'w', encoding='utf-8') as f:
    f.write(src)

print("\n🎉 form.html uspješno ažuriran!")
print("   Ukupno troškovi = samo payment_method='private' (gotovina/privatna kartica)")
print("   Za isplatu = dnevnice + privatni troškovi - akontacija")
