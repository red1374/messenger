""" Custom exception classes """


class IncorrectDataRecivedError(Exception):
    """
    Исключение  - некорректные данные получены от сокета
    """
    def __str__(self):
        return 'Принято некорректное сообщение от удалённого компьютера.'


class NonDictInputError(Exception):
    """
    Function parameter isn't a dict
    """
    def __init__(self, parameter):
        self.parameter = parameter

    def __str__(self):
        return f'Function argument must be a dict type! But {type(self.parameter)} given'


class ReqFieldMissingError(Exception):
    """
    Error - there's no required field at given dict
    """
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'There is no \'{self.missing_field}\' field at given dict'


class ServerError(Exception):
    """ Server error exception"""
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text
