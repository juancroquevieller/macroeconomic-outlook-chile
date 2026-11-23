"""Independent checks against the published BDE observation table."""
import re,html,json,urllib.request
from pathlib import Path
MONTHS=dict(zip(['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],range(1,13)))
def published(code):
    url='https://si3.bcentral.cl/siete/ES/Siete/Cuadro/CAP_IND_SEC/MN_IND_SEC20/IS_COM1?idSerie='+code
    raw=urllib.request.urlopen(url,timeout=60).read().decode('utf-8')
    match=re.search(r'<table id="listaObsHtmlAll".*?</table>',raw,re.S)
    if not match: raise ValueError('Observation table unavailable')
    rows=[]
    for period,value in re.findall(r'<tr><td>(.*?)</td><td>(.*?)</td></tr>',match[0]):
        rows.append((html.unescape(period),html.unescape(value)))
    return url,rows
if __name__=='__main__':
    root=Path(__file__).parent
    report=[]
    snap=json.loads((root/'data/snapshot.json').read_text(encoding='utf-8'))
    for key,spec in snap['series'].items():
        if not spec.get('id'): continue
        try:
            url,rows=published(spec['id'])
            period,value=rows[0]
            report.append(dict(series=key,url=url,published_period=period,published_value=value,api_latest=spec['rows'][-1],status='REVIEW_REQUIRED'))
        except Exception as exc:
            report.append(dict(series=key,status='UNAVAILABLE',error=type(exc).__name__))
    (root/'verification').mkdir(exist_ok=True)
    (root/'verification/source_checks.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
