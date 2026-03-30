#!/usr/bin/env python3
"""
Patch v3 za templates/invoice_list.html — primijeni na TRENUTNU lokalnu verziju.
Rješava:
  1. Filteri u jednom redu (flex-wrap:nowrap, fiksne širine)
  2. Šira kolona Broj računa
  3. Uklanja kolonu Korisnik, dodaje ℹ gumb u Akcije
  4. (sadrži i prethodne fixove: Veza PN kolona, fmt_date, stisnutije kolone)

Pokreni: python3 patch_invoice_list_v3.py
"""
import shutil, os

TARGET = os.path.join('templates', 'invoice_list.html')
BACKUP = TARGET + '.bak_v3'

if not os.path.exists(TARGET):
    print(f"❌ Nije pronađen: {TARGET}"); exit(1)

shutil.copy2(TARGET, BACKUP)
print(f"✅ Backup: {BACKUP}")

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

fixes = 0

# ═══════════════════════════════════════════════════════════════════════════
# FIX 1: Filteri — jedan red, bez wrapa, auto širine
# ═══════════════════════════════════════════════════════════════════════════
OLD_FILTER_DIV = '    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">'
NEW_FILTER_DIV = '    <div style="display:flex;gap:6px;flex-wrap:nowrap;align-items:center;">'
if OLD_FILTER_DIV in content:
    content = content.replace(OLD_FILTER_DIV, NEW_FILTER_DIV, 1); fixes += 1
    print("✅ FIX 1a: flex-wrap:nowrap na filter div")
else:
    print("⚠️  FIX 1a nije pronađen")

# Search input malo uži da ostane mjesta za selecte
OLD_SEARCH = '      <input type="text" id="inv-search" class="form-control" placeholder="Pretraži..." style="width:180px;" oninput="filterInv()">'
NEW_SEARCH = '      <input type="text" id="inv-search" class="form-control" placeholder="Pretraži..." style="width:150px;flex-shrink:0;" oninput="filterInv()">'
if OLD_SEARCH in content:
    content = content.replace(OLD_SEARCH, NEW_SEARCH, 1); fixes += 1
    print("✅ FIX 1b: Search input width")

# Selecti — auto width da stane tekst, flex-shrink:0
OLD_PAID_SEL = '      <select id="inv-paid" class="form-control" style="width:130px;" onchange="filterInv()">'
NEW_PAID_SEL = '      <select id="inv-paid" class="form-control" style="width:148px;flex-shrink:0;" onchange="filterInv()">'
if OLD_PAID_SEL in content:
    content = content.replace(OLD_PAID_SEL, NEW_PAID_SEL, 1); fixes += 1
    print("✅ FIX 1c: Plaćenost select")

OLD_LIQ_SEL = '      <select id="inv-liq" class="form-control" style="width:140px;" onchange="filterInv()">'
NEW_LIQ_SEL = '      <select id="inv-liq" class="form-control" style="width:152px;flex-shrink:0;" onchange="filterInv()">'
if OLD_LIQ_SEL in content:
    content = content.replace(OLD_LIQ_SEL, NEW_LIQ_SEL, 1); fixes += 1
    print("✅ FIX 1d: Likvidacija select")

OLD_PAY_SEL = '      <select id="inv-payment" class="form-control" style="width:160px;" onchange="filterInv()">'
NEW_PAY_SEL = '      <select id="inv-payment" class="form-control" style="width:176px;flex-shrink:0;" onchange="filterInv()">'
if OLD_PAY_SEL in content:
    content = content.replace(OLD_PAY_SEL, NEW_PAY_SEL, 1); fixes += 1
    print("✅ FIX 1e: Način plaćanja select")

# ═══════════════════════════════════════════════════════════════════════════
# FIX 2 + 3 + Veza PN: Cijeli <thead> blok — zamijeni odjednom
# ═══════════════════════════════════════════════════════════════════════════
OLD_THEAD = '''      <thead>
        <tr>
          <th style="width:32px;"></th>
          <th style="width:120px;">Broj računa</th>
          <th>Partner</th>
          <th style="width:95px;">OIB</th>
          <th style="text-align:right;width:90px;">Iznos</th>
          <th style="width:88px;">Datum</th>
          <th style="width:88px;">Dospijeće</th>
          <th style="text-align:center;width:72px;">Plaćeno</th>
          <th style="text-align:center;width:82px;">Likvidirano</th>
          <th style="width:32px;text-align:center;" title="Napomena">💬</th>
          <th style="width:75px;">Korisnik</th>
          <th style="width:100px;">Akcije</th>
        </tr>
      </thead>'''

