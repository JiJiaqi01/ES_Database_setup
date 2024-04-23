from openai_RAG_using_tavily import openai_rag,prompt
from fastapi import FastAPI
from typing import Union
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None



@app.get("/rag/")
def get_answer(question: str):
    res=openai_rag(question)
    return res

