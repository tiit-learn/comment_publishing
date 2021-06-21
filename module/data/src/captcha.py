"""
captcha.py: Модуль обработки CAPTCHA. Обрабатывает полученную в base64
            изображение и возвращает ответ в виде строки.
            Работает с сервисом:
                - anti-captcha.com
"""
import logging as log
logging = log.getLogger('main.' + __name__)

import json
import os
import time
import threading
import urllib

from base64 import b64encode

from . import utils
from ..constants.const import MAIN_DIR, SYS_DIR_CONFIGS, SYS_DIR_TEMP

CAPTCHA_DIR = os.path.join(MAIN_DIR, SYS_DIR_TEMP, 'CAPTCHA')
os.makedirs(CAPTCHA_DIR, exist_ok=True)
CONF_PATH = os.path.join(MAIN_DIR, SYS_DIR_CONFIGS, os.getenv('CONFIG'))

parser = utils.get_from_conf(CONF_PATH)

CLIENT_KEY = parser.get('ANTICAPTCHA', 'CLIENT_KEY')


def captcha_tool(img_base64, site_url):
    """
    Функция получения и решения капчи на странице, для отправки сообщения.
    """

    url = urllib.parse.urlparse(site_url).netloc
    settings_json = json.dumps({"clientKey": CLIENT_KEY,
                                "task": {"type": "ImageToTextTask",
                                         "body": b64encode(img_base64.content).decode('ascii'),
                                         "phrase": False,
                                         "case": True,
                                         "numeric": False,
                                         "math": 0,
                                         "minLength": 0,
                                         "maxLength": 0}})

    anticaptcha_url = 'https://api.anti-captcha.com/createTask'
    header = {'Content-Type': 'application/json'}

    anticaptcha_resp = utils.response(
        anticaptcha_url, 'POST', data=settings_json, headers=header, timeout=40)

    if json.loads(anticaptcha_resp.text)['errorId'] == 0:
        task_id = json.loads(anticaptcha_resp.text)['taskId']
        logging.debug('ID Задачи: %s' % task_id)

        captcha_done = captcha_wait(task_id)

        if captcha_done:
            os.makedirs(os.path.join(CAPTCHA_DIR, 'DONE'), exist_ok=True)
            with open(os.path.join(CAPTCHA_DIR, 'DONE', captcha_done + '.jpg'), 'wb') as f:
                f.write(img_base64.content)
        else:
            # Не получена CAPTCHA
            os.makedirs(os.path.join(CAPTCHA_DIR, 'NOT DONE'), exist_ok=True)
            with open(os.path.join(CAPTCHA_DIR, 'NOT DONE', url.replace('.', '_') + '.jpg'), 'wb') as f:
                f.write(img_base64.content)
            return False
    else:
        logging.error('Ошибка отправки запроса АнтиКапчи: %s' %
                      (json.loads(anticaptcha_resp.text)['errorDescription']))
        return None
    return captcha_done


def captcha_wait(task_id):
    """
    Функция получения результата решения CAPTCHA.
    Функция делает RESP_COUNT запросов на получение
    с интервалом TIME_WAIT сек.
    """

    RESP_COUNT = 10
    TIME_WAIT = 5

    time.sleep(TIME_WAIT)
    payload_data = json.dumps({"clientKey": CLIENT_KEY,
                               "taskId": task_id})
    header = {'Content-Type': 'application/json'}

    for resp in range(RESP_COUNT):

        logging.debug('Ожидаю результат CAPTCHA: Task ID [%s]' % (task_id))
        captcha_resp = utils.response('https://api.anti-captcha.com/getTaskResult',
                                      'POST',
                                      data=payload_data,
                                      headers=header)
        logging.debug('Ответ ожидания CAPTCHA:\n\n%s\n' %
                      json.loads(captcha_resp.text))
        if json.loads(captcha_resp.text).get('status', False) == 'ready':
            captcha_result = json.loads(captcha_resp.text)['solution']['text']
            logging.debug(
                'Полученнный результат CAPTCHA: [%s]' % (captcha_result))
            return captcha_result

        time.sleep(10)
    return False
