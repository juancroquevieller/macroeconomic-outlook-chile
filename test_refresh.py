"""Refresh state must distinguish an attempt from a successful fetch."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
import refresh
class RefreshTests(unittest.TestCase):
    def exercise(self,fail):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir()
            spec=dict(key='test',id='TEST',frequency='MONTHLY',aggregation='mean')
            prior={'series':{'test':{'rows':[['2020-01-01',100]]}},'last_success':'2020-01-01T00:00:00+00:00'}
            (root/'registry.json').write_text(json.dumps([spec]))
            (root/'data/snapshot.json').write_text(json.dumps(prior))
            response=Mock();response.json.return_value={'status':'REQUEST_SUCCEEDED','Results':{'series':[{'data':[{'year':'2020','period':'M01','value':'100'}]}]}}
            raw={'Series':{'seriesId':'TEST','Obs':[{'statusCode':'OK','indexDateString':'01-01-2020','value':'100'}]}}
            with patch.object(refresh,'ROOT',root),patch.dict('os.environ',{'BCCH_API_TOKEN':'test-only'}),patch.object(refresh,'request',side_effect=RuntimeError('test failure') if fail else None,return_value=raw),patch('us_cpi.retrieve',return_value={'rows':[['2020-01-01',100]]}),patch('builtins.print'):
                result=refresh.refresh()
            after=json.loads((root/'data/snapshot.json').read_text(encoding='utf-8'))
            self.assertEqual(result,fail)
            self.assertEqual(after['series']['test']['rows'],prior['series']['test']['rows'])
            self.assertNotEqual(after['last_attempt'],prior['last_success'])
            if fail:
                self.assertEqual(after['last_success'],prior['last_success'])
                self.assertEqual(after['failures'][0]['series'],'test')
            else:
                self.assertNotEqual(after['last_success'],prior['last_success'])
                self.assertEqual(after['failures'],[])
    def test_partial_failure_preserves_data_and_success_time(self): self.exercise(True)
    def test_unchanged_data_advances_success_time(self): self.exercise(False)
