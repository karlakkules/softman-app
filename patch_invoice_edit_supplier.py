#!/usr/bin/env python3
"""
Patch za dodavanje supplier dropdown-a u EDIT modal ulaznih računa.
Pokreni: python3 patch_invoice_edit_supplier.py
"""
import os, sys, shutil

PATH = os.path.join('templates', 'invoice_list.html')
if not os.path.exists(PATH):
    print(f"❌ {PATH} nije pronađen!"); sys.exit(1)

with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

if 'edit-supplier-search' in content:
    print("⚠️  invoice_list.html već ima supplier dropdown u edit modalu — preskačem.")
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════════
# 1. Zamijeni HTML edit modala — dodaj supplier dropdown
# ═══════════════════════════════════════════════════════════════════

OLD_EDIT = """    <div class="modal-body">
      <input type="hidden" id="edit-inv-id">
      <div class="form-row form-row-2" style="margin-bottom:12px;">
        <div class="form-group">
          <label class="form-label">Naziv partnera</label>
          <input type="text" class="form-control" id="edit-partner">
        </div>
        <div class="form-group">
          <label class="form-label">OIB partnera</label>
          <input type="text" class="form-control" id="edit-oib" maxlength="11">
        </div>
      </div>"""

NEW_EDIT = """    <div class="modal-body">
      <input type="hidden" id="edit-inv-id">
      <div class="form-row form-row-2" style="margin-bottom:12px;">
        <div class="form-group">
          <label class="form-label">Naziv partnera</label>
          <input type="text" class="form-control" id="edit-partner">
        </div>
        <div class="form-group">
          <label class="form-label">OIB partnera</label>
          <input type="text" class="form-control" id="edit-oib" maxlength="11">
        </div>
      </div>
      <div class="form-group" style="margin-bottom:12px;">
        <label class="form-label" style="font-size:11px;color:var(--gray-500);margin-bottom:4px;">Dobavljač s liste</label>
        <div style="display:flex;gap:6px;align-items:center;">
          <div style="flex:1;position:relative;">
            <input type="text" class="form-control" id="edit-supplier-search"
              placeholder="Pretraži dobavljača..." style="font-size:13px;" autocomplete="off"
              oninput="filterEditSupplierDropdown()" onfocus="showEditSupplierDropdown()">
            <input type="hidden" id="edit-supplier-id">
            <div id="edit-supplier-dropdown" style="display:none;position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid var(--gray-300);border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,0.15);z-index:99999;max-height:200px;overflow-y:auto;margin-top:2px;"></div>
          </div>
          <button type="button" class="btn btn-sm btn-secondary" onclick="quickAddEditSupplier()" title="Dodaj novog dobavljača" style="padding:0 10px;height:36px;flex-shrink:0;">➕</button>
        </div>
        <div id="edit-supplier-match" style="display:none;margin-top:4px;font-size:12px;color:#27ae60;font-weight:600;"></div>
      </div>"""

if OLD_EDIT in content:
    content = content.replace(OLD_EDIT, NEW_EDIT, 1)
    print("✅ Edit modal HTML ažuriran s supplier dropdownom")
else:
    print("⚠️  Nije pronađen marker za edit modal HTML — ručno provjeri")
    print("   Tražio sam: 'edit-inv-id' + 'Naziv partnera' + 'OIB partnera' blok")

# ═══════════════════════════════════════════════════════════════════
# 2. Dodaj JS funkcije za edit supplier dropdown
# ═══════════════════════════════════════════════════════════════════

