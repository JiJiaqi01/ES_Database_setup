from langchain_openai import ChatOpenAI, OpenAIEmbeddings,OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from datetime import datetime,timedelta,timezone
from elasticsearch import Elasticsearch
from langchain_elasticsearch import ElasticsearchStore


#running local using docker

OPENAI_BASE_URL="https://api.chatanywhere.com.cn/v1"
OPENAI_API_KEY="sk-AUnJk0FMih4MJp32GAyNzEQRi5KtVeiZlvRU6tROmaOAFvD9"
OPENAI_MODEL="gpt-3.5-turbo-0125"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

#create openai_embedding
embeddings= OpenAIEmbeddings(openai_api_base=OPENAI_BASE_URL,
                             openai_api_key=OPENAI_API_KEY,
                             model=OPENAI_EMBEDDING_MODEL)

es=Elasticsearch(hosts=["http://172.29.0.15:9200"])

#run this on virtual (域名和http格式不一致)
vectorstore = ElasticsearchStore(
    embedding=embeddings,
    #index_name只有一个,数据库存的啥这里填啥
    index_name="bio_database",
    es_url="http://172.29.0.15:9200",
    es_user="elastic",
    es_password="aidd123A",
    es_connection=es,
)


#create a template for the chatbot
template = """You work as a biodiesel trader and researcher, specializing in the commodity futures market. You can provide the following services by following the instructions below:
1. Get real-time biodiesel related news and data through the web interface.
2. Predict the price trend of commodities in the future based on historical data.
3. Identify and explain the main factors affecting commodity prices, including but not limited to macroeconomic indicators, geopolitical events, changes in supply and demand, etc.
4. Provide operational suggestions based on data analysis, such as buying, holding or selling.
Make sure your analysis includes data sources, analysis methods, and reasoning processes.

You can only answer the question using information from the search results provided.
Use an unbiased and journalistic tone. Combine search results together into a coherent answer.
Do not repeat text. Cite search results using [\[number\]] notation.
Only cite the most relevant results that answer the question accurately.
Place these citations at the end of the sentence or paragraph that reference them - do not put them all at the end.
If different results refer to different entities within the same name, write separate answers for each entity.
If you want to cite multiple results for the same sentence, format it as [\[number1\]] [\[number2\]], split with space.
However, you should NEVER do this with the same number - if you want to cite number1 multiple times for a sentence, only do [\[number1\]] not [\[number1\]] [\[number1\]]

You should use bullet points in your answer for readability. Put citations where they apply rather than putting them all at the end.

Anything between the following context html blocks is retrieved from a knowledge bank, not part of the conversation with the user.

{context}

question: {question}

REMEMBER: If there is no relevant information within the context, don't try to make up an answer.
Anything between the preceding 'context' html blocks is retrieved from a knowledge bank, not part of the conversation with the user.
The current date is {current_date} in format year/month/day.

"""


#generate the prompt
prompt = PromptTemplate.from_template(template)

#make a filter to get more precise information


def get_filter(question):
    #现在template只有三个keyword,后续可加入，但是由于是metadata进行filter,入库的时候估计还得添加额外内容
    template = """You are here to help me to interpret a question and response with several key points:
    1. What is the key information this question is asking for, response with format  "keyword: " following with a term not exceed five words
    2. How many returns does this question ask for,response with format  "Limit: " following with a number
    3. Is there any date information required in the question, such as "latest", "year 2022" if there is, response with the format "Time range: " and add the time condition
    If the question ask for latest, recent, or any other words similar to this meaning, generate a date range from 30 days ago to now, the time now is {current_utc_time}
    If anything else specific, calculate that date range using numbers of days from now.
    In any case, your answer should follow the time format: '%Y-%m-%dT%H:%M:%SZ' to '%Y-%m-%dT%H:%M:%SZ' 
    
    Remember:
    Your answer should be in the following format, and I will notate what you should response using (your answer). Anything else should keep as the format

    The format is:
    Keyword: (your answer)
    Limit:  (your answer)
    Time range: (your answer)

    question: {question}


    """
    #generate the prompt
    prompt = PromptTemplate.from_template(template)
    #use Open AI as our model
    #此处直接使用openai中转点的api,如果后续有官方的api可调整变量
    llm=ChatOpenAI(base_url='https://api.chatanywhere.com.cn/v1',api_key='sk-AUnJk0FMih4MJp32GAyNzEQRi5KtVeiZlvRU6tROmaOAFvD9', model='gpt-3.5-turbo-0125')


    #create a llm_chain
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    current_utc=datetime.now(timezone.utc)
    #use the chain to query a answer
    answer=llm_chain.invoke(
        {
            "question": question,
            "current_utc_time": current_utc
        }
    )
    ans=answer['text']
    return ans




