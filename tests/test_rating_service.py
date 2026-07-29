import unittest
from services.rating_service import evaluate_rating, display_score, bayesian_user_score, CRITERIA, profile_weights

class RatingServiceTests(unittest.TestCase):
    def sample(self):
        weights=profile_weights('default')
        return {'category_profile':'default','reviewed_by':1,'approved_by':2,'sources':[{'type':'official_product','status':'active'} for _ in range(3)],'criteria':{key:{'score':8.0,'weight':weights[key],'reason_tr':'Doğrulanmış gerekçe','reason_en':'Verified reason','evidence_ids':['s1'],'status':'verified'} for key in CRITERIA}}
    def test_weighted_score(self): self.assertAlmostEqual(evaluate_rating(self.sample()).overall_score,8.0)
    def test_reviewer_cannot_approve(self):
        r=self.sample(); r['approved_by']=1; self.assertFalse(evaluate_rating(r).publishable)
    def test_missing_data_not_zero(self):
        r=self.sample(); r['criteria']['security']['status']='insufficient_data'; result=evaluate_rating(r); self.assertAlmostEqual(result.raw_score,7.2); self.assertGreater(result.raw_score,0)
    def test_bounds(self):
        r=self.sample(); r['criteria']['features']['score']=11; self.assertFalse(evaluate_rating(r).publishable)
    def test_rounding(self): self.assertEqual(display_score(7.95),'8.0')
    def test_bayesian(self): self.assertLess(bayesian_user_score(10,1),10)
if __name__=='__main__': unittest.main()
