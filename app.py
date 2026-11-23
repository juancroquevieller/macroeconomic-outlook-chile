from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from model import monthly,quarterly,refs,evaluate
ROOT=Path(__file__).parent
st.set_page_config(page_title="Chile | Economy & Retail",page_icon="🇨🇱",layout="wide")
st.markdown("""<style>
.block-container{padding:4.5rem 2.2rem 2rem;max-width:1500px}
h1{letter-spacing:-.04em!important;font-size:2.7rem!important;padding-bottom:.25rem!important}
h3{font-size:1.3rem!important;letter-spacing:-.02em}
[data-testid="stSidebar"]{min-width:230px!important;max-width:230px!important}
[data-testid="stSidebar"] .block-container{padding:2rem 1rem}
[data-testid="stMetric"]{background:#f2f7f6;padding:16px 18px;border-radius:10px;border-top:3px solid #167565}
[data-testid="stMetricLabel"] p{white-space:normal!important;font-size:.95rem!important}
[data-testid="stMetricValue"]{font-size:2rem!important;letter-spacing:-.03em}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-color:#dfe7e7!important;border-radius:12px!important}
[data-testid="stCaptionContainer"]{color:#536872;font-size:.86rem}
.readout{display:flex;gap:18px;flex-wrap:wrap;margin:4px 0 0;line-height:1.6;font-size:14px}
.readout b{font-size:17px;margin-left:5px}
.channel-table{width:100%;border-collapse:collapse;font-size:14px}
.channel-table th{font-size:12px;color:#536872;font-weight:600;text-align:right;border-bottom:1px solid #dfe7e7;padding:9px 5px}
.channel-table td{padding:12px 5px;border-bottom:1px solid #edf1f1;text-align:right;font-variant-numeric:tabular-nums}
.channel-table td:first-child,.channel-table th:first-child{text-align:left;width:42%}
@media(max-width:700px){
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stMetric"]) {gap:12px!important}
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stMetric"]) > [data-testid="stColumn"] {min-width:calc(50% - 6px)!important;width:calc(50% - 6px)!important;flex:1 1 calc(50% - 6px)!important}
[data-testid="stMetric"]{padding:12px!important;min-height:105px}
[data-testid="stMetricLabel"] p{font-size:.85rem!important}
.block-container{padding:4rem 1rem 1rem}h1{font-size:2rem!important}.readout{gap:9px}}
</style>""",unsafe_allow_html=True)
st.caption("CHILE  /  ECONOMIC OBSERVATORY")
st.title("Economy & Retail")
st.write("A clear view of Chile’s economy and the forces shaping goods retail.")
path=ROOT/'data/snapshot.json'
data=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'series':{}}
series=data['series']
view=st.sidebar.radio("Explore",["Macroeconomic outlook","Retail outlook","Assignment view","Sources & methodology"])
window=st.sidebar.selectbox("History",["5 years","Since 2018","10 years","All available"])
cut={'Since 2018':pd.Timestamp('2018-01-01'),'5 years':pd.Timestamp.now()-pd.DateOffset(years=5),'10 years':pd.Timestamp.now()-pd.DateOffset(years=10),'All available':pd.Timestamp('1900-01-01')}[window]
st.sidebar.caption("Complete calendar quarters. Monthly releases appear separately as latest signals.")
def stamp(value):
    return pd.Timestamp(value).tz_convert('America/Chicago').strftime('%b %d, %Y · %H:%M %Z') if value else 'Not completed'
