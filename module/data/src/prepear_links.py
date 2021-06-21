"""
prepear_links: Скрипты для обработки файла или БД, которые содержат,
               ссылки, которые необходимо опубликовать.
               Приводит полученные строки к общему форматирования и
               возвращает полученный список. 
"""
import logging as log
logging = log.getLogger('main.' + __name__)
import os

from ..constants.const import MAIN_DIR, SYS_DIR_CONFIGS
from .utils import get_from_conf
from .db_queue import get_all_add_date_null

CONF_PATH = os.path.join(MAIN_DIR, SYS_DIR_CONFIGS, os.getenv('CONFIG'))


def get_urls_from_db(table_name):
    """
    Функция возврата списка URL из БД.
    Возвращает только URL с самой старшей датой, у которых
    нет значения в поле публикации.

    Функция форматирует полученнные строки в соответствие с требуемым
    форматом скрипта

    [url, id, add_date, comment_date]

    При этом comment_date всегда возвращется None, так как URL еще не
    публиковался.
    """

    parser = get_from_conf(CONF_PATH)

    DB_DIR = parser.get('DB', 'LINKS_DB_DIR')
    DB_NAME = parser.get('DB', 'LINKS_DB_NAME')

    if DB_NAME in os.listdir(DB_DIR):
        db_p = os.path.join(DB_DIR, DB_NAME)
        logging.info('Find path to DB: %s' % db_p)
        data = get_all_add_date_null(table_name, db_p)
        logging.debug('[%s] Get %s links' % (DB_NAME, len(data)))

        node_id = None
        node_list = []

        for line in data:
            if node_id == None and not line[2]:
                node_id = line[0]
            if node_id != line[0]:
                break
            else:
                node_list.append(tuple([line[3], line[0], line[1], None]))

        logging.debug('[%s] Get %s links to publish' % (DB_NAME,
                                                        len(node_list)))

        return node_list
    else:
        logging.error('[%s] not found in [%s]' % (DB_NAME, DB_DIR))
        return False


def get_urls_from_file(file_path):
    """
    Функция получения ссылок из указанного файла.
    Функция форматирует полученнные строки в соответствие с требуемым
    форматом скрипта

    [url, None, None, None]

    Для согласования с общим форматом в скрипте.
    Формат записи в файл должен быть, каждый URL в новой строке.
    """
    url_list = []

    if os.path.exists(file_path):
        logging.debug('Find file with URLs - %s' % os.path.abspath(file_path))
        with open(file_path) as file:
            for line in file:
                url_list.append(tuple([line.strip(), None, None, None]))
        return url_list
    else:
        logging.error('File [%s] not found' % (file_path))
        return False


def get_urls(from_file=None, table_name='links'):
    """
    Функция проверки существующих БД и получения URL для публикации
    """
    if from_file:
        return get_urls_from_file(from_file)
    else:
        return get_urls_from_db(table_name)
