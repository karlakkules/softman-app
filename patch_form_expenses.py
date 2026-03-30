#!/usr/bin/env python3
"""
Patch: form.html
1. Ukloni cijeli SECTION: TROŠKOVI (manualni redci)
2. updateTotals() - čita troškove iz pn_expenses (privatno/kartica) umjesto manualnih redaka
3. saveOrder() - ukloni 'expenses' iz payloada (više ne šalje manualne troškove)
"""
import shutil, os, sys

TEMPLATE = os.path.join(os.path.dirname(__file__), 'templates', 'form.html')

if not os.path.exists(TEMPLATE):
    print(f"❌ Nije pronađen: {TEMPLATE}")
    sys.exit(1)

shutil.copy(TEMPLATE, TEMPLATE + '.bak')
print("✅ Backup kreiran: form.html.bak")

with open(TEMPLATE, 'r', encoding='utf-8') as f:
    src = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 1: Ukloni cijeli SECTION: TROŠKOVI (od section-divider do zatvaranja carda)
# ─────────────────────────────────────────────────────────────────────────────
OLD1 = '''<!-- ── SECTION: TROŠKOVI ── -->
<div class="section-divider">
  <span class="section-divider-label" data-hr="💰 Troškovi" data-en="💰 Expenses">💰 Troškovi</span>
  <div class="section-divider-line"></div>
</div>
<div class="card" style="margin-bottom:16px;">
  <div class="card-header">
    <span class="card-title" data-hr="Popis troškova" data-en="Expense list">Popis troškova</span>
    {% if not locked %}
    <button type="button" class="btn btn-sm btn-secondary" onclick="addExpenseRow()" title="Dodaj novi redak troška">
      ➕ <span data-hr="Dodaj trošak" data-en="Add expense">Dodaj trošak</span>
    </button>
    {% endif %}
  </div>
  <div class="card-body">
    <!-- Header labels -->
    <div style="display:grid;grid-template-columns:160px 1fr 110px 130px 36px;gap:8px;padding-bottom:6px;border-bottom:2px solid var(--gray-200);margin-bottom:4px;">
      <span style="font-size:11px;font-weight:700;color:var(--gray-600);text-transform:uppercase;" data-hr="Kategorija" data-en="Category">Kategorija</span>
      <span style="font-size:11px;font-weight:700;color:var(--gray-600);text-transform:uppercase;" data-hr="Opis" data-en="Description">Opis</span>
      <span style="font-size:11px;font-weight:700;color:var(--gray-600);text-transform:uppercase;" data-hr="Privatno" data-en="Privately paid">Privatno</span>
      <span style="font-size:11px;font-weight:700;color:var(--gray-600);text-transform:uppercase;" data-hr="Iznos (€)" data-en="Amount (€)">Iznos (€)</span>
      <span></span>
    </div>
    <div id="expenses-container">
      <!-- Rows injected by JS -->
    </div>
    <div style="display:flex;justify-content:flex-end;margin-top:12px;padding-top:12px;border-top:2px solid var(--gray-200);">
      <div style="text-align:right;">
        <div style="font-size:11px;color:var(--gray-400);text-transform:uppercase;letter-spacing:0.05em;" data-hr="Ukupno ostali troškovi" data-en="Total other expenses">Ukupno ostali troškovi</div>
        <div style="font-size:20px;font-weight:700;color:var(--navy);font-family:'DM Mono',monospace;" id="expenses-total">0,00 €</div>
      </div>
    </div>
  </div>
</div>'''

NEW1 = '<!-- SECTION TROŠKOVI uklonjen — troškovi se unose kroz Troškovi s dokumentima -->'

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 2: updateTotals() — čita iz window._pnExpensesData umjesto manualnih redaka
# ─────────────────────────────────────────────────────────────────────────────
OLD2 = '''function updateTotals() {
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
}'''

NEW2 = '''function updateTotals() {
  // Zbroji troškove s dokumentima gdje je payment_method = 'private' ili 'card'
  const pnExps = window._pnExpensesData || [];
  const expTotal = pnExps
    .filter(e => e.payment_method === 'private' || e.payment_method === 'card')
    .reduce((s, e) => s + (parseFloat(e.amount) || 0), 0);

  const advance = parseFloat(document.getElementById('advance_payment').value || 0);
  const dnevTotal = dnevniceData.total || 0;
  const payout = dnevTotal + expTotal - advance;

  const fmt = v => v.toFixed(2).replace('.', ',') + ' €';
  document.getElementById('summary-dnevnice').textContent = fmt(dnevTotal);
  document.getElementById('summary-expenses').textContent = fmt(expTotal);
  document.getElementById('summary-advance').textContent = fmt(advance);
  document.getElementById('summary-payout').textContent = fmt(payout);
}'''

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 3: saveOrder() — ukloni 'expenses: getExpenses()' iz payloada
# ─────────────────────────────────────────────────────────────────────────────
OLD3 = '    expenses: getExpenses()'
NEW3 = '    // expenses se ne šalju — unose se kroz pn_expenses (Troškovi s dokumentima)'

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 4: Init — ukloni addExpenseRow() pozive, dodaj učitavanje _pnExpensesData
# ─────────────────────────────────────────────────────────────────────────────
OLD4 = '''  // Load existing expenses if editing
  if (EXISTING_EXPENSES.length > 0) {
    EXISTING_EXPENSES.forEach(e => addExpenseRow(e));
  } else if (!LOCKED) {
    addExpenseRow(); // start with one blank row only when editable
  }
  // Lock form AFTER expenses are rendered so static inputs also get locked
  lockForm();'''

NEW4 = '''  // Učitaj pn_expenses za rekapitulaciju (privatno/kartica)
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
  }
  // Lock form
  lockForm();'''

patches = [
    ("Ukloni SECTION TROŠKOVI (manualni redci)", OLD1, NEW1),
    ("updateTotals() - čita pn_expenses",        OLD2, NEW2),
    ("saveOrder() - ukloni expenses payload",     OLD3, NEW3),
    ("Init - zamijeni addExpenseRow s fetch",     OLD4, NEW4),
]

ok = True
for label, old, new in patches:
    if old not in src:
        print(f"⚠️  PATCH PRESKOČEN — pattern nije pronađen: {label}")
        print(f"   Tražim: {repr(old[:100])}")
        ok = False
    else:
        src = src.replace(old, new, 1)
        print(f"✅ Patch primijenjen: {label}")

if ok:
    with open(TEMPLATE, 'w', encoding='utf-8') as f:
        f.write(src)
    print("\n🎉 form.html uspješno ažuriran!")
    print("   Reload stranice — manualni troškovi su uklonjeni, rekapitulacija čita pn_expenses.")
else:
    print("\n❌ Neki patchi nisu primijenjeni — template nije mijenjan.")
