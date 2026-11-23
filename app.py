from pathlib import Path
from html import escape
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from model import monthly,quarterly,observations,refs,evaluate
ROOT=Path(__file__).parent
st.set_page_config(page_title='Chile | Macro & Retail',page_icon='🇨🇱',layout='wide')
st.markdown('''<style>
.block-container{padding:3.8rem 2rem 2rem;max-width:1500px}
h1{font-size:1.9rem!important;font-weight:600!important;letter-spacing:-.025em;padding-bottom:.4rem!important}
h3{font-size:1.2rem!important;letter-spacing:-.02em}
[data-testid="stSidebar"]{min-width:250px!important;max-width:250px!important}
[data-testid="stCaptionContainer"] p{color:#526773!important;font-size:.86rem!important}
.readout{display:flex;gap:16px;flex-wrap:wrap;font-size:14px;line-height:1.6;margin:0 0 3px}
.readout b{font-size:18px;margin-left:4px}
.channel-table{width:100%;border-collapse:collapse;font-size:14px}
.channel-table th,.channel-table td{text-align:right;padding:10px 5px;border-bottom:1px solid #e3eaea}
.channel-table th{font-size:13px;color:#526773}
.channel-table td:first-child,.channel-table th:first-child{text-align:left;width:38%}
@media(max-width:700px){.block-container{padding:3.7rem 1rem 1rem}h1{font-size:1.55rem!important}.readout{gap:10px}}
</style>''',unsafe_allow_html=True)
data=json.loads((ROOT/'data/snapshot.json').read_text(encoding='utf-8'))
series=data['series']
view=st.sidebar.radio('Explore',['Macroeconomic outlook','Retail outlook','Assignment view','Sources & methodology'])
timeframe=st.sidebar.radio('Timeframe',['Monthly','Quarterly'],horizontal=True)
history=st.sidebar.selectbox('History',['5 years','10 years','Since 2018','All available'])
today=pd.Timestamp.now().normalize()
earliest=min(pd.Timestamp(s['rows'][0][0]) for s in series.values() if s['rows'])
default_start={'5 years':today-pd.DateOffset(years=5),'10 years':today-pd.DateOffset(years=10),'Since 2018':pd.Timestamp('2018-01-01'),'All available':earliest}[history]
chosen=st.sidebar.date_input('Start / end',(max(earliest,default_start).date(),today.date()),min_value=earliest.date(),max_value=today.date(),key='dates_'+history,format='YYYY-MM-DD')
if len(chosen)!=2: st.info('Select both a start and an end date.');st.stop()
start,end=map(pd.Timestamp,chosen)
if start>end: st.error('The start date must precede the end date.');st.stop()
st.sidebar.caption('Edit either date above. Each chart uses its own available history; missing periods are not filled.')
st.sidebar.caption('Monthly: IMACEC activity proxy. Quarterly: GDP. Panels containing GDP or goods consumption stay quarterly.')
def stamp(v): return pd.Timestamp(v).tz_convert('America/Chicago').strftime('%d %b %Y · %H:%M %Z') if v else 'Not completed'
st.sidebar.caption('Last successful refresh: '+stamp(data.get('last_success')))
st.sidebar.caption('Last attempt: '+stamp(data.get('last_attempt'))+' · Scheduled 1st & 16th.')
st.title({'Macroeconomic outlook':'Macroeconomic - Chile','Retail outlook':'Retail - Chile','Assignment view':'Key indicators - Chile','Sources & methodology':'Sources & methodology - Chile'}[view])
if data.get('failures'): st.warning('Partial refresh: some series retain previous observations. See Sources & methodology.')
COLORS=['#14776a','#c46b22','#7562ad','#367fa0','#ad536d']
LABELS={'gdp':'Total GDP','mining':'Mining GDP','nonmining':'Non-mining GDP','imacec_total':'Total IMACEC','imacec_mining':'Mining IMACEC','imacec':'Non-mining IMACEC','imacec_commerce':'Commerce IMACEC','cpi':'CPI inflation','tpm':'Policy rate','participation':'Participation','offline':'In-store sales','online_all':'Online sales','penetration_all':'Online share','consumption_durable':'Durable goods','consumption_nondurable':'Non-durable goods','durables':'Durables','nondurables':'Non-durables','retail_value':'Retail sales','sales_expectations':'Sales expectations'}
def label(k): return LABELS.get(k,series.get(k,{}).get('label',k))
def grain(keys,requested=None):
    return 'Quarterly' if any(series.get(k,{}).get('frequency')=='QUARTERLY' for k in keys) else requested or timeframe