st.caption("Updated "+stamp(data.get('last_success'))+" · Official data · Refreshes on the 1st & 16th")
st.sidebar.caption("Last refresh attempt: "+stamp(data.get('last_attempt')))
if data.get('failures'): st.warning("Partial refresh: some series retain their previous valid observations. See Sources & methodology.")
if not series: st.info("Official data is being connected. No synthetic observations are displayed.")
COLORS=['#167565','#d07931','#7764a5','#3578ab','#b24e66']
SHORT={'gdp':'Total GDP','mining':'Mining','nonmining':'Non-mining','cpi':'Inflation','tpm':'Policy rate',
'eee_nonmining':'Non-mining outlook','eee_inflation':'Inflation outlook','online_all':'Online sales','penetration_all':'Online share',
'consumption_durable':'Durable goods','consumption_nondurable':'Non-durable goods','durables':'Durables','nondurables':'Non-durables',
'participation':'Participation','offline':'In-store sales','sales_expectations':'Sales sentiment','imacec':'Non-mining activity'}
def label(k): return SHORT.get(k,series.get(k,{}).get('label',k))
def source(keys):
    with st.expander("Sources & definitions"):
        dependencies={'participation':['workforce','population'],'offline':['online_all','penetration_all']}
        expanded=list(dict.fromkeys(k for key in keys for k in dependencies.get(key,[key])))
        for key in expanded:
            spec=series.get(key)
            if spec:
                st.caption(f"{label(key)} · {spec['publisher']} · {spec['frequency'].lower()} · latest source observation {spec['rows'][-1][0]} · [Original series]({spec.get('source_url','')})")
        st.caption("Charts use complete calendar quarters. Monthly observations are aggregated before growth is calculated. Dates and native units are detailed in Sources & methodology.")

