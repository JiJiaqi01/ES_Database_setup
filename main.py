from openai_RAG_using_tavily import openai_rag,prompt
from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI, Request

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None

@app.get("/rag/")
def get_answer(question: str):
    res=openai_rag(question)
    return res

@app.post("/search_futures_news")
async def search_futures_news(request: Request):
    data = await request.json()
    question = data.get("question")
    res=openai_rag(question)
    return { "response": res, "status": "success" }


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(
    app = "main:app",
    host = "0.0.0.0",
    port = 8000,
  )
