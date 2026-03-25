#!/usr/bin/env python3
"""
Patch za dodavanje supplier dropdown-a u expense forme.
Pokreni iz root direktorija projekta:
  python3 patch_supplier_dropdown.py
"""
import os, sys, shutil

# ═══════════════════════════════════════════════════════════════════
# 1. PATCH orders.html — expense-detail-modal
# ═══════════════════════════════════════════════════════════════════

ORDERS_PATH = os.path.join('templates', 'orders.html')
if not os.path.exists(ORDERS_PATH):
    print(f"❌ {ORDERS_PATH} nije pronađen!"); sys.exit(1)

with open(ORDERS_PATH, 'r', encoding='utf-8') as f:
    orders = f.read()

if 'exp-supplier-search' in orders:
    print("⚠️  orders.html već ima supplier dropdown — preskačem.")
else:
    # A) Zamijeni R1 polja u expense-detail-modal — dodaj supplier dropdown
    OLD_R1_ORDERS = '''      <div id="exp-r1-fields" style="display:none;">
        <div style="background:#e8f0f7;border:1px solid #aac4db;border-radius:6px;padding:8px 12px;margin-bottom:14px;font-size:12px;color:var(--navy);font-weight:600;">
          📋 R1 račun — podaci o partneru (vidljivo i u modulu Ulazni računi)
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;">
          <div class="form-group" style="grid-column:1/-1;">
            <label class="form-label">Naziv partnera</label>
            <input type="text" class="form-control" id="exp-partner-name" placeholder="Naziv tvrtke...">
          </div>
          <div class="form-group">
            <label class="form-label">OIB partnera</label>
            <input type="text" class="form-control" id="exp-partner-oib" placeholder="12345678901" maxlength="11">
          </div>
          <div class="form-group">
            <label class="form-label">Broj računa</label>
            <input type="text" class="form-control" id="exp-invoice-number" placeholder="R-001/2026">
          </div>
          <div class="form-group">
            <label class="form-label">Datum dospijeća</label>
            <input type="date" class="form-control" id="exp-due-date">
          </div>
        </div>
        <hr style="border:none;border-top:1px solid var(--gray-200);margin:12px 0;">
      </div>'''

    NEW_R1_ORDERS = '''      <div id="exp-r1-fields" style="display:none;">
        <div style="background:#e8f0f7;border:1px solid #aac4db;border-radius:6px;padding:8px 12px;margin-bottom:14px;font-size:12px;color:var(--navy);font-weight:600;">
          📋 R1 račun — podaci o partneru (vidljivo i u modulu Ulazni računi)
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;">
          <div class="form-group" style="grid-column:1/-1;">
            <label class="form-label">Naziv partnera</label>
            <input type="text" class="form-control" id="exp-partner-name" placeholder="Naziv tvrtke...">
          </div>
          <div class="form-group" style="grid-column:1/-1;">
            <label class="form-label" style="font-size:11px;color:var(--gray-500);margin-bottom:4px;">Dobavljač s liste</label>
            <div style="display:flex;gap:6px;align-items:center;">
              <div style="flex:1;position:relative;">
                <input type="text" class="form-control" id="exp-supplier-search"
                  placeholder="Pretraži dobavljača..." style="font-size:13px;" autocomplete="off"
                  oninput="filterExpSupplierDropdown()" onfocus="showExpSupplierDropdown()">
                <input type="hidden" id="exp-supplier-id">
                <div id="exp-supplier-dropdown" style="display:none;position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid var(--gray-300);border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,0.15);z-index:99999;max-height:200px;overflow-y:auto;margin-top:2px;"></div>
              </div>
              <button type="button" class="btn btn-sm btn-secondary" onclick="quickAddExpSupplier()" title="Dodaj novog dobavljača" style="padding:0 10px;height:36px;flex-shrink:0;">➕</button>
            </div>
            <div id="exp-supplier-match" style="display:none;margin-top:4px;font-size:12px;color:#27ae60;font-weight:600;"></div>
          </div>
          <div class="form-group">
            <label class="form-label">OIB partnera</label>
            <input type="text" class="form-control" id="exp-partner-oib" placeholder="12345678901" maxlength="11">
          </div>
          <div class="form-group">
            <label class="form-label">Broj računa</label>
            <input type="text" class="form-control" id="exp-invoice-number" placeholder="R-001/2026">
          </div>
          <div class="form-group">
            <label class="form-label">Datum dospijeća</label>
            <input type="date" class="form-control" id="exp-due-date">
          </div>
        </div>
        <hr style="border:none;border-top:1px solid var(--gray-200);margin:12px 0;">
      </div>'''

    if OLD_R1_ORDERS in orders:
        orders = orders.replace(OLD_R1_ORDERS, NEW_R1_ORDERS)
        print("✅ orders.html: R1 polja ažurirana s supplier dropdownom")
    else:
        print("⚠️  orders.html: Nije pronađen marker za R1 polja — ručno provjeri")

    # B) Dodaj JS funkcije za supplier dropdown PRIJE </script>{% endblock %}
    SUPPLIER_JS_ORDERS = '''
// ═══════════════════════════════════════════════════════════════════
// SUPPLIER DROPDOWN za expense forme
// ═══════════════════════════════════════════════════════════════════
let _expSuppliersCache = [];

async function loadExpSuppliers() {
  try {
    const res = await fetch('/api/suppliers');
    const d = await res.json();
    _expSuppliersCache = d.suppliers || d || [];
  } catch(e) { _expSuppliersCache = []; }
  return _expSuppliersCache;
}

async function showExpSupplierDropdown() {
  if (!_expSuppliersCache.length) await loadExpSuppliers();
  filterExpSupplierDropdown();
  const el = document.getElementById('exp-supplier-dropdown');
  if (el) el.style.display = 'block';
}

function filterExpSupplierDropdown() {
  const q = (document.getElementById('exp-supplier-search')?.value || '').toLowerCase();
  const list = document.getElementById('exp-supplier-dropdown');
  if (!list) return;
  const filtered = _expSuppliersCache.filter(s =>
    !q || s.name.toLowerCase().includes(q) ||
    (s.oib && s.oib.includes(q)) ||
    (s.address && s.address.toLowerCase().includes(q))
  );
  if (!filtered.length) {
    list.innerHTML = '<div style="padding:10px 14px;color:var(--gray-400);font-size:13px;">Nema rezultata</div>';
  } else {
    list.innerHTML = filtered.map(s =>
      `<div data-sid="${s.id}" style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);">
        <div style="font-weight:600;color:var(--navy);">${s.name}</div>
        ${s.oib ? `<div style="font-size:11px;color:var(--gray-400);">OIB: ${s.oib}${s.address ? ' · ' + s.address : ''}</div>` : ''}
      </div>`
    ).join('');
    list.querySelectorAll('[data-sid]').forEach(el => {
      el.addEventListener('mousedown', function(e) {
        e.preventDefault();
        const s = _expSuppliersCache.find(x => String(x.id) === this.dataset.sid);
        if (!s) return;
        selectExpSupplier(s);
      });
      el.addEventListener('mouseover', function() { this.style.background = 'var(--accent-light)'; });
      el.addEventListener('mouseout', function() { this.style.background = ''; });
    });
  }
  list.style.display = 'block';
}

function selectExpSupplier(s) {
  document.getElementById('exp-supplier-search').value = s.name;
  document.getElementById('exp-supplier-id').value = s.id;
  document.getElementById('exp-partner-name').value = s.name;
  document.getElementById('exp-partner-oib').value = s.oib || '';
  document.getElementById('exp-supplier-dropdown').style.display = 'none';
  const badge = document.getElementById('exp-supplier-match');
  if (badge) { badge.style.display = 'block'; badge.textContent = '✅ ' + s.name; }
}

function tryAutoMatchExpSupplier(partnerName, oib) {
  if (!_expSuppliersCache.length) return;
  let match = null;
  if (oib && oib.length >= 10)
    match = _expSuppliersCache.find(s => s.oib && s.oib.trim() === oib.trim());
  if (!match && partnerName) {
    const pn = partnerName.toLowerCase().trim();
    match = _expSuppliersCache.find(s => s.name.toLowerCase().trim() === pn);
  }
  if (match) {
    selectExpSupplier(match);
  }
}

async function quickAddExpSupplier() {
  const name = document.getElementById('exp-partner-name')?.value || '';
  const oib = document.getElementById('exp-partner-oib')?.value || '';
  const supplierName = prompt('Naziv dobavljača:', name);
  if (!supplierName) return;
  const supplierOib = prompt('OIB (opcionalno):', oib);
  try {
    const res = await fetch('/api/suppliers', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name: supplierName, oib: supplierOib || '', address: '' })
    });
    const d = await res.json();
    if (d.success || d.id) {
      toast('Dobavljač dodan!', 'success');
      await loadExpSuppliers();
      const newS = _expSuppliersCache.find(s => s.id == d.id);
      if (newS) selectExpSupplier(newS);
    } else { toast(d.error || 'Greška', 'error'); }
  } catch(e) { toast('Greška: ' + e.message, 'error'); }
}

// Zatvori dropdown kad klik van
document.addEventListener('click', function(e) {
  const dd = document.getElementById('exp-supplier-dropdown');
  const search = document.getElementById('exp-supplier-search');
  if (dd && search && !search.contains(e.target) && !dd.contains(e.target)) {
    dd.style.display = 'none';
  }
});

// Patch openExpenseDetail da učita supplier-e i pokuša auto-match
const _origOpenExpenseDetail = typeof openExpenseDetail === 'function' ? openExpenseDetail : null;
if (_origOpenExpenseDetail) {
  const _wrappedOpenExpenseDetail = openExpenseDetail;
  openExpenseDetail = async function(ocrResult) {
    await _wrappedOpenExpenseDetail(ocrResult);
    // Nakon otvaranja forme, učitaj supplier-e i auto-match
    if (_expDocType === 'r1') {
      await loadExpSuppliers();
      tryAutoMatchExpSupplier(
        ocrResult.data?.partner_name || '',
        ocrResult.data?.partner_oib || ''
      );
    }
  };
}
'''

    # Dodaj JS prije zadnjeg </script>
    close_script = '</script>\n{% endblock %}'
    if close_script in orders:
        orders = orders.replace(close_script, SUPPLIER_JS_ORDERS + '\n</script>\n{% endblock %}', 1)
        print("✅ orders.html: Supplier dropdown JS dodan")
    else:
        print("⚠️  orders.html: Ne mogu pronaći </script>\\n{% endblock %}")

    shutil.copy2(ORDERS_PATH, ORDERS_PATH + '.bak2')
    with open(ORDERS_PATH, 'w', encoding='utf-8') as f:
        f.write(orders)
    print(f"📁 Backup: {ORDERS_PATH}.bak2")


