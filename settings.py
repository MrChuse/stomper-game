from datetime import datetime
import logging
import logging.config
import os

PROFILER = False
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
        }
    },
    'loggers': {
        'root': {
            'level': 'INFO',
            'handlers': ['console']
        },
        'utils': {
            'level': 'DEBUG',
            'handlers': ['file'],
            'propagate': False
        }
    }
})
