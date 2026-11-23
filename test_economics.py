import unittest
from economics import quarterly,yoy,quarterly_penetration,reference,errors
class EconomicsTests(unittest.TestCase):
 def test_incomplete(self):
  self.assertEqual(quarterly([("2020-01-01",1),("2020-03-01",3)]),{})
 def test_growth_after_sum(self):
  self.assertEqual(yoy({"2020-Q1":10,"2021-Q1":15})["2021-Q1"],50)
 def test_weights(self):
  on=[("2020-01-01",10),("2020-02-01",90),("2020-03-01",10)]
  p=[(d,x) for (d,_),x in zip(on,[10,90,10])]
  self.assertAlmostEqual(quarterly_penetration(on,p)["2020-Q1"],100*110/300)
 def test_zero_denominator(self):
  self.assertEqual(yoy({"2020-Q1":0,"2021-Q1":5}),{})
 def test_reference(self):
  dates=[f"{y}-{m:02d}-01" for y in range(2015,2020) for m in range(1,13)]
  fx=[(d,600 if d<"2019-10" else 9000) for d in dates]
  cpi=[(d,100) for d in dates]
  result=reference(fx,cpi,cpi,"2015-01","2019-09")
  self.assertTrue(all(v==600 for d,v in result))
  self.assertEqual(result[0][0],dates[0])
  self.assertEqual(result[-1][0],dates[-1])
  scaled=reference(fx,[(d,v*3) for d,v in cpi],cpi,"2015-01","2019-09")
  self.assertEqual(result,scaled)
 def test_errors(self):
  self.assertEqual(errors([(3,1),(1,3)])["Bias"],0)
if __name__=="__main__": unittest.main()
