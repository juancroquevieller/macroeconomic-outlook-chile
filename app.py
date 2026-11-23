from pathlib import Path
from html import escape
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from model import monthly,quarterly,observations,refs,evaluate
ROOT=Path(__file__).parent
st.set_page_config(page_title='Chile | Macro & Retail',page_icon='CL',layout='wide')
st.markdown('''<style>
.block-container{padding:2.7rem 2rem 1rem;max-width:1900px}
h1{font-size:1.9rem!important;font-weight:600!important;letter-spacing:-.025em;padding-bottom:.4rem!important}
h3{font-size:1.2rem!important;letter-spacing:-.02em}
[data-testid="stDialog"] div:has(> [role="dialog"]){width:calc(100vw - 32px)!important;max-width:calc(100vw - 32px)!important} [data-testid="stDialog"] [role="dialog"]{width:100%!important;max-width:100%!important;height:94vh;overflow:auto} [data-testid="stDialog"] [data-testid="stVerticalBlock"]{max-width:100%;min-width:0} [data-testid="stDialog"] [data-testid="stPlotlyChart"]{max-width:100%} [data-testid="stVerticalBlock"]{gap:.65rem} .readout{margin-top:4px}
[data-testid="stCaptionContainer"] p{color:#526773!important;font-size:.86rem!important}
[data-testid="stCaptionContainer"]{color:#526773!important} .readout{display:flex;gap:16px;flex-wrap:wrap;font-size:14px;line-height:1.6;margin:0 0 3px}
.chart-description{font-size:13px;color:#435b68;line-height:1.4;margin:0 0 2px}.readout b{font-size:14px;margin-left:4px}
.channel-table{width:100%;border-collapse:collapse;font-size:14px}
.channel-table th,.channel-table td{text-align:right;padding:10px 5px;border-bottom:1px solid #e3eaea}
.channel-table th{font-size:13px;color:#526773}
.channel-table td:first-child,.channel-table th:first-child{text-align:left;width:38%}
@media(max-width:700px){.block-container{padding:3.7rem 1rem 1rem}h1{font-size:1.55rem!important}.readout{gap:10px}}
</style>''',unsafe_allow_html=True)
data=json.loads((ROOT/'data/snapshot.json').read_text(encoding='utf-8'))
series=data['series']
view=st.radio('Explore',['Macroeconomic outlook','Retail outlook','Sources & methodology'],horizontal=True,label_visibility='collapsed')
freq,left,right,spacer=st.columns([1,1,1,2],vertical_alignment='bottom')
with freq: timeframe=st.radio('Timeframe',['Monthly','Quarterly'],horizontal=True)
today=pd.Timestamp.now(tz='America/Chicago').tz_localize(None).normalize()
earliest=min(pd.Timestamp(v['rows'][0][0]) for v in series.values() if v['rows'])
code='Q' if timeframe=='Quarterly' else 'M'
limit=(today.to_period('M')+12).end_time.normalize()
periods=pd.period_range(earliest,limit,freq=code)
periods=periods[periods.end_time.normalize()<=limit]
def period_label(p): return f'{p.year} Q{p.quarter}' if code=='Q' else p.strftime('%Y · %b')
def pick_period(name,default,key,frequency=None):
    code='Q' if (frequency or timeframe)=='Quarterly' else 'M'
    periods=pd.period_range(earliest,limit,freq=code)
    periods=periods[periods.end_time.normalize()<=limit]
    default=min(max(default.asfreq(code),periods[0]),periods[-1])
    year_col,part_col=st.columns([1,1],gap='small')
    years=sorted(set(periods.year))
    with year_col: year=st.selectbox(name+' year',years,index=years.index(default.year),key=key+'_year')
    available=[p for p in periods if p.year==year]
    parts=[p.quarter if code=='Q' else p.month for p in available]
    preferred=default.quarter if code=='Q' else default.month
    part_key=key+'_part'
    if part_key in st.session_state and st.session_state[part_key] not in parts:
        st.session_state[part_key]=min(parts,key=lambda v:abs(v-st.session_state[part_key]))
    with part_col:
        part=st.selectbox(name+(' quarter' if code=='Q' else ' month'),parts,index=parts.index(preferred) if preferred in parts else len(parts)-1,format_func=lambda n:f'Q{n}' if code=='Q' else pd.Timestamp(2000,n,1).strftime('%b'),key=part_key)
    return available[parts.index(part)]
