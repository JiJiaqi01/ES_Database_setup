import requests
from bs4 import BeautifulSoup
import re
from time import sleep
from urllib.robotparser import RobotFileParser
from collections import deque
from langchain_openai import OpenAIEmbeddings
from elasticsearch import Elasticsearch
from langchain_elasticsearch import ElasticsearchStore
from langchain_core.documents.base import Document
#use log to find errors while running
from logger import logger

headers = {
    "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

#build constants
OPENAI_BASE_URL="https://api.chatanywhere.com.cn/v1"
OPENAI_API_KEY="sk-AUnJk0FMih4MJp32GAyNzEQRi5KtVeiZlvRU6tROmaOAFvD9"
OPENAI_MODEL="gpt-3.5-turbo-0125"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"


#create openai_embedding
embeddings= OpenAIEmbeddings(openai_api_base=OPENAI_BASE_URL,
                             openai_api_key=OPENAI_API_KEY,
                             model=OPENAI_EMBEDDING_MODEL)

#es=elasticsearch.Elasticsearch(hosts=["http://elastic:aidd123A@172.29.0.15:9200"])
es=Elasticsearch(hosts=["http://172.29.0.10:9200"])
#run this on virtual (域名和http格式不一致)
vectorstore = ElasticsearchStore(
    embedding=embeddings,
    #index_name只有一个,数据库存的啥这里填啥
    index_name="bio_database",
    es_url="http://172.29.0.10:9200",
    #es_user="elastic",
    #es_password="aidd123A",
    es_connection=es,
)
#test if the url scraped from eia already stored or not
def document_exists(url, es=es, index="bio_database"):
    query = {
        "query": {
            "term": {
                "metadata.url": url
            }
        }
    }
    response = es.search(index=index, body=query)
    return response['hits']['total']['value'] > 0
  
url="https://www.eia.gov/petroleum/"
print(document_exists(url))
