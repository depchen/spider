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

class ArticleType_answer(DocType):
    # 知乎的回答ITEM
    suggest = Completion(analyzer=ik_analyzer)
    zhihu_id = Keyword()
    url = Keyword()
    question_id= Keyword()
    author_id= Keyword()
    content = Text(analyzer="ik_max_word")
    praise_num= Integer()
    comments_num = Integer()
    create_time=Date()
    update_time=Date()
    crawl_time=Date()

    class Meta:
        index="zhihuanswer"
        doc_type="answer"

if __name__=="__main__":
    ArticleType_answer.init()