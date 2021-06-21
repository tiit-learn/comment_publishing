import logging as log
logging = log.getLogger('main.' + __name__)

import os
import sqlite3
import time

from datetime import datetime


def do_query(db_name, query, many=False, query_list=None):
    for i in range(10):
        try:
            conn = sqlite3.connect(db_name)
            curs = conn.cursor()
            if many:
                curs.executemany(query, query_list)
            else:
                curs.execute(query)
            response_data = curs.fetchall()
            conn.commit()
        except Exception:
            """
            Try againe
            """
        else:
            curs.close()
            conn.close()
            return response_data
    return False

# Запросы для работы с комментаряими


def add_links_to_db(db_path, links_list, bulk=False):
    """
    Функция отправки информации о сайтах комментариев в БД.
    В аргументе bulk указывается возможность отправки в links_list
    """
    # logging.info('Сохранение сайта комментариев в БД')
    query = """INSERT INTO all_links (cms, status, status_code, domain_url, comment_url, add_date, last_comment_date, msg) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    return do_query(db_path, query, many=bulk, query_list=links_list)


def get_all_add_date_null(table_name, db_path):
    """
    Функция получения из БД всей таблицы, у которой есть столбец add_date,
    который равен NULL.
    Отсортирована по столбцу node_date по возрастанию.
    """
    query = """SELECT * FROM %s WHERE add_date is NULL ORDER BY node_date ASC""" % table_name
    return do_query(db_path, query)


def get_uniq_urls(db_path):
    """
    Функция возвращает список всех URL
    """
    query = """SELECT DISTINCT comment_url FROM all_links ORDER BY comment_url"""
    return do_query(db_path, query)


def get_link_data(url, db_path):
    """
    Функция для получения данных об URL в БД.
    """
    query = """SELECT * FROM all_links WHERE comment_url="%s" """ % url
    return do_query(db_path, query)


def save_url_to_db(db_path, *args):
    # Функция генерации запроса на сохранение сайта в БД ссылок
    query = """INSERT INTO all_links (cms, status, status_code, domain_url, comment_url, last_comment_date) VALUES (?, ?, ?, ?, ?, ?)"""

    return do_query(db_path, query, True, [args])


def save_urls_date_comment(db_path, urls):
    """
    Функция сохраняет информацию о публикации
    ссылок в комментариях
    """

    date = tuple(url[2] for url in urls)
    _id = urls[0][1]
    query = """UPDATE links SET add_date = %s WHERE id = %s AND node_date IN %s""" % (time.time(), _id,
                                                                                      date if len(date) > 1 else '(%s)' % date[0])

    return do_query(db_path, query)
