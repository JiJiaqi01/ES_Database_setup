from langchain_openai import ChatOpenAI, OpenAIEmbeddings,OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
import openai
from datetime import datetime,timedelta,timezone

template = """You are here to help me to interpret a question and response with several key points:
1. What is the key information this question is asking for, response with format  "keyword: " following with a term not exceed five words
2. How many returns does this question ask for,response with format  "Limit: " following with a number
3. Is there any date information required in the question, such as "latest", "year 2022" if there is, response with the format "Time range: " and add the time condition
If the question ask for latest, recent, or any other words similar to this meaning, generate a date range from 30 days ago to now, the time now is {current_utc_time}
If anything else specific, calculate that date range using numbers of days from now.
In any case, your answer should follow the time format: '%Y-%m-%dT%H:%M:%SZ'

Remember:
Your answer should be in the following format, the string in the "" is what you must remain unchanged, and I will
notate what you should response using (your answer)

The format is:
"Keyword: " (your answer)
"Limit: " (your answer)
"Time range" (your answer)

question: {question}


"""


#generate the prompt
prompt = PromptTemplate.from_template(template)

def get_filter(question):
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




#get the response date range:
"""
q=""
response=get_filter(q)
result = response.split("\n")
time=result[2]
cc=time[12:-1].split(" to ")
index=0
for element in cc:
     cc[index]=element.lstrip()
     index=index+1
#now cc is in UTC time string format
#change into datetime
time_string=cc[0] # or cc[1]
datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')
#now this can convert




OPENAI_BASE_URL="https://api.chatanywhere.com.cn/v1"
OPENAI_API_KEY="sk-AUnJk0FMih4MJp32GAyNzEQRi5KtVeiZlvRU6tROmaOAFvD9"
OPENAI_MODEL="gpt-3.5-turbo-0125"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
embeddings= OpenAIEmbeddings(openai_api_base=OPENAI_BASE_URL,
                             openai_api_key=OPENAI_API_KEY,
                             model=OPENAI_EMBEDDING_MODEL)


text = "This is a test query."
query_result = embeddings.embed_query(text)
"""
