"""
posting.py: файл содержит функции, которые принимают и обрабатывают данные
            для последующей отправки в многопоточном режиме.
"""
import logging as log
logging = log.getLogger('main.' + __name__)
import os
import time
import traceback
import sys
import urllib
import threading

from collections import Counter
from concurrent import futures

from requests.exceptions import ConnectionError, ReadTimeout

from . import db_queue as db
from . import cms as CMS
from .deco import timer, result_saving
from .utils import get_from_conf, response, save_html_response, save_txt_log
from .prepear_sites import check_data_site
from ..constants.const import MAIN_DIR, SYS_DIR_CONFIGS
from ..constants import site_status

CONF_PATH = os.path.join(MAIN_DIR, SYS_DIR_CONFIGS, os.getenv('CONFIG'))
parser = get_from_conf(CONF_PATH)

PROJECT_NAME = parser.get('MAIN', 'PROJECT_NAME')
WORKER_COUNT = parser.get('MAIN', 'WORKER_COUNT')
DB_DIR = parser.get('DB', 'POSTS_DB_DIR')
DB_NAME = parser.get('DB', 'POSTS_DB_NAME')

DB_PATH = os.path.join(DB_DIR, DB_NAME)

LINKS_DB_DIR = parser.get('DB', 'LINKS_DB_DIR')
LINKS_DB_NAME = parser.get('DB', 'LINKS_DB_NAME')
LINKS_DB_PATH = os.path.join(LINKS_DB_DIR, LINKS_DB_NAME)

STATUS = {}


def post_comment(url: str, cms=None, post_urls=None, resp=None) -> dict:
    """
    Функция отправки сообщения на страницу. Возвращает статус отправки.
    """

    logging.debug('Trying Post: %s' % url)

    # Получить запрос
    if not resp:
        resp = response(url, 'GET')

    response_data = resp

    logging.debug('Сайт %s' % (cms))

    if cms.lower() == 'WordPress'.lower():
        status, resp = CMS.wp.post(response_data, post_urls)
    elif cms.lower() == 'DataLife Engine'.lower():
        status, resp = CMS.dle.post(response_data, post_urls)
    else:
        # Если не найдена CMS
        status = site_status.CMS_NOT_FOUND

    return status, resp


@result_saving
def pre_post(site_number, site_data, post_urls):
    """
    Функция подготовки данных к отправке в приделах 1 потока.
    """

    # threading.current_thread().setName('Thread %s [#%s]' % (threading.current_thread().ident,
    #                                                         site_number))

    # logging.info('START: %s' % (site_data))

    cms = site_status.CMS_NOT_FOUND
    status = None
    status_code = None
    resp = None

    url, cms = site_data.strip().split(';')

    domain_url = urllib.parse.urlparse(url).netloc
    comment_url = url
    comment_date = time.time()

    try:
        # Получить начальные данные о ссылке.
        status, response = check_data_site(site_data, url, cms)
        logging.debug('Check Data Result. URL: %s - CMS: %s' % (url, cms))

        if not STATUS.get(cms):
            STATUS[cms] = []

        if status != True:
            # Если статус не равен True, вызвать исключение, так
            # как статус определяется при проверке check_data_site
            resp = response
        else:
            # Если проверка пройдена, попробовать получить статус
            # отправки
            status, resp = post_comment(url, cms, post_urls, response)
    except ConnectionError:
        status = site_status.CONN_ERR
        if not STATUS.get(cms):
            STATUS[cms] = []
        STATUS[cms].append(status)

        return ('ConnectionError %s' % url, (DB_PATH,
                                             cms, status,
                                             status_code,
                                             domain_url,
                                             comment_url,
                                             comment_date))
    except ReadTimeout:
        status = site_status.TIMEOUT
        if not STATUS.get(cms):
            STATUS[cms] = []
        STATUS[cms].append(status)

        return ('ReadTimeout %s' % url, (DB_PATH,
                                         cms, status,
                                         status_code,
                                         domain_url,
                                         comment_url,
                                         comment_date))
    except Exception as err:
        # Если возникает ошибка
        error = err.__class__.__name__

        if not 'cms' in locals().keys():
            cms = site_status.CMS_NOT_FOUND
        if not 'url' in locals().keys():
            url = '[%s] %s' % (site_number, site_data)

        if not STATUS.get(cms):
            STATUS[cms] = []
        STATUS[cms].append(error)
        return ('%s: %s\n%s' % (error,
                                url,
                                traceback.format_exc()), (DB_PATH,
                                                          cms, status,
                                                          status_code,
                                                          domain_url,
                                                          comment_url,
                                                          comment_date))
    else:
        STATUS[cms].append(status)

        # Отправка результатов в БД
        status_code = resp.status_code if not resp is None else ' '
        if not save_txt_log(url, cms, status):
            logging.debug('Cant saved log file - %s %s %s' %
                          (url, cms, status))
        save_html_response(resp, status, cms, url, resp_log=True)

        return ('[%s] - %s %s' % (status, url, cms), (DB_PATH,
                                                      cms, status,
                                                      status_code,
                                                      domain_url,
                                                      comment_url,
                                                      comment_date))


