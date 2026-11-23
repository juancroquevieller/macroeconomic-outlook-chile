import unittest
from datetime import datetime,timezone
from unittest.mock import patch,Mock
import us_cpi
NOW=datetime(2026,11,22,tzinfo=timezone.utc)
def history(last='2026-10-01'):
    return [[f'{y}-{m:02d}-01',100.+y-2009+m/100] for y in range(2009,2027) for m in range(1,13) if f'{y}-{m:02d}-01'<=last and (y,m)!=(2025,10)]
class CpiTests(unittest.TestCase):
    def test_bls_missing_month_does_not_discard_current_release(self):
        responses=[]
        for first,last in [(2009,2018),(2019,2026)]:
            items=[dict(year=d[:4],period='M'+d[5:7],value=str(v)) for d,v in history() if first<=int(d[:4])<=last]
            if first==2019:items.append(dict(year='2025',period='M10',value='-'))
            response=Mock();response.json.return_value={'status':'REQUEST_SUCCEEDED','Results':{'series':[{'seriesID':'CUUR0000SA0','data':items}]}};responses.append(response)
        with patch.object(us_cpi.requests,'get',side_effect=responses):rows=us_cpi.bls_rows(NOW)
        self.assertEqual(rows[-1][0],'2026-10-01');self.assertNotIn('2025-10-01',dict(rows))
    def test_fresh_fred_beats_stale_bls(self):
        with patch.object(us_cpi,'bls_rows',return_value=history('2026-02-01')),patch.object(us_cpi,'fred_rows',return_value=history()):s=us_cpi.retrieve(now=NOW)
        self.assertEqual(s['publisher'],'BLS via FRED');self.assertGreater(s['cross_checked_observations'],100)
    def test_stale_feeds_cannot_report_success(self):
        with patch.object(us_cpi,'bls_rows',return_value=history('2026-02-01')),patch.object(us_cpi,'fred_rows',return_value=history('2026-02-01')):
            with self.assertRaises(ValueError):us_cpi.retrieve(now=NOW)
    def test_saved_coverage_cannot_move_backwards(self):
        with patch.object(us_cpi,'bls_rows',return_value=history('2026-09-01')),patch.object(us_cpi,'fred_rows',return_value=history('2026-09-01')):
            with self.assertRaises(ValueError):us_cpi.retrieve(previous={'rows':history()},now=NOW)
    def test_disagreement_rejected(self):
        altered=history();altered[-1][1]+=1
        with patch.object(us_cpi,'bls_rows',return_value=history()),patch.object(us_cpi,'fred_rows',return_value=altered):
            with self.assertRaises(ValueError):us_cpi.retrieve(now=NOW)
    def test_fred_missing_values_remain_missing(self):
        text='observation_date,CPIAUCNS\n'+'\n'.join(d+','+str(v) for d,v in history())+'\n2025-10-01,\n'
        response=Mock();response.text=text
        with patch.object(us_cpi.requests,'get',return_value=response):rows=us_cpi.fred_rows(NOW)
        self.assertEqual(rows[-1][0],'2026-10-01');self.assertNotIn('2025-10-01',dict(rows))
