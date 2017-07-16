# -*- coding: utf-8 -*-
__author__ = 'emma'

from django.db import models
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Keyword, Text
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer
connections.create_connection(hosts=["localhost"])

#由于原码的问题，要做一个这样的转换
class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}

ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])

class MjType(DocType):
    # content = scrapy.Field(
    #     input_processor=
    # )
    #添加一个自动补全的字段
    suggest = Completion(analyzer=ik_analyzer)
    url = Keyword()
    title = Text(analyzer="ik_max_word")
    tags = Keyword()
    content = Text(analyzer="ik_max_word")

    class Meta:
        index = "onem3point"
        doc_type = 'mj'


class GDType(DocType):
    suggest = Completion(analyzer=ik_analyzer)
    post_date = Text(analyzer="ik_max_word")
    url = Keyword()
    company = Keyword()
    position = Keyword()
    content = Text(analyzer="ik_max_word")
    answer = Text(analyzer="ik_max_word")

    class Meta:
        index = "glassdoor"
        doc_type = 'gd'



if __name__ == "__main__":
    MjType.init() #根据定义的类直接生成索引信息
    GDType.init()
