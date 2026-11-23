"""US all-items CPI-U, NSA (1982-84=100): BLS CUUR0000SA0 / FRED CPIAUCNS."""
import csv,io,math
from datetime import datetime,timezone
import requests
BLS='https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0'
FRED='https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCNS'

def validate(rows,today):
    result=sorted(rows)
    dates=[d for d,v in result]
    if not result or len(set(dates))!=len(dates):raise ValueError('Empty or duplicate CPI observations')
    for d,v in result:
        dt=datetime.strptime(d,'%Y-%m-%d')
        if dt.day!=1 or d>today.date().isoformat() or not math.isfinite(v) or v<=0:raise ValueError('Invalid CPI observation')
    # Both complete anchor windows are essential. Missing months outside them stay gaps.
    available=set(dates)
    for year in range(2010,2020):
        for month in range(1,13):
            if year==2019 and month>9:continue
            if f'{year}-{month:02d}-01' not in available:raise ValueError('Incomplete CPI anchor history')
    return result

def bls_rows(today):
    rows=[]
    for first in range(2009,today.year+1,10):
        r=requests.get(BLS,params={'startyear':first,'endyear':min(first+9,today.year)},timeout=(10,60));r.raise_for_status()
        raw=r.json()
        if raw.get('status')!='REQUEST_SUCCEEDED':raise ValueError('BLS request rejected')
        series=raw['Results']['series']
        if len(series)!=1 or series[0]['seriesID']!='CUUR0000SA0':raise ValueError('Wrong BLS series')
        for item in series[0]['data']:
            if item['period']=='M13':continue
            if item['value'].strip() in ('-','.', ''):continue
            rows.append([f"{item['year']}-{int(item['period'][1:]):02d}-01",float(item['value'])])
    return validate(rows,today)

def fred_rows(today):
    r=requests.get(FRED,timeout=(10,60));r.raise_for_status()
    reader=csv.DictReader(io.StringIO(r.text))
    if not reader.fieldnames or 'CPIAUCNS' not in reader.fieldnames:raise ValueError('Wrong FRED series')
    date_key='observation_date' if 'observation_date' in reader.fieldnames else 'DATE'
    rows=[[item[date_key],float(item['CPIAUCNS'])] for item in reader if item[date_key]>='2009-01-01' and item['CPIAUCNS'].strip() not in ('','-','.')]
    return validate(rows,today)

def retrieve(previous=None,now=None,bcch_request=None):
    now=now or datetime.now(timezone.utc)
    checks=[];candidates=[]
    for name,loader,url in [('BLS',bls_rows,'https://data.bls.gov/timeseries/CUUR0000SA0'),('BLS via FRED',fred_rows,'https://fred.stlouisfed.org/series/CPIAUCNS')]:
        try:
            rows=loader(now);candidates.append((name,rows,url))
            checks.append(dict(source=name,status='ok',latest=rows[-1][0]))
        except Exception as e:checks.append(dict(source=name,status='unavailable',error=type(e).__name__))
    # A monthly release should normally cover at least two calendar months ago.
    minimum_month=now.year*12+now.month-2
    def fresh(rows):
        y,m=map(int,rows[-1][0][:7].split('-'));return y*12+m>=minimum_month
    if not any(fresh(c[1]) for c in candidates) and bcch_request:
        try:
            raw=bcch_request({'function':'GetSeries','timeseries':'F019.IPC.IND.10.M','firstdate':'2009-01-01'})
            if raw['Series']['seriesId']!='F019.IPC.IND.10.M':raise ValueError('Wrong fallback series')
            rows=validate([[datetime.strptime(x['indexDateString'],'%d-%m-%Y').date().isoformat(),float(x['value'])] for x in raw['Series']['Obs'] if x.get('statusCode')=='OK'],now)
            candidates.append(('BLS via BCCh',rows,'https://si3.bcentral.cl/siete/ES/Siete/Cuadro/CAP_EI/MN_EI11/EI_IndicePrecios_EEUU?idSerie=F019.IPC.IND.10.M'))
            checks.append(dict(source='BLS via BCCh',status='ok',latest=rows[-1][0]))
        except Exception as e:checks.append(dict(source='BLS via BCCh',status='unavailable',error=type(e).__name__))
    eligible=[c for c in candidates if fresh(c[1]) and (not previous or c[1][-1][0]>=previous['rows'][-1][0])]
    if not eligible:raise ValueError('US CPI feeds unavailable, stale, or older than saved data; previous data retained')
    name,rows,url=max(eligible,key=lambda c:c[1][-1][0])
    matched=0
    for other,other_rows,_ in candidates:
        if other==name or other=='BLS via BCCh':continue
        common=set(dict(rows))&set(dict(other_rows));matched=len(common)
        if any(abs(dict(rows)[d]-dict(other_rows)[d])>0.0011 for d in common):raise ValueError('BLS/FRED CPI values disagree')
    return dict(key='us_cpi',label='US consumer prices',rows=rows,retrieved_at=now.isoformat(),publisher=name,unit='Index, 1982-84=100',frequency='MONTHLY',aggregation='mean',growth=False,source_url=url,source_id='CUUR0000SA0' if name=='BLS' else 'CPIAUCNS',seasonal_adjustment='Not seasonally adjusted',source_title='US city average, all items CPI-U',source_checks=checks,cross_checked_observations=matched)
