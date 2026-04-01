#!/usr/bin/env python3
"""
Patch: Poništi odobrenje evidencije vozila
1. app.py — novi endpoint POST /api/vehicle-log/<id>/unapprove
2. vehicle_log_form.html — gumb "Poništi odobrenje" umjesto statičnog "Odobreno" badgea
"""
import shutil
from pathlib import Path

errors = []

# ════════════════════════════════════════════════════════
# app.py — novi endpoint unapprove
# ════════════════════════════════════════════════════════
APP = Path('app.py')
if not APP.exists():
    print('ERROR: app.py nije pronađen!'); exit(1)

shutil.copy(APP, APP.with_suffix('.py.bak'))
c = APP.read_text(encoding='utf-8')

NEW_ENDPOINT = """
@app.route('/api/vehicle-log/<int:log_id>/unapprove', methods=['POST'])
@login_required
def unapprove_vehicle_log(log_id):
    \"\"\"Poništi odobrenje evidencije — vraća u status Nacrt.\"\"\"
    conn = get_db()
    user = get_current_user()
    if not (user and (user.get('is_admin') or user.get('can_approve_vehicle_log'))):
        conn.close()
        return jsonify({'error': 'Nemate pravo poništavanja odobrenja'}), 403
    conn.execute(
        "UPDATE vehicle_log SET is_approved=0, approved_at=NULL, approved_by_id=NULL WHERE id=?",
        (log_id,)
    )
    conn.commit()
    conn.close()
    audit('unapprove', module='sluzbeni_automobil', entity='vehicle_log', entity_id=log_id,
          detail='Odobrenje poništeno — vraćeno u Nacrt')
    return jsonify({'success': True})

"""

MARKER = "@app.route('/api/vehicle-log/<int:log_id>/approve', methods=['POST'])"
if MARKER in c:
    c = c.replace(MARKER, NEW_ENDPOINT + MARKER)
    print('✅ app.py: unapprove endpoint dodan')
else:
    errors.append('app.py: approve marker nije pronađen')

APP.write_text(c, encoding='utf-8')

# ════════════════════════════════════════════════════════
# vehicle_log_form.html — gumb za poništavanje
# ════════════════════════════════════════════════════════
TFORM = Path('templates/vehicle_log_form.html')
if not TFORM.exists():
    errors.append('vehicle_log_form.html ne postoji')
else:
    shutil.copy(TFORM, TFORM.with_suffix('.html.bak'))
    fc = TFORM.read_text(encoding='utf-8')

    # Zamijeni statični "Odobreno" badge s gumbom za poništavanje
    OLD_APPROVED = """{% if can_approve %}
{% if log.is_approved %}
<span class="btn btn-secondary" style="opacity:0.6;cursor:default;">✅ Odobreno</span>
{% else %}
<button class="btn btn-secondary" onclick="approveLog()" id="approve-btn" title="Odobri evidenciju — dodaje potpis direktora">✍️ Odobri</button>
{% endif %}
{% endif %}"""

    NEW_APPROVED = """{% if can_approve %}
{% if log.is_approved %}
<span class="btn btn-secondary" style="opacity:0.6;cursor:default;background:#e8f8f5;color:#27ae60;border-color:#a8d5b5;">✅ Odobreno</span>
<button class="btn btn-secondary" onclick="unapproveLog()" id="unapprove-btn" title="Poništi odobrenje — vraća evidenciju u status Nacrt" style="background:#fef9e7;color:#e67e22;border-color:#f5c6a0;">↩️ Poništi odobrenje</button>
{% else %}
<button class="btn btn-secondary" onclick="approveLog()" id="approve-btn" title="Odobri evidenciju — dodaje potpis direktora">✍️ Odobri</button>
{% endif %}
{% endif %}"""

    if OLD_APPROVED in fc:
        fc = fc.replace(OLD_APPROVED, NEW_APPROVED)
        print('✅ vehicle_log_form.html: gumb Poništi odobrenje dodan')
    else:
        errors.append('vehicle_log_form.html: approve blok pattern nije pronađen')

    # Dodaj JS funkciju unapproveLog() nakon approveLog()
    OLD_JS = """async function approveLog() {
  const logId = document.getElementById('log-id').value;
  if (!logId) { toast('Prvo spremi evidenciju!', 'error'); return; }
  if (!confirm('Odobriti evidenciju? Bit će dodan potpis direktora.')) return;
  const res = await fetch(`/api/vehicle-log/${logId}/approve`, { method: 'POST' });
  const d = await res.json();
  if (d.success) {
    toast('Evidencija odobrena!', 'success');
    // Zamijeni gumb s "Odobreno"
    const btn = document.getElementById('approve-btn');
    if (btn) {
      btn.outerHTML = '<span class="btn btn-secondary" style="opacity:0.6;cursor:default;">✅ Odobreno</span>';
    }
  } else {
    toast(d.error || 'Greška pri odobravanju', 'error');
  }
}"""

    NEW_JS = """async function approveLog() {
  const logId = document.getElementById('log-id').value;
  if (!logId) { toast('Prvo spremi evidenciju!', 'error'); return; }
  if (!confirm('Odobriti evidenciju? Bit će dodan potpis direktora.')) return;
  const res = await fetch(`/api/vehicle-log/${logId}/approve`, { method: 'POST' });
  const d = await res.json();
  if (d.success) {
    toast('Evidencija odobrena!', 'success');
    setTimeout(() => location.reload(), 700);
  } else {
    toast(d.error || 'Greška pri odobravanju', 'error');
  }
}

async function unapproveLog() {
  const logId = document.getElementById('log-id').value;
  if (!logId) return;
  if (!confirm('Poništiti odobrenje? Evidencija će se vratiti u status Nacrt.')) return;
  const res = await fetch(`/api/vehicle-log/${logId}/unapprove`, { method: 'POST' });
  const d = await res.json();
  if (d.success) {
    toast('Odobrenje poništeno — evidencija je u statusu Nacrt.', 'success');
    setTimeout(() => location.reload(), 700);
  } else {
    toast(d.error || 'Greška pri poništavanju', 'error');
  }
}"""

    if OLD_JS in fc:
        fc = fc.replace(OLD_JS, NEW_JS)
        print('✅ vehicle_log_form.html: unapproveLog() JS funkcija dodana')
    else:
        errors.append('vehicle_log_form.html: approveLog() JS pattern nije pronađen')

    TFORM.write_text(fc, encoding='utf-8')

print()
if errors:
    print('⚠️  NISU primijenjeni:')
    for e in errors: print(f'   ❌ {e}')
else:
    print('✅ Svi patchi primijenjeni!')
    print('\nNakon restarta Flask:')
    print('  - Odobrena evidencija prikazuje zeleni "✅ Odobreno" badge + narančasti "↩️ Poništi odobrenje" gumb')
    print('  - Klik na gumb vraća evidenciju u Nacrt s potvrdom')
