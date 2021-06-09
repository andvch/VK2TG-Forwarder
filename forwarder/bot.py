"""Запускает 2 потока для обработки сообщений в Телеграме и в ВК."""

from string import ascii_letters, digits
from random import choice
from telegram.ext import Updater, Defaults, CommandHandler, MessageHandler, Filters
from forwarder.vk import VkApi
from forwarder.messageconverter import ConvertedForwardedMessages
from forwarder.signer import Signer
from forwarder.config import (
    TG_TOKEN,
    VK_TOKEN,
    DATE_FORMAT,
    PASSWORD_LENGTH,
    TG_DELETED_OLD_LINKS_MESSAGE,
    TG_SUCCESS_REGISTRATION_MESSAGE,
    TG_FAILED_DETACH_MESSAGE,
    TG_SUCCESS_DETACH_MESSAGE,
    TG_RE_REGISTRATION_MESSAGE,
    TG_NEW_REGISTRATION_MESSAGE,
    VK_SUCCESS_REGISTRATION_MESSAGE,
    VK_FAILED_REGISTRATION_MESSAGE,
    send_message_text
)

cd_tg_dict = {}
tg_cd_dict = {}
tg_vk_dict = {}
vk_tg_dict = {}


def start(bot, _):
    """Обработчик Телеграмм-команды start. Генерирует ключ для связки аккаунтов."""
    if bot.effective_user.id in tg_cd_dict:
        cd_tg_dict.pop(tg_cd_dict[bot.effective_user.id])
        tg_cd_dict.pop(bot.effective_user.id)
    if bot.effective_user.id in tg_vk_dict:
        vk_tg_dict.pop(tg_vk_dict[bot.effective_user.id])
        tg_vk_dict.pop(bot.effective_user.id)
        bot.message.reply_text(TG_DELETED_OLD_LINKS_MESSAGE)

    code = ''.join(choice(ascii_letters + digits) for i in range(PASSWORD_LENGTH))
    tg_cd_dict[bot.effective_user.id] = code
    cd_tg_dict[code] = bot.effective_user.id

    bot.message.reply_text(TG_SUCCESS_REGISTRATION_MESSAGE)
    bot.message.reply_text(code)


def detach(bot, _):
    """Обработчик Телеграмм-команды для удаления связки аккаунтов."""
    if (bot.effective_user.id not in tg_vk_dict) and (bot.effective_user.id not in tg_cd_dict):
        bot.message.reply_text(TG_FAILED_DETACH_MESSAGE)
    else:
        if bot.effective_user.id in tg_cd_dict:
            cd_tg_dict.pop(tg_cd_dict[bot.effective_user.id])
            tg_cd_dict.pop(bot.effective_user.id)
        if bot.effective_user.id in tg_vk_dict:
            vk_tg_dict.pop(tg_vk_dict[bot.effective_user.id])
            tg_vk_dict.pop(bot.effective_user.id)
        bot.message.reply_text(TG_SUCCESS_DETACH_MESSAGE)


def print_answer(bot, _):
    """Обработчик Телеграмм-сообщений, которые не являются коммандами."""
    if bot.effective_user.id in tg_vk_dict:
        bot.message.reply_text(TG_RE_REGISTRATION_MESSAGE)
    else:
        bot.message.reply_text(TG_NEW_REGISTRATION_MESSAGE)


def vk_mainloop(vk, bot):
    """Обработка сообщений ВК."""
    for vk_message in vk.listen():
        if vk_message['from_id'] < 0:
            continue  # drops own messages

        if vk_message['text'] in cd_tg_dict:
            if vk_message['from_id'] in vk_tg_dict:
                tg_vk_dict.pop(vk_tg_dict[vk_message['from_id']])
            vk_tg_dict[vk_message['from_id']] = cd_tg_dict[vk_message['text']]
            tg_vk_dict[cd_tg_dict[vk_message['text']]] = vk_message['from_id']
            tg_cd_dict.pop(cd_tg_dict[vk_message['text']])
            cd_tg_dict.pop(vk_message['text'])
            vk.send_message(VK_SUCCESS_REGISTRATION_MESSAGE,
                            vk_message['from_id'])
            continue

        if vk_message['from_id'] not in vk_tg_dict:
            vk.send_message(VK_FAILED_REGISTRATION_MESSAGE + bot.link,
                            vk_message['from_id'])
            continue

        message = ConvertedForwardedMessages(vk_message)
#        vk.send_message(f'В какой чат переслать {message.num_messages_to_send} сообщений?',
#                         vk_message['from_id'],
#                         vk_message['id'])

        sig = Signer(vk.get_names(message.author_ids), date_format=DATE_FORMAT)
        num = message.send(bot, vk_tg_dict[vk_message['from_id']], sig)
        vk.send_message(send_message_text(num, message.num_messages_to_send),
                        vk_message['from_id'],
                        vk_message['id'])


def main():
    """Запускает 2 потока для обработки сообщений в Телеграме и в ВК."""
    vk = VkApi(VK_TOKEN)
    updater = Updater(TG_TOKEN, defaults=Defaults(
        parse_mode='Markdown',
        disable_web_page_preview=True
    ))
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("detach", detach))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, print_answer))
    updater.start_polling()

    vk_mainloop(vk, updater.bot)


if __name__ == "__main__":
    main()