with left: first=pick_period('From',periods[max(0,len(periods)-72 if code=='M' else len(periods)-24)],'from_'+code)
with right: last=pick_period('To',today.to_period(code),'to_'+code)
start=first.start_time;end=last.end_time.normalize()
if start>end: st.error('Choose a starting period before the ending period.');st.stop()
def stamp(v): return pd.Timestamp(v).tz_convert('America/Chicago').strftime('%d %b %Y · %H:%M %Z') if v else 'Not completed'
def period(d,f): return f'Q{d.quarter} {d.year}' if f=='Quarterly' else d.strftime('%b %Y')
relevant=['imacec_total','cpi','fx','unemployment'] if view=='Macroeconomic outlook' else ['retail','retail_value','online_all']
latest=max((observations(data,k,timeframe).index.max() for k in relevant),default=pd.NaT)
with spacer: st.caption('Refreshed '+stamp(data.get('last_success'))+'  |  Newest available: '+period(latest,timeframe))
if data.get('failures'): st.warning('Partial refresh: some series retain previous observations. See Sources & methodology.')
COLORS=['#014169','#37968C','#00C1D5','#00859B','#78365F']
LABELS={'gdp':'Total GDP','mining':'Mining GDP','nonmining':'Non-mining GDP','imacec_total':'Total IMACEC','imacec_mining':'Mining IMACEC','imacec':'Non-mining IMACEC','imacec_commerce':'Commerce IMACEC','cpi':'CPI inflation','tpm':'Policy rate','participation':'Participation','offline':'In-store sales','online_all':'Online sales','penetration_all':'Online share','consumption_durable':'Durable goods','consumption_nondurable':'Non-durable goods','durables':'Durables','nondurables':'Non-durables','retail_value':'Retail sales','sales_expectations':'Sales expectations'}
def label(k): return LABELS.get(k,series.get(k,{}).get('label',k))
def grain(keys,requested=None):
    return 'Quarterly' if any(series.get(k,{}).get('frequency')=='QUARTERLY' for k in keys) else requested or timeframe
def ends(index,f): return index.to_period('Q' if f=='Quarterly' else 'M').end_time.normalize()
def trim(s,f):
    dates=ends(s.index,f)
    return s[(dates>=start)&(dates<=end)]
def values(k,f=None,growth=None): return trim(observations(data,k,f or timeframe,growth),f or timeframe)
def period(d,f): return f'Q{d.quarter} {d.year}' if f=='Quarterly' else d.strftime('%b %Y')
source_panels={}
def source(keys,f,title=''):
    panel=st.expander('Sources & definitions')
    source_panels[title]=panel
    with panel:
        deps={'participation':['workforce','population'],'offline':['online_all','penetration_all']}
        for key in dict.fromkeys(k for item in keys for k in deps.get(item,[item])):
            s=series.get(key)
            if s: st.caption(f"{label(key)} · {s['publisher']} · native {s['frequency'].lower()} · {s['unit']} · [Original series]({s.get('source_url','')}) · available {s['rows'][0][0]} to {s['rows'][-1][0]}")
        st.caption('Monthly YoY compares the same month last year. Quarterly growth is calculated after aggregation. Indices and FX are averaged; sales flows are summed; CPI and TPM use period-end values. Labor observations are rolling three-month estimates; quarterly mode selects calendar-quarter endpoints. No interpolation.')
