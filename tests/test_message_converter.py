from unittest.mock import MagicMock
from forwarder.messageconverter import ConvertedMessage

forwarders = [(2, 100), (3, 1000)]
tg_chat_id = 555


def test_empty_message():
    vk_message = {'from_id': 1, 'date': 0}
    msg = ConvertedMessage(vk_message, forwarders=forwarders)
    assert not msg


def test_text_only_message():
    vk_message = {'from_id': 1, 'date': 0, 'text': 'Hello!'}
    msg = ConvertedMessage(vk_message, forwarders=forwarders)
    assert msg
    bot = MagicMock()
    msg.send(bot, tg_chat_id)
    assert len(bot.method_calls) == 1
    bot.send_message.assert_called_with(tg_chat_id, 'Hello!')


def test_message_with_signature():
    vk_message = {'from_id': 1, 'date': 0, 'text': 'Hello!'}
    msg = ConvertedMessage(vk_message, forwarders=forwarders)
    assert msg
    bot, signer = MagicMock(), MagicMock(return_value='With love')
    msg.send(bot, tg_chat_id, signer)
    signer.assert_called_with(vk_message['from_id'], vk_message['date'], forwarders)
    assert len(bot.method_calls) == 1
    bot.send_message.assert_called_with(tg_chat_id, 'Hello!\n\nWith love')


def test_message_with_photo():
    vk_message = {'from_id': 1, 'date': 0, 'text': 'Hello!', 'attachments': [
        {'type': 'photo', 'photo': {'sizes': [
            {'width': 5, 'height': 4, 'url': 'middle.jpg'},
            {'width': 3, 'height': 3, 'url': 'small.jpg'},
            {'width': 5, 'height': 5, 'url': 'big.jpg'},
            {'width': 4, 'height': 5, 'url': 'middle2.jpg'}
        ]}}
    ]}
    msg = ConvertedMessage(vk_message, forwarders=forwarders)
    assert msg
    bot = MagicMock()
    msg.send(bot, tg_chat_id)
    assert len(bot.method_calls) == 1
    bot.send_photo.assert_called_with(tg_chat_id, caption='Hello!', photo='big.jpg')


def test_attachments_limit():
    vk_message = {'from_id': 1, 'date': 0, 'text': 'Hello!', 'attachments': [
        {'type': 'photo', 'photo': {'sizes': [
            {'width': 300, 'height': 300, 'url': f'photo_{i}.jpg'}
        ]}}
        for i in range(10)
    ]}
    msg = ConvertedMessage(vk_message, forwarders=forwarders, attachment_group_limit=3)
    assert msg
    bot = MagicMock()
    msg.send(bot, tg_chat_id)
    assert len(bot.method_calls) == 4
    assert bot.send_media_group.call_count == 3
    assert bot.send_photo.call_count == 1
    bot.send_photo.assert_called_with(tg_chat_id, caption=None, photo='photo_9.jpg')


def test_attachment_groups():
    def attachment(i):
        return [
            {'type': 'photo', 'photo': {'sizes': [
                {'width': 300, 'height': 300, 'url': f'photo_{i}.jpg'}
            ]}},
            {'type': 'doc', 'doc': {'ext': 'pdf', 'url': f'doc_{i}.pdf'}},
            {'type': 'doc', 'doc': {'ext': 'gif', 'url': f'anim_{i}.gif'}}
        ][i % 3]

    vk_message = {'from_id': 1, 'date': 0, 'text': 'Hello!',
                  'attachments': [attachment(i) for i in range(7)]}
    msg = ConvertedMessage(vk_message, forwarders=forwarders, attachment_group_limit=3)
    assert msg
    bot = MagicMock()
    msg.send(bot, tg_chat_id)
    assert len(bot.method_calls) == 4
    assert bot.send_media_group.call_count == 2
    assert bot.send_animation.call_count == 2
    bot.send_animation.assert_called_with(tg_chat_id, caption=None, animation='anim_5.gif')
