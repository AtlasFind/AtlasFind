import unittest
from validators.rating_validator import validate_rating_profiles
class ProfileTests(unittest.TestCase):
    def test_profiles(self): self.assertEqual(validate_rating_profiles(),[])
if __name__=='__main__': unittest.main()
