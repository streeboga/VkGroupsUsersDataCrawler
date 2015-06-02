import sys
import argparse
from grab.spider import Spider, Task
import requests
import xlsxwriter


class VkSpider(Spider):
    __slots__ = ['ids', 'wb', 'ws', 'cur_col', 'parsed']

    def __init__(self, ids):
        super().__init__()
        self.ids = ids
        self.wb = xlsxwriter.Workbook('vk.xlsx')
        self.ws = self.wb.add_worksheet()
        self.cur_col = -1
        self.parsed = 0

    def create_grab_instance(self, **kwargs):
        g = super(VkSpider, self).create_grab_instance(**kwargs)
        g.setup(headers={
            'accept-language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4'
        })
        return g

    def task_generator(self):
        vk_url = 'https://vk.com/id{0}'
        for user_id in self.ids:
            yield Task('parse_page', url=vk_url.format(user_id))

        print('Parsed pages: {0}'.format(self.parsed))
        self.wb.close()

    def task_parse_page(self, grab, task):
        try:
            if len(grab.doc.select('//*[@id="profile_info"]/h4/div[contains(@class, "profile_deleted")]').text()) > 0:
                print("-- Hidden user's page")
                return
        except Exception:
            pass

        try:
            username = grab.doc.select('//*[@id="profile_info"]/h4/div[contains(@class, "page_name")]').text()
            city = grab.doc.select("//*[@id='profile_full_info']//div[contains(@class, 'clear_fix') and div[@class='label fl_l'] = 'Город:']/div[@class='labeled fl_l']/a").text()
            print((username, city))
            self.cur_col += 1
            self.ws.write(self.cur_col, 0, username)

            self.parsed += 1
        except Exception:
            pass


if __name__ == '__main__':
    pattern = "https://api.vk.com/method/groups.getMembers?group_id={0}&count={1}&offset={2}"
    can_next = True
    offset = 0
    count = 1000
    max_users = count + 1
    myset = set()

    argParser = argparse.ArgumentParser()
    argParser.add_argument('-g', '--group')
    args = argParser.parse_args()
    group = args.group or ''

    if len(group) == 0:
        sys.exit('Usage: (-g group_name_or_id)')

    while offset < max_users:
        r = requests.get(pattern.format(group, count, offset))
        req = r.json()
        offset += count
        if 'response' in req:
            print('Current {0}, total {1}'.format(offset, req['response']['count']))

            if 'count' in req['response']:
                max_users = req['response']['count']

            if 'users' in req['response']:
                myset |= set(req['response']['users'])

    print('Total users: {0}. Set: {1}'.format(len(myset), myset))

    if len(myset) > 0:
        print('Starting spider...')
        s = VkSpider(myset)
        s.run()
