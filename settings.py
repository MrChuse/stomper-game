from datetime import datetime
import logging
import logging.config

PROFILER = False
FPS = 60
UPS = 60

logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s:%(levelname)s\t%(filename)s:%(lineno)s\t%(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'INFO',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': f'log-{datetime.now():%Y-%m-%d-%H-%M-%S}.log'
        }
    },
    'loggers': {
        'root': {
            'level': 'INFO',
            'handlers': ['console']
        },
        'utils': {
            'level': 'DEBUG',
            'handlers': ['file']
        }
    }
})
