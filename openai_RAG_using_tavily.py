from langchain_openai import ChatOpenAI, OpenAIEmbeddings,OpenAI
from os import environ, getenv, path
#from openai import OpenAI as OA
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from datetime import datetime

#LLM using tavily
from langchain_community.tools.tavily_search import TavilySearchResults, TavilyAnswer
from tavily import TavilyClient


'''
question="what are biofuels?"
res=tavily.search(question)
'''

class Open_AI:
    base_url = getenv("OPENAI_BASE_URL", "https://api.chatanywhere.com.cn/v1")
    api_key = getenv("OPENAI_API_KEY", "sk-xxx")
    model = getenv("OPENAI_MODEL", "gpt-3.5-turbo-0125")
    embedding_model = getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")



#create a template for the chatbot
template = """You can only answer the question using information from the search results provided.
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


#this function is for generating answer using RAG. input is the user's question
def openai_rag(question):
    #use tavily as source
    #find the api-key
    tavily_api_key=getenv("TAVILY_API_KEY",'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')

    tavily = TavilyClient(api_key=tavily_api_key)

    #以下代码限制域名
    '''
    #set search domain
    domains=["www.eia.gov","ww2.arb.ca.gov","www.iata.org","biofuels-news.com","www.spglobal.com","commission.europa.eu"]

    #first use tavily to surf answer
    #there are total six domains for search, each pick the highest two scores
    index=0

    #generate context
    context="<context>"
    #count for counting id
    count=1
    #add reference
    reference= "### Reference"+"\n"
    #add url list
    url_list=""

    for i in domains:
        #select each index as result
        res=tavily.search(question,include_domains=[domains[index]])
        index=index+1

        #res is a dictionary, get the results
        results=res['results']
        #we want the first two item in results dict
        #count the number to determine the break
        break_number=1

        #use for loop to get every element in the results dict
        for item in results:
            content=item['content']
            line="\n"+f"""<doc id={count}> """+content+"</doc>"
            context=context+line
            reference_line="\n"+f"""- [[{count}] """+item['title']+f"""]({item['url']})"""
            reference=reference+reference_line
            url_line=f"""[\[{count}\]]: {item['url']}"""+"\n"
            url_list=url_list+url_line
            count=count+1
            #each time we finished the context, test if we already run twice
            if break_number==2:
                break
            break_number=break_number+1

    '''
    #generate context
    context="<context>"
    #count for counting id
    count=1
    #add reference
    reference= "### Reference"+"\n"
    #add url list
    url_list=""

    #first use tavily to surf answer
    print(f'question: {question}')
    res=tavily.search(
        question,
        include_domains=['www.eia.gov'],
        include_answer=True,
        # topic = "news",
        # days = 14
    ) or {}
    print(f'answer: {res["answer"]}')
    #res is a dictionary, get the results
    results=res['results']

    #use for loop to get every element in the results dict
    for item in results:
        content=item['content']
        line="\n"+f"""<doc id={count}> """+content+"</doc>"
        context=context+line
        reference_line="\n"+f"""- [[{count}] """+item['title']+f"""]({item['url']})"""
        reference=reference+reference_line
        url_line=f"""[\[{count}\]]: {item['url']}"""+"\n"
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
            "question": question,
        }
    )


    ans=answer['text']

    final_answer=ans+"\n"+"\n"+"\n"+reference+"\n"+"\n"+"\n"+url_list
    return final_answer
