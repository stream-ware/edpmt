import unittest
from edpmt.utils import get_system_info

class TestUtils(unittest.TestCase):
    def test_get_system_info(self):
        info = get_system_info()
        self.assertIsInstance(info, dict)
        self.assertIn('platform', info)
        self.assertIn('cpu', info)
        self.assertIn('memory', info)

if __name__ == '__main__':
    unittest.main()
