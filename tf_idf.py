import importlib
import sys
import time

importlib.reload(sys)

import requests
from bs4 import BeautifulSoup
import time
import pymongo
import xlrd

import os.path
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal, LAParams
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed


from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys

time1 = time.time()

#数据库连接
cilent = pymongo.MongoClient('4localhost', 27017)  # 读取训练好的词集
db = cilent['Report']
col = db['rawpdf']

#下载地址
downloadpath='/Users/billchen/Desktop/test1'

#读取URL
def reportcrawler():
    # 读取excel中的行业代码
    workbook = xlrd.open_workbook(r'/Users/billchen/Documents/internship/东证期货/Copy of 若干行业名单20190723.xlsx')
    sheet1 = workbook.sheet_by_name('sw钢铁')
    rows1 = sheet1.nrows
    codes = list()
    for i in range(1, rows1):
        codes.append([sheet1.cell(i, 0).value, sheet1.cell(i, 2).value])

    header = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"}
    # 读取年度报告
    for each in codes:
        urlsh = 'http://www.sse.com.cn/assortment/stock/list/info/announcement/index.shtml?productId='+str(each[0])[:-3]
        urlsz = 'http://www.szse.cn/disclosure/listed/fixed/index.html'
        url=''
        if str(each[0])[-3:] == ".SH":
            url=urlsh
        else:
            url=urlsz
        if url=='':
            print("Wrong stock id!")
            continue

        print(url)

        # Chrome 配置
        # coption=webdriver.ChromeOptions()
        # prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': downloadpath}
        # coption.add_experimental_option('prefs',prefs)
        # browser =webdriver.Chrome(chrome_options=coption)

        browser = webdriver.Safari()

        browser.get(url)
        browser.maximize_window()
        time.sleep(1)

        if str(each[0])[-3:] == ".SH":
            # s1=browser.find_element_by_id('single_select_2')
            # print(s1.get_attribute('type'))
            # print(Select(s1).options)
            # Select(s1).select_by_value("YEARLY")

            browser.find_element_by_class_name("form-control").send_keys("年年度报告摘要")

            browser.find_element_by_id('btnQuery').click()
            contents=browser.page_source
            # print(contents)
            browser.close()

            soup = BeautifulSoup(contents, 'lxml')
            titles = soup.select('dl.modal_pdf_list > dd > em > a')
            print(titles)
            dates = soup.select('dl.modal_pdf_list > dd > span')
            print(dates)
            count=0
            for title in titles:
                print(title.get('href'))
                print(title.text + dates[count].text)
                col.insert_one({'url': title.get('href'),
                                'title': title.text+dates[count].text})
                count+=1

            time.sleep(2)
        else:
            browser.find_element_by_id("input_code").send_keys(each[0][:-3])
            time.sleep(1)
            browser.find_element_by_id("input_code").send_keys(Keys.ENTER)
            # browser.find_element_by_id('query-btn').click()
            print("pass")
            tt1=browser.find_element_by_class_name('disclosure-tbody')
            print(tt1.get_attribute('innerHTML'))
            contentsz = browser.page_source
            # print(contentsz)
            expandbutton=browser.find_elements_by_css_selector("[class='btn btn-default c-selectex-btn  dropdown-btn']")
            expandbutton[2].click()
            choice=browser.find_elements_by_css_selector('ul#c-selectex-menus-3 > li')
            choice[0].click()

            time.sleep(1)
            reports = browser.find_elements_by_class_name("titledownload-icon")
            print(reports)

            for link in reports:
                link.click()
                break

            print("pass1")

            browser.close()


            # soup = BeautifulSoup(contentsz, 'lxml')
            # titlessz = soup.select('tbody.disclosure-tbody > tr > td.text-left text-title-td')
            # # titlessz = soup.find_all('a', {'class': 'annon-title-link'})
            # print(titlessz)

            # print(datesz)
            # count = 0
            # for titlesz in titlessz:
            #     print(titlesz.get('href'))
            #     print(titlesz.text + datesz[count].text)
            #     col.insert_one({'url': titlesz.get('href'),
            #                     'title': titlesz.text + datesz[count].text})
            #     count += 1
            #
            # time.sleep(2)



    return titles

#下载数据库中所有域名的pdf
def downloadreport():
    if not os.path.exists(downloadpath):
        os.mkdir(downloadpath)


    for each in col.find():
        if each['title'].find("年度报告")!=-1:
            detail_url=each['url']
            fname=downloadpath+r"/"+each['title']+".pdf"

            print(detail_url)

            r = requests.get(detail_url)

            with open(fname, 'wb') as f:
                f.write(r.content)
            print('已下载：', fname)
            f.close()


def parse(filename):
    '''解析PDF文本，并保存到TXT文件中'''
    fp = open(filename, 'rb')
    # 用文件对象创建一个PDF文档分析器
    parser = PDFParser(fp)
    # 创建一个PDF文档
    doc = PDFDocument()
    # 连接分析器，与文档对象
    parser.set_document(doc)
    doc.set_parser(parser)

    # 提供初始化密码，如果没有密码，就创建一个空的字符串
    doc.initialize()

    # 检测文档是否提供txt转换，不提供就忽略
    if not doc.is_extractable:
        raise PDFTextExtractionNotAllowed
    else:
        # 创建PDF，资源管理器，来共享资源
        rsrcmgr = PDFResourceManager()
        # 创建一个PDF设备对象
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        # 创建一个PDF解释其对象
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        # 循环遍历列表，每次处理一个page内容
        # doc.get_pages() 获取page列表
        for page in doc.get_pages():
            interpreter.process_page(page)
            # 接受该页面的LTPage对象
            layout = device.get_result()
            # 这里layout是一个LTPage对象 里面存放着 这个page解析出的各种对象
            # 一般包括LTTextBox, LTFigure, LTImage, LTTextBoxHorizontal 等等
            # 想要获取文本就获得对象的text属性，
            for x in layout:
                if (isinstance(x, LTTextBoxHorizontal)):
                    with open(filename[:-4]+r'.txt', 'a') as f:
                        results = x.get_text()
                        print(results)
                        f.write(results + "\n")


if __name__ == '__main__':
    reportcrawler()
    downloadreport()
    for root, dirs, files in os.walk(downloadpath):
        for name in files:
            filename=os.path.join(root,name)
            if filename[-3:]=="pdf":
                parse(filename)

    command_deletepdf="rm "+downloadpath+"/*.pdf"
    os.system(command_deletepdf)





