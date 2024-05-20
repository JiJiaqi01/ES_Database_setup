from langchain_openai import ChatOpenAI, OpenAIEmbeddings,OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate


template = """You are here to help me to interpret a question and response with several key points:
1. What is the key information this question is asking for, response with format  "keyword: " following with a term not exceed five words
2. How many returns does this question ask for,response with format  "Limit: " following with a number
3. Is there any date information required in the question, such as "latest", "year 2022" if there is, response with the format "Time range: " and add the time condition

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

    #use the chain to query a answer
    answer=llm_chain.invoke(
        {
            "question": question
        }
    )


    ans=answer['text']
    return ans