def chart_description(fig):
    f=(fig.layout.meta or {}).get('frequency',timeframe)
    keys=[(t.meta or {}).get('key','') for t in fig.data]
    if 'imacec_total' in keys or 'gdp' in keys:
        return 'Real growth vs the same period last year (%) | '+('IMACEC monthly activity index' if f=='Monthly' else 'Quarterly GDP')
    if 'cpi' in keys:return 'Consumer-price inflation: year over year | Policy rate: period-end (%)'
    if 'fx' in keys:return 'Nominal CLP per USD (left) | Real exchange-rate index (right) | Higher = weaker peso'
    if 'unemployment' in keys:return 'Unemployment: % of workforce (left) | Participation: % of age 15+ population (right)'
    if 'sales_expectations' in keys:return 'Commerce business sentiment | Index: above 50 = net optimism'
    if 'retail_value' in keys:return 'Nominal retail sales | CLP billions per period | Includes price changes'
    if any(k.startswith('consumption_') for k in keys):return 'Real household goods consumption and non-mining GDP | Growth vs a year earlier (%) | Quarterly'
    if 'imacec_commerce' in keys:return 'Real activity growth vs a year earlier (%) | Commerce includes wholesale, retail and vehicles'
    if 'retail' in keys:return 'Retail sales volume | Inflation-adjusted growth vs the same period last year (%)'
    if any(k.startswith('penetration_') for k in keys):return 'Online share of nominal retail sales (%) | Experimental BCCh coverage'
    if 'online_all' in keys:return 'Nominal sales growth vs the same period last year (%) | Online and implied in-store sales'
    if any(k.startswith('online_') for k in keys):return 'Channel online sales | Nominal growth vs the same period last year (%)'
    return f+' | '+str(fig.layout.yaxis.title.text or '')

def coverage_note(fig,f):
    anchors=[t for t in fig.data if 'anchor' in (t.meta or {})]
    if anchors:
        dates=[pd.Timestamp(x) for t in anchors for x in t.x]
        if dates:st.caption('FX reference coverage: '+period(min(dates),f)+' to '+period(max(dates),f)+'. Limited by common CPI data; not forecasts.')

