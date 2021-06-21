"""
prepear_post.py: модуль генерации сообщения для отправки на сайт.
"""
import logging as log
logging = log.getLogger('main.' + __name__)

import os
import random
import string

from ..constants.const import MAIN_DIR, SYS_DIR_CONFIGS
from .utils import get_from_conf


CONF_PATH = os.path.join(MAIN_DIR, SYS_DIR_CONFIGS, os.getenv('CONFIG'))
parser = get_from_conf(CONF_PATH)

NAMES_FILE = parser.get('POSTS', 'NAMES_FILE')
POSTS_FILE = parser.get('POSTS', 'POSTS_FILE')


def creat_profile() -> dict:
    """
    Функция генерации случайного сообщения, случайного имени и случайного email
    """
    adresses = ['mail.com', 'mail.ru', 'list.com',
                'google.com', 'yahoo.com', 'somesite.com']
    profile = {}

    with open(os.path.join(MAIN_DIR, NAMES_FILE), encoding='utf-8') as names:
        profile['name'] = random.choice(names.read().split('|'))
    with open(os.path.join(MAIN_DIR, POSTS_FILE), encoding='utf-8') as names:
        profile['post'] = random.choice(names.read().split('|'))

    profile['email'] = ''.join(random.choice(string.ascii_lowercase) for i in range(
        random.randint(10, 16))) + '@' + random.choice(adresses)

    logging.debug('Сгенерированный профиль:\n\n%s (%s)\n%s\n' %
                  (profile['name'], profile['email'], profile['post']))
    return profile


def creat_post(post_urls):
    """
    Функция создания сообщения для отправки.
    """
    profile = creat_profile()
    post_urls_list = [url[0] for url in post_urls]
    comment = '%s\n\n%s' % (profile['post'],
                            '\n\n'.join(post_urls_list))
    author = profile['name']
    email = profile['email']

    comment_data = {'comment': comment,
                    'author': author,
                    'email': email}

    return comment_data
