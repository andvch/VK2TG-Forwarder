from telegram.ext import Updater, Defaults
from vk import VkApi
from messageconverter import ConvertedForwardedMessages
from signer import Signer

with open('config') as f:
    exec(f.read())

def vk_mainloop(vk, bot):
    for vk_message in vk.listen():
        # print(vk_message)
        if vk_message['from_id'] < 0:
            continue
        message = ConvertedForwardedMessages(vk_message)
        #vk.send_message(
        #        f'В какой чат переслать {message.num_messages_to_send} сообщений?',
        #        vk_message['from_id'],
        #        vk_message['id'])

        sig = Signer(vk.get_names(message.author_ids), date_format=DATE_FORMAT)
        num = message.send(bot, CHAT_ID, sig)
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
    vk_mainloop(vk, updater.bot)
    #vk_thread = threading.Thread(target=vk_mainloop)
    #tg_thread = threading.Thread(target=tg_mainloop)