#this function is for generating answer using RAG. input is the user's question
def openai_rag_es(question):
    #use es database
    #generate context
    context="<context>"
    #count for counting id
    count=1
    #add reference
    reference= "### Reference"+"\n"
    #add url list
    url_list=""

    #get_filter to refine the search
    filters=get_filter(question)
    #filters in format "keyword: xxxxxxxx\nlimit: xxxxxxx\n timerange:  xxxxxxx\n"
    #split by \n
    key_list = filters.split("\n")
    time = key_list[2]
    #test if there is a condition
    entry=time[12:]
    if entry=="None":
        #no range needed
        need_range=False
    else:
        time_utc=time[12:].split("to")
        index=0
        for element in time_utc:
            time_utc[index]=element.lstrip()
            index=index+1
            #now time_utc contains two element in utc format representing time range
        start_date=time_utc[0]
        end_date=time_utc[1]
        need_range=True
        #generate filter
    if need_range:
        filter=[
            {
              "range": {
                  "metadata.date": {
                      "gte": start_date,
                      "lte": end_date
                      }
                  }
              ]
    #use es to search using similarity(choose from mmr and similarity)
    
    #不确定search和similarity_search_by_vector有没有什么区别, similarity_search_by_vector(embeddings)
    res=vectorstore.similarity_search(question,filter=filter)
    #now we have our response, we want the content, and the url, stored in
    #res should be a list of documents

    #use for loop to get every element in the results dict
    for item in res:
        #the indices that store text information, assuming text
        #the only problem is the text may be the entire page,
        #我不知道数据库是怎么安放文本内容的，不知道是不是全部内容还是部分
        content=item.page_content
        line="\n"+f"""<doc id={count}> """+content+"</doc>"
        context=context+line

        #assume the indices store url is url
        url_source=item.metadata
        url=url_source['url']
        try:
            title=url_source['title']
        except:
            title=content[0:50]+"..."
        #
        reference_line="\n"+f"""- [[{count}] """+title+f"""]({url})"""
        reference=reference+reference_line

        #same way to get url
        url_line=f"""[\[{count}\]]: {url}"""+"\n"
        url_list=url_list+url_line
        count=count+1
  
    #results is a list with several dictionary in each index
    current_time=datetime.now()
    cdate=str(current_time.year)+"/"+str(current_time.month)+"/"+str(current_time.day)

    #use Open AI as our model
    #此处直接使用openai中转点的api,如果后续有官方的api可调整变量
    llm=ChatOpenAI(base_url='https://api.chatanywhere.com.cn/v1',api_key='sk-AUnJk0FMih4MJp32GAyNzEQRi5KtVeiZlvRU6tROmaOAFvD9', model='gpt-3.5-turbo-0125')


    #create a llm_chain
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    #use the chain to query a answer
    answer=llm_chain.invoke(
        {
            "current_date":cdate,
            "context": context,
            "question": question
        }
    )


    ans=answer['text']

    final_answer=ans+"\n"+"\n"+"\n"+reference+"\n"+"\n"+"\n"+url_list
    return final_answer
