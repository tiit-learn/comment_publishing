"""
prepear_sites: Скрипты для получения URL на страницу с комментариями. 
"""
import logging as log
logging = log.getLogger('main.' + __name__)

import os
import time
import threading

from requests import exceptions as req_exc
from urllib.parse import urlparse

from ..constants.const import MAIN_DIR, SYS_DIR_CONFIGS
from ..constants import site_status
from ..constants.cms_data import CMS_DATA
from .utils import get_from_conf, response, save_html_response
from .db_queue import get_uniq_urls, get_link_data


CONF_PATH = os.path.join(MAIN_DIR, SYS_DIR_CONFIGS, os.getenv('CONFIG'))
parser = get_from_conf(CONF_PATH)

DB_DIR = parser.get('DB', 'POSTS_DB_DIR')
DB_NAME = parser.get('DB', 'POSTS_DB_NAME')
FILE_NAME = parser.get('DB', 'POSTS_FILE_NAME')


def check_data_site(site_data, url, cms) -> set:
    """
    Функция принимает строку и пытается разделить ее на две части.
        1. url - Ссылка на страницу с комментариями
        2. cms - На название CMS страницы с комментариями

    Функция возвращает множество, в виде (url, cms)
    Если не получается выделить url или cms, функция возвращеает (data, None) 
    """

    logging.debug('Check Site Data: %s' %
                  (site_data))

    # Если CMS не передата, постараться ее определить
    # Опреботка и проверка URL
    url, status, response = check_url(url)

    if (not cms or cms == site_status.CMS_NOT_FOUND) and status == True:
        cms, status = check_cms(url)
    elif (not cms or cms == site_status.CMS_NOT_FOUND) and status != True:
        cms, _ = check_cms(url)

    return (status, response)


def check_url(url):
    """
    Функция определяет URL, проверяет длину URL, добавляет протокол,
    если необходимо, Проверяет ответ сайта.
    """

    logging.debug('Check URL: %s' % url)
    # очистить от символов переноса строки и пробела в начале
    # и конце строки.
    url = url.strip()

    # Если длина URL сильно маленькая, вероятней всего это ошибка.
    if len(url) < 10:
        status = '%s' % (site_status.BAD_URL)
        return url, status, None

    # Если нет протокола в URL, добавить его
    if not urlparse(url).scheme:
        url = 'http://' + url.lstrip('//')

    # Получить объект response и проверить его ответ
    try:
        url_resp = response(url, 'GET')
    except req_exc.ConnectionError:
        # Если страница не загрузилась.
        status = '%s' % (site_status.CONN_ERR)
        return url, status, None
    except Exception as err:
        # Если в процессе загрузки страницы были ошибки и страница
        # не загрузилась - вернуть status != True
        logging.debug('Site load error: %s' %
                      (err))
        status = '%s' % (site_status.BAD_SITE_STATUS)
        return url, status, None
    if url_resp.status_code != 200:
        # Если статус ответа после загрузки != 200
        # вернуть status != True
        status = site_status.BAD_PAGE_STATUS
        return url, status, url_resp
    # Все хорошо, вернуть url, status == True
    return url, True, url_resp


def check_cms(url: str) -> str:
    """
    Функция определения CMS ссылки, в случае если сайта нет в БД.
    """
    logging.debug('Check CMS: %s' %
                  (url))

    data = response(url, 'GET')
    find = None

    for cms in CMS_DATA.keys():
        if not find:
            for element in CMS_DATA[cms].values():
                for part in element:
                    if part.lower() in data.text.lower():
                        find = cms
        else:
            break

    if find:
        status = True
        logging.debug('CMS: %s' %
                      (find))
    else:
        # Если CMS не найдена, отправлем None и записываем
        # html для последующего разбора.
        status = '%s' % (site_status.CMS_NOT_FOUND)

        return site_status.CMS_NOT_FOUND, status

    return find, status


def check_sites_url_in_db(sites_data, db_path, debug=False):
    """
    Функция проверки URL из файла, для последующего комментария.
    Условие доступности:

        3 последних статуса не находятся в

        ['NOT_WORK', 'DELETE', 'NEED_REGISTRATION', 'FAIL', 'NOT FOUND FORM', 'ERROR']
    """

    need_done = []
    bad_url = []

    for num, link_data in enumerate(sites_data[:], 1):
        t = link_data[:]
        link_data = link_data[0].strip()

        if 'http' not in link_data[:4]:
            link_data = 'http://' + link_data

        db_link_data = sorted(get_link_data(link_data, db_path),
                              key=lambda x: x[7])

        if db_link_data:
            # Получаем список последних 3х статусов
            status = [(stat[2], stat[-2]) for stat in db_link_data[-3:]]
            bad_count = 0
            for stat in status:
                time_delta = time.time() - stat[1]

                # Если есть плохой статус или дата последнего комментария
                # меньше 1 дня назад. 86400 = 1 день в UNIX time
                days_left = 86400 * 0.5

                if stat[0] in site_status.BAD_STATUS or (time_delta < days_left):
                    bad_count += 1
        else:
            status = None
            bad_count = 0

        # 1 означает количество плохих статусов в БД. Если больше, то не
        # добавляем.
        if bad_count < 3:
            need_done.append('%s;%s' % (link_data,
                                        db_link_data[0][1] if db_link_data else ''))
        else:
            bad_url.append(link_data)

        if debug:
            print('[%s] %s -> %s' % (num, link_data,
                                     'Добавить' if bad_count < 3 else 'Не добавлять'))

    logging.info("""Проверка URL:

%s

        Всего сайтов передано: %s
        Всего нужно добавить: %s
        Всего не добавляем: %s

%s
        """ % ('-' * 80,
               len(sites_data),
               len(need_done),
               len(bad_url),
               '-' * 80))

    return need_done


def get_sites_from_db(db_path):
    """
    Функция возвращает список уникальных URL с записями о их CMS
    """
    urls = get_uniq_urls(db_path)
    return urls


def get_sites(source=None):
    """
    Функция конструктор для получения данных о имеющихся сайтах.
    Может принимать список сайтов из файла / БД / файла и БД.
        source = None: получает списки из файла и БД
        source = 'file_path': принимает путь к файлу
        source = 'database': принимает либо путь к файлу БД,
                           либо если указано просто 'database', пробует найти БД
                           из conf.ini
    """
    if DB_NAME in os.listdir(DB_DIR):
        DB_PATH = os.path.join(DB_DIR, DB_NAME)

    if source == None:
        # Если source = None, выгружает все уникальные сайты из БД.
        # проходит файл с URL и пытается найти URL из файла в выгрузке
        # из БД.
        all_urls = get_sites_from_db(DB_PATH)

        with open(FILE_NAME) as file:
            for line in file:
                find = False

                for url in all_urls:
                    if line[:].strip().split(';')[0] in url and not find:
                        find = True
                if not find:
                    all_urls.append((line[:].strip(),))

        all_urls = check_sites_url_in_db(all_urls, DB_PATH)

        return all_urls
    elif source == 'database':
        all_urls = check_sites_url_in_db(get_sites_from_db(DB_PATH), DB_PATH)
        return all_urls
    else:
        if os.path.exists(source):
            logging.info('File [%s] found' % source)
            FILE = source
        else:
            logging.error('File [%s] not found' % source)
            logging.error('Take [%s] file' % FILE_NAME)
            FILE = FILE_NAME

        all_urls = []
        with open(FILE) as file:
            for line in file:
                all_urls.append(line.strip())
        all_urls = check_sites_url_in_db(all_urls, DB_PATH)
        return all_urls