def ends(index,f): return index.to_period('Q' if f=='Quarterly' else 'M').end_time.normalize()
def trim(s,f):
    dates=ends(s.index,f)
    return s[(dates>=start)&(dates<=end)]
def values(k,f=None,growth=None): return trim(observations(data,k,f or timeframe,growth),f or timeframe)
def period(d,f): return str(d.to_period('Q')) if f=='Quarterly' else d.strftime('%b %Y')
def source(keys,f):
    with st.expander('Sources & definitions'):
        deps={'participation':['workforce','population'],'offline':['online_all','penetration_all']}
        for key in dict.fromkeys(k for item in keys for k in deps.get(item,[item])):
            s=series.get(key)
            if s: st.caption(f"{label(key)} · {s['publisher']} · native {s['frequency'].lower()} · {s['unit']} · [Original series]({s.get('source_url','')}) · available {s['rows'][0][0]} to {s['rows'][-1][0]}")
        st.caption('Monthly YoY compares the same month last year. Quarterly growth is calculated after aggregation. Indices and FX are averaged; sales flows are summed; CPI and TPM use period-end values. Labor observations are rolling three-month estimates; quarterly mode selects calendar-quarter endpoints. No interpolation.')
def style(fig,unit,height=295):
    fig.update_layout(template='plotly_white',height=height,margin=dict(l=8,r=14,t=10,b=8),font=dict(family='Arial, sans-serif',size=13,color='#354f5b'),yaxis_title=unit,legend=dict(orientation='h',y=-.22,x=0,font=dict(size=12)),hovermode='x unified',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
    fig.update_xaxes(showgrid=False,nticks=6,tickformat='%b %y' if (end-start).days<1100 else '%Y')
    fig.update_yaxes(gridcolor='#e6eded',zeroline=True,zerolinecolor='#b3c4c7')
    return fig
def render(fig,unit,height=295): st.plotly_chart(style(fig,unit,height),width='stretch',config={'displayModeBar':False})
def expectation(key):
    s=monthly(data,key);s=s[s.index<=end]
    if not len(s): return
    d,v=s.index[-1],s.iloc[-1]
    target=(d+pd.DateOffset(months=11)).strftime('%b %Y') if key=='eee_inflation' else str(d.to_period('Q'))
    name='CPI inflation' if key=='eee_inflation' else 'non-mining GDP growth'
    st.caption(f'EEE outlook · {name}: {v:.1f}% for {target} · survey {d:%b %Y}. '+('Quarterly GDP outlook, not a monthly IMACEC forecast.' if key!='eee_inflation' and timeframe=='Monthly' else 'Survey consensus, not an observed value.'))

def draw(title,keys,growth=None,unit=None,target=None,f=None,forecast=None):
    f=grain(keys,f);st.subheader(title)
    fig=go.Figure();units=set();readouts=[];dates=[];plotted=[]
    for i,k in enumerate(keys):
        s=values(k,f,growth)
        if s.empty: continue
        isgrowth=growth if growth is not None else series.get(k,{}).get('growth',k=='offline')
        u='% YoY' if isgrowth else series.get(k,{}).get('unit','%');units.add(u)
        d=s.index[-1];dates.append(period(d,f));plotted.append((k,s,u))
        suffix='%' if '%' in u else ''
        readouts.append(f'<span style="color:{COLORS[i%5]}">{escape(label(k))} <b>{s.iloc[-1]:,.1f}{suffix}</b></span>')
        full=s.reindex(pd.date_range(s.index.min(),s.index.max(),freq='QS' if f=='Quarterly' else 'MS'))
        fig.add_trace(go.Scatter(x=ends(full.index,f),y=full,name=label(k),mode='lines',connectgaps=False,line=dict(color=COLORS[i%5],width=2.3,shape='hv' if k=='tpm' else 'linear'),hovertemplate='%{x|%b %Y}: %{y:,.2f}<extra>%{fullData.name}</extra>'))
    if not plotted: st.info('No observations in the selected range. Try an earlier/later date or a longer history.');return
    st.markdown('<div class="readout">'+''.join(readouts)+'</div>',unsafe_allow_html=True)
    date_text=dates[0] if len(set(dates))==1 else ' · '.join(label(k)+': '+period(s.index[-1],f) for k,s,u in plotted)
    st.caption(f+' · latest '+date_text)
    if target is not None: fig.add_hline(y=target,line_dash='dot',line_color='#74858e',annotation_text='3% inflation target' if target==3 else f'{target:g} neutral',annotation_position='top left')
    render(fig,unit or ', '.join(sorted(units)))
    k,s,u=plotted[0];d=s.index[-1];prior=d-pd.DateOffset(months=3 if f=='Quarterly' else 1)
    if prior in s:
        difference=s[d]-s[prior];changeunit='pp' if '%' in u else 'CLP' if k=='fx' else 'index points' if 'Index' in u else u
        st.caption(f'{label(k)}: {difference:+.2f} {changeunit} vs {period(prior,f)}'+(' in the YoY growth rate.' if u=='% YoY' else '.'))
    if forecast: expectation(forecast)
    source(keys+([forecast] if forecast else []),f)

def exchange():
    mode=st.radio('Exchange-rate measure',['CLP/USD + references','Real exchange-rate index'],horizontal=True)
    if mode=='Real exchange-rate index':
        draw('Exchange rates',['tcr'],False)
        st.caption('BCCh multilateral real exchange-rate index. A rise indicates real depreciation.');return
    st.subheader('Exchange rates')
    observed=values('fx',timeframe,False);fig=go.Figure();references=[]
    for i,(name,s) in enumerate(refs(data).items()):
        if timeframe=='Quarterly':
            counts=s.resample('QS').count();s=s.resample('QS').mean().where(counts==3).dropna()
        s=trim(s,timeframe)
        if s.empty: continue
        references.append(s)
        fig.add_trace(go.Scatter(x=ends(s.index,timeframe),y=s,name=['Ref. 2010–14','Ref. 2015–Sep 19'][i],line=dict(color=['#b3a3ce','#c4ab85'][i],dash='dot',width=1.5),fill='tonexty' if i else None,fillcolor='rgba(150,130,175,.10)'))
    if len(observed):
        st.markdown(f'<div class="readout"><span style="color:{COLORS[0]}">CLP per USD <b>{observed.iloc[-1]:,.1f}</b></span></div>',unsafe_allow_html=True)
        st.caption(timeframe+' average · latest '+period(observed.index[-1],timeframe))
        fig.add_trace(go.Scatter(x=ends(observed.index,timeframe),y=observed,name='Observed CLP/USD',line=dict(color=COLORS[0],width=2.5)))
    if not fig.data: st.info('No observations in this date range.');return
    render(fig,'CLP per USD')
    st.caption('Higher = weaker peso. Shading shows two historical price-adjusted anchors, not a forecast or confidence interval.')
    with st.expander('How to interpret the reference range'):
        st.write('Anchors: January 2010–December 2014 and January 2015–September 2019. The second excludes the October 2019 social unrest. Each line uses the median bilateral real exchange rate over its reference period, translated into nominal pesos using current relative consumer prices. Structural changes can keep the peso outside this range.')
        st.latex(r'q_t=S_t CPI_{US,t}/CPI_{Chile,t},\quad S_t^{ref}=median(q_{anchor}) CPI_{Chile,t}/CPI_{US,t}')
        st.caption('Reference lines start after each anchor ends and stop at the latest common CPI/FX month. Quarterly lines require three common months. This bilateral calculation differs from BCCh’s multilateral TCR.')
    source(['fx','cpi','us_cpi'],timeframe)

if view=='Macroeconomic outlook':
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True):
        keys=['imacec_total','imacec_mining','imacec'] if timeframe=='Monthly' else ['gdp','mining','nonmining']
        draw('Economic activity',keys,forecast='eee_nonmining')
        st.caption('IMACEC is a monthly activity proxy for GDP, not monthly GDP.' if timeframe=='Monthly' else 'Official real GDP and direct-sector mining split. Growth rates are not additive.')
    with b,st.container(border=True):
        draw('Inflation & policy',['cpi','tpm'],unit='Percent',target=3,forecast='eee_inflation')
        st.caption('CPI: year-over-year inflation. Policy rate: period-end level. Forecasts stay outside the observed-data chart.')
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True): exchange()
    with b,st.container(border=True):
        mode=st.radio('Labor measure',['Unemployment','Participation'],horizontal=True)
        draw('Employment',['unemployment' if mode=='Unemployment' else 'participation'],False,unit='% of workforce' if mode=='Unemployment' else '% of population aged 15+')
        w=values('workforce',growth=False);p=values('participation',growth=False)
        if len(w) and len(p): st.caption(f'Workforce {w.iloc[-1]:.2f} million · Participation {p.iloc[-1]:.1f}% · {period(w.index[-1],timeframe)}.')
        st.caption('Monthly releases describe overlapping three-month windows ending in the labeled month.' if timeframe=='Monthly' else 'Calendar-quarter estimates selected from INE rolling-quarter releases.')
