from unittest.mock import MagicMock, call
from forwarder.messageconverter import ConvertedForwardedMessages

tg_chat_id = 555


def test_empty_message():
    vk_message = {'from_id': 1, 'date': 0, 'fwd_messages': [
        {'from_id': 2, 'date': 100, 'fwd_messages': [
            {'from_id': 3, 'date': 1000}
        ]}
    ]}
    msg = ConvertedForwardedMessages(vk_message)
    assert not msg


vk_big_message = {
    'from_id': 123, 'date': 10001, 'text': '0',
    'fwd_messages': [
        {'from_id': 12, 'date': 1000, 'text': '2', 'fwd_messages': [
            {'from_id': 33, 'date': 100, 'text': '3'},
            {'from_id': 12, 'date': 101, 'fwd_messages': [
                {'from_id': 1, 'date': 0, 'text': '4'}
            ]},
            {'from_id': 33, 'date': 102, 'text': '5'}
        ]},
        {'from_id': 12, 'date': 101, 'text': '6'}
    ],
    'reply_message': {'from_id': 1, 'date': 1001, 'text': '1'}
}


def test_sending_order():
    msg = ConvertedForwardedMessages(vk_big_message)
    assert msg.num_messages_to_send == 7
    bot = MagicMock()
    msg.send(bot, tg_chat_id)
    for i in range(msg.num_messages_to_send):
        assert bot.method_calls[i] == call.send_message(tg_chat_id, str(i))


def test_signature():
    msg = ConvertedForwardedMessages(vk_big_message)
    bot, signer = MagicMock(), MagicMock(return_value='sig')
    msg.send(bot, tg_chat_id, signer)
    assert len(signer.call_args_list) == 7
    assert signer.call_args_list[0] == ((123, 10001, []),)
    assert signer.call_args_list[1] == ((1, 1001, [(123, 10001)]),)
    assert signer.call_args_list[2] == ((12, 1000, [(123, 10001)]),)
    assert signer.call_args_list[3] == ((33, 100, [(12, 1000), (123, 10001)]),)
    assert signer.call_args_list[4] == ((1, 0, [(12, 101), (12, 1000), (123, 10001)]),)
    assert signer.call_args_list[5] == ((33, 102, [(12, 1000), (123, 10001)]),)
    assert signer.call_args_list[6] == ((12, 101, [(123, 10001)]),)
