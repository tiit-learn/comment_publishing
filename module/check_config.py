"""
check_config.py: Скрипт проверяет наличие конфигурационного файла. В случае
                 отсутствия, создает его.
                 Читает необходимые данные.
"""
import os
import sys
import logging as log

from configparser import ConfigParser
from datetime import datetime
# from .data.src.utils import get_from_conf
from .data.constants.const import (MAIN_DIR,
                                   SYS_DIR_DB,
                                   SYS_DIR_LOGS,
                                   SYS_DIR_TEMP,
                                   SYS_DIR_CONFIGS,
                                   CONF_SECTIONS,
                                   CONF_OPTIONS,
                                   CONF_FMT)
# Установка хендлера для logging
logging = log.getLogger('main.' + __name__)
# Создание директорий для logs/db/temp/cons
for DIR in (SYS_DIR_DB,
            SYS_DIR_LOGS,
            SYS_DIR_TEMP,
            SYS_DIR_CONFIGS):
    DIR_PATH = os.path.join(MAIN_DIR, DIR)
    os.makedirs(DIR_PATH, exist_ok=True)

configs_path = os.path.join(MAIN_DIR, SYS_DIR_CONFIGS)


def get_from_conf(path):
    """
    TODO: Придумать как устранить дублирование кода. Данная функция есть в
          utils.py
    Функция возвращает объект конфигурационного файла для
    последующей работы с ним.
    """
    parser = ConfigParser()
    parser.read(path)
    return parser

def get_config_path():
    """
    Функция создает стандартные рабочие каталоги, если их нет и устанавливает
    в переменную окружения название конфигурационного файла для дальнейшего
    доступа к нему из любой точки работы приложения.
    """
    # Получение всех доступных конфигураций.
    configs = {str(num): conf for num, conf in enumerate(
        os.listdir(configs_path), 1) if conf.endswith('.ini')}
    config = get_choice(configs)
    assert config, 'Не получил конфиги.'
    return config


def get_choice(configs):
    """
    Функция выбора конфигурационного файла для работы.
    """
    # Выбор конфига для работы
    print('Find %s config(s)' % len(configs.values()))
    print('=' * 80)
    for key, item in configs.items():
        name = get_from_conf(os.path.join(configs_path, item))
        name = name.get('MAIN', 'PROJECT_NAME')
        print('\t', f'[{key}]'.ljust(3), f'-> {item} ({name})')
    print('-' * 80)
    print('\t', '[n]'.ljust(3), '-> Creat new config')
    print('\t', '[0]'.ljust(3), '-> Exit')
    print('=' * 80)
    while True:
        choice = input('Please choice: ')
        if choice.lower() == 'n':
            print('Start create new config')
            return create_new_conf()
        elif choice in configs.keys():
            return configs[choice]
        elif choice == '0':
            print('Exit program')
            return False

def create_new_conf(file_name=False):
    """
    Функция генерации нового файла конфигурации.
    """
    today = datetime.today()
    DATE_FMT = '%s-%s-%s %s:%s:%s' % (today.day, today.month,
                                      today.year, today.hour,
                                      today.minute, today.second)
    if not file_name:
        while True:
            file_name = input('Введите название файла: ')
            file_path = os.path.join(configs_path, file_name) + '.ini'
            if not os.path.isfile(file_path):
                break
            print('Файл существует. Введите другое название.')

    logging.info('Создание конфигурационного файла [%s]\n' % file_name)
    PROJECT_NAME = input('Введите название проекта: ')
    WORKER_COUNT = input('Введите количество worker: ')
    NAMES_FILE = input('Введите путь к файлу с именами: ')
    POSTS_FILE = input('Введите путь к файлу с шаблонами постов: ')
    LOG_PATH_DIR = input('Введите путь к каталогу с логами: ')
    HTML_LOG_DIR = input('Введите название каталога с html логами: ')
    TXT_LOG_DIR = input('Введите название каталога с txt логами: ')
    CLIENT_KEY = input('Введите API key Для ANTICAPTCHA: ')
    LINKS_DB_DIR = input('Введите путь к каталогу с DB links: ')
    LINKS_DB_NAME = input('Введите название DB links: ')
    POSTS_DB_DIR = input('Введите путь к каталогу с DB posts сайтами: ')
    POSTS_DB_NAME = input('Введите название DB posts с сайтами: ')
    POSTS_FILE_NAME = input('Введите путь к файлу с доп. ссылками: ')

    with open(file_path, 'w') as conf:
        conf.write(CONF_FMT % (DATE_FMT,
                               PROJECT_NAME if PROJECT_NAME else 'UNKNOWN',
                               WORKER_COUNT if WORKER_COUNT else 20,
                               NAMES_FILE if NAMES_FILE else 'names.txt',
                               POSTS_FILE if POSTS_FILE else 'posts.txt',
                               LOG_PATH_DIR if LOG_PATH_DIR else os.path.join(
                                   MAIN_DIR, SYS_DIR_LOGS),
                               HTML_LOG_DIR if HTML_LOG_DIR else 'HTML_LOGS',
                               TXT_LOG_DIR if TXT_LOG_DIR else 'TXT_LOGS',
                               CLIENT_KEY if CLIENT_KEY else None,
                               LINKS_DB_DIR if LINKS_DB_DIR else None,
                               LINKS_DB_NAME if LINKS_DB_NAME else None,
                               POSTS_DB_DIR if POSTS_DB_DIR else os.path.join(
                                   MAIN_DIR, SYS_DIR_DB),
                               POSTS_DB_NAME if POSTS_DB_NAME else 'sites.db',
                               POSTS_FILE_NAME if POSTS_FILE_NAME else None))

    return os.path.basename(file_path)


def check_conf(conf):
    """
    Функция проверяет конфигурационный файл на наличие существующих файлов.
    """

    if not os.path.isfile(os.path.join(MAIN_DIR, SYS_DIR_CONFIGS, conf)):
        breakpoint()
        conf = create_new_conf(conf)

    print('\n', (' Checking config [%s] files ' % conf).center(80, '='),
          '\n', sep='')
    parser = get_from_conf(os.path.join(configs_path, conf))

    NAMES_FILE = os.path.join(MAIN_DIR,
                              parser.get('POSTS', 'NAMES_FILE'))

    POSTS_FILE = os.path.join(MAIN_DIR,
                              parser.get('POSTS', 'POSTS_FILE'))

    LINKS_DB = os.path.join(parser.get('DB', 'LINKS_DB_DIR'),
                            parser.get('DB', 'LINKS_DB_NAME'))
    POSTS_DB = os.path.join(parser.get('DB', 'POSTS_DB_DIR'),
                            parser.get('DB', 'POSTS_DB_NAME'))

    need_check = [NAMES_FILE, POSTS_FILE, LINKS_DB, POSTS_DB]

    for check in need_check:
        assert os.path.exists(check), 'Не найден %s' % check
        print('\t%s -> [Found]' % check)

    print('\n', 'Seccess... Setup [%s] to environ' % conf, '\n',
          ''.center(80, '-'), '\n', sep='')
    os.environ['CONFIG'] = conf


"""
Проверка аргументов командной строки. Если командная строка содержит
второй аргумент, проверить не является ли это рабочим конфигурационным файлом.
"""
if len(sys.argv) < 2:
    check_conf(get_config_path())
else:
    print('Checking config %s ...' % sys.argv[1])
    check_conf(sys.argv[1])
