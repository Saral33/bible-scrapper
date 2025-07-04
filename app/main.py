from typing import Dict
from fastapi import FastAPI, Query
from playwright.async_api import async_playwright
from controllers.scrape_controller import scrape_website_controller

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/scrape")
async def scrape_website(book:str):
    return await scrape_website_controller(book)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)