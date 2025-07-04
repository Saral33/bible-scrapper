from app.constants.book_constanst import name_mapper
from controllers.scrape_controller import scrape_website_controller
import asyncio

async def main():
    for book in name_mapper:
        await scrape_website_controller(book)

if __name__ == "__main__":
    asyncio.run(main())