"""Period-aware views built from immutable source observations."""
import pandas as pd
from economics import reference
def monthly(snapshot,key):
    spec=snapshot.get('series',{}).get(key)
    if not spec: return pd.Series(dtype=float)
    s=pd.Series({pd.Timestamp(d):v for d,v in spec['rows']}).sort_index()
    s=s[s.index<=pd.Timestamp.now().normalize()]
    if spec['frequency']=='DAILY':
        s=s.resample('MS').last() if key=='tpm' else s.resample('MS').mean()
        s=s[s.index.to_period('M')<pd.Timestamp.now().to_period('M')]
    else: s.index=s.index.to_period('M').to_timestamp()
    return s
def quarterly(snapshot,key,growth=None):
    if key=='participation':
        a,b=quarterly(snapshot,'workforce',False),quarterly(snapshot,'population',False)
        return (100*a/b).dropna()
    if key.startswith('penetration_'):
        suffix=key[len('penetration_'):]
        on=monthly(snapshot,'online_'+suffix); p=monthly(snapshot,key)/100
        joint=pd.concat([on.rename('on'),p.rename('p')],axis=1).dropna()
        joint=joint[(joint.p>0)&(joint.p<=1)]
        total=joint.on/joint.p
        numerator=joint.on.resample('QS').sum(min_count=3)
        denominator=total.resample('QS').sum(min_count=3)
        s=(100*numerator/denominator).dropna()
    elif key=='offline':
        on,p=monthly(snapshot,'online_all'),monthly(snapshot,'penetration_all')/100
        s=(on*(1-p)/p).where(p>0).dropna().resample('QS').sum(min_count=3).dropna()
    else:
        spec=snapshot.get('series',{}).get(key)
        if not spec: return pd.Series(dtype=float)
        s=monthly(snapshot,key)
        if spec['frequency']=='QUARTERLY': s.index=s.index.to_period('Q').start_time
        elif spec['aggregation']=='rolling':
            s=s[s.index.month.isin([3,6,9,12])]
            s.index=s.index.to_period('Q').start_time
        else:
            counts=s.resample('QS').count()
            agg=spec['aggregation']
            s=s.resample('QS').sum(min_count=3) if agg=='sum' else s.resample('QS').last() if agg=='last' else s.resample('QS').mean()
            s=s[counts==3]
    s=s[s.index.to_period('Q')<pd.Timestamp.now().to_period('Q')].sort_index()
    isgrowth=growth if growth is not None else snapshot.get('series',{}).get(key,{}).get('growth',key=='offline')
    if isgrowth:
        full=s.reindex(pd.date_range(s.index.min(),s.index.max(),freq='QS')) if len(s) else s
        s=100*(full/full.shift(4)-1)
    return s.dropna()
def annual(snapshot,key,growth=None):
    """Calendar-year aggregates, never a partial year or a mean of growth rates.

    GDP flows sum four quarters; monthly flow totals sum twelve months;
    indices and FX average twelve months. CPI, TPM and labor use December
    endpoints (labor is explicitly Oct-Dec, not annual-average employment).
    """
    if key=='participation':
        return (100*annual(snapshot,'workforce',False)/annual(snapshot,'population',False)).dropna()
    if key.startswith('penetration_'):
        on=monthly(snapshot,'online_'+key[len('penetration_'):])
        share=monthly(snapshot,key)/100
        joint=pd.concat([on.rename('on'),share.rename('share')],axis=1).dropna()
        joint=joint[(joint.share>0)&(joint.share<=1)]
        s=100*joint.on.resample('YS').sum(min_count=12)/(joint.on/joint.share).resample('YS').sum(min_count=12)
    elif key=='offline':
        on,share=monthly(snapshot,'online_all'),monthly(snapshot,'penetration_all')/100
        s=(on*(1-share)/share).where((share>0)&(share<=1)).resample('YS').sum(min_count=12)
    else:
        spec=snapshot.get('series',{}).get(key)
        if not spec:return pd.Series(dtype=float)
        raw=monthly(snapshot,key)
        if raw.empty:return raw
        agg=spec.get('aggregation','mean')
        if spec['frequency']=='QUARTERLY':
            s=raw.resample('YS').sum(min_count=4).where(raw.resample('YS').count()==4)
        elif agg in ['last','rolling']:
            s=raw[raw.index.month==12].copy()
            s.index=s.index.to_period('Y').start_time
        else:
            s=raw.resample('YS').sum(min_count=12) if agg=='sum' else raw.resample('YS').mean()
            s=s.where(raw.resample('YS').count()==12)
    s=s[s.index.year<pd.Timestamp.now().year].sort_index()
    isgrowth=growth if growth is not None else snapshot.get('series',{}).get(key,{}).get('growth',key=='offline')
    if isgrowth and len(s):
        s=s.reindex(pd.date_range(s.index.min(),s.index.max(),freq='YS'))
        s=100*(s/s.shift(1).where(s.shift(1)!=0)-1)
    return s.dropna()

