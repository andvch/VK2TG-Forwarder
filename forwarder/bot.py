from string import ascii_letters, digits
from random import choice
from telegram.ext import Updater, Defaults, CommandHandler, MessageHandler, Filters
from vk import VkApi
from messageconverter import ConvertedForwardedMessages
from signer import Signer

with open('config') as f:
    exec(f.read())

cd_tg_dict = {}
tg_cd_dict = {}
tg_vk_dict = {}
vk_tg_dict = {}

def start(bot, _):
    if tg_cd_dict.get(bot.effective_user.id):
        del cd_tg_dict[tg_cd_dict[bot.effective_user.id]]
        del tg_cd_dict[bot.effective_user.id]
    if tg_vk_dict.get(bot.effective_user.id):
        del vk_tg_dict[tg_vk_dict[bot.effective_user.id]]
        del tg_vk_dict[bot.effective_user.id]
        bot.message.reply_text('Ваша прошлая связка "ВК-Telegram" была удалена.')
    code = ''.join(choice(ascii_letters + digits) for i in range(8))
    tg_cd_dict[bot.effective_user.id] = code
    cd_tg_dict[code] = bot.effective_user.id
    
    bot.message.reply_text('''Чтобы получать сообщения из ВК в данный диалог, напишите пароль из следующего \
сообщения боту в ВК: https://vk.com/im?sel=-204978468.
Чтобы удалить свои данные, нажмите команду "/detach".''')
    bot.message.reply_text(code)

def detach(bot, _):
    if (tg_vk_dict.get(bot.effective_user.id) is None) and (tg_cd_dict.get(bot.effective_user.id) is None):
        bot.message.reply_text('Ваши данные отсутствуют. Для того, чтобы зарегистрироваться, \
нажмите команду "/start".')
    else:
        if tg_vk_dict.get(bot.effective_user.id):
            del vk_tg_dict[tg_vk_dict[bot.effective_user.id]]
            del tg_vk_dict[bot.effective_user.id]
        if tg_cd_dict.get(bot.effective_user.id):
            del cd_tg_dict[tg_cd_dict[bot.effective_user.id]]
            del tg_cd_dict[bot.effective_user.id]
        bot.message.reply_text('Ваши данные были удалены. Для того, чтобы снова зарегистрироваться, \
нажмите команду "/start".')

def print_answer(bot, _):
    if tg_vk_dict.get(bot.effective_user.id):
        bot.message.reply_text('''Если вы хотите изменить адресанта сообщений в ВК, нажмите команду "/start".''')
    else:
        bot.message.reply_text('''Здравствуйте!
Чтобы зарегистрироваться и иметь возможность пересылать себе сообщения из ВК\
(подробнее: https://github.com/andvch/VK2TG-Forwarder) нажмите команду "/start".''')

def vk_mainloop(vk, bot):
    for vk_message in vk.listen():
        # print(vk_message)
        if vk_message['from_id'] < 0:
            continue

        if cd_tg_dict.get(vk_message['text']):
            if vk_tg_dict.get(vk_message['from_id']):
                del tg_vk_dict[vk_tg_dict[vk_message['from_id']]] # Удаляем старую связку telegram-vk
            vk_tg_dict[vk_message['from_id']] = cd_tg_dict[vk_message['text']]
            tg_vk_dict[cd_tg_dict[vk_message['text']]] = vk_message['from_id']
            del tg_cd_dict[cd_tg_dict[vk_message['text']]] # Удаляем связку telegram-code, так как пароль был использован
            del cd_tg_dict[vk_message['text']] # Удаляем связку telegram-code, так как пароль был использован
            vk.send_message(
                    '''Поздравляем!
Теперь вы можете писать сюда сообщения и они будут пересланы зарегистрированному вами аккаунту в Telegram.''',
                    vk_message['from_id'])
            continue
        
        if vk_tg_dict.get(vk_message['from_id']) is None:
            vk.send_message(
                    f'Вы не являетесь зарегистрированным участником. Напишите боту в Telegram: {bot.link}',
                    vk_message['from_id'])
            continue

            
        message = ConvertedForwardedMessages(vk_message)
        #vk.send_message(
        #        f'В какой чат переслать {message.num_messages_to_send} сообщений?',
        #        vk_message['from_id'],
        #        vk_message['id'])

        sig = Signer(vk.get_names(message.author_ids), date_format=DATE_FORMAT)
        num = message.send(bot, vk_tg_dict[vk_message['from_id']], sig)
        vk.send_message(
                f'Доставлено {num} из {message.num_messages_to_send} сообщений',
                vk_message['from_id'],
                vk_message['id'])

if __name__ == "__main__":
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
    #vk_thread = threading.Thread(target=vk_mainloop)
    #tg_thread = threading.Thread(target=tg_mainloop)
