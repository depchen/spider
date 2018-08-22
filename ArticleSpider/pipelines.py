# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.7html
import codecs
import json
import MySQLdb
import MySQLdb.cursors
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi
from ArticleSpider.models.es_types import ArticleType
from w3lib.html import remove_tags

class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item

class ArticleImagePipeline(ImagesPipeline):
    #获取图片的本地path
    def item_completed(self, results, item, info):
        for ok,value in results:
            image_file_path=value["path"]
        item["front_path_url"]=image_file_path
        return item
        pass
#自定义json文件的导出
class JsonWithEncodingPipeline(object):
    # 调用自定义json 导出json文件
    def __init__(self):
        self.file=codecs.open("article.json","w",encoding="utf-8")
    def process_item(self,item,spider):
        lines=json.dumps(dict(item),ensure_ascii=False)+"\n"
        self.file.write(lines)
        return item
    def spider_closed(self,spider):
        self.file.close()

class JsonExporterPipleline(object):
    #调用scrapy提供json export导出json文件
    def __init__(self):
        self.file=open("articleexport.json",'wb')
        self.exporter=JsonItemExporter(self.file,encoding="utf-8",ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self,spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self,item,spider):
        self.exporter.export_item(item)
        return item

class MysqlPipeline(object):
    #调用自定义的mysql连接
    def __init__(self):
        self.conn=MySQLdb.connect("localhost","root","depchen","article_spider",charset="utf8",use_unicode=True)
        self.cursor=self.conn.cursor()

    def process_item(self,item,spider):
        insert_sql="""
            insert into article(url_object_id,title,url,create_time,fav_nums)
            VALUES (%s,%s,%s,%s,%s)
        """
        self.cursor.execute(insert_sql,(item["url_object_id"],item["title"],item["url"],item["create_time"],item["fav_num"]))
        self.conn.commit()

class MysqlTwistedPipline(object):
    def __init__(self,dbpool):
        self.dbpool=dbpool
    #twisted提供的异步操作
    @classmethod
    def from_settings(cls,settings):
        dbparms=dict(
        host=settings["MYSQL_HOST"],
        db=settings["MYSQL_DBNAME"],
        user=settings["MYSQL_USER"],
        password=settings["MYSQL_PASSWORD"],
        charset='utf8',
        cursorclass=MySQLdb.cursors.DictCursor,
        use_unicode=True,
        )
        dbpool=adbapi.ConnectionPool("MySQLdb",**dbparms)
        return cls(dbpool)

    def process_item(self,item,spider):
        #asynchronous execution
        query=self.dbpool.runInteraction(self.do_insert,item)
        query.addErrback(self.handle_error,item,spider)

    def handle_error(self,failure,item,spider):
        #insertion error handling
        print(failure)

    def do_insert(self,cursor,item):
        #according to different items, perform different sql
        insert_sql,params=item.get_insert_sql()
        cursor.execute(insert_sql,params)


class ElasticsearchPipeline(object):
    #将数据写入到es中
    def process_item(self,item,spider):
        #将item转换为es的数据
        item.save_to_es()
        return item