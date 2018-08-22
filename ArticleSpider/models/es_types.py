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

class ArticleType(DocType):
    #伯乐在线文章类型
    suggest=Completion(analyzer=ik_analyzer)
    title = Text(analyzer="ik_max_word")  # 标题
    create_time = Date()# 创建时间
    url = Keyword()  # url
    url_object_id =Keyword()  # url md5
    front_image_url = Keyword() # 列表图片url
    front_path_url = Keyword()  # 本地图片url
    praise_num = Integer()  # 点赞数
    comment_num = Integer() # 评论数
    fav_num = Integer()  # 收藏数
    tags = Text(analyzer="ik_max_word")  # 标签
    content = Text(analyzer="ik_max_word")  # 内容

    class Meta:
        index="jobbole"
        doc_type="article"

if __name__=="__main__":
    ArticleType.init()