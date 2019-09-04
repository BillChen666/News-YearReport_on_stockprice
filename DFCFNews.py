from selenium import webdriver
import pymongo
import requests
from bs4 import BeautifulSoup
from lxml import etree
import time

cilent = pymongo.MongoClient('localhost', 27017)
db = cilent['KDX']
col = db['DFCF']


browser = webdriver.Chrome()   # 初始化浏览器
for i in range(2, 605):  # 要爬取的页数
    url = 'http://so.eastmoney.com/news/s?keyword=%E5%BA%B7%E5%BE%97%E6%96%B0&pageindex='\
          +str(i)+'&searchrange=32768&sortfiled=4'
    browser.get(url)
    hrefs = browser.find_elements_by_css_selector('body > div.container > div.main.clearflaot >'
                                                  ' div.modules > div.module.module-news-list >'
                                                  ' div > h3 > a')
    dates = browser.find_elements_by_xpath('/html/body/div[2]/div[2]/div[2]/div[3]/div/p')
    for nh, date in zip(hrefs, dates):
        print(nh.text, nh.get_attribute('href'), date.text)
        col.insert_one({'title':nh.text,
                        'url': nh.get_attribute('href'),
                        'text': date.text})
    if i%10 == 0:  # 每爬取10个暂停3秒
        time.sleep(3)

browser.close()


data = list()
for each in col.find():
    data.append([each['title'], each['url']])

header = {'User-Agent': "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)"}
for i in range(3031, 6032):
    try:
        wb_data = requests.get(data[i][1], headers=header)
        wb_data.encoding = 'utf-8'
        soup = BeautifulSoup(wb_data.text, 'lxml')

        contents = soup.select('p')
        content = str()
        for each in contents:
            content += each.text

        print(data[i][1], content)
        col.update_one({'url': data[i][1]}, {'$set': {'content': content}})
    except Exception as e:
        print(str(e))
        continue