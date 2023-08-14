import logging.handlers
import time
import os

logger_info = logging.getLogger('info')
logger_info.setLevel(logging.INFO)
logger_debug = logging.getLogger('debug')
logger_debug.setLevel(logging.DEBUG)
logger_error = logging.getLogger('error')
logger_error.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - PROCESS( %(process)d ) FILENAME( %(filename)s ) LINE( %(lineno)s ) MESSAGE( %(message)s )')

try:
    os.mkdir('./logs')
    command0 = 'chmod -R 777 {}'.format('./logs')
    res0 = os.system(command0)
    logger_info.info(res0)
except Exception as e:
    pass

current_path = os.path.dirname(__file__)
full_absolute_path = os.path.join(current_path, '../logs/{}.log'.format(time.strftime("%Y-%m-%d_%H-%M-%S")))

handler = logging.handlers.RotatingFileHandler(full_absolute_path, maxBytes=5242880, backupCount=100)
handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger_info.addHandler(console_handler)
logger_debug.addHandler(console_handler)
logger_error.addHandler(console_handler)

logger_info.addHandler(handler)
logger_debug.addHandler(handler)
logger_error.addHandler(handler)
