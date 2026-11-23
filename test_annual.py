import json
import unittest
from pathlib import Path
import pandas as pd
from model import observations, annual_reference

class AnnualTests(unittest.TestCase):
    def spec(self,values,start='2020-01-01',freq='MS',aggregation='mean'):
        return dict(frequency='QUARTERLY' if freq=='QS' else 'MONTHLY',aggregation=aggregation,rows=[[d.strftime('%Y-%m-%d'),v] for d,v in zip(pd.date_range(start,periods=len(values),freq=freq),values)])

    def test_growth_from_annual_levels_not_average_growth(self):
        d={'series':{'retail':self.spec([10]*6+[100]*6+[20]*12)}}
        s=observations(d,'retail','Annual',True)
        self.assertAlmostEqual(s.loc['2021-01-01'],100*(240/660-1))
        self.assertNotAlmostEqual(s.iloc[0],10.) # average monthly YoY would be +10%

    def test_gdp_flows_sum_four_quarters_and_reject_partial_year(self):
        d={'series':{'gdp':self.spec([10,20,30,40,20,30,40,50,100,100,100],freq='QS',aggregation='native')}}
        levels=observations(d,'gdp','Annual',False)
        self.assertEqual(levels.loc['2020-01-01'],100)
        self.assertEqual(levels.loc['2021-01-01'],140)
        self.assertNotIn(pd.Timestamp('2022-01-01'),levels.index)
        self.assertAlmostEqual(observations(d,'gdp','Annual',True).iloc[0],40.)

    def test_nominal_totals_require_twelve_months(self):
        d={'series':{'retail_value':self.spec([10]*12+[50]*11,aggregation='sum')}}
        s=observations(d,'retail_value','Annual',False)
        self.assertEqual(list(s),[120])

    def test_year_end_cpi_policy_and_labor(self):
        d={'series':{'cpi':self.spec([100]*12+[101]*11+[110],aggregation='last'),'tpm':self.spec(list(range(12))+[99]*11,aggregation='last'),'unemployment':self.spec(list(range(12))+[99]*11,aggregation='rolling')}}
        self.assertAlmostEqual(observations(d,'cpi','Annual',True).iloc[0],10.)
        self.assertEqual(list(observations(d,'tpm','Annual',False)),[11])
        self.assertEqual(list(observations(d,'unemployment','Annual',False)),[11])

    def test_online_share_is_sales_weighted_and_offline_is_consistent(self):
        d={'series':{'online_all':self.spec([10]*6+[30]*6),'penetration_all':self.spec([10]*6+[50]*6)}}
        self.assertAlmostEqual(observations(d,'penetration_all','Annual',False).iloc[0],25.)
        self.assertAlmostEqual(observations(d,'offline','Annual',False).iloc[0],720.)

    def test_missing_year_not_skipped_and_anchor_gaps_not_filled(self):
        spec=self.spec([100]*36)
        spec['rows']=[r for r in spec['rows'] if r[0]!='2021-06-01']
        self.assertTrue(observations({'series':{'x':spec}},'x','Annual',True).empty)
        s=pd.Series(100.,index=pd.date_range('2020-01-01','2022-12-01',freq='MS'))
        s.loc['2021-06-01']=float('nan')
        r=annual_reference(s)
        self.assertTrue(pd.isna(r.loc['2021-01-01']))
        self.assertEqual(r.iloc[-1],100.)

    def test_2025_shutdown_exception_uses_exactly_eleven_real_months(self):
        s=pd.Series(range(100,112),dtype=float,index=pd.date_range('2025-01-01','2025-12-01',freq='MS'))
        s.loc['2025-10-01']=float('nan')
        result=annual_reference(s)
        self.assertAlmostEqual(result.loc['2025-01-01'],s.mean())
        self.assertEqual(result.attrs['month_counts'],{'2025':11})
        self.assertTrue(pd.isna(s.loc['2025-10-01']))
        # Do not depend on an explicit NaN row being present in the source.
        self.assertAlmostEqual(annual_reference(s.dropna()).iloc[0],s.mean())
        # A subsequently published October value restores twelve-month weighting.
        s.loc['2025-10-01']=200.
        restored=annual_reference(s)
        self.assertAlmostEqual(restored.iloc[0],s.mean())
        self.assertEqual(restored.attrs['month_counts'],{'2025':12})

    def test_shutdown_exception_rejects_other_missing_months(self):
        base=pd.Series(100.,index=pd.date_range('2025-01-01','2025-12-01',freq='MS'))
        for missing in [['2025-09-01'],['2025-10-01','2025-11-01']]:
            self.assertTrue(annual_reference(base.drop(pd.to_datetime(missing))).empty)
        other_year=pd.Series(100.,index=pd.date_range('2024-01-01','2024-12-01',freq='MS'))
        self.assertTrue(annual_reference(other_year.drop(pd.Timestamp('2024-10-01'))).empty)
        current=pd.Series(100.,index=pd.date_range(f'{pd.Timestamp.now().year}-01-01',periods=12,freq='MS'))
        self.assertTrue(annual_reference(current).empty)

    def test_annual_dashboard_and_independent_workspace(self):
        from streamlit.testing.v1 import AppTest
        a=AppTest.from_file('app.py',default_timeout=60).run()
        a.radio[1].set_value('Annual').run()
        self.assertFalse(a.exception)
        self.assertFalse(any('month' in s.label or 'quarter' in s.label for s in a.selectbox))
        specs=[json.loads(c.proto.spec) for c in a.get('plotly_chart')]
        self.assertEqual(len(specs),4)
        self.assertEqual(specs[0]['data'][0]['name'],'Total GDP')
        self.assertTrue(all(s['layout']['xaxis']['tickformat']=='%Y' for s in specs))
        self.assertEqual(specs[0]['data'][0]['customdata'][-1],'2025')
        source=json.loads(Path('data/snapshot.json').read_text(encoding='utf-8'))
        coverage=12 if any(d=='2025-10-01' for d,v in source['series']['us_cpi']['rows']) else 11
        for trace in specs[2]['data'][2:]:
            self.assertEqual(trace['meta']['months_by_year']['2025'],coverage)
            self.assertEqual('11-month average' in trace['customdata'][-1],coverage==11)
        a.radio[0].set_value('Retail outlook').run()
        self.assertFalse(a.exception)
        self.assertEqual(next(r for r in a.radio if r.label=='Online / in-store measure').value,'Sales growth')
        specs=[json.loads(c.proto.spec) for c in a.get('plotly_chart')]
        self.assertEqual(specs[3]['data'][3]['line']['color'],'#78365F')
        self.assertEqual(specs[3]['data'][4]['line']['color'],'#72777D')
        a.radio[0].set_value('Macroeconomic outlook').run()
        a.radio[1].set_value('Monthly').run()
        a.session_state['chart_frequency_Economic activity']='Annual'
        a.button(key='expand_Economic activity').click().run()
        self.assertFalse(a.exception)
        specs=[json.loads(c.proto.spec) for c in a.get('plotly_chart')]
        self.assertEqual(specs[0]['data'][0]['name'],'Total IMACEC')
        self.assertEqual(specs[-1]['data'][0]['name'],'Total GDP')
        self.assertEqual(specs[-1]['layout']['xaxis']['tickformat'],'%Y')

if __name__=='__main__':unittest.main()
