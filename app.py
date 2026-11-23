from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from model import monthly,quarterly,refs,evaluate
ROOT=Path(__file__).parent
st.set_page_config(page_title="Chile | Economy & Retail",page_icon="🇨🇱",layout="wide")
st.markdown("<style>.block-container{padding-top:2rem;max-width:1450px}h1{letter-spacing:-.04em}div[data-testid=stMetric]{background:#f5f7f8;padding:16px;border-radius:10px}</style>",unsafe_allow_html=True)
st.caption("CHILE OBSERVATORY")
st.title("Economy & Retail")
st.write("The economic backdrop. The consumer pulse. The shift online.")
path=ROOT/'data/snapshot.json'
data=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'series':{}}
series=data['series']
view=st.sidebar.radio("Explore",["Macroeconomic outlook","Retail outlook","Assignment view","Sources & methodology"])
window=st.sidebar.selectbox("History",["Since 2018","5 years","10 years","All available"])
cut={'Since 2018':pd.Timestamp('2018-01-01'),'5 years':pd.Timestamp.now()-pd.DateOffset(years=5),'10 years':pd.Timestamp.now()-pd.DateOffset(years=10),'All available':pd.Timestamp('1900-01-01')}[window]
st.sidebar.caption("Complete calendar quarters. Monthly releases appear separately as latest signals.")
def stamp(value):
    return pd.Timestamp(value).tz_convert('America/Chicago').strftime('%b %d, %Y · %H:%M %Z') if value else 'Not completed'
st.caption("Last successful full refresh: "+stamp(data.get('last_success'))+" | Last attempt: "+stamp(data.get('last_attempt')))
if data.get('failures'): st.warning("Partial refresh: some series retain their previous valid observations. See Sources & methodology.")
if not series: st.info("Official data is being connected. No synthetic observations are displayed.")
COLORS=['#167565','#d07931','#7764a5','#3578ab','#b24e66']
def label(k): return series.get(k,{}).get('label',{'participation':'Participation','offline':'In-store','online_all':'Online retail'}.get(k,k))
def source(keys):
    for key in keys:
        spec=series.get(key)
        if spec:
            st.caption(f"{label(key)} · {spec['publisher']} · native {spec['frequency'].lower()} · latest observation {spec['rows'][-1][0]} · [Source]({spec.get('source_url','')})")
def draw(title,keys,growth=None,unit=None,target=None,forecast=None):
    st.subheader(title)
    fig=go.Figure()
    units=set()
    for i,k in enumerate(keys):
        s=quarterly(data,k,growth);s=s[s.index>=cut]
        if not len(s): continue
        fig.add_trace(go.Scatter(x=s.index+pd.offsets.QuarterEnd(0),y=s,name=label(k),line=dict(color=COLORS[i%5],width=2.5),hovertemplate='%{x|%Y Q%q}: %{y:,.2f}<extra>%{fullData.name}</extra>'))
        st.caption(label(k)+' · latest plotted quarter '+str(s.index[-1].to_period('Q')))
        units.add('% YoY' if (growth if growth is not None else series.get(k,{}).get('growth',k=='offline')) else series.get(k,{}).get('unit','%'))
    if target is not None: fig.add_hline(y=target,line_dash='dot',annotation_text=f"{target:g}% inflation target")
    if forecast:
        fs=monthly(data,forecast)
        if len(fs):
            d,v=fs.index[-1],fs.iloc[-1]
            when=d+pd.DateOffset(months=11) if forecast=='eee_inflation' else d+pd.offsets.QuarterEnd(0)
            fig.add_trace(go.Scatter(x=[when],y=[v],name='EEE consensus · '+when.strftime('%b %Y'),mode='markers',marker=dict(symbol='diamond-open',size=12,color='#d07931'),hovertext='Survey issued '+d.strftime('%b %Y')))
    if not fig.data: st.info("No verified observations available.");return
    fig.update_layout(template='plotly_white',height=330,margin=dict(l=5,r=5,t=25,b=5),yaxis_title=unit or ', '.join(units),legend=dict(orientation='h',y=-.24),hovermode='x unified')
    st.plotly_chart(fig,width='stretch')
    source(keys)
def signals(keys):
    columns=st.columns(len(keys))
    for col,key in zip(columns,keys):
        s=monthly(data,key)
        if len(s):
            spec=series[key]; v=s.iloc[-1]
            if spec.get('growth') and len(s)>12 and s.index[-1]-pd.DateOffset(months=12) in s.index:
                v=100*(v/s.loc[s.index[-1]-pd.DateOffset(months=12)]-1);unit='% YoY'
            else: unit=spec['unit']
            col.metric(label(key),f"{v:,.1f}"+('%' if '%' in unit else ''))
            col.caption(s.index[-1].strftime('%b %Y')+' · '+unit)
