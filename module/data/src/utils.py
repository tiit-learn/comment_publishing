"""
file utils.py: Вспомогательные функции для работы
               основного скрипта
"""
import logging as log
logging = log.getLogger('main.' + __name__)
import os
import random
import requests_html
import time
import threading

from configparser import ConfigParser
from urllib.parse import urlparse

from ..constants.const import MAIN_DIR, SYS_DIR_CONFIGS
from ..constants.site_status import BAD_STATUS



def get_from_conf(path):
    """
    Функция возвращает объект конфигурационного файла для
    последующей работы с ним.
    """
    parser = ConfigParser()
    parser.read(path)
    return parser

CONF_PATH = os.path.join(MAIN_DIR, SYS_DIR_CONFIGS, os.getenv('CONFIG'))
parser = get_from_conf(CONF_PATH)

PROJECT_NAME = parser.get('MAIN', 'PROJECT_NAME')
LOG_PATH_DIR = parser.get('LOGS', 'LOG_PATH_DIR')
HTML_LOG_DIR = parser.get('LOGS', 'HTML_LOG_DIR')
TXT_LOG_DIR = parser.get('LOGS', 'TXT_LOG_DIR')

_now = time.strptime(time.ctime())
DIR_DATE_TODAY = '%s_%s_%s' % (_now.tm_year, _now.tm_mon, _now.tm_mday)
LOG_PATH = os.path.join(MAIN_DIR, LOG_PATH_DIR, PROJECT_NAME, DIR_DATE_TODAY)


def counter(dict_data):
    """
    Функция
    """
    cms = dict_data['cms']
    status = dict_data['status']

    COUNT.setdefault(cms, {})
    COUNT[cms].setdefault(status, 0)
    COUNT[cms][status] += 1


def response(url: str,
             method: str=None,
             data: dict=None,
             headers: dict=None,
             cookies: dict=None,
             timeout: bool=120) -> requests_html.HTML:
    """
    Функция
    """
    header_data = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'}
    if headers:
        header_data.update(headers)

    session = requests_html.HTMLSession()

    if 'GET' in method:
        resp = session.get(url, headers=header_data,
                           cookies=cookies, timeout=timeout)
    elif 'POST' in method:
        resp = session.post(url, headers=header_data,
                            cookies=cookies, data=data, timeout=timeout)

    return resp


def save_html_response(resp, status, cms, url, msg=False, resp_log=False) -> str:
    """
    Функция определяет результат ответа запроса, если длина ответа больше 1000,
    возвращает title страницы и записывает ответ в файл.

    Если длина страницы мнее 1000, то возвращает полность ответ
    """
    logging.debug('Saving HTML: %s - %s' %
                  (threading.current_thread().name, status))

    if resp_log:
        save_response(resp, status, cms, url)


def save_response(resp, status, cms, url):
    """Функция сохранения файла ответа, если установлена глобальная
    переменная RESP_LOG"""
    if resp is None:
        url_domain = urlparse(url).netloc
        code = ''
        resp_text = 'None'
    else:
        url_domain = urlparse(resp.url).netloc
        code = resp.status_code
        resp_text = resp.text

    html_file = '%s%s_%s_.html' % ('%s' % cms + '_' if cms else '',
                                   url_domain,
                                   code)

    html_file = html_file.replace(':', '_')
    html_status_dir = os.path.join(LOG_PATH, HTML_LOG_DIR, cms, status)
    os.makedirs(html_status_dir, exist_ok=True)

    with open(os.path.join(html_status_dir, html_file),
              'w', encoding='utf-8') as html:
        html.write(resp_text)

    logging.debug('Saving CMS HTML: %s - [%s] in %s' %
                  (threading.current_thread().name, html_file, os.path.abspath(html_status_dir)))


def save_txt_log(url, cms, status):
    """
    Функция сохранения логов в файле.
    """

    project_log_dir = os.path.join(LOG_PATH, TXT_LOG_DIR, cms, status)
    os.makedirs(project_log_dir, exist_ok=True)
    log_file_path = os.path.join(project_log_dir, '%s.log' % status)
    for i in range(1000):
        try:
            with open(log_file_path, 'a') as file:
                file.write('%s;%s\n' % (url, cms))
        except Exception:
            pass
        else:
            return True
        time.sleep(random.randrange(5))
    return False
