""" Custom exception classes """


class NonDictInputError(Exception):
    """Function parameter isn't a dict"""
    def __init__(self, parameter):
        self.parameter = parameter

    def __str__(self):
        return f'Function argument must be a dict type! But {type(self.parameter)} given'


class ReqFieldMissingError(Exception):
    """Error - there's no required field at a given dict"""
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'There is no \'{self.missing_field}\' field at given dict'


class ServerError(Exception):
    """Server error exception"""
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


""" -- Meta class exceptions ------------------------------------ """


class ExceptionsMetaClassError(Exception):
    """Parameter or functions error"""
    def __init__(self, parameter):
        self.parameter = parameter

    def __str__(self):
        return f'Found function or parameter from exceptions list: {self.parameter}!'


class RequiredMetaClassError(Exception):
    """Required parameter or functions error"""
    def __init__(self, parameter):
        self.parameter = parameter

    def __str__(self):
        return f'Cant\'t find a required parameters : {self.parameter}!'


class VariableMetaClassError(Exception):
    """Variable exception"""
    def __init__(self, parameter):
        # self.parameter = f'{parameter.name}: <class {parameter.type}>'
        self.parameter = parameter

    def __str__(self):
        return f'Exception for class variable found : {self.parameter}!'


""" -- Descriptors class exceptions ------------------------------ """


class PortValueError(Exception):
    """Exception for incorrect port value"""
    def __init__(self, parameter):
        self.parameter = parameter

    def __str__(self):
        return f'Incorrect port value. Value must have positive value!'