NEW_THEAD = '''      <thead>
        <tr>
          <th style="width:28px;"></th>
          <th style="width:136px;">Broj računa</th>
          <th style="min-width:150px;">Partner</th>
          <th style="width:90px;">OIB</th>
          <th style="text-align:right;width:80px;">Iznos</th>
          <th style="width:82px;">Datum</th>
          <th style="width:82px;">Dospijeće</th>
          <th style="text-align:center;width:68px;">Veza PN</th>
          <th style="text-align:center;width:62px;">Plaćeno</th>
          <th style="text-align:center;width:74px;">Likvidirano</th>
          <th style="width:28px;text-align:center;" title="Napomena">💬</th>
          <th style="width:96px;">Akcije</th>
        </tr>
      </thead>'''

if OLD_THEAD in content:
    content = content.replace(OLD_THEAD, NEW_THEAD, 1); fixes += 1
    print("✅ FIX 2+3+PN: Thead zamijenjen (Korisnik uklonjen, Veza PN dodan, Broj računa širi)")
else:
    print("⚠️  Thead block nije pronađen")

# ═══════════════════════════════════════════════════════════════════════════
# FIX 4: tbody redovi — dodaj Veza PN td, ukloni Korisnik td, dodaj ℹ u Akcije
# Radi se u nekoliko koraka na specifičnim patternima
# ═══════════════════════════════════════════════════════════════════════════

# FIX 4a: Datum — dodaj fmt_date filter
OLD_DATE = "          <td style=\"font-size:12px;white-space:nowrap;\">{{ inv.invoice_date or '—' }}</td>"
NEW_DATE = "          <td style=\"font-size:12px;white-space:nowrap;\">{{ inv.invoice_date|fmt_date or '—' }}</td>"
if OLD_DATE in content:
    content = content.replace(OLD_DATE, NEW_DATE, 1); fixes += 1
    print("✅ FIX 4a: invoice_date fmt_date")

# FIX 4b: Dospijeće — dodaj Veza PN td odmah iza, dodaj fmt_date
OLD_DUE = "          <td style=\"font-size:12px;white-space:nowrap;\">{{ inv.due_date or '—' }}</td>\n          <td style=\"text-align:center;\">"
NEW_DUE = """          <td style="font-size:12px;white-space:nowrap;">{{ inv.due_date|fmt_date or '—' }}</td>
          <td style="font-size:12px;text-align:center;">
            {% if inv.pn_auto_id %}
            <a href="/orders/{{ inv.pn_order_id }}/edit"
               style="color:var(--accent);font-weight:700;text-decoration:none;font-family:'DM Mono',monospace;"
               title="Otvori PN {{ inv.pn_auto_id }}"
               onclick="event.stopPropagation();">{{ inv.pn_auto_id }}</a>
            {% else %}<span style="color:var(--gray-300);">—</span>{% endif %}
          </td>
          <td style="text-align:center;">"""
if OLD_DUE in content:
    content = content.replace(OLD_DUE, NEW_DUE, 1); fixes += 1
    print("✅ FIX 4b: Veza PN td + due_date fmt_date")
else:
    print("⚠️  FIX 4b: due_date+Veza PN pattern nije pronađen")

# FIX 4c: paid_at tooltip — fmt_date
OLD_PAID_TITLE = 'title="Uredi podatke plaćanja · {{ inv.paid_at }}{% if inv.paid_card_last4 %} · {{ inv.paid_card_last4 }}{% endif %}"'
NEW_PAID_TITLE = 'title="Uredi podatke plaćanja · {{ inv.paid_at|fmt_date }}{% if inv.paid_card_last4 %} · {{ inv.paid_card_last4 }}{% endif %}"'
if OLD_PAID_TITLE in content:
    content = content.replace(OLD_PAID_TITLE, NEW_PAID_TITLE); fixes += 1
    print("✅ FIX 4c: paid_at fmt_date u tooltip")

OLD_SPAN_TITLE = 'title="{{ inv.paid_at }}{% if inv.paid_card_last4 %} · {{ inv.paid_card_last4 }}{% endif %}"'
NEW_SPAN_TITLE = 'title="{{ inv.paid_at|fmt_date }}{% if inv.paid_card_last4 %} · {{ inv.paid_card_last4 }}{% endif %}"'
if OLD_SPAN_TITLE in content:
    content = content.replace(OLD_SPAN_TITLE, NEW_SPAN_TITLE); fixes += 1
    print("✅ FIX 4d: paid_at fmt_date u span tooltip")