def annual_reference(s):
    """Mean monthly FX references, with a documented 2025 shutdown exception.

    BLS computes its 2025 annual CPI average from 11 published months.
    Apply that available-month principle to our derived FX references only
    when October 2025 is the sole missing month. Never fill monthly inputs.
    All other years still require 12 observations; current years stay absent.
    """
    if s.empty:return s
    counts=s.resample('YS').count()
    means=s.resample('YS').mean()
    result=means.where(counts==12)
    expected=pd.date_range('2025-01-01','2025-12-01',freq='MS')
    missing=set(expected)-set(s.dropna().index)
    shutdown_year=pd.Timestamp('2025-01-01')
    if missing=={pd.Timestamp('2025-10-01')} and counts.get(shutdown_year)==11:
        result.loc[shutdown_year]=means.loc[shutdown_year]
    result=result[result.index.year<pd.Timestamp.now().year]
    if not result.notna().any():return result.iloc[:0]
    result=result.loc[result.first_valid_index():result.last_valid_index()]
    result.attrs['month_counts']={str(d.year):int(counts[d]) for d in result.dropna().index}
    return result

def refs(snapshot):
    def rows(key): return [(d.strftime('%Y-%m-%d'),float(v)) for d,v in monthly(snapshot,key).items()]
    result={}
    for start,end in [('2010-01','2014-12'),('2015-01','2019-09')]:
        data=reference(rows('fx'),rows('cpi'),rows('us_cpi'),start,end)
        s=pd.Series({pd.Timestamp(d):v for d,v in data},dtype=float)
        if not s.empty: result[start+' to '+end]=s.reindex(pd.date_range(s.index.min(),s.index.max(),freq='MS'))
    return result
def quarterly_reference(s):
    result=s.resample('QS').mean().where(s.resample('QS').count()==3)
    if not result.notna().any():return result.iloc[:0]
    return result.loc[result.first_valid_index():result.last_valid_index()]

def evaluate(snapshot):
    records=[]
    for fk,actual in [('eee_gdp','gdp'),('eee_nonmining','nonmining')]:
        target=quarterly(snapshot,actual,True)
        for d,f in monthly(snapshot,fk).items():
            q=d.to_period('Q').start_time
            if q in target:
                records.append(dict(series=fk,issued=d,target=q,forecast=f,actual=target[q],lead_group='Quarter month '+str((d.month-1)%3+1),baseline=target.get(q-pd.DateOffset(years=1),float('nan'))))
    cpi=monthly(snapshot,'cpi')
    if len(cpi): cpi=cpi.reindex(pd.date_range(cpi.index.min(),cpi.index.max(),freq='MS'))
    actual=100*(cpi/cpi.shift(12)-1)
    for d,f in monthly(snapshot,'eee_inflation').items():
        target=d+pd.DateOffset(months=11)
        if target in actual and pd.notna(actual[target]):
            records.append(dict(series='eee_inflation',issued=d,target=target,forecast=f,actual=actual[target],lead_group='11 months',baseline=actual.get(d-pd.DateOffset(months=1),float('nan'))))
    frame=pd.DataFrame(records)
    if frame.empty: return frame,pd.DataFrame()
    frame['error']=frame.forecast-frame.actual
    metrics=frame.groupby(['series','lead_group']).error.agg(n='count',MAE=lambda x:x.abs().mean(),RMSE=lambda x:(x.pow(2).mean())**.5,Bias='mean').reset_index()
    frame['baseline_error']=frame.baseline-frame.actual
    matched=frame.dropna(subset=['baseline_error'])
    benchmark=matched.groupby(['series','lead_group']).agg(common_n=('error','count'),EEE_MAE_common=('error',lambda x:x.abs().mean()),Baseline_MAE_common=('baseline_error',lambda x:x.abs().mean())).reset_index()
    metrics=metrics.merge(benchmark,on=['series','lead_group'],how='left')
    return frame,metrics

def observations(snapshot,key,timeframe='Monthly',growth=None):
    """Display-frequency values; never upsample quarterly GDP into monthly data."""
    if timeframe=='Annual': return annual(snapshot,key,growth)
    if timeframe=='Quarterly': return quarterly(snapshot,key,growth)
    if snapshot.get('series',{}).get(key,{}).get('frequency')=='QUARTERLY':
        raise ValueError('Quarterly source requires a quarterly panel: '+key)
    if key=='participation':
        s=100*monthly(snapshot,'workforce')/monthly(snapshot,'population')
    elif key=='offline':
        on,p=monthly(snapshot,'online_all'),monthly(snapshot,'penetration_all')/100
        s=(on*(1-p)/p).where((p>0)&(p<=1))
    else: s=monthly(snapshot,key)
    s=s[s.index.to_period('M')<pd.Timestamp.now().to_period('M')].sort_index()
    if growth if growth is not None else snapshot.get('series',{}).get(key,{}).get('growth',key=='offline'):
        if len(s): s=s.reindex(pd.date_range(s.index.min(),s.index.max(),freq='MS'))
        s=100*(s/s.shift(12).where(s.shift(12)!=0)-1)
    return s.dropna()
