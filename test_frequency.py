import unittest,json
from datetime import date
from pathlib import Path
import pandas as pd
from model import observations
class FrequencyTests(unittest.TestCase):
    def test_monthly_yoy_requires_same_calendar_month(self):
        d={'series':{'x':dict(frequency='MONTHLY',growth=True,rows=[['2020-01-01',100],['2020-03-01',100],['2021-01-01',110],['2021-02-01',120]])}}
        s=observations(d,'x');self.assertAlmostEqual(s.loc['2021-01-01'],10);self.assertNotIn(pd.Timestamp('2021-02-01'),s.index)
    def test_cannot_disguise_gdp_as_monthly(self):
        d={'series':{'gdp':dict(frequency='QUARTERLY',rows=[['2020-01-01',100]])}}
        with self.assertRaises(ValueError):observations(d,'gdp','Monthly')
    def test_monthly_offline_and_participation(self):
        def spec(v):return dict(frequency='MONTHLY',rows=[['2020-01-01',v]])
        d={'series':{'online_all':spec(20),'penetration_all':spec(25),'workforce':spec(6),'population':spec(10)}}
        self.assertAlmostEqual(observations(d,'offline',growth=False).iloc[0],60)
        self.assertAlmostEqual(observations(d,'participation',growth=False).iloc[0],60)
    def test_both_frequencies_and_historical_date_range(self):
        from streamlit.testing.v1 import AppTest
        a=AppTest.from_file('app.py',default_timeout=60).run();self.assertFalse(a.exception)
        self.assertEqual(a.title[0].value,'Macroeconomic - Chile');self.assertEqual(len(a.metric),0)
        a.sidebar.radio[1].set_value('Quarterly').run();self.assertFalse(a.exception)
        a.sidebar.date_input[0].set_value((date(2018,1,1),date(2020,12,31))).run();self.assertFalse(a.exception)
        a.sidebar.radio[0].set_value('Retail outlook').run();self.assertFalse(a.exception)
        a.sidebar.radio[1].set_value('Monthly').run();self.assertFalse(a.exception)
        demand=next(r for r in a.radio if r.label=='Demand measure');demand.set_value('Goods consumption').run();self.assertFalse(a.exception)
        self.assertTrue(any('Quarterly' in c.value for c in a.caption))
if __name__=='__main__':unittest.main()
