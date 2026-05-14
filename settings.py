from datetime import datetime
import logging
import logging.config
import os

PROFILER = True
FPS = 60
UPS = 60

try:
    os.mkdir('logs')
except FileExistsError:
    pass
logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s:%(levelname)s:%(name)s\t%(filename)s:%(lineno)s\t%(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'DEBUG',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': f'logs/log-{datetime.now():%Y-%m-%d-%H-%M-%S}.log'
        },
        'file_conn': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': f'logs/log-{datetime.now():%Y-%m-%d-%H-%M-%S}-conn.log'
        },
        'file_send': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': f'logs/log-{datetime.now():%Y-%m-%d-%H-%M-%S}-send.log'
        },
        'file_recv': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': f'logs/log-{datetime.now():%Y-%m-%d-%H-%M-%S}-recv.log'
        }
    },
    'loggers': {
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'file']
        },
        'utils': {
            'level': 'DEBUG',
            'handlers': ['file_conn'],
            'propagate': False
        },
        'utils.send': {
            'level': 'DEBUG',
            'handlers': ['file_send'],
        },
        'utils.recv': {
            'level': 'DEBUG',
            'handlers': ['file_recv'],
        }
    }
})
