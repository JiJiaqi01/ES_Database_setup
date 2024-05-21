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

# User-Agent header for the requests
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
                "metadata.url.keyword": url
            }
        }
    }
    response = es.search(index=index, body=query)
    return response['hits']['total']['value'] > 0


#建立函数方便爬取不同网页
def store_es(url,headers=headers):
    #url 为对应网页
    #返回页面源代码
    response=requests.get(url=url,headers=headers)
    html_text=response.text
    #用soup筛选<p>获取文本
    soup=BeautifulSoup(html_text,'html.parser')
    ele=soup.select('p')
    #用full_text来存储页面文本信息
    full_text=""
    #遍历response set去除<xxx> 保留文本
    #网页爬取ele[27:-2], 之前的都是一样的menu curel oil....etc. 去除重复部分方便搜索
    for element in ele[27:-2]:
        full_text=full_text+element.get_text(separator="\n",strip=True)
    #获取标题
    try:
        ele_title=soup.select('title')
        element=ele_title[0]
        title=element.get_text(separator="\n",strip=True)
    except:
        title=full_text[:40]+"..."
    #将该得到的数据text,html,url导入es,并用openai embedding向量化
    vectorstore.add_documents(documents=[Document(page_content=full_text,
                                                  metadata={
                                                      "url":url,
                                                      "html":html_text,
                                                      "title":title,
                                                      }
                                                  )
                                         ]
                              )


# Initialize the RobotFileParser
rp = RobotFileParser()

# Function to check if fetching a URL is allowed
def can_fetch(url):
    rp.set_url(requests.compat.urljoin(url, '/robots.txt'))
    rp.read()
    return rp.can_fetch(headers['User-Agent'], url)

# Function to extract links from the given URL
def get_links(url, domain):
    if can_fetch(url):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            if response.encoding is None:
                response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                full_link = requests.compat.urljoin(url, link['href'])
                if full_link.startswith(domain):
                    yield full_link
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
    else:
        print(f"Access denied by robots.txt: {url}")

# Function to crawl the web starting from a base URL
def crawl(start_url):
    domain = '{uri.scheme}://{uri.netloc}'.format(uri=requests.utils.urlparse(start_url))
    queue = deque([start_url])
    visited = set()

    while queue:
        url = queue.popleft()
        if url not in visited:
            #这里的url都是没有爬过的
            #把这里的url爬取一下获取文本内容，使用try
            visited.add(url)
            #做判断，此处输出的url都是未入库的，直接用这些url做爬取传输
            if not document_exists(url):
                #print(f"Visiting: {url}")
                #url里面有些是下载链接 （xlsx）和重复网页 （#）不需要重复爬取
                if "#" not in url and not url.endswith((".xls", ".xlsx",".mp3",".csv",".zip")):
                    try:
                        #sleep for a while
                        sleep(2)
                        store_es(url)
                    except Exception as e:
                        print(e.with_traceback())
                        logger.error(e)
                else:
                    print("Invalid url: "+url)
            else:
                print("Repeated url: "+url)
            #now use loop to get the next url
            try:
                for next_url in get_links(url, domain):
                    if next_url not in visited:
                        queue.append(next_url)
            except Exception as e:
                print(e.with_traceback())
                logger.error(e)

# Start the crawler


# Set the domain and start URL
domain = 'https://www.eia.gov'
start_url = domain
# Start crawling from the base URL
crawl(start_url)
