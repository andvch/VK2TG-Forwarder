"""Описание класса для работы бота в ВК."""

import requests
import random


class VkApi:
    """Класс обеспечивает работу бота в ВК.

    Args:
        token (:obj:`str`): Уникальный код ВК-бота.
        wait (:obj:`int`, optional):.
    """
    api_version = '5.130'
    lp_version = '3'
    new_message_event_type = 4

    def __init__(self, token, wait=25):
        self.token = token
        self.wait = wait
        self.__get_server()

    def __get_server(self, update_ts=True):
        params = {'access_token': self.token,
                  'v': self.api_version,
                  'lp_version': self.lp_version}
        response = requests.get('https://api.vk.com/method/messages.getLongPollServer',
                                params=params).json()['response']

        self.key = response['key']
        self.server = response['server']
        if update_ts:
            self.ts = response['ts']

    def listen(self):
        while True:
            params = {'act': 'a_check',
                      'key': self.key,
                      'ts': self.ts,
                      'wait': self.wait,
                      'mode': '0',
                      'version': self.lp_version}
            response = requests.get(f'https://{self.server}',
                                    params=params,
                                    timeout=self.wait + 5).json()

            if 'failed' in response:
                # https://vk.com/dev/using_longpoll?f=2.%20Answer%20Format
                if response['failed'] == 1:
                    self.ts = response['ts']
                elif response['failed'] == 2:
                    self.__get_server(update_ts=False)
                elif response['failed'] == 3:
                    self.__get_server()
                else:
                    raise Exception(f"{self.lp_version} version are deprecated")
                continue

            self.ts = response['ts']

            message_ids = []
            for event in response['updates']:
                if event[0] == self.new_message_event_type:
                    message_ids.append(event[1])
            if message_ids:
                messages = self.get_messages(message_ids)
                for message_id in message_ids:
                    yield messages[message_id]

    def get_messages(self, message_ids):
        params = {'access_token': self.token,
                  'v': self.api_version,
                  'message_ids': ','.join(map(str, set(message_ids)))}
        response = requests.get('https://api.vk.com/method/messages.getById',
                                params=params).json()['response']
        return dict([(message['id'], message) for message in response['items']])

    def get_names(self, ids):
        users, groups = set(), set()
        for vk_id in ids:
            if vk_id > 0:
                users.add(vk_id)
            else:
                groups.add(vk_id)

        params = {'access_token': self.token,
                  'v': self.api_version,
                  'user_ids': ','.join(map(str, users)),
                  'fields': 'screen_name,sex'}
        users_response = requests.get('https://api.vk.com/method/users.get',
                                      params=params).json()['response']

        params = {'access_token': self.token,
                  'v': self.api_version,
                  'group_ids': ','.join(map(str, groups))}
        groups_response = requests.get('https://api.vk.com/method/groups.getById',
                                       params=params).json()['response']

        result = {}
        for user in users_response:
            name = f"{user['first_name']} {user['last_name']}".strip()
            screen_name = user.get('screen_name', f"id{user['id']}")
            result[user['id']] = (name, screen_name, user.get('sex', 0))
        for group in groups_response:
            screen_name = group.get('screen_name', f"public{group['id']}")
            result[-group['id']] = (group['name'], screen_name, 0)
        return result

    def send_message(self, text, user_id, reply_to=None):
        random_id = random.randint(-2**31, 2**31 - 1)
        params = {'access_token': self.token,
                  'v': self.api_version,
                  'message': text,
                  'user_id': user_id,
                  'random_id': random_id}
        if reply_to is not None:
            params['reply_to'] = reply_to
        requests.get('https://api.vk.com/method/messages.send',
                     params=params)
