# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import datetime
import scrapy
import re
import redis
from scrapy.loader.processors import MapCompose,TakeFirst,Join
from scrapy.loader import ItemLoader
from ArticleSpider.utils.common import extract_num
from ArticleSpider.settings import SQL_DATE_FORMAT,SQL_DATETIME_FORMAT
from w3lib.html import remove_tags
from ArticleSpider.models.es_types import ArticleType
from ArticleSpider.models.es_types_zhihuquestion import ArticleType_question
from ArticleSpider.models.test import ArticleType_question1
from ArticleSpider.models.es_types_zhihuanswer import ArticleType_answer
from ArticleSpider.models.es_types_lagou import ArticleType_lagou

from elasticsearch_dsl.connections import connections
es=connections.create_connection(ArticleType._doc_type.using)

redis_cli=redis.StrictRedis()

class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def date_convert(value):
    try:
        create_time=datetime.datetime.strptime(value,"%Y/%m/%d").date()
    except Exception as e:
        create_time=datetime.datetime.now().date()

    return create_time


def return_value(value):
    return value


def get_nums(value):
    match_re = re.match(".*?(\d+).*", value)
    if (match_re):
        nums = int(match_re.group(1))
    else:
        nums = 0

    return nums


def remove_comment_tags(value):
    #去掉评论
    if "评论" in value:
        return ""
    else:
        return value

def gen_suggests(index,info_tuple):
    #根据字符串生成字符串搜索建议数组
    used_word=set()
    suggests=[]
    for text,weight in info_tuple:
        if text:
            #调用es的analysis接口分析
            words=es.indices.analyze(index=index,analyzer="ik_max_word",params={'filter':["lowercase"]},body=text)
            anylyzed_words=set([r["token"] for r in words["tokens"] if len(r["token"])>1])
            new_words=anylyzed_words-used_word
            used_word.update(anylyzed_words)
        else:
            new_words=set()
        if new_words:
            suggests.append({"input":list(new_words),"weight":weight})
    return suggests

class ArticleItemLoader(ItemLoader):
    #自定义itemload
    default_output_processor = TakeFirst()


class JobBoleArticleItem(scrapy.Item):
    title=scrapy.Field()
    create_time=scrapy.Field(
        input_processor=MapCompose(date_convert)
    )
    url=scrapy.Field()#url
    url_object_id=scrapy.Field()
    front_image_url=scrapy.Field(
        out_processor=MapCompose(return_value)
    )
    front_path_url = scrapy.Field()
    praise_num = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    comment_num = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_num = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    tags=scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(",")
    )#标签
    content=scrapy.Field()#内容

    def get_insert_sql(self):
        insert_sql = """
                           insert into article(url_object_id,title,url,create_time,fav_nums，
                           front_image_url,front_image_path,praise_nums,comment_nums,tags,content)
                           VALUES (%s,%s,%s,%s,%s，%s,%s,%s,%s,%s,%s)
                           ON DUPLICATE KEY UPDATE content=VALUES (fav_nums)   
                       """
        front_image_url=""
        if self["front_image_url"]:
            front_image_url=self["front_image_url"][0]
        params=(self["url_object_id"], self["title"], self["url"], self["create_time"],
                self["fav_num"],front_image_url,self["front_path_url"],
                self["praise_num"],self["comment_num"],self["tags"],self["content"])
        return insert_sql,params

    def save_to_es(self):
        # 将item转换为es的数据
        article = ArticleType()
        article.title = self['title']
        article.create_time = self['create_time']
        article.content = remove_tags(self['content'])
        article.front_image_url = self['front_image_url']
        if "front_image_path" in self:
            article.front_image_path = self['front_image_path']
        article.praise_num = self['praise_num']
        article.fav_num = self['fav_num']
        article.comment_num = self['comment_num']
        article.url = self['url']
        article.tags = self['tags']
        article.meta.id = self['url_object_id']
        article.suggest=gen_suggests(ArticleType._doc_type.index,((article.title,10),(article.tags,7)))
        article.save()
        redis_cli.incr("jobbole_count")
        return

class ZhihuQuestionItem(scrapy.Item):
    #知乎的问题ITEM
    zhihu_id=scrapy.Field()
    topics=scrapy.Field()
    url=scrapy.Field()
    title=scrapy.Field()
    content=scrapy.Field(
        input_processor=MapCompose(remove_tags),
    )
    answer_num=scrapy.Field()
    comments_num=scrapy.Field()
    watch_user_num=scrapy.Field()
    click_num=scrapy.Field()
    crawl_time=scrapy.Field()

    def get_insert_sql(self):
        #插入知乎question表的字段
        insert_sql="""
        insert into zhihu_question(zhihu_id,topics,url,title,content,answer_num,
        comments_num,watch_user_num,click_num,crawl_time)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE content=VALUES (content),answer_num=VALUES (answer_num),
        comments_num=VALUES (comments_num),watch_user_num=VALUES (watch_user_num),
        click_num=VALUES (click_num)
        """
        zhihu_id=self["zhihu_id"][0]
        topics=",".join(self["topics"])
        url=self["url"][0]
        title="".join(self["title"])
        content="".join(self["content"])
        answer_num=extract_num("".join(self["answer_num"]))
        comments_num = extract_num("".join(self["comments_num"]))

        # if len(self["watch_user_num"])==2:
        #     watch_user_num=int(self["watch_user_num"][0])
        #     click_num=int(self["watch_user_num"][1])
        # else:
        #     watch_user_num=int(self["watch_user_num"][0])
        #     click_num=0
        crawl_time=datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)
        params=(zhihu_id,topics,url,title,content,answer_num,comments_num,crawl_time)
        return insert_sql,params

    def save_to_es(self):
        # 将item转换为es的数据
        insert_sql,params=ZhihuQuestionItem.get_insert_sql(self)

        article = ArticleType_question()
        article.crawl_time = params[7]
        article.topics = params[1]
        article.url = params[2]
        article.title = params[3]
        article.content = params[4]
        article.answer_num = params[5]
        article.comments_num = params[6]
        # article.watch_user_num = params[7]
        # article.click_num=params[8]
        article.meta.id= params[0]
        article.suggest = gen_suggests(ArticleType_question._doc_type.index, ((article.content, 10),(article.title,7)))
        article.save()
        redis_cli.incr("zhihu_q_count")
        return