def fx_details():
    with st.expander("Historical reference range · what might relative prices imply?"):
        st.write("Two anchors: January 2010–December 2014 and January 2015–September 2019. The second ends before the October 2019 social unrest.")
        result=refs(data);fig=go.Figure()
        for i,(name,s) in enumerate(result.items()):
            counts=s.resample('QS').count();s=s.resample('QS').mean().where(counts==3).dropna();s=s[(s.index>=cut)&(s.index.to_period('Q')<pd.Timestamp.now().to_period('Q'))]
            fig.add_trace(go.Scatter(x=s.index+pd.offsets.QuarterEnd(0),y=s,name=name,fill='tonexty' if i else None,line=dict(dash='dot')))
        observed=quarterly(data,'fx',False);observed=observed[observed.index>=cut]
        if len(observed): fig.add_trace(go.Scatter(x=observed.index+pd.offsets.QuarterEnd(0),y=observed,name='Observed CLP/USD',line=dict(color=COLORS[0])))
        if result: st.plotly_chart(fig.update_layout(yaxis_title='CLP per USD',template='plotly_white',height=380),width='stretch')
        else: st.info("Complete common CPI/FX history is not yet available.")
        st.latex(r"q_t=S_t\frac{CPI_{US,t}}{CPI_{Chile,t}},\quad S_t^{ref}=median(q_{reference})\frac{CPI_{Chile,t}}{CPI_{US,t}}")
        st.write("A higher CLP/USD number means a weaker peso. The band represents sensitivity to historical reference periods, not a confidence interval, official fair value, or forecast. Structural changes can place the exchange rate outside it. References stop at the latest common month with all three inputs.")
        st.caption("Monthly calculations precede quarterly averaging. The bilateral reference is distinct from BCCh’s multilateral TCR.")
if view=='Macroeconomic outlook':
    st.subheader("Latest signals");signals(['imacec','eee_nonmining','eee_inflation','tpm'])
    a,b=st.columns(2)
    with a:
        draw("Economic activity",['gdp','mining','nonmining'],forecast='eee_nonmining')
        st.caption("Official direct-sector mining split. Growth rates are not additive.")
    with b:
        draw("Inflation & policy",['cpi','tpm'],unit='Percent',target=3,forecast='eee_inflation')
        st.caption("CPI: quarter-end year-over-year change. TPM: quarter-end policy rate. The EEE diamond refers to its exact future target month.")
    a,b=st.columns(2)
    with a:
        which=st.radio("Exchange-rate measure",['Nominal CLP/USD','Real exchange-rate index'],horizontal=True)
        draw("Exchange rates",['fx' if which.startswith('Nominal') else 'tcr'],False)
        fx_details()
    with b:
        draw("Employment",['unemployment','participation'],False,unit='%')
        w=quarterly(data,'workforce',False)
        if len(w): st.metric('Workforce · '+str(w.index[-1].to_period('Q')),f'{w.iloc[-1]:.2f} million')
        st.caption("Calendar-quarter estimates selected from INE’s rolling-quarter series; participation = workforce / population aged 15+.")