# ═══════════════════════════════════════════════════════════════════
# 2. PATCH form.html — pn-exp-detail-modal (ista logika)
# ═══════════════════════════════════════════════════════════════════

FORM_PATH = os.path.join('templates', 'form.html')
if not os.path.exists(FORM_PATH):
    print(f"❌ {FORM_PATH} nije pronađen!"); sys.exit(1)

with open(FORM_PATH, 'r', encoding='utf-8') as f:
    form = f.read()

if 'pnexp-supplier-search' in form:
    print("⚠️  form.html već ima supplier dropdown — preskačem.")
else:
    # Zamijeni R1 polja u pn-exp-detail-modal
    OLD_R1_FORM = '''      <div id="pnexp-r1-fields" style="display:none;">
        <div style="background:#e8f0f7;border:1px solid #aac4db;border-radius:6px;padding:8px 12px;margin-bottom:12px;font-size:12px;color:var(--navy);font-weight:600;">📋 R1 račun — vidljivo i u modulu Ulazni računi</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">
          <div class="form-group" style="grid-column:1/-1;"><label class="form-label">Naziv partnera</label><input type="text" class="form-control" id="pnexp-partner-name"></div>
          <div class="form-group"><label class="form-label">OIB partnera</label><input type="text" class="form-control" id="pnexp-partner-oib" maxlength="11"></div>
          <div class="form-group"><label class="form-label">Broj računa</label><input type="text" class="form-control" id="pnexp-invoice-number"></div>
          <div class="form-group"><label class="form-label">Datum dospijeća</label><input type="date" class="form-control" id="pnexp-due-date"></div>
        </div>
        <hr style="border:none;border-top:1px solid var(--gray-200);margin:10px 0;">
      </div>'''

    NEW_R1_FORM = '''      <div id="pnexp-r1-fields" style="display:none;">
        <div style="background:#e8f0f7;border:1px solid #aac4db;border-radius:6px;padding:8px 12px;margin-bottom:12px;font-size:12px;color:var(--navy);font-weight:600;">📋 R1 račun — vidljivo i u modulu Ulazni računi</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">
          <div class="form-group" style="grid-column:1/-1;"><label class="form-label">Naziv partnera</label><input type="text" class="form-control" id="pnexp-partner-name"></div>
          <div class="form-group" style="grid-column:1/-1;">
            <label class="form-label" style="font-size:11px;color:var(--gray-500);margin-bottom:4px;">Dobavljač s liste</label>
            <div style="display:flex;gap:6px;align-items:center;">
              <div style="flex:1;position:relative;">
                <input type="text" class="form-control" id="pnexp-supplier-search"
                  placeholder="Pretraži dobavljača..." style="font-size:13px;" autocomplete="off"
                  oninput="filterPnExpSupplierDropdown()" onfocus="showPnExpSupplierDropdown()">
                <input type="hidden" id="pnexp-supplier-id">
                <div id="pnexp-supplier-dropdown" style="display:none;position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid var(--gray-300);border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,0.15);z-index:99999;max-height:200px;overflow-y:auto;margin-top:2px;"></div>
              </div>
              <button type="button" class="btn btn-sm btn-secondary" onclick="quickAddPnExpSupplier()" title="Dodaj novog dobavljača" style="padding:0 10px;height:36px;flex-shrink:0;">➕</button>
            </div>
            <div id="pnexp-supplier-match" style="display:none;margin-top:4px;font-size:12px;color:#27ae60;font-weight:600;"></div>
          </div>
          <div class="form-group"><label class="form-label">OIB partnera</label><input type="text" class="form-control" id="pnexp-partner-oib" maxlength="11"></div>
          <div class="form-group"><label class="form-label">Broj računa</label><input type="text" class="form-control" id="pnexp-invoice-number"></div>
          <div class="form-group"><label class="form-label">Datum dospijeća</label><input type="date" class="form-control" id="pnexp-due-date"></div>
        </div>
        <hr style="border:none;border-top:1px solid var(--gray-200);margin:10px 0;">
      </div>'''

    if OLD_R1_FORM in form:
        form = form.replace(OLD_R1_FORM, NEW_R1_FORM)
        print("✅ form.html: R1 polja ažurirana s supplier dropdownom")
    else:
        print("⚠️  form.html: Nije pronađen marker za R1 polja — ručno provjeri")

    # Dodaj JS za supplier dropdown u form.html
    SUPPLIER_JS_FORM = '''
// ═══════════════════════════════════════════════════════════════════
// SUPPLIER DROPDOWN za pn_expense forme (form.html)
// ═══════════════════════════════════════════════════════════════════
let _pnExpSuppliersCache = [];

async function loadPnExpSuppliers() {
  try {
    const res = await fetch('/api/suppliers');
    const d = await res.json();
    _pnExpSuppliersCache = d.suppliers || d || [];
  } catch(e) { _pnExpSuppliersCache = []; }
  return _pnExpSuppliersCache;
}

async function showPnExpSupplierDropdown() {
  if (!_pnExpSuppliersCache.length) await loadPnExpSuppliers();
  filterPnExpSupplierDropdown();
  const el = document.getElementById('pnexp-supplier-dropdown');
  if (el) el.style.display = 'block';
}

function filterPnExpSupplierDropdown() {
  const q = (document.getElementById('pnexp-supplier-search')?.value || '').toLowerCase();
  const list = document.getElementById('pnexp-supplier-dropdown');
  if (!list) return;
  const filtered = _pnExpSuppliersCache.filter(s =>
    !q || s.name.toLowerCase().includes(q) || (s.oib && s.oib.includes(q))
  );
  if (!filtered.length) {
    list.innerHTML = '<div style="padding:10px 14px;color:var(--gray-400);font-size:13px;">Nema rezultata</div>';
  } else {
    list.innerHTML = filtered.map(s =>
      `<div data-sid="${s.id}" style="padding:8px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--gray-100);">
        <div style="font-weight:600;color:var(--navy);">${s.name}</div>
        ${s.oib ? `<div style="font-size:11px;color:var(--gray-400);">OIB: ${s.oib}${s.address ? ' · ' + s.address : ''}</div>` : ''}
      </div>`
    ).join('');
    list.querySelectorAll('[data-sid]').forEach(el => {
      el.addEventListener('mousedown', function(e) {
        e.preventDefault();
        const s = _pnExpSuppliersCache.find(x => String(x.id) === this.dataset.sid);
        if (!s) return;
        selectPnExpSupplier(s);
      });
      el.addEventListener('mouseover', function() { this.style.background = 'var(--accent-light)'; });
      el.addEventListener('mouseout', function() { this.style.background = ''; });
    });
  }
  list.style.display = 'block';
}

function selectPnExpSupplier(s) {
  document.getElementById('pnexp-supplier-search').value = s.name;
  document.getElementById('pnexp-supplier-id').value = s.id;
  document.getElementById('pnexp-partner-name').value = s.name;
  document.getElementById('pnexp-partner-oib').value = s.oib || '';
  document.getElementById('pnexp-supplier-dropdown').style.display = 'none';
  const badge = document.getElementById('pnexp-supplier-match');
  if (badge) { badge.style.display = 'block'; badge.textContent = '\\u2705 ' + s.name; }
}

async function quickAddPnExpSupplier() {
  const name = document.getElementById('pnexp-partner-name')?.value || '';
  const oib = document.getElementById('pnexp-partner-oib')?.value || '';
  const supplierName = prompt('Naziv dobavljača:', name);
  if (!supplierName) return;
  const supplierOib = prompt('OIB (opcionalno):', oib);
  try {
    const res = await fetch('/api/suppliers', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name: supplierName, oib: supplierOib || '', address: '' })
    });
    const d = await res.json();
    if (d.success || d.id) {
      toast('Dobavljač dodan!', 'success');
      await loadPnExpSuppliers();
      const newS = _pnExpSuppliersCache.find(s => s.id == d.id);
      if (newS) selectPnExpSupplier(newS);
    } else { toast(d.error || 'Greška', 'error'); }
  } catch(e) { toast('Greška: ' + e.message, 'error'); }
}

document.addEventListener('click', function(e) {
  const dd = document.getElementById('pnexp-supplier-dropdown');
  const search = document.getElementById('pnexp-supplier-search');
  if (dd && search && !search.contains(e.target) && !dd.contains(e.target)) dd.style.display = 'none';
});

// Patch openPnExpDetail da učita supplier-e i auto-match
const _origOpenPnExpDetail = typeof openPnExpDetail === 'function' ? openPnExpDetail : null;
if (_origOpenPnExpDetail) {
  const _wrapped = openPnExpDetail;
  openPnExpDetail = async function(ocrResult) {
    _wrapped(ocrResult);
    if (_pnExpDocType === 'r1') {
      await loadPnExpSuppliers();
      let match = null;
      const oib = ocrResult.data?.partner_oib || '';
      const pname = ocrResult.data?.partner_name || '';
      if (oib && oib.length >= 10) match = _pnExpSuppliersCache.find(s => s.oib && s.oib.trim() === oib.trim());
      if (!match && pname) match = _pnExpSuppliersCache.find(s => s.name.toLowerCase().trim() === pname.toLowerCase().trim());
      if (match) selectPnExpSupplier(match);
    }
  };
}
'''

    close_script = '</script>\n{% endblock %}'
    if close_script in form:
        form = form.replace(close_script, SUPPLIER_JS_FORM + '\n</script>\n{% endblock %}', 1)
        print("✅ form.html: Supplier dropdown JS dodan")
    else:
        print("⚠️  form.html: Ne mogu pronaći </script>\\n{% endblock %}")

    shutil.copy2(FORM_PATH, FORM_PATH + '.bak2')
    with open(FORM_PATH, 'w', encoding='utf-8') as f:
        f.write(form)
    print(f"📁 Backup: {FORM_PATH}.bak2")


print("\n🎉 Patch završen!")
print("   Oba modala sada imaju searchable supplier dropdown s:")
print("   - Pretraga dobavljača po imenu/OIB-u")
print("   - Auto-match nakon OCR-a (po OIB-u pa po imenu)")
print("   - ➕ gumb za dodavanje novog dobavljača")
print("   - Automatsko popunjavanje Naziv partnera i OIB iz šifrarnika")
