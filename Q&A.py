import json
import random
import time
from urllib.parse import urlencode
from multiprocessing import Pool
import requests
import pymongo

from config import *

"""
爬取知乎首页推荐问答
"""

client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB]
table = db[MONGO_TABLE]


class ZhihuSpider(object):

    def get_page(self, url):
        headers = {
            'User-Agent': random.choice(User_Agent),
            'Cookie': COOKIE,
            'Referer': 'https://www.zhihu.com/'
        }
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            html = response.text
            return html
        return None

    def parse_page(self, html):
        data = json.loads(html)['data']
        try:
            for item in data:
                # 回答方
                answer = item['target'].get('author')
                # 答者
                answer_user = answer['name']
                # 回答
                content = item['target'].get('content')
                # 提问方
                question = item['target'].get('question')
                # 提问
                title = question['title']
                # 提问者
                question_user = question['author'].get('name')
                # 构造储存信息的字典result
                result = {
                    '提问': title,
                    '提问者': question_user,
                    '答题者': answer_user,
                    '回答': content,
                }
                yield result
        except TypeError:
            pass

    def save_to_mongo(self, result):
        try:
            if table.insert(result):
                print('保存到mongoDB')
        except pymongo.errors.InvalidOperation:
            pass


def main(data):
    root_url = 'https://www.zhihu.com/api/v3/feed/topstory/recommend?'
    spider = ZhihuSpider()
    # 构造URL
    url = root_url + urlencode(data)
    html = spider.get_page(url=url)
    result = spider.parse_page(html=html)
    spider.save_to_mongo(result=result)
    time.sleep(1)


if __name__ == '__main__':
    data = [{'page_number': page, 'desktop': 'true', 'session_token': '6214605cf007945023b42ccc70cd151c'} for page in
            range(START, END + 1)]
    pool = Pool()
    pool.map(main, data)
