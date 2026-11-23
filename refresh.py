"""Authenticated refresh. Raw responses never contain request URLs or credentials."""
import os,json,time,sys
from pathlib import Path
from datetime import datetime,timezone
import requests
ROOT=Path(__file__).parent
ENDPOINT="https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
def request(params):
    for attempt in range(3):
        try:
            r=requests.get(ENDPOINT,params={**params,"token":os.environ["BCCH_API_TOKEN"]},timeout=(10,60))
            r.raise_for_status()
            data=r.json()
            if data.get("Codigo")!=0: raise ValueError("BCCh rejected the request")
            return data
        except (requests.RequestException,ValueError):
            if attempt==2: raise RuntimeError("BCCh request failed; URL and credential withheld") from None
            time.sleep(2**attempt)
def refresh():
    folder=ROOT/"data"; folder.mkdir(exist_ok=True)
    path=folder/"snapshot.json"
    old=json.loads(path.read_text()) if path.exists() else {"series":{}}
    now=datetime.now(timezone.utc).isoformat()
    old["last_attempt"]=now; failures=[]
    registry=json.loads((ROOT/"registry.json").read_text())
    if not os.environ.get("BCCH_API_TOKEN"):
        raise RuntimeError("Set BCCH_API_TOKEN in GitHub Actions Secrets before refreshing.")
    for spec in registry:
        try:
            raw=request({"function":"GetSeries","timeseries":spec["id"],"firstdate":"2009-01-01"})
            series=raw["Series"]
            if series["seriesId"]!=spec["id"]: raise ValueError("Unexpected series ID")
            rows=[]
            for x in series["Obs"]:
                if x.get("statusCode")!="OK": continue
                d=datetime.strptime(x["indexDateString"],"%d-%m-%Y").date().isoformat()
                v=float(x["value"])*spec.get("scale",1)
                if not __import__("math").isfinite(v): raise ValueError("Non-finite observation")
                rows.append([d,v])
            if not rows or len({x[0] for x in rows})!=len(rows): raise ValueError("Empty or duplicate dates")
            rows.sort()
            (folder/"raw").mkdir(exist_ok=True)
            (folder/"raw"/(spec["key"]+".json")).write_text(json.dumps(raw,ensure_ascii=False),encoding="utf-8")
            old["series"][spec["key"]]={"rows":rows,"retrieved_at":now,"source_title":series.get("descripEsp"),**spec}
        except Exception as e:
            failures.append({"series":spec["key"],"error":type(e).__name__})

    try:
        rows=[]
        for first,last in [(2009,2018),(2019,datetime.now().year)]:
            response=requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/',json={"seriesid":["CUUR0000SA0"],"startyear":str(first),"endyear":str(last)},timeout=60)
            response.raise_for_status()
            raw=response.json()
            if raw['status']!='REQUEST_SUCCEEDED': raise ValueError('BLS request rejected')
            for item in raw['Results']['series'][0]['data']:
                if item['period']!='M13':
                    rows.append([item['year']+'-'+item['period'][1:]+'-01',float(item['value'])])
        rows.sort()
        if not rows: raise ValueError('BLS empty response')
        old['series']['us_cpi']=dict(key='us_cpi',label='US consumer prices',rows=rows,retrieved_at=now,publisher='BLS',unit='Index, 1982-84=100',frequency='MONTHLY',aggregation='mean',growth=False,source_url='https://data.bls.gov/timeseries/CUUR0000SA0')
    except Exception as e:
        failures.append({'series':'us_cpi','error':type(e).__name__})
    old["failures"]=failures
    if not failures: old["last_success"]=now
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding="utf-8"); temp.replace(path)
    print(json.dumps({"attempt":now,"series":len(old["series"]),"failures":failures}))
    return bool(failures)
if __name__=="__main__":
    try: sys.exit(int(refresh()))
    except Exception as e:
        print(str(e) if isinstance(e,RuntimeError) else type(e).__name__); sys.exit(1)
