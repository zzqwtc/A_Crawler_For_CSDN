from bs4 import BeautifulSoup
import requests
import random
import time
import logging
import datetime
import os
from retry import retry
from fake_useragent import UserAgent


class get_url():
    def __init__(self,url,logger):
        self.blog_url = url
        self.logger = logger

    @retry()
    def get_response(self,url):
        global ua
        headers = {
            "user-agent":ua.random
        }
        try:
            r = requests.get(url = url,headers = headers,timeout = 5)
            r.raise_for_status()
            soup = BeautifulSoup(r.text,'lxml')
            return soup
        except:
            self.logger.error("error when request the url (get_response())")

    def get_url_of_each_page(self,url):
        soup = self.get_response(url)

        article_div = soup.find('div',attrs={'class' : 'article-list'})
        if article_div is None:
            return []

        articles = article_div.find_all('h4')

        article_url = []
        for article in articles:
            article_url.append(article.find('a').get("href"))

        return article_url
        
    def get_page(self):
        article_urls = []

        cnt = 0
        while 1:
            cnt += 1
            page_url = self.blog_url + "article/list/" + str(cnt)
            url = self.get_url_of_each_page(page_url)
            if url:
                article_urls += url
            else:
                break

        return article_urls


class visit_url():
    cnt = 0
    total = 0
    def __init__(self,url,logger):
        self.url = url
        self.logger = logger

    @retry()
    def visit_url(self):
        global ua
        headers = {
            "user-agent":ua.random
        }
        for url in self.url:
            try:
                r = requests.get(url = url,headers = headers,timeout = 5)
                r.raise_for_status()
                visit_url.cnt += 1
                visit_url.total += 1
                soup = BeautifulSoup(r.text,'lxml')
                title = soup.find('h1',attrs={"class":"title-article"})
                self.logger.info("成功访问！{} ({})" .format(title.text.strip(),url))
            except:
                self.logger.error("error when visit the url (visit_url())")
                raise
            

    def run(self):
        self.visit_url()


@retry()
def user_profile(logger):
    global ua
    headers = {
        "user-agent":ua.random
    }
    try:
        r = requests.get(url =my_website,headers = headers)
        soup = BeautifulSoup(r.text,'lxml')
        soup = soup.find('div', attrs={'class': 'data-info d-flex item-tiling'})
        information = soup.find_all('dl')
        for inf in information:
            # print(type(inf.text))
            classification = inf.find('dd')
            if(classification.text == "访问"):
                print("当前总访问量为 ：%s" % inf.get("title"))
                return int(inf.get("title"))
    except:
        logger.error("error when get user's profile (user_profile())")
        raise

def set_logger(today):
    logger = logging.getLogger()
    fh = logging.FileHandler(filename = today + '.log', encoding='utf-8',mode = 'a')
    formater = logging.Formatter("%(asctime)s - %(pathname)s[line:%(lineno)d] - 进程 %(process)d - %(levelname)s: %(message)s")
    fh.setFormatter(formater)
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)
    return logger,fh

def reset_logger(logger,fh):
    logging.shutdown()
    logger.removeHandler(fh)

def clean_log_by_day(today):
    today += ".log"
    flag = 0
    log_name = ""
    for root,dirs,files in os.walk(os.path.abspath('')):
        for file in files:
            if file[-4:] == ".log":
                log_name = file
                flag = 1
                break
            if flag == 1:
                break

    
    if os.path.exists(log_name):
        if today != log_name:
            os.remove(log_name)
            f = open(today,'a')
            f.close()

cnt = 0
urls = []
my_website = "https://blog.csdn.net/******/" # 将******替换成自己的博客主页 url
ua = UserAgent()

def run():
    
    while 1:
        global cnt
        global urls

        start_time = time.time()
        date_today = str(datetime.date.today()) # 获取当天的日期
        clean_log_by_day(date_today) # 判断已经存在的日志是否是今天的 不是今天的就清理掉并创建一个新的
        logger,fh = set_logger(date_today) # 获取 logging对象和 FileHandler对象

        # 如果已经爬取到作者的所有文章的url 则直接访问
        if len(urls) == 0:
            get_urls = get_url(my_website,logger)
            urls = get_urls.get_page()

        visit_url.cnt = 0
        visit_url(urls,logger).run()
    
        print("本轮成功访问链接数: %d" % visit_url.cnt)
        now = user_profile(logger)
        print("本轮访问量增加: %d" % (now - cnt))
        cnt = now

        sleeptime = random.randint(5,10)
        logger.info("等待{}s".format(sleeptime))
        logger.info("本轮用时：{}".format(time.time() - start_time))
        reset_logger(logger,fh)

        time.sleep(sleeptime)

if __name__ == "__main__":
    run()

