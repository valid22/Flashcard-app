import logging
from loguru import logger

class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        if '"%s" %s %s' in record.msg:
            msg = '"%s" %s %s' % record.args 
        else:
            msg = record.getMessage()
        logger_opt.log(record.levelno, msg )
