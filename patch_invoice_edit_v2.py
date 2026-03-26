#!/usr/bin/env python3
"""
Robustan patch za supplier dropdown u edit modalu ulaznih računa.
Traži edit modal po ID-u 'edit-inv-id' i ubacuje supplier dropdown.
Pokreni: python3 patch_invoice_edit_v2.py
"""
import os, sys, shutil, re

PATH = os.path.join('templates', 'invoice_list.html')
if not os.path.exists(PATH):
    print(f"❌ {PATH} nije pronađen!"); sys.exit(1)

with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

if 'edit-supplier-search' in content:
    print("⚠️  Supplier dropdown u edit modalu već postoji — preskačem.")
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════════
# 1. PRONAĐI I ZAMIJENI edit modal body — ubaci supplier dropdown
#    Tražimo: </div> nakon edit-oib, prije Broj računa
# ═══════════════════════════════════════════════════════════════════

# Tražimo pattern: zatvaranje div-a za OIB partnera row, pa odmah Broj računa row
# Ovo je robusnije od traženja točnog whitespace-a
pattern = re.compile(
    r'(id="edit-oib"[^>]*>)\s*'           # edit-oib input
    r'(</div>\s*</div>\s*)'                # zatvaranje form-group i form-row
    r'(\s*<div class="form-row form-row-2"[^>]*>\s*<div class="form-group">\s*<label[^>]*>Broj ra)',
    re.DOTALL
)

SUPPLIER_HTML = r"""\1\2
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
      </div>
\3"""

match = pattern.search(content)
if match:
    content = pattern.sub(SUPPLIER_HTML, content, count=1)
    print("✅ Supplier dropdown HTML umetnut u edit modal")
else:
    # Fallback: traži jednostavniji marker
    # Traži "edit-oib" i onda dodaj blok NAKON zatvaranja tog form-row-2
    marker_oib = 'id="edit-oib"'
    marker_broj = '>Broj ra'  # Broj računa label
    
    oib_pos = content.find(marker_oib)
    broj_pos = content.find(marker_broj, oib_pos) if oib_pos >= 0 else -1
    
    if oib_pos >= 0 and broj_pos >= 0:
        # Nađi </div> koji zatvara form-row-2 (između oib i broj)
        # Traži zadnji </div> prije "Broj ra"
        segment = content[oib_pos:broj_pos]
        # Pronađi poziciju zadnjeg zatvaranja div-a u tom segmentu
        last_close_div = segment.rfind('</div>')
        if last_close_div >= 0:
            insert_pos = oib_pos + last_close_div + len('</div>')
            supplier_block = """
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
      </div>
"""
            content = content[:insert_pos] + supplier_block + content[insert_pos:]
            print("✅ Supplier dropdown HTML umetnut u edit modal (fallback metoda)")
        else:
            print("❌ Ne mogu pronaći poziciju za umetanje — ručno dodaj supplier dropdown")
    else:
        print(f"❌ Markeri nisu pronađeni (oib_pos={oib_pos}, broj_pos={broj_pos})")

# ═══════════════════════════════════════════════════════════════════
# 2. DODAJ JS funkcije za edit supplier dropdown
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
        ${s.oib ? `<div style="font-size:11px;color:var(--gray-400);">OIB: ${s.oib}${s.address ? ' \\u00b7 ' + s.address : ''}</div>` : ''}
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
        if (badge) { badge.style.display = 'block'; badge.textContent = '\\u2705 ' + s.name; }
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
        if (badge) { badge.style.display = 'block'; badge.textContent = '\\u2705 ' + newS.name; }
      }
    } else { toast(d.error || 'Greška', 'error'); }
  } catch(e) { toast('Greška: ' + e.message, 'error'); }
}

document.addEventListener('click', function(e) {
  const dd = document.getElementById('edit-supplier-dropdown');
  const search = document.getElementById('edit-supplier-search');
  if (dd && search && !search.contains(e.target) && !dd.contains(e.target)) dd.style.display = 'none';
});

// Patch openEditModal — auto-match supplier kad se otvori
const _origOpenEditModal = openEditModal;
openEditModal = async function(el) {
  await _origOpenEditModal(el);
  if (!_suppliersCache.length) await loadInvSuppliers();
  const partnerName = document.getElementById('edit-partner')?.value || '';
  const oib = document.getElementById('edit-oib')?.value || '';
  const searchEl = document.getElementById('edit-supplier-search');
  const idEl = document.getElementById('edit-supplier-id');
  const badge = document.getElementById('edit-supplier-match');
  if (searchEl) searchEl.value = '';
  if (idEl) idEl.value = '';
  if (badge) badge.style.display = 'none';
  let match = null;
  if (oib && oib.length >= 10)
    match = _suppliersCache.find(s => s.oib && s.oib.trim() === oib.trim());
  if (!match && partnerName) {
    const pn = partnerName.toLowerCase().trim();
    match = _suppliersCache.find(s => s.name.toLowerCase().trim() === pn);
  }
  if (match) {
    if (searchEl) searchEl.value = match.name;
    if (idEl) idEl.value = match.id;
    if (badge) { badge.style.display = 'block'; badge.textContent = '\\u2705 ' + match.name; }
  }
};
"""

# Pronađi zadnji </script> prije {% endblock %}
close_marker = '</script>\n{% endblock %}'
if close_marker in content:
    content = content.replace(close_marker, EDIT_SUPPLIER_JS + '\n</script>\n{% endblock %}', 1)
    print("✅ Edit supplier dropdown JS dodan")
else:
    # Try \r\n
    close_marker2 = '</script>\r\n{% endblock %}'
    if close_marker2 in content:
        content = content.replace(close_marker2, EDIT_SUPPLIER_JS + '\n</script>\n{% endblock %}', 1)
        print("✅ Edit supplier dropdown JS dodan (CRLF)")
    else:
        # Last resort: find </script> followed by {% endblock %} with any whitespace
        pattern_close = re.compile(r'(</script>)\s*({% endblock %})')
        if pattern_close.search(content):
            content = pattern_close.sub(EDIT_SUPPLIER_JS + r'\n\1\n\2', content, count=1)
            print("✅ Edit supplier dropdown JS dodan (regex)")
        else:
            print("❌ Ne mogu pronaći </script>{% endblock %} marker za JS umetanje")

# Backup i zapis
shutil.copy2(PATH, PATH + '.bak_edit')
with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎉 Done! Edit modal u invoice_list.html sada ima supplier dropdown.")
print("   Otvori račun za uređivanje → vidjet ćeš 'Dobavljač s liste' dropdown.")
