import functools
import logging
import os
import sys
import re
import traceback
import socket

sys.path.append(os.path.join(os.getcwd(), '..'))

import logs.server_log_config
import logs.client_log_config


class Log:
    """Class - logger decorator. Add information about called method to a log"""
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func

    def __call__(self, *args, **kwargs):
        """Adding information about called method to a log file"""
        pattern = re.compile('([A-z0-9_-]+).py$')
        if not sys.argv or not sys.argv[0]:
            logger_name = 'app'
        else:
            res = re.findall(pattern, sys.argv[0])
            logger_name = 'app' if not res else res[0]
        parent_func_name = traceback.format_stack()[0].strip().split()[-1]

        res = self.func(*args, **kwargs)

        log = logging.getLogger(logger_name)
        log.info(f'"{self.func.__name__}({args}, {kwargs})" function called. Result: {res}')
        log.info(f'Function {self.func.__name__}() called from function {parent_func_name}')

        return res


def login_required(func):
    """Checks that client is authorized on a server.
    Generate TypeError exception if it's not
    """

    def checker(*args, **kwargs):
        from server.core import MessageProcessor
        from common.variables import ACTION, PRESENCE

        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    # -- Checking if a client in a MessageProcessor clients_names list
                    for client in args[0].clients_names:
                        if args[0].clients_names[client] == arg:
                            found = True

            # -- Checking that a message not a presence --------
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True

            # -- If client noe authorized and not a presence message raise an exception
            if not found:
                raise TypeError

        return func(*args, **kwargs)

    return checker
