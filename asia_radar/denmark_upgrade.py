"""Idempotent Denmark UI extension applied after existing geography and Bosch upgrades."""
from __future__ import annotations
import re
MARKER="/* DENMARK_COUNTRY_V1 */"
CARD='''    <button type="button" class="country-card" data-country="Dinamarca" aria-pressed="false"><img class="flag-image" src="assets/flags/dk.svg" alt="" width="34" height="26" decoding="async"><span class="countrycopy"><strong>Dinamarca</strong><small>Notícias nas últimas 24 h</small></span><span class="selection" aria-hidden="true">✓</span></button>'''
def upgrade_denmark_dashboard(html):
    if MARKER in html:
        return html
    anchor='<div class="countrygrid" id="countries"'
    a=html.find(anchor)
    b=html.find("\n  </div>",a) if a>=0 else -1
    if a<0 or b<0: raise RuntimeError("Denmark: country navigation not found")
    html=html[:b]+"\n"+CARD+html[b:]
    pattern=r'(const countries=\[)([^\]]+)(\];)'
    matches=list(re.finditer(pattern,html))
    if len(matches)!=1 or '"Portugal"' not in matches[0].group(2):
        raise RuntimeError("Denmark: country JS list changed")
    html=re.sub(pattern,lambda m:m.group(1)+m.group(2)+',"Dinamarca"'+m.group(3),html,count=1)
    for before,after in [
       ('"Portugal":"🇵🇹"','"Portugal":"🇵🇹","Dinamarca":"🇩🇰"'),
       ('"Portugal":"pt"','"Portugal":"pt","Dinamarca":"dk"'),
       ('<option value="Portugal">🇵🇹 Portugal</option>',
        '<option value="Dinamarca">Dinamarca</option><option value="Portugal">🇵🇹 Portugal</option>'),
    ]:
       if before not in html: raise RuntimeError("Denmark: missing interface anchor "+before)
       html=html.replace(before,after,1)
    if "</style>" not in html: raise RuntimeError("Denmark: CSS not found")
    return html.replace("</style>",MARKER+"\n</style>",1)
