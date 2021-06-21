# Main status
CMS_NOT_FOUND = 'NOT FOUND CMS'
CONN_ERR = 'CONNECTION ERROR'
TIMEOUT = 'TIMEOUT'
BAD_URL = 'BAD URL'
BAD_SITE_STATUS = 'BAD SITE STATUS'
BAD_PAGE_STATUS = 'BAD PAGE STATUS'
UNKNOWN_ERROR = 'UNKNOWN ERROR'
# Comment Status
DONE = 'DONE'
NOT_FOUND_FORM = 'NOT FOUND FORM'
NOT_FOUND_BUTTON = 'NOT FOUND BUTTON'
MODERATION = 'MODERATION'
RESPONSE_COMMENT_ERROR = 'COMMENT ERROR'
COMMENT_UNKNOWN_ERROR = 'COMMENT UNKNOWN ERROR'
NEED_REGISTRATION = 'NEED REGISTRATION'
NOT_FOUND_COMMENT_LINK = 'NOT FOUND COMMENT LINK'
NOT_FOUND_ID = 'NOT FOUND ID'
# Captcha Status
# Не смог получить на сайте картинку Captcha
CAPTCHA_CANT_GET_IMG = 'CAPTCHA CANT GET IMG'
# Сервис антикапчи не отдал решение
CAPTCHA_ANTI_FAIL = 'CAPTCHA ANTICAPTCHA FAIL'
CAPTCHA = 'CAPTCHA FAIL'  # Проблема с CPATCHA после отправки сообщения
CAPTCHA_FORM_NOT_FOUND = 'CAPTCHA FORM NOT FOUND'  # Не найдена форма CAPTCHA
# For check data
BAD_STATUS = ['NOT_WORK',
              'DELETE',
              'NEED_REGISTRATION',
              'FAIL',
              'NOT FOUND FORM',
              'ERROR',
              'BAD SITE STATUS',
              'COMMENT UNKNOWN ERROR',
              'CONNECTION ERROR',
              'BAD PAGE STATUS',
              'COMMENT ERROR',
              'SSLError',
              'TIMEOUT',
              'NOT FOUND CMS'
              ]
BAD_CMS = ['Bitrix',
           'Ucoz',
           'SiteEdit',
           'Joomla',
           'phpBB',
           'vBulletin']