EDIT_SUPPLIER_JS = """
// ═══════════════════════════════════════════════════════════════════
// SUPPLIER DROPDOWN za Edit modal ulaznih računa
// ═══════════════════════════════════════════════════════════════════

async function showEditSupplierDropdown() {
  if (!_suppliersCache.length) await loadInvSuppliers();
  filterEditSupplierDropdown();
  const el = document.getElementById('edit-supplier-dropdown');
  if (el) el.style.display = 'block';
}

function filterEditSupplierDropdown() {
  const q = (document.getElementById('edit-supplier-search')?.value || '').toLowerCase();
  const list = document.getElementById('edit-supplier-dropdown');
  if (!list) return;
  const filtered = _suppliersCache.filter(s =>
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
        const s = _suppliersCache.find(x => String(x.id) === this.dataset.sid);
        if (!s) return;
        document.getElementById('edit-supplier-search').value = s.name;
        document.getElementById('edit-supplier-id').value = s.id;
        document.getElementById('edit-partner').value = s.name;
        document.getElementById('edit-oib').value = s.oib || '';
        document.getElementById('edit-supplier-dropdown').style.display = 'none';
        const badge = document.getElementById('edit-supplier-match');
        if (badge) { badge.style.display = 'block'; badge.textContent = '✅ ' + s.name; }
      });
      el.addEventListener('mouseover', function() { this.style.background = 'var(--accent-light)'; });
      el.addEventListener('mouseout', function() { this.style.background = ''; });
    });
  }
  list.style.display = 'block';
}

async function quickAddEditSupplier() {
  const name = document.getElementById('edit-partner')?.value || '';
  const oib = document.getElementById('edit-oib')?.value || '';
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
      await loadInvSuppliers();
      const newS = _suppliersCache.find(s => s.id == d.id);
      if (newS) {
        document.getElementById('edit-supplier-search').value = newS.name;
        document.getElementById('edit-supplier-id').value = newS.id;
        document.getElementById('edit-partner').value = newS.name;
        document.getElementById('edit-oib').value = newS.oib || '';
        const badge = document.getElementById('edit-supplier-match');
        if (badge) { badge.style.display = 'block'; badge.textContent = '✅ ' + newS.name; }
      }
    } else { toast(d.error || 'Greška', 'error'); }
  } catch(e) { toast('Greška: ' + e.message, 'error'); }
}

// Zatvori edit supplier dropdown kad klik van
document.addEventListener('click', function(e) {
  const dd = document.getElementById('edit-supplier-dropdown');
  const search = document.getElementById('edit-supplier-search');
  if (dd && search && !search.contains(e.target) && !dd.contains(e.target)) dd.style.display = 'none';
});

// Patch openEditModal da učita supplier-e i auto-match
const _origOpenEditModal = openEditModal;
openEditModal = async function(el) {
  await _origOpenEditModal(el);
  // Učitaj dobavljače i pokušaj match
  if (!_suppliersCache.length) await loadInvSuppliers();
  const partnerName = document.getElementById('edit-partner')?.value || '';
  const oib = document.getElementById('edit-oib')?.value || '';
  // Reset
  document.getElementById('edit-supplier-search').value = '';
  document.getElementById('edit-supplier-id').value = '';
  const badge = document.getElementById('edit-supplier-match');
  if (badge) badge.style.display = 'none';
  // Auto-match
  let match = null;
  if (oib && oib.length >= 10)
    match = _suppliersCache.find(s => s.oib && s.oib.trim() === oib.trim());
  if (!match && partnerName) {
    const pn = partnerName.toLowerCase().trim();
    match = _suppliersCache.find(s => s.name.toLowerCase().trim() === pn);
  }
  if (match) {
    document.getElementById('edit-supplier-search').value = match.name;
    document.getElementById('edit-supplier-id').value = match.id;
    if (badge) { badge.style.display = 'block'; badge.textContent = '✅ ' + match.name; }
  }
};
"""

# Pronađi </script> na kraju invoice_list.html (zadnji)
# Koristimo isti pattern — umetni PRIJE zadnjeg </script>\n{% endblock %}
close_marker = '</script>\n{% endblock %}'
if close_marker in content:
    content = content.replace(close_marker, EDIT_SUPPLIER_JS + '\n</script>\n{% endblock %}', 1)
    print("✅ Edit supplier dropdown JS dodan")
else:
    print("⚠️  Ne mogu pronaći </script>\\n{% endblock %} marker")

# Backup i zapis
shutil.copy2(PATH, PATH + '.bak')
with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎉 invoice_list.html patchiran!")
print("   Edit modal sada ima searchable supplier dropdown s:")
print("   - Auto-match partnera kad se otvori modal")
print("   - Pretraga po imenu/OIB-u")
print("   - ➕ gumb za dodavanje novog dobavljača")
