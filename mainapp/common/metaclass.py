import dis
import logging
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))

app_log = logging.getLogger('app')

from mainapp.common.errors import ExceptionsMetaClassError, RequiredMetaClassError, VariableMetaClassError


class DictChecker:
    """ Checks class dictionary for functions and parameters exceptions """
    def __init__(self, class_name, class_dict, extra_params, required_params, class_vars_exception):
        self.class_name = class_name
        self.class_dict = class_dict
        self.extra_params = extra_params
        self.required_params = required_params
        self.class_vars_exception = class_vars_exception

    def run(self):
        if not self.class_dict or\
                (not self.extra_params and not self.required_params and not self.class_vars_exception):
            return False

        required_params = list(self.required_params)
        for func in self.class_dict:
            try:
                result = dis.get_instructions(self.class_dict[func])
            except TypeError:
                # print(f'Type error: {func}')
                # Searching for class variable wrong type
                for pattern in self.class_vars_exception:
                    if type(self.class_dict[func]).__name__ == pattern:
                        app_log.error(f'{self.class_name}: Exception for class variable found : {func}!')
                        raise VariableMetaClassError(func)
            else:
                for param in result:
                    # Searching for parameters from exceptions list
                    if param.argval in self.extra_params:
                        app_log.error(f'{self.class_name}: Found function or parameter from exceptions list: {param.argval}!')
                        raise ExceptionsMetaClassError(param.argval)

                    if param.argval in required_params:
                        del required_params[required_params.index(param.argval)]

        # Check required parameters
        if required_params:
            app_log.error(f'{self.class_name}: Cant\'t find a required parameters : {required_params}!')
            raise RequiredMetaClassError(required_params)


class ClientVerifier(type):
    """ Client class verifier """
    def __new__(cls, name, bases, class_dict):
        extra_params = ('accept', 'listen')
        required_params = ('AF_INET', )
        class_vars_exception = ('socket', )

        new_class = super(ClientVerifier, cls).__new__(cls, name, bases, class_dict)
        checker = DictChecker(type(new_class).__name__, class_dict, extra_params, required_params, class_vars_exception)

        checker.run()

        return new_class


class ServerVerifier(type):
    """ Server class verifier """
    def __new__(cls, name, bases, class_dict):
        extra_params = ('connect', )
        required_params = ('AF_INET', )
        class_vars_exception = ()

        new_class = super(ServerVerifier, cls).__new__(cls, name, bases, class_dict)
        checker = DictChecker(type(new_class).__name__, class_dict, extra_params, required_params, class_vars_exception)

        checker.run()

        return new_class


if __name__ == '__main__':
    class A(metaclass=ClientVerifier):
        pass

    a = A()
