import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from client import create_presence, process_ans


class TestClass(unittest.TestCase):
    def setUp(self) -> None:
        self.presense_dict = {
            ACTION: PRESENCE,
            TIME: 1.1,
            USER: {
                ACCOUNT_NAME: 'Guest'
            }
        }


    def test_def_presense(self):
        test = create_presence()
        test[TIME] = 1.1
        self.assertEqual(test, self.presense_dict)

    def test_def_presense_with_user_name(self):
        """ Check create_presence function input value """
        user_name = 'Test User'
        test = create_presence(user_name)
        dict_with_user_name = self.presense_dict
        dict_with_user_name[USER][ACCOUNT_NAME] = user_name
        test[TIME] = 1.1
        self.assertEqual(test, dict_with_user_name)

    def test_presense_is_a_dict(self):
        """ Checks function return value type """
        test = create_presence()
        self.assertIsInstance(test, dict)

    def test_200_ans(self):
        """Тест корректтного разбора ответа 200"""
        self.assertEqual(process_ans({RESPONSE: 200}), '200 : OK')

    def test_200_str_ans(self):
        """ Tests function correct processing object with response string value """
        self.assertEqual(process_ans({RESPONSE: 200}), '200 : OK')

    def test_400_ans(self):
        """Тест корректного разбора 400"""
        self.assertEqual(process_ans({RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')

    def test_no_response(self):
        """Тест исключения без поля RESPONSE"""
        self.assertRaises(ValueError, process_ans, {ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