def print_report():
    """
    Функция вывод отчета о проделанной работе.
    Определяется по количеству статусам
    """
    print('-' * 80)
    print('Отчет о статусах'.center(80))
    print('-' * 80, '\n', sep='')

    counter = 0

    for cms in STATUS.keys():
        print('%s (%s)' % (cms, len(STATUS[cms])))
        for (status, count) in sorted(Counter(STATUS[cms]).items(),
                                      key=lambda x: str(x[0])):
            counter += count

            print('\t%-25s - %s' % (status if status != True else 'GOOD',
                                    count))
    print('\n', ('Total sites: %s' % counter).rjust(80), sep='')


@ timer
def threads_post(sites_data, post_urls, timeout):
    """
    Функция отправки данных в Thread, каждый элемент переданного списка сайтов.
    """
    # Если не переданы URL для постинга отменить
    # Или нет достпных сайтов для комментариев.
    if len(post_urls) < 1:
        print('Нет ссылок [post_urls] для комментариев.')
        return False
    elif len(sites_data) < 1:
        print('Нет доступных сайтов [sites_data] для комментариев.')
        return False

    workers = min(int(WORKER_COUNT), os.cpu_count() * 2)

    with futures.ThreadPoolExecutor(max_workers=int(workers)) as executor:
        future_task = {executor.submit(pre_post, *(site_number,
                                                   site_data,
                                                   post_urls)): (site_number, site_data) for (site_number, site_data) in enumerate(sites_data[:], 1)}

    try:
        for future in futures.as_completed(future_task, timeout=timeout):
            future.result()
    except Exception as e:
        logging.critical('Ошибка %s' % e)
        logging.debug('ИСКАТЬ ОШИБКУ %s' % e, exc_info=True)

    # Инициализация потоков, в зависимости от установленного в конфигах
    # кол-ва WORKER_COUNT.
    # thread_worker = futures.ThreadPoolExecutor(max_workers=int(WORKER_COUNT))
    # # threads_results - словарь результатов работы каждого потока.
    # threads_results = []

    # # Цикл обработки словаря с передачей данных в поток.
    # # Каждый поток нумируется через enumerate.
    # for site_number, site_data in enumerate(sites_data[:], 1):

    #     thread_result = thread_worker.submit(pre_post, *(site_number,
    #                                                      site_data,
    #                                                      post_urls))
    #     threads_results.append(thread_result)

    # for result in threads_results:
    #     # Ожиданение потока timeout=120 - 2 минуты.
    #     logging.info('WORK DONE with %s' % result.result(timeout=timeout))

    # Сохранение данных о ссылках [urls] в комментариях
    db.save_urls_date_comment(LINKS_DB_PATH, post_urls)

    # Вывод отчета о статусах
    print_report()
    # results = []
