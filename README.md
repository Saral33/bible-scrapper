# chapter-scraper

A FastAPI-based web service for scraping Bible chapter and verse data from bible.com using Playwright, and exporting the results as structured JSON files.

## Features

- **REST API** with FastAPI
- **Scrapes** all chapters and verses for a given book of the Bible
- **Exports** results as JSON files (one per book)
- **Asynchronous** scraping using Playwright for fast, headless browser automation

## Project Structure

```
py-scraper/
├── app/
│   ├── constants/
│   │   └── book_constanst.py   # Book name mappings and chapter counts
│   ├── main.py                 # FastAPI app entry point
│   └── output/                 # Scraped JSON output files
├── controllers/
│   └── scrape_controller.py    # Scraping logic and controller
├── pyproject.toml              # Project dependencies
├── uv.lock                     # Dependency lock file
└── README.md                   # This file
```

## API Endpoints

### `GET /`

- Returns: `{ "message": "Hello World" }`
- Health check endpoint.

### `GET /scrape?book=Genesis`

- **Query Parameter:** `book` (e.g., "Genesis", "Exodus", etc.)
- **Description:** Scrapes all chapters and verses for the specified book and saves the result as a JSON file in `app/output/`.
- **Returns:** `{ "url": "ok", "title": "ok" }` on success.

## How It Works

- The `/scrape` endpoint launches a Playwright browser, navigates to the relevant bible.com pages, and extracts all verses and headings for each chapter of the requested book.
- Book names and chapter counts are mapped using `app/constants/book_constanst.py`.
- The scraped data is saved as a JSON file named after the book (e.g., `Genesis.json`) in `app/output/`.

## Usage

### 1. Install dependencies

```bash
uv pip install -r pyproject.toml
```

### 2. Run the server

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Scrape a book

Open your browser or use `curl`:

```
http://localhost:8000/scrape?book=Genesis
```

The output will be saved to `app/output/Genesis.json`.

## Configuration

- **Book names:** Use the canonical names as listed in `app/constants/book_constanst.py`.
- **Output:** All scraped data is saved in `app/output/`.

## Requirements

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- FastAPI
- Playwright (and its browser dependencies)

## Notes

- The scraper uses a real browser (Chromium) via Playwright, so it may open browser windows during scraping. If don't want browser to open put Headless=True
- The scraping logic is robust to different navigation structures on bible.com, but may need updates if the site changes or DOM element changes