def style(fig,unit,height=310):
    fig.update_layout(template='plotly_white',height=height,margin=dict(l=10,r=15,t=20,b=10),
        font=dict(family='Arial, sans-serif',size=13,color='#354f5b'),yaxis_title=unit,
        legend=dict(orientation='h',y=-.2,x=0,font=dict(size=12)),hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
    fig.update_xaxes(showgrid=False,tickformat='%Y',nticks=6)
    fig.update_yaxes(gridcolor='#e9eeee',zeroline=True,zerolinecolor='#bdcbcf')
    return fig

def draw(title,keys,growth=None,unit=None,target=None,forecast=None):
    st.subheader(title)
    fig=go.Figure();units=set();readouts=[];dates=[]
    for i,k in enumerate(keys):
        values=quarterly(data,k,growth);values=values[values.index>=cut]
        if not len(values): continue
        isgrowth=growth if growth is not None else series.get(k,{}).get('growth',k=='offline')
        u='% YoY' if isgrowth else series.get(k,{}).get('unit','%')
        units.add(u);dates.append(str(values.index[-1].to_period('Q')))
        suffix='%' if '%' in u else ''
        readouts.append(f'<span style="color:{COLORS[i%5]}">{label(k)} <b>{values.iloc[-1]:,.1f}{suffix}</b></span>')
        fig.add_trace(go.Scatter(x=values.index+pd.offsets.QuarterEnd(0),y=values,name=label(k),mode='lines',
            line=dict(color=COLORS[i%5],width=2.5),hovertemplate='%{x|%b %Y}: %{y:,.2f}<extra>%{fullData.name}</extra>'))
    if not fig.data: st.info("No verified observations available.");return
    st.markdown('<div class="readout">'+''.join(readouts)+'</div>',unsafe_allow_html=True)
    st.caption('Latest complete quarter: '+', '.join(dict.fromkeys(dates)))
    if target is not None: fig.add_hline(y=target,line_dash='dot',line_color='#778d97',annotation_text=f"{target:g}% target",annotation_position='top left')
    if forecast:
        fs=monthly(data,forecast)
        if len(fs):
            d,v=fs.index[-1],fs.iloc[-1]
            when=d+pd.DateOffset(months=11) if forecast=='eee_inflation' else d+pd.offsets.QuarterEnd(0)
            name=('EEE inflation' if forecast=='eee_inflation' else 'EEE non-mining')+' · '+when.strftime('%b %Y')
            fig.add_trace(go.Scatter(x=[when],y=[v],name=name,mode='markers',marker=dict(symbol='diamond-open',size=11,color='#7764a5'),hovertemplate='Survey issued '+d.strftime('%b %Y')+'<br>Target %{x|%b %Y}: %{y:.1f}%<extra></extra>'))
    st.plotly_chart(style(fig,unit or ', '.join(sorted(units))),width='stretch',config={'displayModeBar':False})
    source(keys+([forecast] if forecast else []))

def signals(keys):
    columns=st.columns(len(keys))
    for col,key in zip(columns,keys):
        s=monthly(data,key)
        if len(s):
            spec=series[key]; v=s.iloc[-1]
            if spec.get('growth') and len(s)>12 and s.index[-1]-pd.DateOffset(months=12) in s.index:
                v=100*(v/s.loc[s.index[-1]-pd.DateOffset(months=12)]-1);unit='% YoY'
            else: unit=spec['unit']
            col.metric(label(key),f"{v:,.1f}"+('%' if '%' in unit else ''),help=spec.get('source_title',spec['label']))
            col.caption((('Target '+(s.index[-1]+pd.DateOffset(months=11)).strftime('%b %Y')) if key=='eee_inflation' else ('Target '+str(s.index[-1].to_period('Q'))) if key.startswith('eee_') else s.index[-1].strftime('%b %Y'))+' · '+unit)
def fx_details():
    with st.expander("Historical reference range · what might relative prices imply?"):
        st.write("Two anchors: January 2010–December 2014 and January 2015–September 2019. The second ends before the October 2019 social unrest.")
        result=refs(data);fig=go.Figure()
        for i,(name,s) in enumerate(result.items()):
            counts=s.resample('QS').count();s=s.resample('QS').mean().where(counts==3).dropna();s=s[(s.index>=cut)&(s.index.to_period('Q')<pd.Timestamp.now().to_period('Q'))]
            fig.add_trace(go.Scatter(x=s.index+pd.offsets.QuarterEnd(0),y=s,name=name,fill='tonexty' if i else None,line=dict(dash='dot')))
        observed=quarterly(data,'fx',False);observed=observed[observed.index>=cut]
        if len(observed): fig.add_trace(go.Scatter(x=observed.index+pd.offsets.QuarterEnd(0),y=observed,name='Observed CLP/USD',line=dict(color=COLORS[0])))
        if result: st.plotly_chart(style(fig,'CLP per USD',350),width='stretch',config={'displayModeBar':False})
        else: st.info("Complete common CPI/FX history is not yet available.")
        st.latex(r"q_t=S_t\frac{CPI_{US,t}}{CPI_{Chile,t}},\quad S_t^{ref}=median(q_{reference})\frac{CPI_{Chile,t}}{CPI_{US,t}}")
        st.write("A higher CLP/USD number means a weaker peso. The band represents sensitivity to historical reference periods, not a confidence interval, official fair value, or forecast. Structural changes can place the exchange rate outside it. References stop at the latest common month with all three inputs.")
        st.caption("Monthly calculations precede quarterly averaging. The bilateral reference is distinct from BCCh’s multilateral TCR.")
if view=='Macroeconomic outlook':
    st.subheader("Latest signals");signals(['imacec','eee_nonmining','eee_inflation','tpm'])
    st.write("")
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True):
        draw("Economic activity",['gdp','mining','nonmining'],forecast='eee_nonmining')
        st.caption("Real growth · official direct mining split. The diamond is the non-mining survey outlook.")
    with b,st.container(border=True):
        draw("Inflation & policy",['cpi','tpm'],unit='Percent',target=3,forecast='eee_inflation')
        st.caption("CPI inflation and policy rate at quarter-end. The diamond targets the stated future month.")
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True):
        which=st.radio("Exchange-rate measure",['Nominal CLP/USD','Real exchange-rate index'],horizontal=True)
        draw("Exchange rates",['fx' if which.startswith('Nominal') else 'tcr'],False)
        st.caption("A higher CLP/USD means a weaker peso.")
        fx_details()
    with b,st.container(border=True):
        employment=st.radio('Labor measure',['Unemployment','Participation'],horizontal=True)
        draw("Employment",['unemployment' if employment=='Unemployment' else 'participation'],False,unit='% of workforce' if employment=='Unemployment' else '% of population aged 15+')
        w=quarterly(data,'workforce',False);part=quarterly(data,'participation',False)
        if len(w) and len(part): st.caption(f"Workforce: {w.iloc[-1]:.2f} million · Participation: {part.iloc[-1]:.1f}% · {w.index[-1].to_period('Q')}")
        st.caption("INE calendar-quarter estimates. Separate views keep changes in each rate visible.")
