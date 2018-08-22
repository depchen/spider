# encoding: utf-8
'''
@author: depchen

@file: es_types.py

@time: 2017/12/13 15:07

@desc:
'''

from elasticsearch_dsl import DocType, Date, datetime,Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Keyword, Text,Integer
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer
from elasticsearch_dsl.connections import connections

connections.create_connection(hosts=["localhost"])
class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return []
ik_analyzer=CustomAnalyzer("ik_max_word",filter=["lowercase"])
class ArticleType_question1(DocType):
    # 知乎的问题ITEM
    suggest = Completion(analyzer=ik_analyzer)
    zhihu_id = Keyword()
    topics = Text(analyzer="ik_max_word")
    url = Keyword()
    title = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")
    answer_num = Integer()
    comments_num = Integer()
    watch_user_num = Integer()
    click_num=Integer()
    crawl_time = Text()

    class Meta:
        index="zhihuquestion1"
        doc_type="question1"

if __name__=="__main__":
    ArticleType_question1.init()