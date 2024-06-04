from playwright.sync_api import sync_playwright
import re
import json
from time import sleep
from bs4 import BeautifulSoup
import requests
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
    index_name="bio_database_new",
    es_url="http://172.29.0.10:9200",
    #es_user="elastic",
    #es_password="aidd123A",
    es_connection=es,
)



xmls=['https://www.spglobal.com/commodityinsights/en/ci/sitemap.xml',
      'https://www.spglobal.com/commodityinsights/plattscontent/en/site-maps/main-sitemap.xml',
      'https://www.spglobal.com/commodityinsights/en/sitemap/podcasts-sitemap',
      'https://www.spglobal.com/commodityinsights/en/sitemap/price-assessments-sitemap',
      'https://www.spglobal.com/commodityinsights/plattscontent/en/site-maps/top250-gea-gma-sitemap.xml',
      'https://www.spglobal.com/en/corp-news-sitemap.xml',
      'https://www.spglobal.com/engineering/en/sitemap.xml',
      'https://www.spglobal.com/en/enterprise/sitemap.xml',
      'https://www.spglobal.com/esg/csa/sitemap.xml',
      'https://www.spglobal.com/esg/s1/sitemap.xml',
      'https://www.spglobal.com/marketintelligence/en/sitemap.xml',
      'https://www.spglobal.com/marketintelligence/en/mi-news-sitemap.xml',
      'https://www.spglobal.com/marketintelligence/en/mi/sitemap.xml',
      'https://www.spglobal.com/mobility/en/sitemap.xml',
      'https://www.spglobal.com/marketintelligence/en/sitemaps/trending-2020-1.xml'
      ]

def store_es(url):
    #url is each element in the list and fileName is how we save them in file.
    with sync_playwright() as driver:
        browser=driver.chromium.launch(headless=False)
        context=browser.new_context()
        page=context.new_page()
        #set a higher timeout default so some websites can be able to generate
        page.set_default_timeout(100000)
        page.goto(url)
        #get the html_text first
        html_text=page.content()
        browser.close()

    #用soup和ele筛选
    soup=BeautifulSoup(html_text,'html.parser')
    ele=soup.select('p')
    #用full_text来存储页面文本信息
    full_text=""
    #遍历response set去除<xxx> 保留文本
    for element in ele:
        full_text=full_text+element.get_text(separator="\n",strip=True)
    #full text stores text, html text stores raw
    title_ele=soup.select('title')
    title=title_ele[0].get_text(separator="\n",strip=True)
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


def get_urls(xml):
    with sync_playwright() as driver:
        browser=driver.chromium.launch(headless=False)
        context=browser.new_context()
        page=context.new_page()
        #set a higher timeout default so some websites can be able to generate
        page.set_default_timeout(100000)
        page.goto(xml)
        #选取loc to get full urls
        tag=page.locator('loc')
        sites=tag.all_text_contents()
        browser.close()
        #sites has all urls in xml
    return sites


for xml in xmls:
    try:
        urls=get_urls(xml)
        #now urls=sites stores all urls
        for url in urls:
            try:
                store_es(url)
            except Exception as e:
                print(e)
                logger.error(e)
    except Exception as e:
        print(e)
        logger.error(e)