elif view=='Retail outlook':
    st.subheader("Latest signals");signals(['retail','online_all','penetration_all','sales_expectations'])
    st.write("")
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True):
        demand=st.radio('Demand measure',['Goods consumption','Sales expectations'],horizontal=True)
        if demand=='Goods consumption':
            draw("Consumer demand",['nonmining','consumption_durable','consumption_nondurable'])
            st.caption('Household goods consumption and domestic retail turnover cover different concepts.')
        else:
            draw("Consumer demand",['sales_expectations'],False,unit='Diffusion index')
            st.caption('Commerce sales expectations: survey sentiment, not a sales-growth forecast.')
    with b,st.container(border=True):
        mode=st.radio('Retail measure',['Real growth','Nominal sales'],horizontal=True)
        draw("Retail scale & categories",['retail','durables','nondurables'] if mode=='Real growth' else ['retail_value'],None if mode=='Real growth' else False)
        st.caption("INE volume growth / IVE nominal sales in CLP billions. Category indices do not establish monetary shares.")
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True):
        mode=st.radio('Online / in-store measure',['Online share','Sales growth'],horizontal=True)
        if mode=='Online share':
            st.subheader("Online versus in-store")
            p=quarterly(data,'penetration_all',False);p=p[p.index>=cut]
            if len(p):
                st.markdown(f'<div class="readout"><span style="color:#167565">Online <b>{p.iloc[-1]:.1f}%</b></span><span>In-store <b>{100-p.iloc[-1]:.1f}%</b></span></div>',unsafe_allow_html=True)
                st.caption('Latest complete quarter: '+str(p.index[-1].to_period('Q')))
            fig=go.Figure()
            for name,values,color in [('Online',p,COLORS[0]),('In-store',100-p,'#dae5e3')]:
                fig.add_trace(go.Bar(x=values.index+pd.offsets.QuarterEnd(0),y=values,name=name,marker_color=color))
            st.plotly_chart(style(fig,'% of nominal sales').update_layout(barmode='stack'),width='stretch',config={'displayModeBar':False})
            source(['online_all','penetration_all'])
        else: draw("Online versus in-store",['online_all','offline'],True,unit='Nominal % YoY')
        st.caption("BCCh experimental online retail universe. In-store growth is implied within this same population; no estimated CLP split.")
    with b,st.container(border=True):
        st.subheader("Retail channels")
        names=['supermarkets','department','specialists','platforms','other'];rows=[]
        short={'supermarkets':'Supermarkets','department':'Department & home','specialists':'Specialists','platforms':'Online platforms','other':'Other retailers'}
        for key in names:
            p=quarterly(data,'penetration_'+key,False);g=quarterly(data,'online_'+key,True)
            common=p.index.intersection(g.index)
            if len(common):
                d=common[-1];prior=d-pd.DateOffset(years=1)
                rows.append({'Channel':short[key],'Quarter':str(d.to_period('Q')),'Online YoY %':g[d],'Online share %':p[d],'Share change pp':p[d]-p.get(prior,float('nan'))})
        if rows:
            st.caption('Latest complete quarter: '+', '.join(dict.fromkeys(r['Quarter'] for r in rows)))
            table='<table class="channel-table"><thead><tr><th>Channel</th><th>Online YoY</th><th>Online share</th><th>YoY Δ pp</th></tr></thead><tbody>'
            for r in rows:
                table+=f"<tr><td>{r['Channel']}</td><td>{r['Online YoY %']:.1f}%</td><td>{r['Online share %']:.1f}%</td><td>{r['Share change pp']:+.1f}</td></tr>"
            st.markdown(table+'</tbody></table>',unsafe_allow_html=True)
        st.caption("Nominal online sales growth, share of each channel’s sales, and annual share change. Channel sizes are not comparable from these indices.")
        with st.expander('Explore a channel over time'):
            selected=st.selectbox('Channel detail',names,format_func=lambda k:label('online_'+k))
            draw("Online penetration",['penetration_'+selected],False)
        st.caption("Department & home includes home improvement. Specialists cover apparel, footwear and household goods. Platforms are not company market shares or marketplace GMV.")
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
if rows and view=='Sources & methodology': st.download_button('Download source observations',pd.DataFrame(rows).to_csv(index=False),'chile-observations.csv','text/csv')
