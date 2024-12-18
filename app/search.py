from flask import current_app
#搜索功能
'''
创建于Elasticsearche的连接
>>> from elasticsearch import Elasticsearch
>>> es = Elasticsearch('http://localhost:9200')
将Elasticsearch数据写入索引
es.index(index='my_index', id=1, document={'text': 'this is a test'})
我们可以发出搜索文档
es.search(index='my_index', query={'match': {'text': 'this test'}})
可以删除索引
es.indices.delete(index='my_index')

编写Elasticsearch索引交互的所有代码，Elasticsearch所有代码都在保存在此模块中.

'''
def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, document=payload)

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)

def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        query={'multi_match': {'query': query, 'fields': ['*']}},
        from_=(page - 1) * per_page,
        size=per_page)
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']