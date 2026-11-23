"""Reproduce source spot checks against public BDE tables, independently of the API."""
import re,html,json,requests
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
MONTHS=dict(zip(['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],range(1,13)))

def published(code):
    search=requests.get('https://si3.bcentral.cl/Search/Buscar/Index/',params={'st':code},timeout=60)
    links=re.findall(r'href=(https://si3.bcentral.cl/siete/login.aspx[^\s>]+)',search.text)
    link=next(html.unescape(x.strip('"')) for x in links if code in x)
    response=requests.get(link,timeout=60)
    match=re.search(r'<table id="listaObsHtmlAll".*?</table>',response.text,re.S)
    if not match: raise ValueError('Observation table unavailable')
    return response.url,[(html.unescape(p),html.unescape(v)) for p,v in re.findall(r'<tr><td>(.*?)</td><td>(.*?)</td></tr>',match[0])]

def period_date(p):
    parts=p.split('.')
    if parts[0] in ['I','II','III','IV']: return f'{parts[1]}-{1+3*["I","II","III","IV"].index(parts[0]):02d}-01'
    if len(parts)==2: return f'{parts[1]}-{MONTHS[parts[0]]:02d}-01'
    return f'{parts[2]}-{MONTHS[parts[1]]:02d}-{int(parts[0]):02d}'

def check(item):
    key,spec=item
    try:
        url,rows=published(spec['id'])
        api=dict(spec['rows'])
        for period,value in rows:
            date=period_date(period)
            if date not in api: continue
            number=float(value.replace('.','').replace(',','.'))
            scale=spec.get('scale',1)
            decimals=len(value.split(',')[1]) if ',' in value else 0
            tolerance=0.5*10**(-decimals)*scale+1e-9
            return dict(series=key,url=url,published_period=period,published_value=value,display_scale=scale,api_value=api[date],absolute_difference=abs(api[date]-number*scale),rounding_tolerance=tolerance,status='PASS' if abs(api[date]-number*scale)<=tolerance else 'MISMATCH')
        raise ValueError('No common published observation')
    except Exception as e: return dict(series=key,status='UNAVAILABLE',error=type(e).__name__)

if __name__=='__main__':
    root=Path(__file__).parent
    snap=json.loads((root/'data/snapshot.json').read_text(encoding='utf-8'))
    with ThreadPoolExecutor(max_workers=4) as pool: report=list(pool.map(check,snap['series'].items()))
    out=root/'verification';out.mkdir(exist_ok=True)
    (out/'source_checks.json').write_text(json.dumps({'checked_at':datetime.now(timezone.utc).isoformat(),'checks':report},indent=2,ensure_ascii=False),encoding='utf-8')
    registry=json.loads((root/'registry.json').read_text(encoding='utf-8'))
    for row in report:
        if row.get('url'):
            snap['series'][row['series']]['source_url']=row['url']
            for spec in registry:
                if spec['key']==row['series']: spec['source_url']=row['url']
        print(row['series'],row['status'])
    (root/'registry.json').write_text(json.dumps(registry,indent=2,ensure_ascii=False),encoding='utf-8')
    (root/'data/snapshot.json').write_text(json.dumps(snap,indent=2,ensure_ascii=False),encoding='utf-8')
