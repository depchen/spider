# -*- coding: utf-8 -*-
import scrapy
import json
from datetime import datetime
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy import signals
from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from ArticleSpider.items import LagouJobItem,LagouJobItemLoader
from ArticleSpider.utils.common import get_md5

class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com']
    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
    headers = {
        'User-Agent': agent,
    }
    rules = (
        Rule(LinkExtractor(allow=("zhaopin/.*",)),follow=True),
        Rule(LinkExtractor(allow=("gongsi/j\d+.html",)), follow=True),
        #Rule(LinkExtractor(allow=("www.lagou.com/zhaopin/",)), callback='parse_job', follow=True),
        Rule(LinkExtractor(allow=r'jobs/\d+.html'), callback='parse_job', follow=True)
    )

    def __init__(self):
        self.browser = webdriver.Chrome(
            executable_path="G:/python/Envs/ArticleSpider/chromedriver.exe")
        super(LagouSpider, self).__init__()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        # 当爬虫退出的时候退出chrome
        print("spider closed")
        self.browser.quit()

    # def get_cookie_from_cache(self):
    #     import os
    #     import pickle
    #     import time
    #     cookie_dict = {}
    #     for parent, dirnames, filenames in os.walk('G:/python/Envs/ArticleSpider/ArticleSpider/cookies/lagou'):
    #         for filename in filenames:
    #             if filename.endswith('.lagou'):
    #                 print(filename)
    #                 with open('G:/python/Envs/ArticleSpider/ArticleSpider/cookies/lagou' + filename, 'rb') as f:
    #                     d = pickle.load(f)
    #                     cookie_dict[d['name']] = d['value']
    #     return cookie_dict

    def start_requests(self):
        self.browser.get("https://passport.lagou.com/login/login.html")
        self.browser.find_element_by_css_selector("div:nth-child(2) > "
                        "form > div:nth-child(1) > input").send_keys(
            "18119318127")
        self.browser.find_element_by_css_selector("div:nth-child(2) > "
                        "form > div:nth-child(2) > input").send_keys(
            "915421")
        self.browser.find_element_by_css_selector(
            "div:nth-child(2) > form > div.input_item.btn_group.clearfix > input").click()
        # import time
        # time.sleep(10)

        Cookies = self.browser.get_cookies()
        jsonCookies=json.dumps(Cookies)
        cookie=json.loads(jsonCookies)
        self.cookie=cookie

        #print(Cookies)
        # cookie_dict = {}
        # import pickle
        # for cookie in Cookies:
        #     # 写入文件
        #     f = open('G:/python/Envs/ArticleSpider/ArticleSpider/cookies/lagou' + cookie['name'] + '.lagou', 'wb')
        #     pickle.dump(cookie, f)
        #     f.close()
        #     cookie_dict[cookie['name']] = cookie['value']
        # return cookie_dict
        self.browser.close()
        return [scrapy.Request(url=self.start_urls[0], cookies=cookie, callback=self.parse)]
    # def parse_start_url(self, response):
    #     return []
    #
    # def process_results(self, response, results):
    #     return results

    def parse_job(self, response):
        # 解析拉勾网的职位
        item_loader=LagouJobItemLoader(item=LagouJobItem(),response=response)
        item_loader.add_css("title",".job-name::attr(title)")
        item_loader.add_value("url",response.url)
        item_loader.add_value("url_object_id",get_md5(response.url))
        item_loader.add_css("salary",".job_request .salary::text")
        item_loader.add_xpath("job_city","//*[@class='job_request']/p/span[2]/text()")
        item_loader.add_xpath("work_years", "//*[@class='job_request']/p/span[3]/text()")
        item_loader.add_xpath("degree_need", "//*[@class='job_request']/p/span[4]/text()")
        item_loader.add_xpath("job_type", "//*[@class='job_request']/p/span[5]/text()")
        item_loader.add_css("tags",".position-label li::text")
        item_loader.add_css("publish_time",".publish_time::text")
        item_loader.add_css("job_advantage",".job-advantage p::text")
        item_loader.add_css("job_desc",".job_bt div")
        item_loader.add_css("job_addr",".work_addr")
        item_loader.add_css("company_url","#job_company dt a::attr(href)")
        item_loader.add_css("company_name","#job_company dt a img::attr(alt)")
        item_loader.add_value("crawl_time",datetime.now())
        job_item=item_loader.load_item()
        # response_text = response.text
        #i['domain_id'] = response.xpath('//input[@id="sid"]/@value').extract()
        #i['name'] = response.xpath('//div[@id="name"]').extract()
        #i['description'] = response.xpath('//div[@id="description"]').extract()
        return job_item
