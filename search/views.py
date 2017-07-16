import json
import redis
from django.shortcuts import render
from django.views.generic.base import View
from search.models import MjType, GDType
from django.http import HttpResponse
from elasticsearch import Elasticsearch
from datetime import datetime

#method2:initial an es connection
client = Elasticsearch(hosts=["127.0.0.1"])

redis_cli = redis.StrictRedis()

class IndexView(View):
    #首页
    def get(self, request):
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)

        return render(request, "index.html", {"topn_search":topn_search})

# Create your views here.
#def Suggest(request):
#django推荐用class来实现
class SearchSuggest(View):
    def get(self, request):
        #通过看html源码来确定key_words位置
        key_words = request.GET.get('s','')
        re_datas = []
        if key_words:
            #method1: use elasticsearch_dsl related method(MjType inherit from elasticsearch_dsl)
            s = MjType.search()
            #'my-suggest'自定义的名称
            s = s.suggest('my_suggest', key_words, completion={
                "field":"suggest", "fuzzy":{
                    "fuzziness":2
                },
                "size":10
            })
            suggestions = s.execute_suggest()
            for match in suggestions.my_suggest[0].options:
                #pass
                source = match._source
                re_datas.append("".join(source["title"]))
        return HttpResponse(json.dumps(re_datas), content_type="application/json")

class SearchView(View):
    def get(self, request):
        key_words = request.GET.get("q","")
        #获取页面中tab页的选择，可根据该对应值实现该tab页的逻辑
        s_type = request.GET.get("s_type","article")

        redis_cli.zincrby("search_keywords_set", key_words)
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)

        page = request.GET.get("p", "1")

        try:
            page = int(page)
        except:
            page = 1
        print(page)
        #redis_cli此时运行的与在redis中运行得到的结果是相同的
        onem3point_count = redis_cli.get("onem3point_count")
        glassdoor_count = redis_cli.get("glassdoor_count")
        start_time = datetime.now()
        #another way to search in es
        #method2:communication with es
        response = client.search(
            index=["onem3point", "glassdoor"],
            #index="onem3point",
            # 自动高亮
            body={
                "query":{
                    "multi_match":{
                        "query":key_words,
                        "fields":["tags", "title", "content", "company", "answer"]
                    }
                },
                #每页有10个
                "from":(page-1)*10,
                "size":10,
                "highlight":{
                    "pre_tags": ["<span class='keyword'>"],
                    "post_tags": ["</span>"],
                    "fields":{
                        "title":{},
                        "content":{},
                        "company":{},
                        "answer":{}
                    }
                }
            }
        )


        end_time = datetime.now()
        last_seconds = (end_time-start_time).total_seconds()
        total_nums = response["hits"]["total"]
        if (page%10) > 0:
            page_nums = int(total_nums/10) +1
        else:
            page_nums = int(total_nums/10)
        hit_list = []
        for hit in response["hits"]["hits"]:
            hit_dict = {}
            hit_dict["index"] = hit["_index"]
            hit_dict["post_date"] = "".join(hit["_source"]["post_date"])
            if "onem3point" in hit["_index"]:
                if "title" in hit["highlight"]:
                    hit_dict["title"] = "".join(hit["highlight"]["title"])
                else:
                    hit_dict["title"] = "".join(hit["_source"]["title"])
            else:
                hit_dict["title"] = hit["_source"]["company"]+"=>"+hit["_source"]["position"]

            if "content" in hit["highlight"]:
                hit_dict["content"] = "".join(hit["highlight"]["content"])[:500]#限制显示500个，避免太长
            else:
                hit_dict["content"] = "".join(hit["_source"]["content"])[:500]


            hit_dict["url"] = "".join(hit["_source"]["url"])
            hit_dict["score"] = hit["_score"]

            hit_list.append(hit_dict)

        return render(request, "result.html", {"page":page,
                                               "all_hits":hit_list,
                                               "key_words":key_words,
                                               "total_nums":total_nums,
                                               "page_nums":page_nums,
                                               "last_seconds":last_seconds,
                                               "onem3point_count":onem3point_count,
                                               "glassdoor_count":glassdoor_count,
                                               "topn_search":topn_search})
