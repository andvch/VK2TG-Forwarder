# from telegram import (
#     InputMediaPhoto,
#     InputMediaVideo,
#     InputMediaAudio,
#     InputMediaDocument
# )


class Attachment:
    def __init__(self, type, **kwargs):
        self.__dict__ = kwargs
        self.type = type

    @property
    def params(self):
        p = self.__dict__.copy()
        for key, value in self.__dict__.items():
            if value is None:
                p.pop(key)
        p.pop('type')
        return p


class ConvertedMessage:
    def __init__(self, vk_message, attachment_group_limit=10, forwarders=[]):
        self.author_id = vk_message['from_id']
        self.date = vk_message['date']
        self.text = vk_message.get('text', '')
        self.forwarders = forwarders
        self.text_attachments = []
        self.attachment_groups = []

        photos, documents, audio, non_grouped_media = [], [], [], []

        for attachment in vk_message.get('attachments', []):
            attachment = self.parse_attachment(attachment)
            if attachment.type in ('link', 'poll'):
                self.text_attachments.append(attachment.text)
            elif attachment.type == 'photo':
                photos.append(attachment)
            elif attachment.type == 'document':
                documents.append(attachment)
            elif attachment.type == 'audio':
                audio.append(attachment)
            elif attachment.type in ('voice', 'animation'):
                non_grouped_media.append([attachment])
            else:
                pass

        self.attachment_groups = []
        for grouped_media in (photos, documents, audio):
            for i in range(0, len(grouped_media), attachment_group_limit):
                self.attachment_groups.append(grouped_media[i: i + attachment_group_limit])
        self.attachment_groups.extend(non_grouped_media)

    def __bool__(self):
        return bool(self.text or self.text_attachments or self.attachment_groups)

    @staticmethod
    def parse_attachment(data):
        a = Attachment(data['type'])
        data = data[a.type]

        if a.type in ('photo', 'sticker'):
            if a.type == 'photo':
                images = data['sizes']
            else:
                images = data['images']
                a.type = 'photo'

            best_size = 0
            for image in images:
                width, height = image['width'], image['height']
                url = image['url']
                if best_size <= width * height:
                    best_size = width * height
                    a.photo = url

        elif a.type == 'doc':
            ext = data.get('ext') or data['title'].split('.')[-1]
            if ext == 'gif':
                a.type = 'animation'
                a.animation = data['url']
            else:
                a.type = 'document'
                a.document = data['url']

        elif a.type == 'link':
            a.text = f"_Ссылка_ [{data.get('title', 'link')}]({data['url']})"

        else:
            a.type = 'unknown'

        return a

    def send(self, bot, tg_chat_id, signer=lambda *args, **kwargs: ''):
        text = []
        if self.text:
            text.append(self.text)
        text.extend(self.text_attachments)
        sig = signer(self.author_id, self.date, self.forwarders)
        if sig:
            text.append(sig)
        text = '\n\n'.join(text)

        ok_counter = 0
        if not self.attachment_groups:
            try:
                bot.send_message(tg_chat_id, text)
                ok_counter += 1
            except:
                pass

        for attachment_group in self.attachment_groups:
            if attachment_group is not self.attachment_groups[0]:
                text = sig if sig else None

            if len(attachment_group) == 1:
                attachment = attachment_group[0]
                try:
                    eval(f"bot.send_{attachment.type}"
                         "(tg_chat_id, caption=text, **attachment.params)")
                    ok_counter += 1
                except:
                    pass
                continue

            media = []
            for attachment in attachment_group:
                params = attachment.params
                params['media'] = params.pop(attachment.type)
                if attachment is attachment_group[0]:
                    params['caption'] = text
                try:
                    media.append(eval(f"InputMedia{attachment.type.title()}(**params)"))
                except:
                    pass

            try:
                bot.send_media_group(tg_chat_id, media)
                ok_counter += 1
            except:
                pass

        return ok_counter


class ConvertedForwardedMessages:
    def __init__(self, vk_message):
        self.messages = []
        self.num_messages_to_send = 0
        self.author_ids = set()
        self.__parse(vk_message)

    def __parse(self, vk_message, forwarders=[]):
        message = ConvertedMessage(vk_message, forwarders=forwarders[::-1])
        if message:
            self.messages.append(message)
            self.num_messages_to_send += max(1, len(message.attachment_groups))

        self.author_ids.add(message.author_id)
        forwarders = forwarders + [(message.author_id, message.date)]
        if 'reply_message' in vk_message:
            self.__parse(vk_message['reply_message'], forwarders)
        for fwd_message in vk_message.get('fwd_messages', []):
            self.__parse(fwd_message, forwarders)

    def send(self, bot, tg_chat_id, signer=lambda *args, **kwargs: ''):
        ok_counter = 0
        for message in self.messages:
            ok_counter += message.send(bot, tg_chat_id, signer)
        return ok_counter