elif view=='Retail outlook':
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True):
        demand=st.radio('Demand measure',['Activity','Goods consumption','Sales expectations'],horizontal=True)
        if demand=='Activity':
            draw('Consumer demand',['imacec','imacec_commerce'] if timeframe=='Monthly' else ['nonmining','imacec_commerce'])
            st.caption('Commerce IMACEC includes wholesale, retail and vehicle trade; it is broader than goods retail.')
        elif demand=='Goods consumption':
            draw('Consumer demand',['nonmining','consumption_durable','consumption_nondurable'],f='Quarterly')
            st.caption('Always quarterly: GDP and household goods consumption. No artificial monthly estimates.')
        else:
            draw('Consumer demand',['sales_expectations'],False,unit='Diffusion index',target=50)
            st.caption('Commerce sales expectations: sentiment, not a growth forecast. Above 50 indicates net optimism.')
    with b,st.container(border=True):
        mode=st.radio('Retail measure',['Real growth','Nominal sales'],horizontal=True)
        draw('Retail scale & categories',['retail','durables','nondurables'] if mode=='Real growth' else ['retail_value'],None if mode=='Real growth' else False)
        st.caption('Volume growth excludes price changes.' if mode=='Real growth' else 'CLP billions per selected period. Nominal levels include prices and seasonality; quarter totals sum three months.')
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True):
        mode=st.radio('Online / in-store measure',['Penetration trend','Sales growth','Sales mix'],horizontal=True)
        if mode=='Penetration trend':
            draw('Online versus in-store',['penetration_all'],False,unit='% of nominal sales')
            p=values('penetration_all',growth=False)
            if len(p):st.caption(f'In-store share: {100-p.iloc[-1]:.1f}% in {period(p.index[-1],timeframe)}. Monthly shares are seasonal; compare the same month a year earlier.')
        elif mode=='Sales growth':draw('Online versus in-store',['online_all','offline'],True,unit='Nominal % YoY')
        else:
            st.subheader('Online versus in-store');p=values('penetration_all',growth=False);fig=go.Figure()
            for name,s,color in [('Online',p,COLORS[0]),('In-store',100-p,'#dbe5e3')]:fig.add_trace(go.Bar(x=ends(s.index,timeframe),y=s,name=name,marker_color=color))
            render(fig.update_layout(barmode='stack',yaxis_range=[0,100]),'% of nominal sales')
            if len(p):st.caption(timeframe+' · latest '+period(p.index[-1],timeframe))
            source(['online_all','penetration_all'],timeframe)
        st.caption('Experimental BCCh retail universe. In-store growth is implied from online sales and penetration; no invented CLP split.')
    with b,st.container(border=True):
        st.subheader('Retail channels')
        names=['supermarkets','department','specialists','platforms','other'];short=['Supermarkets','Department & home','Specialists','Online platforms','Other retailers'];pairs=[];common=None
        for k in names:
            p=values('penetration_'+k,growth=False);g=values('online_'+k,growth=True)
            dates=p.index.intersection(g.index);common=dates if common is None else common.intersection(dates);pairs.append((p,g))
        if common is not None and len(common):
            d=common[-1];st.caption(timeframe+' · comparable channel snapshot: '+period(d,timeframe))
            table='<table class="channel-table"><tr><th>Channel</th><th>Online YoY</th><th>Online share</th><th>YoY Δ pp</th></tr>'
            for name,(p,g) in zip(short,pairs):
                # Prior-year comparison is independent of the displayed start date.
                prior=observations(data,'penetration_'+names[short.index(name)],timeframe,False).get(d-pd.DateOffset(years=1),float('nan'))
                delta=f'{p[d]-prior:+.1f}' if pd.notna(prior) else '—'
                table+=f'<tr><td>{name}</td><td>{g[d]:.1f}%</td><td>{p[d]:.1f}%</td><td>{delta}</td></tr>'
            st.markdown(table+'</table>',unsafe_allow_html=True)
        else:st.info('No common channel observation within the selected dates.')
        st.caption('Nominal online growth and share within each channel—not channel market size. All rows use the same date.')
        with st.expander('Explore a channel over time'):
            selected=st.selectbox('Channel detail',names,format_func=lambda k:label('online_'+k))
            draw('Online penetration',['penetration_'+selected],False)
        st.caption('Department & home includes home improvement. Specialists cover apparel, footwear and household goods. Online platforms include online-only sellers and intermediaries; this is not marketplace GMV.')
