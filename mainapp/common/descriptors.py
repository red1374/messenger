import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import DEFAULT_PORT


class CheckPort:
    """Class - descriptor. Used to manipulate with class method and
    class arguments before it was called or used
    """
    def __get__(self, instance, owner):
        return instance.__dict__[self.my_attr]

    def __set__(self, instance, value):
        """Checking argument value and setting default value if it's wrong"""
        if isinstance(value, str):
            value = int(value) if value.isdigit() else 0

        if not value or value <= 0:
            print(f'Port value sets to it\'s default value: {DEFAULT_PORT}')
            value = DEFAULT_PORT

        instance.__dict__[self.my_attr] = int(value)

    def __delete__(self, instance):
        del instance.__dict__[self.my_attr]

    def __set_name__(self, owner, my_attr):
        self.my_attr = my_attr