class ZhihuAnswerItem(scrapy.Item):
    #知乎的问题回答item
    zhihu_id=scrapy.Field()
    url=scrapy.Field()
    question_id=scrapy.Field()
    author_id=scrapy.Field()
    content=scrapy.Field()
    praise_num=scrapy.Field()
    comments_num=scrapy.Field()
    create_time=scrapy.Field()
    update_time=scrapy.Field()
    crawl_time=scrapy.Field()
    def get_insert_sql(self):
        #插入知乎answer表的字段
        #会遇到主键冲突的问题，所以必须要：没有的话，插入；有的话更新
        insert_sql="""
        insert into zhihu_answer(zhihu_id,url,question_id,author_id,content,praise_num,comments_num,
        create_time,update_time,crawl_time)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE content=VALUES(content),comments_num=VALUES (comments_num),praise_num=VALUES (praise_num),
        update_time=VALUES (update_time)
        """
        create_time=datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time=datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        params=(
            self["zhihu_id"],self["url"],self["question_id"],
            self["author_id"],self["content"],self["praise_num"],
            self["comments_num"],create_time,update_time,
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )
        return insert_sql,params

    def save_to_es(self):
        # 将item转换为es的数据
        insert_sql,params=ZhihuAnswerItem.get_insert_sql(self)

        article = ArticleType_answer()
        article.url = params[1]
        article.question_id = params[2]
        article.author_id = params[3]
        article.content = params[4]
        article.praise_num = params[5]
        article.comments_num = params[6]
        article.create_time = params[7]
        article.update_time=params[8]
        article.crawl_time=params[9]
        article.meta.id= params[0]
        article.suggest = gen_suggests(ArticleType_answer._doc_type.index,((article.content,10),(article.praise_num,7)))
        article.save()
        redis_cli.incr("zhihu_a_count")
        return


def remove_splash(value):
    #去除斜线
    return value.replace("/","")


def handle_jobaddr(value):
    addr_list=value.split("\n")
    addr_list=[item.strip() for item in addr_list if item.strip()!="查看地图"]
    return "".join(addr_list)


class LagouJobItemLoader(ItemLoader):
    #自定义itemload
    default_output_processor = TakeFirst()


class LagouJobItem(scrapy.Item):
    #拉钩网职位信息
    title=scrapy.Field()
    url=scrapy.Field()
    url_object_id=scrapy.Field()
    salary=scrapy.Field()
    job_city=scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    work_years=scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    degree_need=scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    job_type=scrapy.Field()
    publish_time=scrapy.Field()
    tags=scrapy.Field(
        input_processor=Join(","),
    )
    job_advantage=scrapy.Field()
    job_desc=scrapy.Field()
    job_addr=scrapy.Field(
        input_processor=MapCompose(remove_tags,handle_jobaddr),
    )
    company_url=scrapy.Field()
    company_name=scrapy.Field()
    crawl_time=scrapy.Field()
    def get_insert_sql(self):
        insert_sql = """
            insert into lagou(title, url,url_object_id, salary, job_city, work_years, degree_need,
            job_type, publish_time, job_advantage, job_desc, job_addr, company_name,company_url,  
            tags,crawl_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE job_desc=VALUES(job_desc),salary=VALUES(salary)
        """
        params = (
            self["title"], self["url"], self["url_object_id"], self["salary"], self["job_city"], self["work_years"], self["degree_need"],
            self["job_type"], self["publish_time"], self["job_advantage"], self["job_desc"], self["job_addr"],
            self["company_name"], self["company_url"],
            self["tags"],self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
            )
        return insert_sql,params

    def save_to_es(self):
        # 将item转换为es的数据
        insert_sql,params=LagouJobItem.get_insert_sql(self)

        article = ArticleType_lagou()

        article.url = params[1]
        article.title = params[0]
        article.salary = params[3]
        article.job_city = params[4]
        article.work_years = params[5]
        article.degree_need = params[6]
        article.job_type = params[7]
        article.publish_time=params[8]
        article.tags=params[14]
        article.job_advantage = params[9]
        article.job_desc = params[10]
        article.job_addr = params[11]
        article.company_url = params[13]
        article.company_name = params[12]
        article.crawl_time = params[15]
        article.meta.id= params[2]
        article.suggest = gen_suggests(ArticleType_lagou._doc_type.index, ((article.title, 10), (article.tags, 7)))
        article.save()
        redis_cli.incr("lagou_count")
        return