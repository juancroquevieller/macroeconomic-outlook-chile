import unittest,json
from pathlib import Path
import pandas as pd
from model import quarterly,evaluate,refs
class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data=json.loads(Path('data/snapshot.json').read_text(encoding='utf-8'))
    def test_all_series_have_complete_quarter(self):
        for key in self.data['series']:
            result=quarterly(self.data,key,False)
            self.assertFalse(result.empty,key)
            self.assertTrue((result.index.to_period('Q')<pd.Timestamp.now().to_period('Q')).all(),key)
    def test_missing_quarter_not_compared_by_position(self):
        s={'series':{'test':dict(frequency='QUARTERLY',aggregation='mean',rows=[['2020-01-01',100],['2020-04-01',100],['2020-10-01',100],['2021-01-01',110],['2021-04-01',120]])}}
        result=quarterly(s,'test',True)
        self.assertAlmostEqual(result.loc['2021-01-01'],10)
        self.assertAlmostEqual(result.loc['2021-04-01'],20)
    def test_quarter_penetration_sales_weighted(self):
        def spec(values): return dict(frequency='MONTHLY',aggregation='mean',rows=[[f'2020-{m:02d}-01',v] for m,v in enumerate(values,1)])
        d={'series':{'online_all':spec([10,20,30]),'penetration_all':spec([10,20,50])}}
        self.assertAlmostEqual(quarterly(d,'penetration_all',False).iloc[0],100*60/260)
    def test_forecast_pairs_and_reference_history(self):
        pairs,metrics=evaluate(self.data)
        self.assertTrue((metrics.n>24).all())
        inflation=pairs[pairs.series=='eee_inflation']
        self.assertTrue(all(a+pd.DateOffset(months=11)==b for a,b in zip(inflation.issued,inflation.target)))
        self.assertEqual(len(refs(self.data)),2)
        self.assertTrue((metrics.common_n>0).all())
class StreamlitTests(unittest.TestCase):
    def test_populated_views(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file('app.py',default_timeout=60).run()
        self.assertFalse(app.exception)
        for view in ['Retail outlook','Assignment view','Sources & methodology']:
            app.sidebar.radio[0].set_value(view).run()
            self.assertFalse(app.exception,view)
        app.sidebar.radio[0].set_value('Macroeconomic outlook').run()
        app.radio[0].set_value('Real exchange-rate index').run() if app.radio[0].label=='Exchange-rate measure' else None
        self.assertFalse(app.exception)
if __name__=='__main__': unittest.main()
