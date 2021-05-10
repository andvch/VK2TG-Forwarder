import locale
locale.setlocale(locale.LC_ALL, '')

from datetime import datetime

class Signer:
    def __init__(self, ids_info, date_format=None):
        self.ids_info = ids_info
        self.date_format = date_format

    def __call__(self, author_id, date, forwarders):
        l = len(forwarders)
        text = [self.one_sig(author_id, date, l)]
        for i in range(l):
            text.append(self.one_sig(*forwarders[i], l - i - 1))
        return '\n'.join(text)

    def one_sig(self, user_id, date, n=0):
        name, screen_name, sex = self.ids_info[user_id]
        text = []
        if n:
            text.append('|' * n)
        text.append(f"[{name}](https://vk.com/{screen_name})")
        if self.date_format:
            date = datetime.fromtimestamp(date).astimezone()
            text.append(f"_{date.strftime(self.date_format)}_")
        return ' '.join(text)
