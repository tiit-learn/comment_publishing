
MAIN_DIR = __package__.split('.')[0]

SYS_DIR_DB = 'db'
SYS_DIR_LOGS = 'logs'
SYS_DIR_TEMP = 'temp'
SYS_DIR_CONFIGS = 'configs'

CONF_SECTIONS = ['MAIN', 'POSTS', 'LOGS', 'ANTICAPTCHA', 'DB']
CONF_OPTIONS = ['WORKER_COUNT',
                'NAMES_FILE', 'POSTS_FILE',
                'HTML_LOG_DIR', 'CLIENT_KEY',
                'LINKS_DB_DIR', 'LINKS_DB_NAME',
                'POSTS_DB_DIR', 'POSTS_DB_NAME',
                'POSTS_FILE_NAME', 'LOG_PATH_DIR',
                'PROJECT_NAME', 'TXT_LOG_DIR']
CONF_FMT = """
# Файл конфигурации - Создан: %s
[MAIN]
PROJECT_NAME = %s
WORKER_COUNT = %s
[POSTS]
NAMES_FILE = %s
POSTS_FILE = %s
[LOGS]
LOG_PATH_DIR = %s
HTML_LOG_DIR = %s
TXT_LOG_DIR = %s
[ANTICAPTCHA]
CLIENT_KEY = %s
[DB]
LINKS_DB_DIR = %s
LINKS_DB_NAME = %s
POSTS_DB_DIR = %s
POSTS_DB_NAME = %s
POSTS_FILE_NAME = %s
"""



