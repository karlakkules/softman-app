#!/usr/bin/env python3
"""
Skripta za automatsko patchiranje form.html — dodaje sekciju 
"Troškovi s dokumentima" (pn_expenses) i pripadajući JavaScript.

Pokreni iz root direktorija projekta:
  python3 patch_form.py
"""

import os
import sys

FORM_PATH = os.path.join('templates', 'form.html')

if not os.path.exists(FORM_PATH):
    print(f"❌ Datoteka {FORM_PATH} nije pronađena!")
    print("   Pokreni skriptu iz root direktorija projekta (gdje je app.py)")
    sys.exit(1)

with open(FORM_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already patched
if 'pn-exp-upload-modal' in content:
    print("⚠️  form.html je već patchiran (pn_expenses sekcija postoji).")
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════════
# BLOK 1: HTML sekcija — umetni PRIJE "<!-- ── SECTION: IZVJEŠĆE ──"
# ═══════════════════════════════════════════════════════════════════

HTML_BLOCK = r"""<!-- ── SECTION: TROŠKOVI S DOKUMENTIMA (pn_expenses) ── -->
{% if order %}
<div class="section-divider">
  <span class="section-divider-label">🧾 Troškovi s dokumentima</span>
  <div class="section-divider-line"></div>
</div>
<div class="card" style="margin-bottom:16px;">
  <div class="card-header">
    <div style="display:flex;align-items:center;gap:10px;">
      <span class="card-title">Dokumenti troškova</span>
      <span id="pn-exp-count" style="background:var(--accent-light);color:var(--accent);padding:1px 7px;border-radius:12px;font-size:11px;font-weight:700;">{{ pn_expenses|length if pn_expenses is defined else 0 }}</span>
    </div>
    {% if not is_deleted %}
    <button type="button" class="btn btn-sm btn-secondary" onclick="openPnExpUpload()" title="Dodaj trošak s dokumentom">
      ➕ Dodaj trošak
    </button>
    {% endif %}
  </div>
  <div class="card-body" style="padding:0;">
    <div id="pn-exp-list">
      {% if pn_expenses is defined and pn_expenses %}
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="background:var(--gray-50);font-size:11px;text-transform:uppercase;color:var(--gray-600);font-weight:700;">
            <th style="padding:8px 12px;text-align:left;">Tip</th>
            <th style="padding:8px 12px;text-align:left;">Datum</th>
            <th style="padding:8px 12px;text-align:left;">Kategorija</th>
            <th style="padding:8px 12px;text-align:left;">Opis / Partner</th>
            <th style="padding:8px 12px;text-align:right;">Iznos</th>
            <th style="padding:8px 12px;text-align:center;">Plaćanje</th>
            <th style="padding:8px 12px;text-align:center;width:80px;">Akcije</th>
          </tr>
        </thead>
        <tbody>
          {% for pe in pn_expenses %}
          <tr id="pn-exp-row-{{ pe.id }}" style="border-bottom:1px solid var(--gray-100);">
            <td style="padding:8px 12px;">
              {% if pe.doc_type == 'r1' %}
              <span style="background:#e8f0f7;color:var(--navy);padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;">R1</span>
              {% else %}
              <span style="background:var(--gray-100);color:var(--gray-600);padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;">Račun</span>
              {% endif %}
            </td>
            <td style="padding:8px 12px;font-size:12px;white-space:nowrap;">{{ pe.doc_date|fmt_date or '—' }}</td>
            <td style="padding:8px 12px;font-size:12px;">{{ pe.category_name or '—' }}</td>
            <td style="padding:8px 12px;font-size:12px;">
              {% if pe.doc_type == 'r1' %}
                <span style="font-weight:600;">{{ pe.partner_name or '' }}</span>
                {% if pe.invoice_number %}<span style="color:var(--gray-400);"> · {{ pe.invoice_number }}</span>{% endif %}
              {% else %}
                {{ pe.description or pe.original_filename or '—' }}
              {% endif %}
            </td>
            <td style="padding:8px 12px;text-align:right;font-weight:700;font-size:13px;white-space:nowrap;">{{ '%.2f'|format(pe.amount or 0) }} €</td>
            <td style="padding:8px 12px;text-align:center;font-size:11px;">
              {% if pe.payment_method == 'private' %}💳 Privatno
              {% elif pe.payment_method == 'transfer' %}🏦 Virman
              {% elif pe.payment_method == 'card' %}💳 {{ pe.card_name or '' }} (*{{ pe.card_last4 or '' }})
              {% endif %}
            </td>
            <td style="padding:8px 12px;text-align:center;">
              <div style="display:flex;gap:4px;justify-content:center;">
                {% if pe.stored_path %}
                <a href="/api/pn-expenses/{{ pe.id }}/pdf" target="_blank" class="btn btn-sm btn-secondary" style="width:28px;height:28px;padding:0;display:flex;align-items:center;justify-content:center;font-size:12px;" title="Pregled dokumenta">📄</a>
                {% endif %}
                {% if not is_deleted %}
                <button type="button" class="btn btn-sm" style="width:28px;height:28px;padding:0;display:flex;align-items:center;justify-content:center;background:#fdecea;color:#c0392b;border:1px solid #f5aca6;border-radius:6px;cursor:pointer;font-size:12px;" onclick="deletePnExp({{ pe.id }})" title="Obriši trošak">🗑</button>
                {% endif %}
              </div>
            </td>
          </tr>
          {% endfor %}
        </tbody>
        <tfoot>
          <tr style="background:var(--gray-50);">
            <td colspan="4" style="padding:8px 12px;text-align:right;font-size:12px;font-weight:700;color:var(--gray-600);">Ukupno dokumentirani troškovi:</td>
            <td style="padding:8px 12px;text-align:right;font-weight:700;font-size:14px;color:var(--navy);font-family:'DM Mono',monospace;">{{ '%.2f'|format(pn_expenses|sum(attribute='amount')) }} €</td>
            <td colspan="2"></td>
          </tr>
        </tfoot>
      </table>
      {% else %}
      <div style="text-align:center;padding:24px;color:var(--gray-400);">
        <div style="font-size:24px;margin-bottom:6px;">🧾</div>
        <div style="font-size:13px;">Nema troškova s dokumentima za ovaj nalog.</div>
        {% if not is_deleted %}<div style="font-size:12px;margin-top:4px;">Koristite gumb "➕ Dodaj trošak" ili dodajte troškove iz modula Putni nalozi.</div>{% endif %}
      </div>
      {% endif %}
    </div>
  </div>
</div>

<!-- Upload troška za ovaj PN -->
<div class="modal-overlay" id="pn-exp-upload-modal">
  <div class="modal" style="width:560px;">
    <div class="modal-header">
      <span class="modal-title">🧾 Dodaj trošak — PN {{ order.auto_id if order else '' }}</span>
      <button class="btn btn-ghost btn-icon" onclick="closePnExpUpload()">✕</button>
    </div>
    <div class="modal-body">
      <div style="display:flex;gap:8px;margin-bottom:16px;">
        <label style="flex:1;display:flex;align-items:center;gap:8px;padding:10px 14px;border:2px solid var(--gray-200);border-radius:8px;cursor:pointer;background:white;font-weight:600;font-size:13px;color:var(--gray-600);" id="pnexp-type-r1-label">
          <input type="radio" name="pnexp-doc-type" value="r1" id="pnexp-type-r1" onchange="onPnExpTypeChange()"> R1 račun
        </label>
        <label style="flex:1;display:flex;align-items:center;gap:8px;padding:10px 14px;border:2px solid var(--accent);border-radius:8px;cursor:pointer;background:var(--accent-light);font-weight:600;font-size:13px;color:var(--navy);" id="pnexp-type-receipt-label">
          <input type="radio" name="pnexp-doc-type" value="receipt" id="pnexp-type-receipt" checked onchange="onPnExpTypeChange()"> Običan račun/potvrda
        </label>
      </div>
      <div id="pnexp-drop-zone" style="border:2px dashed var(--accent);border-radius:10px;padding:32px;text-align:center;cursor:pointer;background:var(--accent-light);" onclick="document.getElementById('pnexp-file-input').click()" ondragover="event.preventDefault();this.style.background='#d0e4f7';" ondragleave="this.style.background='var(--accent-light)';" ondrop="handlePnExpDrop(event)">
        <div style="font-size:32px;margin-bottom:6px;">📄</div>
        <div style="font-size:13px;color:var(--navy);font-weight:600;">Kliknite ili povucite datoteku</div>
        <div style="font-size:11px;color:var(--gray-500);margin-top:4px;">PDF, JPG, PNG</div>
      </div>
      <input type="file" id="pnexp-file-input" accept=".pdf,.jpg,.jpeg,.png,.tiff,.tif" style="display:none;" onchange="handlePnExpFile(this.files[0])">
      <div id="pnexp-ocr-progress" style="display:none;text-align:center;padding:20px;">
        <div style="font-size:22px;margin-bottom:6px;">⏳</div>
        <div style="font-size:13px;color:var(--navy);">OCR obrada...</div>
      </div>
    </div>
  </div>
</div>

<!-- Detaljna forma za trošak ovog PN-a -->
<div class="modal-overlay" id="pn-exp-detail-modal" style="z-index:1002;">
  <div class="modal" style="width:620px;max-height:85vh;display:flex;flex-direction:column;">
    <div class="modal-header">
      <span class="modal-title">🧾 Detalji troška — PN {{ order.auto_id if order else '' }}</span>
      <button class="btn btn-ghost btn-icon" onclick="closePnExpDetail()">✕</button>
    </div>
    <div class="modal-body" style="overflow-y:auto;">
      <input type="hidden" id="pnexp-temp-filename">
      <input type="hidden" id="pnexp-original-filename">
      <input type="hidden" id="pnexp-ocr-raw">
      <div id="pnexp-r1-fields" style="display:none;">
        <div style="background:#e8f0f7;border:1px solid #aac4db;border-radius:6px;padding:8px 12px;margin-bottom:12px;font-size:12px;color:var(--navy);font-weight:600;">📋 R1 račun — vidljivo i u modulu Ulazni računi</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">
          <div class="form-group" style="grid-column:1/-1;"><label class="form-label">Naziv partnera</label><input type="text" class="form-control" id="pnexp-partner-name"></div>
          <div class="form-group"><label class="form-label">OIB partnera</label><input type="text" class="form-control" id="pnexp-partner-oib" maxlength="11"></div>
          <div class="form-group"><label class="form-label">Broj računa</label><input type="text" class="form-control" id="pnexp-invoice-number"></div>
          <div class="form-group"><label class="form-label">Datum dospijeća</label><input type="date" class="form-control" id="pnexp-due-date"></div>
        </div>
        <hr style="border:none;border-top:1px solid var(--gray-200);margin:10px 0;">
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
        <div class="form-group"><label class="form-label">Kategorija</label><select class="form-control" id="pnexp-category"><option value="">— odaberi —</option>{% for cat in categories %}<option value="{{ cat.id }}">{{ cat.name }}</option>{% endfor %}</select></div>
        <div class="form-group"><label class="form-label">Iznos (€) *</label><input type="number" class="form-control" id="pnexp-amount" step="0.01" style="font-weight:700;"></div>
        <div class="form-group"><label class="form-label">Datum dokumenta</label><input type="date" class="form-control" id="pnexp-doc-date"></div>
        <div class="form-group"><label class="form-label">Opis</label><input type="text" class="form-control" id="pnexp-description" placeholder="Gorivo, cestarina..."></div>
      </div>
      <div style="margin-top:10px;"><label class="form-label" style="font-weight:700;">💳 Način plaćanja</label><select class="form-control" id="pnexp-payment-method"><option value="private">Privatna kartica/gotovina</option><option value="transfer">Virman/transakcijski</option>{% for card in bank_cards %}<option value="card:{{ card.id }}">{{ card.card_name }} (*{{ card.last4 }})</option>{% endfor %}</select></div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closePnExpDetail()">Odustani</button>
      <button class="btn btn-primary" onclick="savePnExp()">💾 Spremi</button>
    </div>
  </div>
</div>
{% endif %}

"""

# ═══════════════════════════════════════════════════════════════════
# BLOK 2: JavaScript — umetni PRIJE </script>
# ═══════════════════════════════════════════════════════════════════

JS_BLOCK = r"""
// ═══════════════════════════════════════════════════════════════════
// PN EXPENSES — Troškovi s dokumentima (form.html)
// ═══════════════════════════════════════════════════════════════════

let _pnExpDocType = 'receipt';

function onPnExpTypeChange() {
  const r1 = document.getElementById('pnexp-type-r1').checked;
  _pnExpDocType = r1 ? 'r1' : 'receipt';
  const r1Label = document.getElementById('pnexp-type-r1-label');
  const recLabel = document.getElementById('pnexp-type-receipt-label');
  if (r1) {
    r1Label.style.borderColor = 'var(--accent)'; r1Label.style.background = 'var(--accent-light)'; r1Label.style.color = 'var(--navy)';
    recLabel.style.borderColor = 'var(--gray-200)'; recLabel.style.background = 'white'; recLabel.style.color = 'var(--gray-600)';
  } else {
    recLabel.style.borderColor = 'var(--accent)'; recLabel.style.background = 'var(--accent-light)'; recLabel.style.color = 'var(--navy)';
    r1Label.style.borderColor = 'var(--gray-200)'; r1Label.style.background = 'white'; r1Label.style.color = 'var(--gray-600)';
  }
}

function openPnExpUpload() {
  _pnExpDocType = 'receipt';
  const el = document.getElementById('pnexp-type-receipt');
  if (el) el.checked = true;
  onPnExpTypeChange();
  document.getElementById('pnexp-drop-zone').style.display = '';
  document.getElementById('pnexp-ocr-progress').style.display = 'none';
  document.getElementById('pnexp-file-input').value = '';
  document.getElementById('pn-exp-upload-modal').classList.add('open');
}
function closePnExpUpload() { document.getElementById('pn-exp-upload-modal').classList.remove('open'); }

function handlePnExpDrop(e) {
  e.preventDefault();
  document.getElementById('pnexp-drop-zone').style.background = 'var(--accent-light)';
  if (e.dataTransfer.files.length) handlePnExpFile(e.dataTransfer.files[0]);
}

async function handlePnExpFile(file) {
  if (!file) return;
  document.getElementById('pnexp-drop-zone').style.display = 'none';
  document.getElementById('pnexp-ocr-progress').style.display = '';
  const fd = new FormData();
  fd.append('file', file);
  fd.append('doc_type', _pnExpDocType);
  try {
    const res = await fetch('/api/pn-expenses/upload', { method: 'POST', body: fd });
    const d = await res.json();
    if (!d.success) { toast(d.error || 'OCR greška', 'error'); closePnExpUpload(); return; }
    closePnExpUpload();
    openPnExpDetail(d);
  } catch(e) { toast('Greška: ' + e.message, 'error'); closePnExpUpload(); }
}

function openPnExpDetail(ocrResult) {
  document.getElementById('pnexp-temp-filename').value = ocrResult.temp_filename || '';
  document.getElementById('pnexp-original-filename').value = ocrResult.original_filename || '';
  document.getElementById('pnexp-ocr-raw').value = ocrResult.data?.ocr_raw || '';
  if (_pnExpDocType === 'r1') {
    document.getElementById('pnexp-r1-fields').style.display = '';
    document.getElementById('pnexp-partner-name').value = ocrResult.data?.partner_name || '';
    document.getElementById('pnexp-partner-oib').value = ocrResult.data?.partner_oib || '';
    document.getElementById('pnexp-invoice-number').value = ocrResult.data?.invoice_number || '';
    document.getElementById('pnexp-due-date').value = ocrResult.data?.due_date || '';
  } else {
    document.getElementById('pnexp-r1-fields').style.display = 'none';
  }
  document.getElementById('pnexp-amount').value = ocrResult.data?.amount_total || '';
  document.getElementById('pnexp-description').value = '';
  document.getElementById('pnexp-category').value = '';
  document.getElementById('pnexp-payment-method').value = 'private';
  let docDateIso = '';
  const rawDate = ocrResult.data?.invoice_date || '';
  if (rawDate) {
    try {
      const parts = rawDate.replace(/\./g, ' ').trim().split(/\s+/);
      if (parts.length >= 3) docDateIso = parts[2] + '-' + parts[1].padStart(2,'0') + '-' + parts[0].padStart(2,'0');
    } catch(e) {}
  }
  document.getElementById('pnexp-doc-date').value = docDateIso;
  document.getElementById('pn-exp-detail-modal').classList.add('open');
}
function closePnExpDetail() { document.getElementById('pn-exp-detail-modal').classList.remove('open'); }

async function savePnExp() {
  const amount = parseFloat(document.getElementById('pnexp-amount').value);
  if (!amount || amount <= 0) { toast('Unesite iznos!', 'error'); return; }
  const orderId = document.getElementById('order-id')?.value;
  if (!orderId) { toast('Nalog mora biti spremljen prije dodavanja troškova!', 'error'); return; }
  const paymentVal = document.getElementById('pnexp-payment-method').value;
  let paymentMethod = paymentVal, bankCardId = null;
  if (paymentVal.startsWith('card:')) { paymentMethod = 'card'; bankCardId = parseInt(paymentVal.split(':')[1]); }
  const payload = {
    doc_type: _pnExpDocType, travel_order_id: parseInt(orderId),
    temp_filename: document.getElementById('pnexp-temp-filename').value,
    original_filename: document.getElementById('pnexp-original-filename').value,
    ocr_raw: document.getElementById('pnexp-ocr-raw').value,
    category_id: document.getElementById('pnexp-category').value || null,
    description: document.getElementById('pnexp-description').value.trim(),
    amount: amount, doc_date: document.getElementById('pnexp-doc-date').value,
    payment_method: paymentMethod, bank_card_id: bankCardId,
  };
  if (_pnExpDocType === 'r1') {
    payload.partner_name = document.getElementById('pnexp-partner-name').value.trim();
    payload.partner_oib = document.getElementById('pnexp-partner-oib').value.trim();
    payload.invoice_number = document.getElementById('pnexp-invoice-number').value.trim();
    payload.due_date = document.getElementById('pnexp-due-date').value;
  }
  try {
    const res = await fetch('/api/pn-expenses', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
    const d = await res.json();
    if (d.success) { toast('Trošak dodan!', 'success'); closePnExpDetail(); setTimeout(() => location.reload(), 600); }
    else { toast(d.error || 'Greška', 'error'); }
  } catch(e) { toast('Greška: ' + e.message, 'error'); }
}

async function deletePnExp(expId) {
  if (!confirm('Obrisati ovaj trošak s dokumentom?')) return;
  try {
    const res = await fetch('/api/pn-expenses/' + expId, { method: 'DELETE' });
    if (res.ok) { toast('Trošak obrisan.', 'success'); const row = document.getElementById('pn-exp-row-' + expId); if (row) row.style.display = 'none'; }
    else { toast('Greška pri brisanju', 'error'); }
  } catch(e) { toast('Greška: ' + e.message, 'error'); }
}

"""

# ═══════════════════════════════════════════════════════════════════
# PRIMIJENI PATCH
# ═══════════════════════════════════════════════════════════════════

# 1. Insert HTML before izvješće section
marker1 = '<!-- ── SECTION: IZVJEŠĆE ── -->'
if marker1 not in content:
    # Try alternate marker
    marker1 = '<!-- ── SECTION: IZVJEŠĆE -->'
    if marker1 not in content:
        print(f"❌ Marker '{marker1}' nije pronađen u form.html!")
        sys.exit(1)

content = content.replace(marker1, HTML_BLOCK + marker1)
print(f"✅ HTML sekcija umetnuta ({len(HTML_BLOCK)} znakova)")

# 2. Insert JS before </script>{% endblock %}
marker2 = '</script>\n{% endblock %}'
if marker2 not in content:
    # Try without newline
    marker2 = '</script>\r\n{% endblock %}'
    if marker2 not in content:
        print("❌ Marker '</script>\\n{% endblock %}' nije pronađen!")
        sys.exit(1)

content = content.replace(marker2, JS_BLOCK + '\n</script>\n{% endblock %}', 1)
print(f"✅ JavaScript blok umetnut ({len(JS_BLOCK)} znakova)")

# 3. Backup i zapis
backup_path = FORM_PATH + '.bak'
import shutil
shutil.copy2(FORM_PATH, backup_path)
print(f"📁 Backup: {backup_path}")

with open(FORM_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎉 form.html uspješno patchiran! ({len(content)} znakova)")
print(f"   Dodana sekcija 'Troškovi s dokumentima' s upload/OCR/delete funkcionalnosti.")
