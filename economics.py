"""Pure transformations. No source fetching or UI dependencies."""
from datetime import date
from statistics import mean, median
from collections import defaultdict

def quarter(d):
    return f"{d[:4]}-Q{(int(d[5:7])-1)//3+1}"

def quarterly(rows, method="mean"):
    groups=defaultdict(dict)
    for d,v in rows:
        groups[quarter(d)][d[:7]]=float(v)
    result={}
    for q,months in groups.items():
        if len(months)!=3: continue
        values=[months[m] for m in sorted(months)]
        result[q]=sum(values) if method=="sum" else values[-1] if method=="last" else mean(values)
    return result

def yoy(values):
    return {q:100*(v/values[f"{int(q[:4])-1}{q[4:]}"]-1)
            for q,v in values.items()
            if f"{int(q[:4])-1}{q[4:]}" in values and values[f"{int(q[:4])-1}{q[4:]}"]!=0}

def quarterly_penetration(online, penetration):
    # Both inputs must describe exactly the same population.
    p=dict(penetration)
    on=[]; total=[]
    for d,v in online:
        if d in p and 0<p[d]<=100:
            on.append((d,v)); total.append((d,v/(p[d]/100)))
    a,b=quarterly(on,"sum"),quarterly(total,"sum")
    return {q:100*a[q]/b[q] for q in a if q in b and b[q]>0}

def reference(fx, chile_cpi, us_cpi, start, end):
    c,u=dict(chile_cpi),dict(us_cpi)
    common={d:s*u[d]/c[d] for d,s in fx if d in c and d in u and min(s,c[d],u[d])>0}
    anchor=[v for d,v in common.items() if start<=d[:7]<=end]
    expected=(int(end[:4])-int(start[:4]))*12+int(end[5:7])-int(start[5:7])+1
    if len(anchor)!=expected: return []
    b=median(anchor)
    return [(d,b*c[d]/u[d]) for d in common if d[:7]>=end]

def errors(pairs):
    differences=[f-a for f,a in pairs]
    if not differences: return {}
    return {"n":len(differences),"MAE":mean(abs(x) for x in differences),
            "RMSE":mean(x*x for x in differences)**.5,"Bias":mean(differences)}
