import requests
from bs4 import BeautifulSoup
import time
import re
import pymongo
import xlwt


def getTitle(header):
    data = list()
    for page in range(10, 68):  # 要爬取的页数
        url = 'http://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php?symbol=sz000002' \
              '&Page=%d'%page
        wb_data = requests.get(url, headers=header)
        wb_data.encoding='gb2312'   # 网页的编码方式

        soup = BeautifulSoup(wb_data.text, 'lxml')
        titles = soup.select('div.datelist > ul > a')   # 要获取的数据所在的标签
        for title in titles:
            mat = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", title.get('href'))   # 用正则表达式匹配出日期
            if mat==None:
                date = 'None'
            else:
                date = mat.group(0)
            data.append([title.get('href'), title.text, date])   # 加入的数据分别为：链接、标题、日期

        time.sleep(5)   # 暂停5秒，以免爬取频率过高被发现

    return data


def getContent(title, header):
    data = list()
    count = 0
    for each in title:
        url = each[0]
        wb_data = requests.get(url, headers=header)
        wb_data.encoding='utf-8'   # 网页编码方式
        soup = BeautifulSoup(wb_data.text, 'lxml')

        contents = soup.select('.article p')   # 新闻主题所在的标签
        content = str()
        temp = list()
        temp.append(each[0]); temp.append(each[1]); temp.append(each[2])
        for each in contents:
            content += each.text
        temp.append(content)

        data.append(temp)

        count = count + 1   # 每隔10条数据，等待3秒
        if count%10==0:
            time.sleep(3)

    return data


def saveDatabse(database, collection, data):
    cilent = pymongo.MongoClient('localhost', 27017)   # pymongo的localhost和端口
    db = cilent[database]   # database 数据库名
    co = db[collection]   # collection 数据集名

    for each in data:
        co.insert_one({'url': each[0],
                       'title': each[1],
                       'date': each[2],
                       'content': each[3]})   # url,title,date,content是数据库的字段名


def saveExcel(data):
    f = xlwt.Workbook()
    sheet1 = f.add_sheet(u'sheet1', cell_overwrite_ok=True)
    for i in range(len(data)):
        sheet1.write(i, 0, data[i][0])
        sheet1.write(i, 1, data[i][1])
        sheet1.write(i, 2, data[i][2])
        sheet1.write(i, 3, data[i][3])
        sheet1.write(i, 4, "  ")

    f.save('test070401.xls')  # 保存文件


if __name__ == '__main__':
    header = {'User-Agent': "Mozilla/4.0 (compatible;"
                            " MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser;"
                            " .NET CLR 1.1.4322; .NET CLR 2.0.50727)"}  # header头，爬虫需要
    title = getTitle(header)
    data = getContent(title, header)
    saveDatabse('TextSentiment', 'WK_News', data)