def style(fig,unit,height=350):
    fig.update_layout(template='plotly_white',height=height,margin=dict(l=8,r=14,t=34 if fig.layout.annotations else 12,b=8),font=dict(family='Arial, sans-serif',size=13,color='#354f5b'),yaxis_title=unit,legend=dict(orientation='h',y=-.22,x=0,font=dict(size=12)),hovermode='x unified',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
    f=(fig.layout.meta or {}).get('frequency',timeframe)
    fig.update_xaxes(showgrid=False,nticks=6,tickformat='Q%q %Y' if f=='Quarterly' else '%b %y' if (end-start).days<1100 else '%Y',hoverformat='Q%q %Y' if f=='Quarterly' else '%b %Y')
    for trace in fig.data:
        if trace.customdata is None:
            trace.customdata=[period(pd.Timestamp(x),f) for x in trace.x]
            trace.hovertemplate='%{customdata}: %{y:,.2f}<extra>%{fullData.name}</extra>'
    fig.update_yaxes(gridcolor='#e6eded',zeroline=True,zerolinecolor='#b3c4c7')
    return fig
@st.dialog('Expanded chart workspace',width='large')
def chart_workspace(fig,unit,title):
    st.subheader(title)
    st.caption('Select lines, adjust the period and axes, or drag to zoom. Double-click the plot to reset. Toolbar: pan, zoom and PNG download.')
    requested=st.radio('Chart timeframe',['Monthly','Quarterly'],index=0 if (fig.layout.meta or {}).get('frequency',timeframe)=='Monthly' else 1,horizontal=True,key='chart_frequency_'+title)
    chart_frequency='Quarterly' if any((t.meta or {}).get('key','').startswith('consumption_') for t in fig.data) else requested
    if chart_frequency!=requested: st.caption('Household consumption is published quarterly; all series in this panel remain quarterly.')
    fig=go.Figure(fig)
    mapping={'imacec_total':'gdp','imacec_mining':'mining','imacec':'nonmining'}
    if chart_frequency=='Monthly':mapping={v:k for k,v in mapping.items()}
    for trace in fig.data:
        meta=trace.meta or {}
        if 'key' in meta:
            key=mapping.get(meta['key'],meta['key'])
            obs=observations(data,key,chart_frequency,meta.get('growth'))
            if meta.get('complement'):obs=100-obs
            if len(obs):obs=obs.reindex(pd.date_range(obs.index.min(),obs.index.max(),freq='QS' if chart_frequency=='Quarterly' else 'MS'))
            trace.x=ends(obs.index,chart_frequency);trace.y=obs
            trace.meta={**meta,'key':key}
            if 'complement' not in meta:trace.name=label(key)
            trace.customdata=None
        elif 'anchor' in meta:
            obs=list(refs(data).values())[meta['anchor']]
            if chart_frequency=='Quarterly':obs=obs.resample('QS').mean().where(obs.resample('QS').count()==3).dropna()
            trace.x=ends(obs.index,chart_frequency);trace.y=obs;trace.customdata=None
    # GDP consensus is a quarterly forecast, never a monthly IMACEC point.
    fig.data=tuple(t for t in fig.data if chart_frequency=='Quarterly' or (t.meta or {}).get('forecast')!='eee_nonmining')
    if chart_frequency=='Quarterly' and title=='Economic activity' and not any((t.meta or {}).get('forecast')=='eee_nonmining' for t in fig.data):
        survey=monthly(data,'eee_nonmining');survey=survey[survey.index<=end]
        if len(survey):
            due=survey.index[-1].to_period('Q').end_time.normalize()
            fig.add_trace(go.Scatter(x=[due],y=[survey.iloc[-1]],name='Survey target '+period(due,'Quarterly'),mode='markers',meta={'forecast':'eee_nonmining'},marker=dict(symbol='diamond-open',size=11,color=COLORS[3])))
    fig.update_layout(meta={'frequency':chart_frequency})
    fig=style(fig,unit,560)
    st.markdown('<div class="chart-description">'+escape(chart_description(fig))+'</div>',unsafe_allow_html=True)
    coverage_note(fig,chart_frequency)
    names=[t.name for t in fig.data]
    chosen=st.multiselect('Variables',names,default=[t.name for t in fig.data if t.visible!='legendonly'])
    ca,cb=st.columns(2)
    with ca: fp=pick_period('Chart from',first,'chart_from_'+chart_frequency,chart_frequency)
    with cb: tp=pick_period('Chart to',last,'chart_to_'+chart_frequency,chart_frequency)
    if fp>tp: st.error('Chart from must precede Chart to.');return
    edited=go.Figure(fig)
    for trace in edited.data: trace.visible=trace.name in chosen
    edited.update_xaxes(range=[fp.start_time,tp.end_time.normalize()])
    clipped=0
    for axis in ['yaxis','yaxis2']:
        if axis=='yaxis2' and not any(t.yaxis=='y2' for t in fig.data):continue
        axis_name='Left axis' if axis=='yaxis' else 'Right axis'
        col1,col2,col3=st.columns([2,1,1])
        with col1: mode=st.selectbox(axis_name,['Automatic','Custom range'],key=title+axis)
        vals=[float(y) for t in fig.data if t.name in chosen and (t.yaxis or 'y')==('y' if axis=='yaxis' else 'y2') for x,y in zip(t.x,t.y) if pd.notna(y) and fp.start_time<=pd.Timestamp(x)<=tp.end_time]
        axis_values=vals+[float(sh.y0) for sh in fig.layout.shapes if axis=='yaxis' and sh.type=='line' and sh.yref=='y' and sh.y0==sh.y1]
        lo,hi=(min(axis_values),max(axis_values)) if axis_values else (0.,100.)
        with col2: low=st.number_input(axis_name+' minimum',value=float(lo),disabled=mode=='Automatic',key=title+axis+'lo')
        with col3: high=st.number_input(axis_name+' maximum',value=float(hi if hi>lo else lo+1),disabled=mode=='Automatic',key=title+axis+'hi')
        if mode=='Automatic':
            pad=max((hi-lo)*.12,.3)
            edited.update_layout(**{axis:dict(range=[lo-pad,hi+pad],autorange=False)})
        if mode=='Custom range':
            if low>=high: st.error('Axis minimum must be less than maximum.');return
            edited.update_layout(**{axis:dict(range=[low,high],autorange=False)})
            clipped+=sum(v<low or v>high for v in vals)
    if clipped: st.warning(f'{clipped} selected observations fall outside the custom axes. They remain in the data download; reset to Automatic to see them.')
    edited.update_layout(height=560)
    st.plotly_chart(edited,width='stretch',config={'displayModeBar':True,'displaylogo':False,'scrollZoom':True})
    rows=[{'series':t.name,'period':x,'value':y} for t in edited.data if t.name in chosen for x,y in zip(t.x,t.y) if fp.start_time<=pd.Timestamp(x)<=tp.end_time]
    st.download_button('Download selected data',pd.DataFrame(rows).to_csv(index=False),title.lower().replace(' ','-')+'.csv','text/csv')
    st.caption('CSV includes the selected traces and periods. No observations are removed when axes are narrowed. Historical values use the latest revised data.')

def render(fig,unit,height=350,title=None):
    title=title or st.session_state.get('_chart_title','Chart')
    fig=style(fig,unit,height)
    fig.update_xaxes(range=[start,end])
    for axis,ref in [('yaxis','y'),('yaxis2','y2')]:
        ys=[float(y) for t in fig.data if t.visible!='legendonly' and (t.yaxis or 'y')==ref for x,y in zip(t.x,t.y) if pd.notna(y) and start<=pd.Timestamp(x)<=end]
        if axis=='yaxis': ys.extend(float(sh.y0) for sh in fig.layout.shapes if sh.type=='line' and sh.yref=='y' and sh.y0==sh.y1)
        if ys and fig.layout.barmode!='stack':
            pad=max((max(ys)-min(ys))*.12,.3)
            fig.update_layout(**{axis:dict(range=[min(ys)-pad,max(ys)+pad])})
    heading,button=st.columns([3,2],vertical_alignment='center')
    with heading: st.subheader(title)
    with button:
        if st.button('Expand / customize',key='expand_'+title,use_container_width=True): chart_workspace(fig,unit,title)
    st.markdown('<div class="chart-description">'+escape(chart_description(fig))+'</div>',unsafe_allow_html=True)
    # Keep full history for the editor, but let the overview autoscale its visible
    # window when the user toggles a legend item (including initially hidden lines).
    displayed=go.Figure(fig)
    for trace in displayed.data:
        indices=[i for i,x in enumerate(trace.x) if start<=pd.Timestamp(x)<=end]
        original_x,original_y,original_custom=list(trace.x),list(trace.y),list(trace.customdata) if trace.customdata is not None else None
        trace.x=[original_x[i] for i in indices];trace.y=[original_y[i] for i in indices]
        if original_custom is not None:trace.customdata=[original_custom[i] for i in indices]
        if not indices and 'forecast' in (trace.meta or {}):trace.showlegend=False
    if displayed.layout.barmode!='stack':displayed.update_yaxes(range=None,autorange=True)
    st.plotly_chart(displayed,width='stretch',config={'displayModeBar':'hover','displaylogo':False,'modeBarButtonsToRemove':['select2d','lasso2d']})

def expectation(key):
    s=monthly(data,key);s=s[s.index<=end]
    if not len(s): return
    d,v=s.index[-1],s.iloc[-1]
    target=(d+pd.DateOffset(months=11)).strftime('%b %Y') if key=='eee_inflation' else period(d,'Quarterly')
    name='CPI inflation' if key=='eee_inflation' else 'non-mining GDP growth'
    st.caption(f'Central bank expectations survey: {name} {v:.1f}% | target {target} | survey {d:%b %Y}')


def draw(title,keys,growth=None,unit=None,target=None,f=None,forecast=None):
    f=grain(keys,f);st.session_state['_chart_title']=title
    fig=go.Figure();fig.update_layout(meta={'frequency':f});units=set();readouts=[];dates=[];plotted=[]
    for i,k in enumerate(keys):
        s=values(k,f,growth)
        if s.empty: continue
        isgrowth=growth if growth is not None else series.get(k,{}).get('growth',k=='offline')
        u='% YoY' if isgrowth else series.get(k,{}).get('unit','%');units.add(u)
        d=s.index[-1];dates.append(period(d,f));plotted.append((k,s,u))
        suffix='%' if '%' in u else ''
        readouts.append(f'<span style="color:{(COLORS[i%5] if i%5!=2 else COLORS[3])}">{escape(label(k))} <b>{s.iloc[-1]:,.1f}{suffix}</b> <small>{period(d,f)}</small></span>')
        all_obs=observations(data,k,f,growth)
        full=all_obs.reindex(pd.date_range(all_obs.index.min(),all_obs.index.max(),freq='QS' if f=='Quarterly' else 'MS'))
        fig.add_trace(go.Scatter(x=ends(full.index,f),y=full,name=label(k),meta={'key':k,'growth':growth},visible='legendonly' if k in ['mining','imacec_mining'] else True,mode='lines',connectgaps=False,line=dict(color=COLORS[i%5],width=2.3,shape='hv' if k=='tpm' else 'linear'),hovertemplate='%{x|%b %Y}: %{y:,.2f}<extra>%{fullData.name}</extra>'))
    if not plotted:
        st.subheader(title)
        st.info('No observations in the selected range. Try an earlier/later date or a longer history.')
        source(keys,f,title)
        return
    readout_html='<div class="readout">'+''.join(r for r,k in zip(readouts,[p[0] for p in plotted]) if k not in ['mining','imacec_mining'])+'</div>'
    date_text=dates[0] if len(set(dates))==1 else ' · '.join(label(k)+': '+period(s.index[-1],f) for k,s,u in plotted)

    if forecast and (forecast=='eee_inflation' or f=='Quarterly'):
        survey=monthly(data,forecast);survey=survey[survey.index<=end]
        if len(survey):
            issued=survey.index[-1];due=(issued+pd.DateOffset(months=11)).to_period('M').end_time.normalize() if forecast=='eee_inflation' else issued.to_period('Q').end_time.normalize()
            fig.add_trace(go.Scatter(x=[due],y=[survey.iloc[-1]],name='Survey target '+period(due,'Monthly' if forecast=='eee_inflation' else 'Quarterly'),customdata=[period(due,'Monthly' if forecast=='eee_inflation' else 'Quarterly')],meta={'forecast':forecast},mode='markers',marker=dict(symbol='diamond-open',size=11,color=COLORS[3]),hovertemplate='Survey consensus: %{y:.1f}%<br>Target %{customdata}<extra></extra>'))
    if target is not None:
        fig.add_hline(y=target,line_dash='dot',line_color=COLORS[3])
        fig.add_annotation(x=0,y=1.08,xref='paper',yref='paper',text='Central bank inflation target: 3%' if target==3 else f'Neutral sentiment: {target:g}',showarrow=False,xanchor='left',yanchor='bottom',bgcolor='white',borderpad=3,font=dict(color=COLORS[0],size=12))
    render(fig,unit or ', '.join(sorted(units)),title=title)
    st.markdown(readout_html,unsafe_allow_html=True)
    if forecast: expectation(forecast)
    source(keys+([forecast] if forecast else []),f,title)
    with source_panels[title]:
        k,s,u=plotted[0];d=s.index[-1];prior=d-pd.DateOffset(months=3 if f=='Quarterly' else 1)
        if k=='retail_value':
            previous=observations(data,k,f,False).get(d-pd.DateOffset(years=1))
            if previous is not None and previous!=0: st.caption(f'Nominal sales: {100*(s[d]/previous-1):+.1f}% vs the same period a year earlier. Not inflation-adjusted.')
        elif prior in s:
            difference=s[d]-s[prior];changeunit='pp' if '%' in u else 'CLP' if k=='fx' else 'index points' if 'index' in u.lower() else u
            st.caption(f'{label(k)}: {difference:+.2f} {changeunit} vs {period(prior,f)}'+(' in the YoY growth rate.' if u=='% YoY' else '.'))
        if forecast: st.caption('EEE is survey consensus, not an observed value. GDP expectations refer to a quarter and are not monthly IMACEC forecasts. Inflation expectations retain their original monthly target even in quarterly view.')


def dual(title,left_key,right_key,left_unit,right_unit):
    fig=go.Figure()
    for i,k in enumerate([left_key,right_key]):
        obs=observations(data,k,timeframe,False)
        full=obs.reindex(pd.date_range(obs.index.min(),obs.index.max(),freq='QS' if timeframe=='Quarterly' else 'MS')) if len(obs) else obs
        fig.add_trace(go.Scatter(x=ends(full.index,timeframe),y=full,name=label(k),meta={'key':k,'growth':False},yaxis='y' if i==0 else 'y2',line=dict(color=COLORS[i],width=2.2),connectgaps=False))
    if left_key=='fx':
        for i,(name,rs) in enumerate(refs(data).items()):
            if timeframe=='Quarterly':rs=rs.resample('QS').mean().where(rs.resample('QS').count()==3).dropna()
            fig.add_trace(go.Scatter(x=ends(rs.index,timeframe),y=rs,name=['Anchor 2010–14','Anchor 2015–Sep 2019'][i],meta={'anchor':i},visible='legendonly',line=dict(color=COLORS[i+2],dash='dot')))
    fig.update_layout(yaxis2=dict(title=right_unit,overlaying='y',side='right',showgrid=False,zeroline=False,tickformat='.1f',nticks=5))
    render(fig,left_unit,title=title)
    coverage_note(fig,timeframe)
    for k in [left_key,right_key]:
        obs=values(k,growth=False)
        if len(obs):st.caption(f'{label(k)}: {obs.iloc[-1]:,.1f} · {period(obs.index[-1],timeframe)}')
    source([left_key,right_key]+(['cpi','us_cpi'] if left_key=='fx' else ['workforce']),timeframe,title)

if view=='Macroeconomic outlook':
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True):
        keys=['imacec_total','imacec','imacec_mining'] if timeframe=='Monthly' else ['gdp','nonmining','mining']
        draw('Economic activity',keys,forecast='eee_nonmining')
        with source_panels['Economic activity']:
            st.caption('IMACEC is a monthly activity proxy for GDP, not monthly GDP.' if timeframe=='Monthly' else 'Official real GDP and direct-sector mining split. Growth rates are not additive.')
    with b,st.container(border=True):
        draw('Inflation & policy',['cpi','tpm'],unit='Percent',target=3,forecast='eee_inflation')
        with source_panels['Inflation & policy']:
            st.caption('CPI: year-over-year inflation. Policy rate: period-end level. EEE diamonds mark target periods when inside the selected window.')
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True):
        dual('Exchange rates','fx','tcr','CLP per USD','Real FX index (1986=100)')
        with source_panels['Exchange rates']:
            st.caption('Higher = weaker peso. Dotted historical anchors are available through the legend or Expand; they are not forecasts.')
        with source_panels['Exchange rates']:
            st.write('Two bilateral price-adjusted reference periods: January 2010–December 2014 and January 2015–September 2019, excluding the social unrest from October 2019. Each uses median(S × US CPI / Chile CPI) in its anchor period, translated with each historical month’s relative CPI. The lines are retrospective comparisons, including dates before the reference period ended; they were not forecasts available at those dates. These are sensitivity references, not fair-value estimates or confidence bounds. They differ from the multilateral BCCh real FX index and end at the latest common CPI month.')
    with b,st.container(border=True):
        dual('Employment','unemployment','participation','Unemployment (% workforce)','Participation (% age 15+)')
        w=values('workforce',growth=False)
        if len(w):st.caption(f'Workforce {w.iloc[-1]:.2f} million · {period(w.index[-1],timeframe)}.')