# FIX 4e: Ukloni <td> Korisnik, dodaj ℹ gumb u Akcije td
OLD_USER_AND_ACTIONS = '''          <td style="font-size:12px;color:var(--gray-500);white-space:nowrap;">
            {{ inv.created_by_username or '—' }}
          </td>
          <td>
            <div style="display:flex;gap:4px;align-items:center;">
              {% if inv.stored_path or inv.liquidated_pdf_path %}
              <a href="/invoices/{{ inv.id }}/pdf" target="_blank"
                class="btn btn-sm btn-secondary"
                style="width:30px;height:30px;padding:0;display:flex;align-items:center;justify-content:center;"
                title="{{ 'Likvidirani PDF' if inv.is_liquidated else 'Originalni dokument' }}">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M3 1h7l3 3v10a1 1 0 01-1 1H3a1 1 0 01-1-1V2a1 1 0 011-1z" fill="#e74c3c" stroke="#c0392b" stroke-width="0.5"/>
                  <path d="M10 1l3 3h-3V1z" fill="#c0392b"/>
                  <text x="3.5" y="11.5" font-family="Arial" font-size="4.5" font-weight="bold" fill="white">PDF</text>
                </svg>
              </a>
              {% endif %}
              {% if current_user.get('is_admin') or current_user.get('can_edit_invoices') %}
              {% if not inv.is_liquidated or current_user.get('is_admin') or current_user.get('can_edit_invoices_liquidated') %}
              <button class="btn btn-sm btn-secondary"
                style="width:30px;height:30px;padding:0;display:flex;align-items:center;justify-content:center;font-size:16px;"
                onclick="openEditModal(this)"
                title="Uredi podatke">✏️</button>
              {% else %}
              <button class="btn btn-sm btn-secondary"
                style="width:30px;height:30px;padding:0;display:flex;align-items:center;justify-content:center;font-size:16px;opacity:0.3;cursor:not-allowed;"
                disabled title="Račun je likvidiran — nemate pravo uređivanja">✏️</button>
              {% endif %}
              <button style="width:30px;height:30px;padding:0;display:flex;align-items:center;justify-content:center;background:#fdecea;color:#c0392b;border:1px solid #f5aca6;border-radius:6px;cursor:pointer;"
                onclick="deleteInv({{ inv.id }}, '{{ inv.partner_name }}')"
                title="Obriši račun">🗑</button>
              {% endif %}
            </div>
          </td>'''

NEW_ACTIONS = '''          <td>
            <div style="display:flex;gap:4px;align-items:center;">
              {% if inv.stored_path or inv.liquidated_pdf_path %}
              <a href="/invoices/{{ inv.id }}/pdf" target="_blank"
                class="btn btn-sm btn-secondary"
                style="width:28px;height:28px;padding:0;display:flex;align-items:center;justify-content:center;"
                title="{{ 'Likvidirani PDF' if inv.is_liquidated else 'Originalni dokument' }}">
                <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                  <path d="M3 1h7l3 3v10a1 1 0 01-1 1H3a1 1 0 01-1-1V2a1 1 0 011-1z" fill="#e74c3c" stroke="#c0392b" stroke-width="0.5"/>
                  <path d="M10 1l3 3h-3V1z" fill="#c0392b"/>
                  <text x="3.5" y="11.5" font-family="Arial" font-size="4.5" font-weight="bold" fill="white">PDF</text>
                </svg>
              </a>
              {% endif %}
              {% if current_user.get('is_admin') or current_user.get('can_edit_invoices') %}
              {% if not inv.is_liquidated or current_user.get('is_admin') or current_user.get('can_edit_invoices_liquidated') %}
              <button class="btn btn-sm btn-secondary"
                style="width:28px;height:28px;padding:0;display:flex;align-items:center;justify-content:center;font-size:15px;"
                onclick="openEditModal(this)"
                title="Uredi podatke">✏️</button>
              {% else %}
              <button class="btn btn-sm btn-secondary"
                style="width:28px;height:28px;padding:0;display:flex;align-items:center;justify-content:center;font-size:15px;opacity:0.3;cursor:not-allowed;"
                disabled title="Račun je likvidiran — nemate pravo uređivanja">✏️</button>
              {% endif %}
              <button style="width:28px;height:28px;padding:0;display:flex;align-items:center;justify-content:center;background:#e8f0f7;color:#1a3a5c;border:1px solid #aac4db;border-radius:6px;cursor:pointer;font-size:13px;font-weight:700;"
                onclick="openInfoPopup({{ inv.id }}, {{ inv | tojson }})"
                title="Info · Korisnik: {{ inv.created_by_username }}{{ ' · Plaćeno: ' + inv.paid_at|fmt_date if inv.paid_at else '' }}{{ ' · ' + inv.paid_card_last4 if inv.paid_card_last4 else '' }}">ℹ</button>
              <button style="width:28px;height:28px;padding:0;display:flex;align-items:center;justify-content:center;background:#fdecea;color:#c0392b;border:1px solid #f5aca6;border-radius:6px;cursor:pointer;"
                onclick="deleteInv({{ inv.id }}, '{{ inv.partner_name }}')"
                title="Obriši račun">🗑</button>
              {% endif %}
            </div>
          </td>'''

