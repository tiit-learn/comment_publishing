"""
dle.py: Модуль для отправки сообщений комментарием на сайты DataLife Engine.
        Модуль проверяет форму, возможность отправки, разгадывание CAPTCHA.

        :xpath_anon_post: - xpath для поиска текста, указывающего на запрет
                            публикации для анониманых пользователей. Если найдено,
                            вернуть False и прекратить работу с данным сайтом.
                            (КРИТИЧЕСКИЙ ПАРАМЕТР)

        :xpath_submit_form: - xpath формы комментариев, если найдено, то
                              прекратить поиск.
                              (КРИТИЧЕСКИЙ ПАРАМЕТР)

        :xpath_submit_id: - xpath ID формы отправки сообщения.
                            (КРИТИЧЕСКИЙ ПАРАМЕТР)

        :xpath_skin: - xpath skin параметра для отправки комментария.
        :submit_links: - xpath ссылки на публикацию.
        :xpath_user_hash: - xpath User Hash формы комментария.
        :xpath_captcha: - xpath captcha элемента.

"""
import logging as log
logging = log.getLogger('main.' + __name__)

import re

from urllib import parse
from .. import prepear_post, utils, captcha
from ...constants import site_status as status

cms = 'DataLife Engine'

# Элемент запрещающий создавать посты анонимам.
xpath_anon_post = [
    "//*[text()[contains(.,'не могут оставлять комментарии')]]"]
# Элемент формы отправки сообщений
xpath_submit_form = ['//*[@name="dle-comments-form"]',
                     '//*[@class="brdform"]']
# Элемент поиска Skin сайта, требование для отправки DLE
xpath_skin = ["//*[contains(@src,'/templates/')]/@src"]
# Элемент ID кнопки
xpath_submit_id = ['//*[@name="post_id"]/@value']
# Элемент hash пользователя
xpath_user_hash = ['//*[@name="user_hash"]/@value']
# Элемент CAPTCHA на странице.
xpath_captcha = ['//*[@id="dle-captcha"]/img[@src]/@src']
# Возможные ссылки для отправки комментария
submit_links = ['/engine/ajax/controller.php?mod=addcomments',
                '/engine/ajax/addcomments.php']
# Элемент ID комментария
comment_id = "//*[contains(@id,'comment')]"


def post(resp, post_urls):
    """
    Функция компоновщик данных перед отправкой
    """
    status, resp = pre_post(resp, post_urls)
    return status, resp