elif view=='Retail outlook':
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True):
        demand=st.radio('Demand measure',['Activity','Goods consumption','Sales expectations'],horizontal=True)
        if demand=='Activity':
            draw('Consumer demand',['imacec','imacec_commerce'] if timeframe=='Monthly' else ['nonmining','imacec_commerce'])
            with source_panels['Consumer demand']:
                st.caption('Commerce IMACEC includes wholesale, retail and vehicle trade; it is broader than goods retail.')
        elif demand=='Goods consumption':
            draw('Consumer demand',['nonmining','consumption_durable','consumption_nondurable'],f='Quarterly')
            with source_panels['Consumer demand']:
                st.caption('Always quarterly: GDP and household goods consumption. No artificial monthly estimates.')
        else:
            draw('Consumer demand',['sales_expectations'],False,unit='Diffusion index',target=50)
            with source_panels['Consumer demand']:
                st.caption('Commerce sales expectations: sentiment, not a growth forecast. Above 50 indicates net optimism.')
    with b,st.container(border=True):
        mode=st.radio('Retail measure',['Real growth','Nominal sales'],horizontal=True)
        draw('Retail scale & categories',['retail','durables','nondurables'] if mode=='Real growth' else ['retail_value'],None if mode=='Real growth' else False)
        with source_panels['Retail scale & categories']:
            st.caption('Volume growth excludes price changes.' if mode=='Real growth' else 'CLP billions per selected period. Nominal levels include prices and seasonality; quarter totals sum three months.')
    a,b=st.columns(2,gap='medium')
    with a,st.container(border=True):
        mode=st.radio('Online / in-store measure',['Penetration trend','Sales growth','Sales mix'],horizontal=True)
        if mode=='Penetration trend':
            draw('Online versus in-store',['penetration_all'],False,unit='% of nominal sales')
            p=values('penetration_all',growth=False)
            if len(p):st.caption(f'In-store share: {100-p.iloc[-1]:.1f}% in {period(p.index[-1],timeframe)}.')
        elif mode=='Sales growth':draw('Online versus in-store',['online_all','offline'],True,unit='Nominal % YoY')
        else:
            st.session_state['_chart_title']='Online versus in-store';p=observations(data,'penetration_all',timeframe,False);fig=go.Figure()
            for name,s,color in [('Online',p,COLORS[0]),('In-store',100-p,COLORS[1])]:fig.add_trace(go.Bar(x=ends(s.index,timeframe),y=s,name=name,meta={'key':'penetration_all','growth':False,'complement':name=='In-store'},marker_color=color))
            render(fig.update_layout(barmode='stack',yaxis_range=[0,100]),'% of nominal sales')
            shown=trim(p,timeframe)
            if len(shown):st.caption(f'Online {shown.iloc[-1]:.1f}% | In-store {100-shown.iloc[-1]:.1f}% | {period(shown.index[-1],timeframe)}')
            source(['online_all','penetration_all'],timeframe,'Online versus in-store')
        with source_panels['Online versus in-store']:
            st.caption('Experimental BCCh retail universe. In-store growth is implied from online sales and penetration; no invented CLP split.')
    with b,st.container(border=True):
        st.subheader('Retail channels')
        names=['supermarkets','department','specialists','platforms','other'];short=['Supermarkets','Department & home','Specialists','Online platforms','Other retailers'];pairs=[];common=None
        for k in names:
            p=values('penetration_'+k,growth=False);g=values('online_'+k,growth=True)
            dates=p.index.intersection(g.index);common=dates if common is None else common.intersection(dates);pairs.append((p,g))
        if common is not None and len(common):
            d=common[-1];st.caption(timeframe+' · comparable channel snapshot: '+period(d,timeframe))
            table='<table class="channel-table"><tr><th>Retail channel</th><th>Online sales<br>YoY growth</th><th>Online<br>share</th><th>Share change<br>pp YoY</th></tr>'
            for name,(p,g) in zip(short,pairs):
                # Prior-year comparison is independent of the displayed start date.
                prior=observations(data,'penetration_'+names[short.index(name)],timeframe,False).get(d-pd.DateOffset(years=1),float('nan'))
                delta=f'{p[d]-prior:+.1f}' if pd.notna(prior) else '—'
                table+=f'<tr><td>{name}</td><td>{g[d]:.1f}%</td><td>{p[d]:.1f}%</td><td>{delta}</td></tr>'
            st.markdown(table+'</table>',unsafe_allow_html=True)
        else:st.info('No common channel observation within the selected dates.')
        source(['online_'+k for k in names]+['penetration_'+k for k in names],timeframe,'Retail channels')
        with source_panels['Retail channels']: st.caption('Nominal online growth and share within each channel—not channel market size. All rows use the same date.')
        with st.expander('Explore a channel over time'):
            selected=st.selectbox('Channel detail',names,format_func=lambda k:short[names.index(k)])
            channel_mode=st.radio('Channel measure',['Online share','Online sales growth'],horizontal=True)
            draw('Online penetration' if channel_mode=='Online share' else 'Online sales growth',['penetration_'+selected] if channel_mode=='Online share' else ['online_'+selected],channel_mode=='Online sales growth',unit='% of channel sales' if channel_mode=='Online share' else 'Nominal % YoY')
        with source_panels['Retail channels']: st.caption('Department & home includes home improvement. Specialists cover apparel, footwear and household goods. Online platforms include online-only sellers and intermediaries; this is not marketplace GMV.')

else:
    st.write('Monthly is the default. IMACEC approximates monthly economic activity; GDP and household consumption remain quarterly. Any panel with a quarterly-only input aggregates every series to quarters. Quarterly averages of IMACEC are still activity indices, not GDP. Labor series remain rolling three-month estimates in monthly mode.')
    st.write('Year-over-year growth compares the same calendar month or quarter one year earlier. Missing observations are not interpolated. Quarterly penetration uses sales weights: sum(online index) / sum(online index / monthly share). In-store relative sales = online index × (1 − share) / share. Independently based indices cannot be summed into channel monetary totals.')
    st.write('The top period selectors allow month or quarter selection, up to 12 months ahead. Expand / customize opens a large chart workspace with series, date and axis controls, zoom, image export and CSV download. Custom axes warn about clipped observations. Mining and FX reference anchors start hidden and can be selected. Dual axes use separately labeled units; matching heights do not imply equal magnitudes.')
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