if OLD_USER_AND_ACTIONS in content:
    content = content.replace(OLD_USER_AND_ACTIONS, NEW_ACTIONS, 1); fixes += 1
    print("✅ FIX 4e: Korisnik td uklonjen, ℹ gumb dodan u Akcije")
else:
    print("⚠️  FIX 4e: User+Actions pattern nije pronađen")

# FIX 4f: colspan empty state row — prilagodi na 11 (uklonjena 1 kolona Korisnik)
OLD_COLSPAN = 'colspan="12"'
NEW_COLSPAN = 'colspan="11"'
if OLD_COLSPAN in content:
    content = content.replace(OLD_COLSPAN, NEW_COLSPAN, 1); fixes += 1
    print("✅ FIX 4f: colspan prilagođen na 11")

# ═══════════════════════════════════════════════════════════════════════════
# FIX 5: Dodaj openInfoPopup() JavaScript funkciju (prije </script>)
# ═══════════════════════════════════════════════════════════════════════════
INFO_POPUP_JS = '''
// ── Info popup (zamjena za Korisnik kolonu) ─────────────────────────────────
function openInfoPopup(id, inv) {
  const paidAt  = inv.paid_at  ? inv.paid_at.substring(0,10).split('-').reverse().join('.') + '.' : '—';
  const createdAt = inv.created_at ? inv.created_at.substring(0,10).split('-').reverse().join('.') + '.' : '—';
  const payMethod = inv.paid_card_last4
    ? 'Kartica *' + inv.paid_card_last4
    : (inv.is_paid ? 'Plaćeno (gotovina/privatno)' : 'Nije plaćeno');

  const rows = [
    ['Korisnik', inv.created_by_username || '—'],
    ['Datum unosa', createdAt],
    ['Plaćeno dana', inv.is_paid ? paidAt : '—'],
    ['Način plaćanja', payMethod],
    ['Dospijeće', inv.due_date ? inv.due_date.substring(0,10).split('-').reverse().join('.') + '.' : '—'],
  ];

  const tableHtml = rows.map(([k, v]) =>
    `<tr><td style="padding:5px 10px 5px 0;font-size:12px;color:var(--gray-500);white-space:nowrap;">${k}</td>
     <td style="padding:5px 0;font-size:13px;font-weight:600;color:var(--navy);">${v}</td></tr>`
  ).join('');

  document.getElementById('info-popup-title').textContent =
    (inv.invoice_number || '—') + ' · ' + (inv.partner_name || '');
  document.getElementById('info-popup-body').innerHTML =
    `<table style="border-collapse:collapse;width:100%;">${tableHtml}</table>`;
  document.getElementById('info-popup-modal').classList.add('open');
}
function closeInfoPopup() {
  document.getElementById('info-popup-modal').classList.remove('open');
}
'''

if 'openInfoPopup' not in content:
    # Ubaci prije zadnjeg </script>
    content = content.replace('</script>\n{% endblock %}', INFO_POPUP_JS + '</script>\n{% endblock %}', 1)
    fixes += 1
    print("✅ FIX 5: openInfoPopup() JS dodan")

# ═══════════════════════════════════════════════════════════════════════════
# FIX 6: Dodaj Info popup modal HTML (prije NOTE POPUP MODAL)
# ═══════════════════════════════════════════════════════════════════════════
INFO_MODAL_HTML = '''<!-- INFO POPUP MODAL -->
<div class="modal-overlay" id="info-popup-modal">
  <div class="modal" style="width:360px;">
    <div class="modal-header">
      <span class="modal-title" id="info-popup-title" style="font-size:13px;font-family:'DM Mono',monospace;"></span>
      <button class="btn btn-ghost btn-icon" onclick="closeInfoPopup()">✕</button>
    </div>
    <div class="modal-body" id="info-popup-body" style="padding:16px 20px;">
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeInfoPopup()">Zatvori</button>
    </div>
  </div>
</div>

'''

if 'info-popup-modal' not in content:
    content = content.replace('<!-- NOTE POPUP MODAL -->', INFO_MODAL_HTML + '<!-- NOTE POPUP MODAL -->', 1)
    fixes += 1
    print("✅ FIX 6: Info popup modal HTML dodan")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎉 Patch v3 završen! ({fixes} fixa primijenjeno)")
print("   git add templates/invoice_list.html && git commit -m 'ui: invoice_list filteri 1 red, korisnik→info gumb, Veza PN' && git push origin main")