def pre_post(resp, post_urls) -> dict:
    """
    Функция сбора и подготовки необходимой информации с страницы DLE.
    Определяется за счет словарей с указанными xpath элементами, для правильного сбора данных
    для отправки.

    Возможные статусы:
        Нельзя публиковать для анонимов - 'NEED REGISTRATION'
        Не найдена форма отправки сообщения - 'NOT FOUND FORM'
        Не найдена ссылка отправки сообщения - 'NOT FOUND LINK'
        Не найдено ID сообщения - 'NOT FOUND ID'

        Сообщение есть на странице - 'DONE'
        Сообщение на модерации - 'MODERATION'
        Сообщение не отправлено - 'DELETE'
        Ошибка отправки сообщения - 'ERROR'

    """
    # Запрос к функции которая, генерирует сообщение для отправки
    comment_data = prepear_post.creat_post(post_urls)

    # Словарь с необходимыми данными для отправки комментария
    data = {'editor_mode': 'wysiwyg',
            'question_answer': '',
            'g_recaptcha_response': '',
            'allow_subscribe': 0,
            'comments': comment_data['comment'],
            'name': comment_data['author'],
            'mail': comment_data['email']}

    for xpath in xpath_anon_post:
        # Проверка возможности публикации анонимов отправки комментария. Если
        # найдено, то вернуть ответ "NEED REGISTRATION"
        if resp.html.xpath(xpath):
            return status.NEED_REGISTRATION, resp

    for xpath in xpath_submit_form:
        # Поиск Формы для отправки сообщения, если не найдено, то прекратить
        # работу с текущим сайтом.
        # Если форма не найдена, вернуть ответ "NOT FOUND FORM"
        data_comment_submit_form = ''
        if resp.html.xpath(xpath):
            data_comment_submit_form = resp.html.xpath(xpath, first=True)
            break
    if not data_comment_submit_form:
        return status.NOT_FOUND_FORM, resp

    for xpath in xpath_skin:
        # Поиск шаблона сайта для отправки сообщения, если не найдено,
        # то прекратить работу с текущим сайтом.
        if resp.html.xpath(xpath):
            data['skin'] = resp.html.xpath(xpath, first=True).split('/')[2]
            break
    if not data.get('skin', False):
        # Если скин не найден и не установлен в data['skin'],
        # попробовать Регулярные Выражения, для поиска. Если и регулярные
        # выражения не найдутся, установить пустую строку а качестве значения.
        skin_pattern = re.compile('dle_skin.*')
        if re.search(skin_pattern, resp.text):
            data['skin'] = re.search(skin_pattern,
                                     resp.text).group().strip().split("'")[1]
        else:
            data['skin'] = ''

    # Поиск кодировки с помощью регулярных выражений, в заголовке ответа.
    charset_find = re.search(re.compile('charset=.*'),
                             resp.headers['Content-Type'])
    if charset_find:
        data_encoding = charset_find.group().split('=')[1]
    else:
        data_encoding = ''

    """
    Поиск страницы Формы для отправки сообщения, если найдено, то break
    работу и установить в comment_url.
    Если страница не найдена, то вернуть ответ 'NOT FOUND LINK'
    """
    for path in submit_links:
        comment_url = ''
        link_response = utils.response(parse.urljoin(resp.url, path), 'GET')
        if link_response.status_code == 200:
            comment_url = parse.urljoin(resp.url, path)
            break
    if not comment_url:
        return status.NOT_FOUND_COMMENT_LINK, link_response

    """
    Поиск ID формы отправки комментария
    Если не найден ID, вернуть ответ 'NOT FOUND ID'
    """
    for xpath in xpath_submit_id:
        if resp.html.xpath(xpath, first=True):
            data['post_id'] = resp.html.xpath(xpath, first=True)
            break
    if not data.get('post_id', False):
        return status.NOT_FOUND_ID, resp

    # Поиск User Hash формы отправки комментария
    # Если не найден User Hash, установить пустое значение.
    for xpath in xpath_user_hash:
        data['user_hash'] = ''
        if resp.html.xpath(xpath, first=True):
            data['user_hash'] = resp.html.xpath(xpath, first=True)
            break

    # Поиск Captcha отправки комментария
    for xpath in xpath_captcha:
        # Если найден Captcha, то отправить в сервис разгадывания капчи.
        data.setdefault('sec_code', None)
        find = False
        if resp.html.xpath(xpath, first=True):
            captcha_url = resp.html.xpath(xpath, first=True)
            headers = {'Referer': resp.url}
            captcha_response = utils.response(parse.urljoin(resp.url, captcha_url),
                                              'GET',
                                              headers=headers, cookies=link_response.cookies)
            if captcha_response.headers['Content-Type'] in ['image/jpeg']:
                data['sec_code'] = captcha.captcha_tool(
                    captcha_response, resp.url)
            find = True
            break

    if not find:
        data['sec_code'] = ''
    # Обработка ответа CAPTCHA
    if data['sec_code'] == False:
        return status.CAPTCHA_ANTI_FAIL, captcha_response
    elif data['sec_code'] == None:
        return status.CAPTCHA_CANT_GET_IMG, captcha_response

    # Отправка сообщения на страницу
    headers = {'Host': parse.urlparse(resp.url).netloc,
               'Origin': parse.urljoin(resp.url, '/'),
               'Referer': resp.url,
               'X-Requested-With': 'XMLHttpRequest',
               'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

    posting_response = utils.response(comment_url,
                                      method='POST',
                                      data=data,
                                      headers=headers,
                                      cookies=link_response.cookies)

    if posting_response.status_code == 200:
        if all(('dle-comments-form' in posting_response.text,
                posting_response.html.xpath(comment_id,
                                            first=True))):
            return status.DONE, posting_response
        elif 'dle-captcha' in posting_response.text:
            return status.CAPTCHA, posting_response
        else:
            return status.COMMENT_UNKNOWN_ERROR, posting_response
    else:
        return status.RESPONSE_COMMENT_ERROR, posting_response
