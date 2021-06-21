"""
comment_post.py - скрипт отправки комментария на сайты в общей БД.
 - Скрипт не зависимый, получает только корневой каталог для нахождения БД
 - Скрипт должен быть многопоточный, для быстрой рассылки по всем сайтам в бд
 - Скрипт должен иметь возможность проверки сайта на принадлежность к тому или
    иному сркипту. Изначальная функциональность должна поддерживать
        - DLE
        - WordPress
        - Bitrix
 - В скрипте должна быть функциональность работы с уже существующей БД, проверка
    на наличие сайта в базе.

    Структура базы должна иметь вид:

    -----------------------------------------------------------------------
    |Страница где можно комментировать|CMS сайта|Дата последней публикации|
    -----------------------------------------------------------------------
    |              STR                |   STR   |          DATE           |
    -----------------------------------------------------------------------

TODO: Добавить результаты прогона в талицу проекта.
"""
import logging as log
import os

date_fmt = '%d-%m-%Y %H:%M'
fmt = '%(asctime)s - [%(name)s] - %(levelname)s - %(threadName)s - %(message)s'

log.basicConfig(level=log.DEBUG,
                format=fmt,
                datefmt=date_fmt,
                filename='logger.log',
                filemode='w')

console = log.StreamHandler()
console.setLevel(log.INFO)

formatter = log.Formatter(fmt,
                          datefmt=date_fmt)

console.setFormatter(formatter)
log.getLogger('').addHandler(console)

logging = log.getLogger(__name__)
logging.debug('Отладка отправки комментария')

import module
if __name__ == '__main__':
    # Получение URL идет из БД, нужно придумать механизм получения
    # произвольных ссылок.
    # В from_file можно указать путь к файлу, тогда скрипт будет чистать ссылки
    # из файла.

    # Сбор URL для создания поста отправки.
    urls = module.get_urls()
    logging.info('Получено %s URLs для публикации' % len(urls))

    # Сбор сайтов для отправки.
    #    source=None: получает списки из файла и БД
    #    source='file_path': принимает путь к файлу
    #    source='database': принимает либо путь к файлу БД,
    #                       либо если указано просто 'database', пробует найти БД
    #                       из conf.ini
    sites = module.get_sites()
    logging.debug('Получено %s SITEs для публикации' % len(sites))
    # Отправка сообщений и сохранение результатов отправки

    module.threads_post(sites[:], urls, 20)
    print('\nСохранение данных о ссылках [urls]\n')
