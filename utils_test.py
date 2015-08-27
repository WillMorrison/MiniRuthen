import unittest
import utils
import world

class UtilsTest(unittest.TestCase):
  
  def testIndexed(self):
    self.assertAlmostEqual(utils.Indexed(100, world.BASE_YEAR + 1, 1.10), 110)
    self.assertAlmostEqual(utils.Indexed(100, world.BASE_YEAR, 123), 100)
    self.assertAlmostEqual(utils.Indexed(100, world.BASE_YEAR + 1), 101)

if __name__ == '__main__':
  unittest.main()
