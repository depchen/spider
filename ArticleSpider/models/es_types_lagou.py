# encoding: utf-8
'''
@author: depchen

@file: es_types.py

@time: 2017/12/13 15:07

@desc:
'''
from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Keyword, Text,Integer
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

from elasticsearch_dsl.connections import connections
connections.create_connection(hosts=["localhost"])

class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return []

ik_analyzer=CustomAnalyzer("ik_max_word",filter=["lowercase"])

class ArticleType_lagou(DocType):
    # 拉钩ITEM
    suggest=Completion(analyzer=ik_analyzer)
    title = Text(analyzer="ik_max_word")
    url = Keyword()
    url_object_id = Keyword()
    salary = Keyword()
    job_city = Text(analyzer="ik_max_word")
    work_years = Keyword()
    degree_need = Text(analyzer="ik_max_word")
    job_type = Text(analyzer="ik_max_word")
    publish_time = Keyword()
    tags = Text(analyzer="ik_max_word")
    job_advantage = Text(analyzer="ik_max_word")
    job_desc = Text(analyzer="ik_max_word")
    job_addr = Keyword()
    company_url = Keyword()
    company_name = Keyword()
    crawl_time = Date()

    class Meta:
        index="lagou"
        doc_type="job"

if __name__=="__main__":
    ArticleType_lagou.init()