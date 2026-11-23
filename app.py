from pathlib import Path
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from economics import quarterly,yoy,reference
ROOT=Path(__file__).parent
st.set_page_config(page_title="Chile | Economy & Retail",page_icon="🇨🇱",layout="wide")
st.title("Chile | Economy & Retail")
st.caption("A personal briefing on economic activity, purchasing power and the changing retail market.")
path=ROOT/"data"/"snapshot.json"
data=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"series":{}}
series=data["series"]
view=st.sidebar.radio("View",["Macroeconomic outlook","Retail outlook","Assignment view","Sources & methodology"])
years=st.sidebar.selectbox("History",["Since 2018","5 years","10 years","All available"])
cut={"Since 2018":"2018","5 years":str(pd.Timestamp.today().year-5),"10 years":str(pd.Timestamp.today().year-10),"All available":"0000"}[years]
st.caption(f"Last successful full refresh: {data.get('last_success','Not yet completed')} · Latest attempt: {data.get('last_attempt','Not yet attempted')}")
if not series: st.warning("Data setup pending. No synthetic observations are displayed. Configure the BCCh API token and run the refresh workflow.")
if data.get("failures"): st.warning("Some sources failed at the last refresh. Their previous valid observations are retained.")
def observations(key):
    return series.get(key,{}).get("rows",[])
def values(key,growth=None):
    s=series.get(key,{})
    rows=observations(key)
    if not rows: return {}
    method=s.get("aggregation","mean")
    if s.get("frequency")=="QUARTERLY":
        from economics import quarter
        result={quarter(d):v for d,v in rows}
    elif s.get("frequency")=="DAILY":
        # Daily policy observations: retain each month's final published rate.
        monthly={}
        for d,v in rows: monthly[d[:7]+"-01"]=v
        result=quarterly(sorted(monthly.items()),"last")
    elif method in ("forecast","penetration"): return {}
    else: result=quarterly(rows,method)
    return yoy(result) if (s.get("growth") if growth is None else growth) else result
def chart(title,keys,growth=None):
    st.subheader(title)
    fig=go.Figure()
    for key in keys:
        s=series.get(key,{})
        result={d:v for d,v in values(key,growth).items() if d[:4]>=cut}
        if result: fig.add_trace(go.Scatter(x=list(result),y=list(result.values()),name=s["label"],mode="lines"))
    if not fig.data:
        st.info("Awaiting verified source series for this panel.")
        return
    fig.update_layout(height=330,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h"),template="plotly_white")
    st.plotly_chart(fig,width="stretch")
    for key in keys:
        s=series.get(key)
        if s: st.caption(f"{s['label']} · {s['publisher']} · {s['unit']} · native {s['frequency'].lower()} · latest {s['rows'][-1][0]} · quarterly {s['aggregation']}")
def latest(keys):
    cols=st.columns(len(keys))
    for col,key in zip(cols,keys):
        s=series.get(key)
        if s:
            d,v=s["rows"][-1]
            col.metric(s["label"],f"{v:,.2f}")
            col.caption(f"{s['unit']} · {d}")
if view=="Macroeconomic outlook":
    st.subheader("Latest signals")
    latest(["eee_nonmining","eee_inflation","tpm"])
    a,b=st.columns(2)
    with a: chart("Economic activity",["gdp","mining","nonmining"])
    with b:
        chart("Inflation",["cpi"])
        st.caption("Inflation target: 3% year over year. Survey expectations refer to a future target month.")
        chart("Monetary policy",["tpm"])
    a,b=st.columns(2)
    with a:
        chart("Exchange rate · CLP per USD",["fx"])
        chart("Real exchange-rate index",["tcr"])
        with st.expander("Historical exchange-rate reference range"):
            st.write("Two historical anchors: January 2010–December 2014 and January 2015–September 2019. The latter excludes the social unrest beginning in October 2019.")
            st.latex(r"q_t=S_t CPI_{US,t}/CPI_{Chile,t}")
            st.latex(r"S^{reference}_t=median(q_{reference}) CPI_{Chile,t}/CPI_{US,t}")
            st.write("The area between these references shows sensitivity to historical assumptions, not a confidence interval or forecast. Structural changes can move the exchange rate outside this range.")
            fig=go.Figure()
            for start,end in [("2010-01","2014-12"),("2015-01","2019-09")]:
                rows=reference(observations("fx"),observations("cpi"),observations("us_cpi"),start,end)
                q=quarterly(rows)
                if q: fig.add_trace(go.Scatter(x=list(q),y=list(q.values()),name=f"{start} to {end}",fill="tonexty" if len(fig.data) else None))
            if fig.data: st.plotly_chart(fig,width="stretch")
            else: st.info("Reference range awaits complete, verified Chile–US CPI and FX histories.")
    with b:
        chart("Employment",["unemployment","participation"])
        chart("Workforce · millions",["workforce"])
elif view=="Retail outlook":
    a,b=st.columns(2)
    with a:
        chart("Consumer demand",["nonmining","goods_consumption"])
        chart("Commerce confidence",["confidence"],False)
        st.caption("Confidence is a survey index, not a forecast of sales growth.")
    with b:
        chart("Retail growth · real YoY",["retail","durables","nondurables"])
        chart("Retail sales · CLP billions",["retail_value"],False)
    a,b=st.columns(2)
    with a:
        chart("Online versus in-store",["online","offline"])
        st.caption("CLP splits are shown only when monetary totals and penetration share the same coverage.")
    with b:
        st.subheader("Retail channels")
        st.dataframe(pd.DataFrame({"Channel":["Supermarkets","Department & home-improvement stores","Apparel, footwear & household equipment","Online platforms","Other retailers"],"Status":["Awaiting compatible series"]*5}),hide_index=True)
        latest(["supermarket_penetration"])
elif view=="Assignment view":
    for title,key in [("GDP growth","gdp"),("Non-mining GDP growth","nonmining"),("Inflation","cpi"),("Monetary policy rate","tpm"),("CLP per USD","fx"),("Unemployment","unemployment"),("Real retail growth","retail"),("Online penetration","penetration")]:
        chart(title,[key])
else:
    st.subheader("Definitions and source coverage")
    st.write("Complete calendar quarters only. Growth is calculated after aggregation. Nominal sales measure money spent; real indices measure volume. Non-mining activity uses the official aggregate.")
    st.write("Quarter-end inflation and policy rates; quarterly-average exchange rates; summed monetary flows. Employment uses the rolling quarters ending March, June, September and December.")
    st.write("Forecast evaluation must match survey dates to target periods. No claim of forecast accuracy is made until historical evaluation is complete.")
    st.link_button("Banco Central statistical database","https://si3.bcentral.cl/siete")
    st.link_button("API activation instructions","https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/acceso_api.html")
    st.dataframe(pd.DataFrame(json.loads((ROOT/"registry.json").read_text())),hide_index=True)
rows=[{"series":key,"date":d,"value":v,"unit":s["unit"],"publisher":s["publisher"],"retrieved_at":s["retrieved_at"]} for key,s in series.items() for d,v in s["rows"]]
if rows: st.download_button("Download source observations",pd.DataFrame(rows).to_csv(index=False),"chile-observations.csv","text/csv")
