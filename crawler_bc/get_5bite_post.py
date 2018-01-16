#!/usr/bin/env python3.6
# coding=utf-8

import sys
sys.path.append('../')
sys.path.append('../../')


from spider_bc_news.spider import Spider


def getJson(soup):
    s = str(soup)
    return s[s.find('{'):s.rfind('}')+1]


def get_info(pid):

    spider = Spider()
    post_url = 'http://www.5bite.com/post/%s.html' % pid

    import pdb; pdb.set_trace()
    soup = spider.getSoup(post_url)

    title = soup.find('h1', {'class': 'post-title'}).text

    entry = soup.find('div', {'class': 'entry'})
    pall = entry.findAll('p')
    content = ''

    for p in pall:
        content = '{}\n{}'.format(p.text, content)

    print(title)
    print(content)


if __name__ == '__main__':
    get_info(20)