elif view=='Assignment view':
    items=[('Economic activity','imacec_total' if timeframe=='Monthly' else 'gdp'),('Non-mining activity','imacec' if timeframe=='Monthly' else 'nonmining'),('Inflation','cpi'),('Policy rate','tpm'),('CLP per USD','fx'),('Unemployment','unemployment'),('Real retail growth','retail'),('Online penetration','penetration_all')]
    for offset in range(0,8,2):
        for col,(title,key) in zip(st.columns(2),items[offset:offset+2]):
            with col,st.container(border=True):draw(title,[key])
else:
    st.write('Monthly is the default. IMACEC approximates monthly economic activity; GDP and household consumption remain quarterly. Any panel with a quarterly-only input aggregates every series to quarters. Quarterly averages of IMACEC are still activity indices, not GDP. Labor series remain rolling three-month estimates in monthly mode.')
    st.write('Year-over-year growth compares the same calendar month or quarter one year earlier. Missing observations are not interpolated. Quarterly penetration uses sales weights: sum(online index) / sum(online index / monthly share). In-store relative sales = online index × (1 − share) / share. Independently based indices cannot be summed into channel monetary totals.')
    st.write('Start/end dates filter the observation period-end shown on the chart. Calculations retain earlier history needed for YoY growth and reference anchors. Historical date selection uses today’s revised data, not real-time vintages. EEE callouts use the latest survey issued by the selected end month and retain their explicit target date.')
    st.write('Refreshes run on the 1st and 16th. A full-success timestamp advances only after all inputs refresh; failed series retain their prior observations. Publication dates differ by series.')
    if data.get('failures'):st.json(data['failures'])
    st.dataframe(pd.DataFrame([{'Series':label(k),'Publisher':s['publisher'],'Native frequency':s['frequency'],'Unit':s['unit'],'First observation':s['rows'][0][0],'Latest observation':s['rows'][-1][0],'Retrieved':s['retrieved_at'],'Source':s.get('source_url','')} for k,s in series.items()]),hide_index=True)
    st.subheader('EEE forecast evaluation')
    pairs,metrics=evaluate(data)
    st.dataframe(metrics,hide_index=True)
    st.download_button('Download matched forecasts',pairs.to_csv(index=False),'eee-evaluation.csv')
    st.caption('Errors in percentage points against revised actuals. GDP is separated by survey month in the target quarter. Inflation targets 11 months after issuance. Matched-sample benchmarks: previous-year same-quarter GDP growth and previous-month CPI inflation. Selection emphasizes retail relevance and usable history, not proven superiority over all alternatives.')
    rows=[{'series':k,'date':d,'value':v,'unit':s['unit']} for k,s in series.items() for d,v in s['rows']]
    st.download_button('Download source observations',pd.DataFrame(rows).to_csv(index=False),'chile-observations.csv','text/csv')
