"""Классы для конвертации и отправки сообщений в Телеграм."""

from telegram import (  # noqa: F401
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaAudio,
    InputMediaDocument,
    Bot
)

from telegram.error import TelegramError
from typing import Any, Callable
import requests


class Attachment:
    """Вложение в Телеграм-сообщении.

    Args:
        type (:obj:`str`): Тип вложения (если вложение не текстовое,
        то должен совпадать с название в телеграм-API).
        kwargs: Параметры, которые будут использованы при отправке.

    """

    def __init__(self, type: str, **kwargs):
        """Конструктор класса Attachment."""
        self.__dict__ = kwargs
        self.type = type

    @property
    def params(self) -> dict:
        """:obj:`dict`: Параметры вложения."""
        p = self.__dict__.copy()
        for key, value in self.__dict__.items():
            if value is None:
                p.pop(key)
        p.pop('type')
        return p


class ConvertedMessage:
    """Конвертированное сообщение из ВК, пригодное для отправки в Телеграм.

    Args:
        vk_message (:obj:`dict`): Сообщение, полученное из ВК.
        attachment_group_limit (:obj:`int`, optional): Максимально допустимое количество
        вложений в одном отправляемом сообщении.
        forwarders (List[(:obj:`int`, :obj:`int`)], optional): Упорядоченный в хронологическом
        порядке список пар id переславших сообщение и времени пересылки в
        формате Unix timestamp.

    """

    def __init__(self, vk_message: dict, attachment_group_limit: int = 10, forwarders: list = []):
        """Конструктор класса ConvertedMessage."""
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

    def __bool__(self) -> bool:
        """Пустое ли сообщение."""
        return bool(self.text or self.text_attachments or self.attachment_groups)

    @staticmethod
    def parse_attachment(
            data: dict,
            file_downloader: Callable[[str], Any] = lambda url: requests.get(url).content
    ) -> Attachment:
        """Конвертирует вложение из ВК для отправки в Телеграм.

        Args:
            data (:obj:`dict`): Вложение, полученное из ВК.
            file_downloader (Callable, optional): Функция, принимающая
            прямую ссылку на данные и возвращающая эти данные.

        Returns:
            :class:`Attachment`

        """
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

        elif a.type == 'audio':
            a.title = data.get('title')
            a.performer = data.get('artist')
            a.duration = data.get('duration')
            a.audio = file_downloader(data['url'])
            a.filename = f"{data.get('title', 'audio')}.mp3"

        elif a.type == 'doc':
            a.type = 'document'
            ext = data.get('ext') or data['title'].split('.')[-1]
            if ext == 'gif':
                a.type = 'animation'
                a.animation = data['url']
            elif ext in ('pdf', 'zip'):  # https://core.telegram.org/bots/api#sending-files
                a.document = data['url']
            else:
                a.document = file_downloader(data['url'])
                a.filename = data['title']

        elif a.type == 'audio_message':
            a.duration = data.get('duration')
            if 'link_ogg' in data:
                a.type = 'voice'
                a.voice = data['link_ogg']
            else:
                a.type = 'audio'
                a.audio = file_downloader(data['link_mp3'])
                a.filename = 'Voice message.mp3'

        elif a.type == 'poll':
            poll = [f"*{data['question']}*"]
            for answer in data['answers']:
                rate = round(answer['rate'])
                votes = answer['votes']
                scale = ('=' * (1 + rate // 10)).ljust(10)[:10]
                poll.append(f"{answer['text']}\n`{scale} {rate}% ({votes})`")
            a.text = '\n\n'.join(poll)

        elif a.type == 'graffiti':
            a.type = 'photo'
            a.photo = data['url']

        elif a.type == 'video':
            a.type = 'link'
            title = data['title']
            url = f"https://vk.com/video{data['owner_id']}_{data['id']}"
            a.text = f"_Видео_ [{title}]({url})"
            # FIXME: broken for private videos

        elif a.type == 'link':
            a.text = f"_Ссылка_ [{data.get('title', 'link')}]({data['url']})"

        elif a.type == 'wall':
            a.type = 'link'
            wall_id = f"{data.get('owner_id') or data['to_id']}_{data['id']}"
            url = f"https://vk.com/wall{wall_id}"
            a.text = f"[Запись на стене]({url})"

        elif a.type == 'wall_reply':
            a.type = 'link'
            wall_id = f"{data.get('owner_id') or data['to_id']}_{data['post_id']}"
            url = f"https://vk.com/wall{wall_id}?reply={data['id']}"
            a.text = f"[Комментарий к записи]({url})"

        else:
            a.type = 'unknown'

        return a

    def send(self, bot: Bot, tg_chat_id: int,
             signer: Callable[[], Any] = lambda *args, **kwargs: '') -> int:
        """Отправляет сообщение в Телеграм-чат.

        Args:
            bot (:class:`telegram.Bot`): Бот, через которого будет осуществлена отправка.
            tg_chat_id (:obj:`int`): Чат, в который будет отправлено сообщение.
            signer (Callable, optional): Функция, принимающая упорядоченный
            в хронологическом порядке список List[(:obj:`int`, :obj:`int`)]
            пар id переславших сообщение и времени пересылки в формате Unix timestamp.

        Returns:
            :obj:`int`: Число фактически отправленных сообщений.

        """
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
            except TelegramError:
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
                except TelegramError:
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
                except TelegramError:
                    pass

            try:
                bot.send_media_group(tg_chat_id, media)
                ok_counter += 1
            except TelegramError:
                pass

        return ok_counter


class ConvertedForwardedMessages:
    """Конвертированные вложенные сообщения из ВК, пригодные для отправки в Телеграм.

    Args:
        vk_message (:obj:`dict`): Сообщение, полученное из ВК.

    """

    def __init__(self, vk_message: dict):
        """Конструктор класса ConvertedForwardedMessages."""
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

    def __bool__(self) -> bool:
        """Пустое ли сообщение."""
        return bool(self.num_messages_to_send)

    def send(self, bot: Bot, tg_chat_id: int,
             signer: Callable[[], Any] = lambda *args, **kwargs: '') -> int:
        """Отправляет сообщение в Телеграм-чат.

        Args:
            bot (:class:`telegram.Bot`): Бот, через которого будет осуществлена отправка.
            tg_chat_id (:obj:`int`): Чат, в который будет отправлено сообщение.
            signer (Callable, optional): Функция, принимающая упорядоченный
            в хронологическом порядке список List[(:obj:`int`, :obj:`int`)]
            пар id переславших сообщение и времени пересылки в формате Unix timestamp.

        Returns:
            :obj:`int`: Число фактически отправленных сообщений.

        """
        ok_counter = 0
        for message in self.messages:
            ok_counter += message.send(bot, tg_chat_id, signer)
        return ok_counter
