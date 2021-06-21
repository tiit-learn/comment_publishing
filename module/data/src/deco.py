import logging as log
logging = log.getLogger('main.' + __name__)

import time
import threading

from . import db_queue as db


def timer(func):
    def wrapper(*args):
        start = time.perf_counter()
        res = func(*args)
        finish = 'Выполнено за: %.3f c' % (time.perf_counter() - start)
        print('-' * 80)
        print(finish.rjust(80))
        print('-' * 80)
        return res
    return wrapper


def result_saving(func):

    def wrapper(*args):

        threading.current_thread().setName('Thread %s [#%s]' % (threading.current_thread().ident,
                                                                args[0]))
        logging.info('START: %s' % (args[1]))
        result = func(*args)

        """
        result[-1] = 

        DB_PATH,
        cms, status,
        status_code,
        domain_url,
        comment_url,
        comment_date
        Сохранение в БД
        """

        db.save_url_to_db(*result[-1])

        logging.info('FINISH: %s' % result[0])

        return result[0]
    return wrapper
