import logging
import os
import sys
from logging import handlers

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.variables import LOGGING_LEVEL

format = logging.Formatter("%(asctime)s %(levelname)-8s %(module)-18s %(message)s")

path = os.getcwd()
path = os.path.join(path, 'server.log')

""" Setting up logger handlers """
file_handler = handlers.TimedRotatingFileHandler(path, interval=1, when='D', encoding='UTF-8')
file_handler.setFormatter(format)

stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(format)
stream_handler.setLevel(logging.ERROR)

""" Create logger register and bind handlers to it """
logger = logging.getLogger('server')
logger.setLevel(LOGGING_LEVEL)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

if __name__ == '__main__':
    logger.critical('Critical message!')
    logger.error('Error message!')
    logger.debug('Debug message!')
    logger.info('Info message')
