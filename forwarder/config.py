"""Здесь хранятся константы и переменные с текстом сообщений."""

import sys
import os
import gettext

datapath = os.path.dirname(sys.argv[0])
gettext.install('config', os.path.join(datapath, 'po'), names=("ngettext",))


def send_message_text(success_cnt, all_cnt):
    """Формируем текст сообщения с отчётом о перессылке сообщений из ВК в Telegram."""
    message = _('Доставлено ') + str(success_cnt) + _(' из ') + str(all_cnt) + ' '
    return message + ngettext("сообщения",
                              "сообщений",
                              all_cnt)


TG_TOKEN = os.getenv('TG_BOT_TOKEN')
VK_TOKEN = os.getenv('VK_BOT_TOKEN')

DATE_FORMAT = "%d %B %Y в %H:%M %Z"
PASSWORD_LENGTH = 8

TG_DELETED_OLD_LINKS_MESSAGE = _('Ваша прошлая связка "ВК-Telegram" была удалена.')
TG_SUCCESS_REGISTRATION_MESSAGE = _('Чтобы получать сообщения из ВК в данный диалог, напишите'
                                    ' пароль из следующего сообщения боту в ВК:'
                                    ' https://vk.com/im?sel=...\nЧтобы удалить свои данные,'
                                    ' нажмите команду "/detach".')
TG_FAILED_DETACH_MESSAGE = _('Ваши данные отсутствуют. Для того, чтобы зарегистрироваться, нажмите'
                             ' команду "/start".')
TG_SUCCESS_DETACH_MESSAGE = _('Ваши данные были удалены. Для того, чтобы снова зарегистрироваться,'
                              ' нажмите команду "/start".')
TG_RE_REGISTRATION_MESSAGE = _('Если вы хотите изменить адресанта сообщений в ВК, нажмите команду'
                               ' "/start".')
TG_NEW_REGISTRATION_MESSAGE = _('Здравствуйте!\nЧтобы зарегистрироваться и иметь возможность'
                                ' пересылать себе сообщения из ВК (подробнее:'
                                ' https://github.com/andvch/VK2TG-Forwarder) нажмите команду'
                                ' "/start".')

VK_SUCCESS_REGISTRATION_MESSAGE = _('Поздравляем!\nТеперь вы можете писать сюда сообщения и они'
                                    ' будут пересланы зарегистрированному вами аккаунту в'
                                    ' Telegram.')
VK_FAILED_REGISTRATION_MESSAGE = _('Вы не являетесь зарегистрированным участником. Напишите боту в'
                                   ' Telegram: ')
