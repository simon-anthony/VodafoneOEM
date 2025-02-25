# emcliext

from copy import copy
from logging import Formatter
import logging

MAPPING = {
    'DEBUG'   : 33, # yellow          10
    'INFO'    : 96, # bright cyan     20
    'NOTICE'  : 92, # bright green    25 - custom
    'WARNING' : 93, # bright yellow   30
    'ERROR'   : 91, # bright red      40
    'CRITICAL': 41, # white on red bg 50
}

PREFIX = '\033['
SUFFIX = '\033[0m'

class ColoredFormatter(Formatter):

    def __init__(self, patern):
        Formatter.__init__(self, patern)

    def format(self, record):
        colored_record = copy(record)
        levelname = colored_record.levelname
        msg = colored_record.msg
        seq = MAPPING.get(levelname, 37) # default white
        colored_levelname = ('{0}{1}m{2}{3}') \
            .format(PREFIX, seq, levelname, SUFFIX)
        colored_record.levelname = colored_levelname
        colored_record.msg = ('{0}{1}m{2}{3}').format(PREFIX, seq, msg, SUFFIX)
        return Formatter.format(self, colored_record)

logging.NOTICE = 25

logging.addLevelName(logging.NOTICE, 'NOTICE')

def notice(self, message, *args, **kws):
    if self.isEnabledFor(logging.NOTICE):
        # Yes, logger takes its '*args' as 'args'.
        self._log(logging.NOTICE, message, args, **kws)
logging.Logger.notice = notice