elif view=='Retail outlook':
    st.subheader("Latest signals");signals(['retail','online_all','penetration_all','sales_expectations'])
    a,b=st.columns(2)
    with a:
        draw("Consumer demand",['nonmining','consumption_durable','consumption_nondurable'])
        with st.expander("What do retailers expect?"):
            draw("Commerce sales expectations",['sales_expectations'],False,unit='Diffusion index')
            st.caption("Survey sentiment, not a sales-growth forecast. Household consumption and domestic retail turnover cover different economic concepts.")
    with b:
        mode=st.radio('Retail measure',['Real growth','Nominal sales'],horizontal=True)
        draw("Retail scale & categories",['retail','durables','nondurables'] if mode=='Real growth' else ['retail_value'],None if mode=='Real growth' else False)
        st.caption("Nominal sales: IVE, CLP billions per quarter. Real growth: INE volume indices. Independently based indices cannot establish category monetary shares.")
    a,b=st.columns(2)
    with a:
        st.subheader("Online versus in-store")
        p=quarterly(data,'penetration_all',False);p=p[p.index>=cut]
        fig=go.Figure()
        for name,s,color in [('Online',p,COLORS[0]),('In-store',100-p,'#c7d9d5')]:
            fig.add_trace(go.Bar(x=s.index+pd.offsets.QuarterEnd(0),y=s,name=name,marker_color=color))
        st.plotly_chart(fig.update_layout(barmode='stack',yaxis_title='% of nominal sales',height=300,template='plotly_white'),width='stretch')
        draw("Channel growth",['online_all','offline'],True,unit='Nominal % YoY')
        st.caption("Penetration and in-store growth are derived within IVOCM’s own population. Published rounded shares introduce approximation. IVE is not multiplied by IVOCM shares to invent CLP channel totals.")
    with b:
        st.subheader("Retail channels")
        names=['supermarkets','department','specialists','platforms','other'];rows=[]
        for key in names:
            p=quarterly(data,'penetration_'+key,False);g=quarterly(data,'online_'+key,True)
            common=p.index.intersection(g.index)
            if len(common):
                d=common[-1]; prior=d-pd.DateOffset(years=1)
                rows.append({'Channel':label('online_'+key),'Quarter':str(d.to_period('Q')),'Online YoY %':g[d],'Online share %':p[d],'Share change pp':p[d]-p.get(prior,float('nan'))})
        st.dataframe(pd.DataFrame(rows),hide_index=True)
        selected=st.selectbox('Channel detail',names,format_func=lambda k:label('online_'+k))
        draw("Online penetration",['penetration_'+selected],False)
        st.caption("Department stores include home improvement; platforms include digital intermediaries and online-only sellers. These are sector aggregates, not company market shares or marketplace GMV.")
elif view=='Assignment view':
    items=[('GDP growth','gdp'),('Non-mining GDP growth','nonmining'),('Inflation','cpi'),('Monetary policy rate','tpm'),('CLP per USD','fx'),('Unemployment','unemployment'),('Real retail growth','retail'),('Online penetration','penetration_all')]
    for offset in range(0,8,2):
        for col,(title,key) in zip(st.columns(2),items[offset:offset+2]):
            with col: draw(title,[key])
else:
    st.subheader("Sources, dates & transformations")
    st.write("Banco Central supplies the principal API. Original producers remain credited. Complete calendar quarters only; each series keeps its own latest available date. Missing periods are not interpolated.")
    st.write("Quarterly monetary flows are summed. Volume indices and FX are averaged. CPI and policy rates use quarter-end observations. Growth = 100 × (current / same quarter last year − 1). GDP components use official chained-volume aggregates, never subtraction of growth rates.")
    st.write("Quarterly penetration = sum(online index) / sum(online index / monthly share). This preserves sales weights within each series; zero or missing shares invalidate that month. In-store relative sales = online index × (1 − share) / share. No cross-category sums of independently based indices.")
    st.write("Automatic refresh: 1st and 16th, 08:17 America/Chicago. Last-success time advances only when all configured inputs refresh successfully; unchanged observations still count as successful retrieval.")
    if data.get('failures'): st.json(data['failures'])
    st.dataframe(pd.DataFrame([{'Series':label(k),'Publisher':s['publisher'],'Unit':s['unit'],'Native frequency':s['frequency'],'Latest observation':s['rows'][-1][0],'Retrieved':s['retrieved_at'],'Source':s.get('source_url','')} for k,s in series.items()]),hide_index=True)
    st.subheader("How accurate were the EEE expectations?")
    pairs,metrics=evaluate(data)
    if len(metrics):
        st.dataframe(metrics,hide_index=True)
        st.download_button('Download matched forecasts',pairs.to_csv(index=False),'eee-evaluation.csv')
    st.caption("Retrospective errors against revised actuals, in percentage points. GDP errors are separated by survey month within the target quarter. Inflation is matched to the exact month 11 months after issuance. Benchmarks use the same matched sample: previous-year same-quarter growth for GDP; previous-month inflation for CPI. Actuals are revised, so this is not a real-time vintage backtest. The non-mining survey is selected for relevance to retail and sufficient history, not a claim that it outperforms every alternative.")
    st.link_button("BCCh methodology: online retail","https://www.bcentral.cl/documents/d/banco-central/nota_tecnica_ivocm")
rows=[{'series':k,'date':d,'value':v,'unit':s['unit'],'publisher':s['publisher'],'retrieved_at':s['retrieved_at']} for k,s in series.items() for d,v in s['rows']]
if rows: st.download_button('Download source observations',pd.DataFrame(rows).to_csv(index=False),'chile-observations.csv','text/csv')
