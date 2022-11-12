import functools
import logging
import os
import sys
import re
import traceback

sys.path.append(os.path.join(os.getcwd(), '..'))

import logs.server_log_config
import logs.client_log_config


class Log:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func

    def __call__(self, *args, **kwargs):
        pattern = re.compile('([A-z0-9_-]+).py$')
        logger_name = re.findall(pattern, sys.argv[0])[0]
        parent_func_name = traceback.format_stack()[0].strip().split()[-1]

        res = self.func(*args, **kwargs)

        log = logging.getLogger(logger_name)
        log.info(f'"{self.func.__name__}({args}, {kwargs})" function called. Result: {res}')
        log.info(f'Function {self.func.__name__}() called from function {parent_func_name}')

        return res
