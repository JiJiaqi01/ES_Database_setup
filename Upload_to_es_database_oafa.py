import requests
from bs4 import BeautifulSoup
import re
import json
from time import sleep
from langchain_openai import OpenAIEmbeddings
import elasticsearch
from langchain_elasticsearch import ElasticsearchStore
from langchain_core.documents.base import Document
#use log to find errors while running
from logger import logger

headers={
    "User_Agent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

OPENAI_BASE_URL="https://api.chatanywhere.com.cn/v1"
OPENAI_API_KEY="sk-AUnJk0FMih4MJp32GAyNzEQRi5KtVeiZlvRU6tROmaOAFvD9"
OPENAI_MODEL="gpt-3.5-turbo-0125"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"


#create openai_embedding
embeddings= OpenAIEmbeddings(openai_api_base=OPENAI_BASE_URL,
                             openai_api_key=OPENAI_API_KEY,
                             model=OPENAI_EMBEDDING_MODEL)

#es=elasticsearch.Elasticsearch(hosts=["http://elastic:aidd123A@172.29.0.15:9200"])
es=elasticsearch.Elasticsearch(hosts=["http://172.29.0.10:9200"])
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
    for element in ele[0:-1]:
        full_text=full_text+element.get_text(separator="\n",strip=True)
    #获取标题
    ele_title=soup.select('title')
    element=ele_title[0]
    title=element.get_text(separator="\n",strip=True)
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
    
#以上函数调用的时候输入网址就可以把网页文本存入es
#下一步，获取网页地址
xml_list=['https://climate.ec.europa.eu/sitemap.xml',
          'https://agriculture.ec.europa.eu/sitemap.xml',
          'https://new-european-bauhaus.europa.eu/sitemap.xml',
          'https://economy-finance.ec.europa.eu/sitemap.xml',
          'https://energy.ec.europa.eu/sitemap.xml',
          'https://environment.ec.europa.eu/sitemap.xml',
          'https://single-market-economy.ec.europa.eu/sitemap.xml',
          'https://research-and-innovation.ec.europa.eu/sitemap.xml',
          'https://commission.europa.eu/sitemap.xml',
          'https://transport.ec.europa.eu/sitemap.xml',
          'https://www.iata.org/sitemap.xml',
          'https://ww2.arb.ca.gov/sitemap.xml?page=1',
          'https://ww2.arb.ca.gov/sitemap.xml?page=2',
          'https://biofuels-news.com/news-sitemap.xml',
          'https://biofuels-news.com/news-sitemap2.xml',
          'https://biofuels-news.com/news-sitemap3.xml',
          'https://biofuels-news.com/news-sitemap4.xml',
          'https://biofuels-news.com/news-sitemap5.xml',
          'https://biofuels-news.com/news-sitemap6.xml',
          'https://biofuels-news.com/news-sitemap7.xml',
          'https://biofuels-news.com/news-sitemap8.xml',
          'https://biofuels-news.com/news-sitemap9.xml'
          ]

sitemap_set=[]
for xml in xml_list:
    response=requests.get(url=xml,headers=headers)
    html_text=response.text
    #Use soup to take all the urls
    soup=BeautifulSoup(html_text,'xml')
    ele=soup.select('loc')
    for element in ele:
        #ele[x]都是str type
        #去除<loc>,<\loc>
        sitemap_set.append(element.get_text(separator="\n",strip=True))

#this step is temporary due to program accidentally interrupted
##stopped at this url /publications/commission-implementing-decision-authorisation-disbursement-first-instalment-non-repayable-support_en
#index 20709
#https://commission.europa.eu/news/commission-launches-survey-collect-additional-feedback-electronic-invoicing-2023-05-24_en connection error 41 times
#index 21183
newset=sitemap_set[21183:]
#建立一个log用于输出程序错误

index_count=-1
#现在网页获取完毕，对每个网页调用store_es
for url in newset:    #sitemap_set:
    #这一步用来确定哪个url出问题了,可通过index寻找
    index_count=index_count+1
    #sleep for a while防止频率太高不让访问了
    sleep(2)
    try:
        store_es(url)
    except Exception as e:
        print(e)
        logger.error(e)

