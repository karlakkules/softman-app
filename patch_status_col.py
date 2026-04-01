import shutil
from pathlib import Path

T = Path('templates/vehicle_log.html')
shutil.copy(T, T.with_suffix('.html.bak'))
c = T.read_text(encoding='utf-8')

# th — fiksna širina za Status, suzi PN nalozi
old = "          <th>Status</th>\n          <th>PN nalozi</th>\n          <th>Akcije</th>"
new = '          <th style="width:120px;min-width:120px;">Status</th>\n          <th style="min-width:0;">PN nalozi</th>\n          <th style="width:72px;">Akcije</th>'
if old in c: c = c.replace(old, new); print('✅ th širine postavljene')
else: print('❌ th pattern nije pronađen')

# td — white-space:nowrap na badge ćeliji
old = '          <td>\n            {% if log.is_approved %}\n              <span style="background:#e8f8f5;color:#27ae60;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">✅ Odobreno</span>\n            {% else %}\n              <span style="background:#fef9e7;color:#e67e22;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">📝 Nacrt</span>\n            {% endif %}\n          </td>'
new = '          <td style="white-space:nowrap;">\n            {% if log.is_approved %}\n              <span style="background:#e8f8f5;color:#27ae60;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;white-space:nowrap;display:inline-block;">✅ Odobreno</span>\n            {% else %}\n              <span style="background:#fef9e7;color:#e67e22;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;white-space:nowrap;display:inline-block;">📝 Nacrt</span>\n            {% endif %}\n          </td>'
if old in c: c = c.replace(old, new); print('✅ td white-space:nowrap dodan')
else: print('❌ td pattern nije pronađen')

T.write_text(c, encoding='utf-8')
print('✅ Gotovo!')
