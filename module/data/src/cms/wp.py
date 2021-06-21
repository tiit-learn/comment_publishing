"""
wp.py: Модуль для отправки сообщений комментарием на сайты WordPress.
       Модуль проверяет форму, возможность отправки.

    Для отправки комментария, достаточно получить:
        :ID Кнопки: отправки
        :Value Кнопки: отправки

"""
import logging as log
logging = log.getLogger('main.' + __name__)

from urllib import parse
from .. import prepear_post, utils
from ...constants import site_status as status

cms = 'WordPress'

# ID Копки отправки сообщения
xpath_submit_IDs = ['//*[@name="comment_post_ID"]/@value',
                    '//*[@name="comment_meta_value"]/@value']

# Значение кнопки отправки
xpath_submit_values = ['//*[@name="submit"]/@value',
                       '//*[@id="comment-submit"]/@value']


def post(resp, post_urls):
    """
    Функция компоновщик данных перед отправкой
    """
    status, resp = pre_post(resp, post_urls)
    return status, resp


def pre_post(resp, post_urls) -> dict:
    """
    Функция сбора и подготовки необходимой информации с
    страницы WordPress

    Возможные статусы:
        Не найдена форма отправки сообщения - 'NOT FOUND FORM'
        Сообщение есть на странице - 'DONE'
        Сообщение на модерации - 'MODERATION'
        Сообщение не отправлено - 'DELETE'
        Ошибка отправки сообщения - 'ERROR'
    """
    # Запрос к функции которая, генерирует сообщение для отправки
    comment_data = prepear_post.creat_post(post_urls)

    # Словарь с необходимыми данными для отправки комментария
    data = {'comment': comment_data['comment'],
            'author': comment_data['author'],
            'email': comment_data['email'],
            'comment_parent': 0}

    # Необходимые headers для запроса.
    headers = {
        'Origin': parse.urlparse(resp.url).netloc,
        'Referer': resp.url,
        'content-type': "application/x-www-form-urlencoded; charset=UTF-8"
    }

    # Поиск ID формы для отправки комментария. Если ID не найден
    # вернуть статус NOT_FOUND_FORM
    for xpath in xpath_submit_IDs:
        data['comment_post_ID'] = ''
        if resp.html.xpath(xpath):
            data['comment_post_ID'] = resp.html.xpath(xpath)
            break
    if not data['comment_post_ID']:
        return status.NOT_FOUND_FORM, resp

    # Поиск кнопки для отправки комментария. Если не найдена,
    # попробовать отправить без нее.
    for xpath in xpath_submit_values:
        # Поиск текста кнопки для отправки комментария
        if resp.html.xpath(xpath):
            data['submit'] = resp.html.xpath(xpath)
            break
        else:
            data['submit'] = ''

    data['url'] = resp.url

    posting_response = utils.response(parse.urljoin(data['url'], '/wp-comments-post.php'),
                                      method='POST',
                                      data=data,
                                      headers=headers)

    logging.debug('Ответ после отправки комментария:\n\n%s\n' %
                  posting_response.headers)

    if posting_response.status_code == 200:
        if all((comment_data['author'] in posting_response.text,
                'unapproved' not in posting_response.url)):
            # Если в тексте ответа страницы есть comment_data['author']
            # и в URL нет unapproved - Все ОК
            return status.DONE, posting_response
        elif 'unapproved' in posting_response.url:
            # Если в ссылке комментария есть unapproved - МОДЕРАЦИЯ
            return status.MODERATION, posting_response
        else:
            return status.COMMENT_UNKNOWN_ERROR, posting_response
    else:
        return status.RESPONSE_COMMENT_ERROR, posting_response
