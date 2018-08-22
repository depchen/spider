# -*- coding: utf-8 -*-
import scrapy
import re
import json
import datetime
try:
    import urlparse as parse
except:
    from urllib import parse
from scrapy.loader import ItemLoader
from ArticleSpider.items import ZhihuAnswerItem,ZhihuQuestionItem
from tools.yundama_request import YDMHttp
from ctypes import *

class ZhihuSpider(scrapy.Spider):
    start_answer_url="https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&limit={1}&offset={2}"
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        "User-Agent": agent
    }

    def parse(self, response):
        #提取出所有url，并跟踪这些url进一步爬取
        #如果提取的url为“/question/xxx”，直接进入下载
        all_urls=response.css("a::attr(href)").extract()
        all_urls=[parse.urljoin(response.url,url) for url in all_urls]
        all_urls=filter(lambda x:True if x.startswith("https") else False,all_urls)
        for url in all_urls:
            #print(url)
            match_obj=re.match("(.*zhihu.com/question/(\d+))(/|$).*",url)
            if match_obj:
                #如果提取到了question相关url则进行提取
                request_url=match_obj.group(1)
                #question_id=match_obj.group(2)
                #print(request_url,question_id)
                yield scrapy.Request(request_url,headers=self.headers,callback=self.parse_question)
            else:
                #否则则继续跟踪该url
                yield scrapy.Request(url,headers=self.headers,callback=self.parse)

    def parse_question(self,response):
        #处理question页面，从页面中提取具体的question item
        if "QuestionHeader-title" in response.text:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = int(match_obj.group(2))
            #处理新版本
            item_loader=ItemLoader(item=ZhihuQuestionItem(),response=response)
            item_loader.add_css("title","h1.QuestionHeader-title::text")
            item_loader.add_css("content",".QuestionHeader-detail")
            item_loader.add_value("url",response.url)
            item_loader.add_value("zhihu_id",question_id)
            item_loader.add_css("answer_num",".List-headerText span::text")
            #item_loader.add_xpath("answer_num","//*[@id='root']/div/main/div/div[2]/div[1]/div[1]/a/text()")
            item_loader.add_css("comments_num",".QuestionHeader-Comment button::text")
            #item_loader.add_css("watch_user_num",".NumberBoard-value::text")
            item_loader.add_css("topics",".QuestionHeader-topics .Popover div::text")
            question_item=item_loader.load_item()
        #如果是request,会路由到下载器进行下载
        #yield scrapy.Request(self.start_answer_url.format(question_id,20,0),headers=self.headers,callback=self.parse_answer)
        #如果是item，会路由到pipelines中
        yield question_item

    def parse_answer(self,response):
        #处理question的answer以json形式
        ans_json=json.loads(response.text)
        is_end=ans_json["paging"]["is_end"]
        next_url=ans_json["paging"]["next"]
        #提取answer中的具体值
        for answer in ans_json["data"]:
            answer_item=ZhihuAnswerItem()
            answer_item["zhihu_id"]=answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()
            yield answer_item
        if not is_end:
            yield scrapy.Request(next_url,headers=self.headers,callback=self.parse_answer)

    def start_requests(self):
        return [scrapy.Request('https://www.zhihu.com/#signin', headers=self.headers,callback=self.login1)]

    def login1(self,response):
        from selenium import webdriver
        browser = webdriver.Firefox(executable_path="G:/python/Envs/ArticleSpider/geckodriver.exe")
        browser.get("https://www.zhihu.com/signin")
        browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys("18119318127")
        browser.find_element_by_css_selector(".SignFlow-password input").send_keys("wei915421")
        browser.find_element_by_css_selector(".Button.SignFlow-submitButton").click()
        import time
        time.sleep(10)
        Cookies = browser.get_cookies()
        print(Cookies)
        cookie_dict = {}
        import pickle
        for cookie in Cookies:
             # 写入文件
             f = open('G:/python/Envs/ArticleSpider/ArticleSpider/cookies/zhihu' + cookie['name'] + '.zhihu', 'wb')
             pickle.dump(cookie, f)
             f.close()
             cookie_dict[cookie['name']] = cookie['value']
        #
        #
        # jsonCookies = json.dumps(Cookies)
        # cookie = json.loads(jsonCookies)
        # self.cookie = cookie
        browser.close()
        return [scrapy.Request(url=self.start_urls[0], headers=self.headers,dont_filter=True, cookies=cookie_dict,callback=self.parse)]


    def login(self, response):
        response_text = response.text
        match_obj = re.match('(.*)', response_text, re.DOTALL)
        xsrf = ''
        if match_obj:
            xsrf = (match_obj.group(1))
        if xsrf:
            post_url = "https://www.zhihu.com/login/phone_num"
            post_data = {
                "_xsrf": xsrf,
                "phone_num": "18119318127",
                "password": "wei915421",
                "captcha": ""
            }
            import time
            t = str(int(time.time() * 1000))
            captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
            yield scrapy.Request(captcha_url, headers=self.headers, meta={"post_data": post_data},
                                 callback=self.login_after_captcha)


    def yundama(self):
        # 用户名
        username = 'depchen'
        # 密码
        password = '915421'

        appid = 4846

        appkey = '8e12802c02d379f13786f05b2f453e40'
        # 图片文件G:\python\Envs\ArticleSpider\captcha.jpg
        filename = 'G:\python\Envs\ArticleSpider\captcha.jpg'
        codetype = 1004
        timeout = 60
        if (username == 'username'):
            print('请设置好相关参数再测试')
            return ""
        else:
            # initialization
            yundama = YDMHttp(username, password, appid, appkey)
            # log in
            uid = yundama.login();
            print('uid: %s' % uid)
            # check balances
            balance = yundama.balance();
            print('balance: %s' % balance)
            # start identification
            text = yundama.decode(filename, codetype, timeout);
            print('text: %s' % text)
            return text


    def login_after_captcha(self, response):
        with open("captcha.jpg", "wb") as f:
            f.write(response.body)
            f.close()

        from PIL import Image
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            pass

        captcha = input("输入验证码\n>")
        #captcha=self.yundama()
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = response.meta.get("post_data", {})
        post_data['captcha'] = captcha
        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.headers,
            callback=self.check_login
        )]

    def check_login(self, response):
        # 验证服务器的返回数据判断是否成功
        text_json = json.loads(response.text)
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)