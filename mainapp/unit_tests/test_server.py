import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from server import process_client_message


class TestServer(unittest.TestCase):
    def setUp(self) -> None:
        self.message = {
            ACTION: PRESENCE,
            TIME: 1.1,
            USER: {
                ACCOUNT_NAME: 'Guest',
            },
        }
        self.err_dict = {
            RESPONSE: 400,
            ERROR: 'Bad Request',
        }
        self.success_dict = {
            RESPONSE: 200,
        }

    def test_success_response(self):
        """ Checks function success response value """

        self.assertEqual(self.success_dict, process_client_message(self.message))

    def test_no_action_parameter(self):
        """ Tests function with message without ACTION parameter """
        test_message = self.message
        del(test_message[ACTION])

        self.assertEqual(self.err_dict, process_client_message(test_message))

    def test_no_user_parameter(self):
        """ Tests function with message without USER parameter """
        test_message = self.message
        del(test_message[USER])

        self.assertEqual(self.err_dict, process_client_message(test_message))

    def test_no_time_parameter(self):
        """ Tests function with message without TIME parameter """
        test_message = self.message
        del(test_message[TIME])

        self.assertEqual(self.err_dict, process_client_message(test_message))

    def test_no_action(self):
        """ Checks function error response value """
        test_message = self.message
        del(test_message[ACTION])

        self.assertEqual(self.err_dict, process_client_message(test_message))

    def test_wrong_action_value(self):
        """ Test function with wrong action value """
        test_message = self.message
        test_message[ACTION] = 'Wrong'

        self.assertEqual(self.err_dict, process_client_message(test_message))

    def test_wrong_account_name(self):
        """ Test message with wrong account name """
        test_message = self.message
        test_message[USER][ACCOUNT_NAME] = 'Test user'

        self.assertEqual(self.err_dict, process_client_message(test_message))

    def test_with_empty_value(self):
        """ Test function with empty message """

        self.assertRaises(TypeError, process_client_message)


if __name__ == '__main__':
    unittest.main()
