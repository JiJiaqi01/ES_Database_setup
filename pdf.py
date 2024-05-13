import aiohttp
import PyPDF2
from PyPDF2 import PdfReader
import asyncio
from io import BytesIO

async def pdf2text(url):
    # # Send a HTTP request to the URL of the PDF file
    #response = requests.get(url)
    # # Create a BytesIO object from the content
    #content = BytesIO(response.content)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.read()
            content = BytesIO(content)
    contents = []
    pdf_reader = PdfReader(content)
    num_pages = len(pdf_reader.pages)
    for page in range(num_pages):
        if page > 50:
            break
        pdf_page = pdf_reader.pages[page]
        contents.append(pdf_page.extract_text())
    return contents

async def main(url):
    res=await pdf2text(url)
    return res
