from playwright.async_api import async_playwright
from typing import Dict
import os
import json
from app.constants.book_constanst import name_mapper, bible_chapter_lengths

async def scrape_website_controller(book: str) -> Dict[str, str]:
    async with async_playwright() as p:
        book_name = name_mapper[book]
        chapter = {}
        
        # First, determine the total number of chapters by checking the navigation
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        total_chapter = bible_chapter_lengths[book]
        # Go to chapter 1 to get the chapter navigation
        url = f"https://www.bible.com/bible/1483/{book_name}.1.NNRV"
        await page.goto(url, timeout=0)
        await page.wait_for_load_state('networkidle')
        
        # Try to find chapter navigation to determine total chapters
        total_chapters = 1  # Default to 1 if we can't find navigation
        
        try:
            # Look for chapter navigation elements
            chapter_nav = await page.query_selector('[data-testid="chapter-nav"]')
            if chapter_nav:
                chapter_links = await chapter_nav.query_selector_all('a')
                if chapter_links:
                    chapter_numbers = []
                    for link in chapter_links:
                        text = await link.inner_text()
                        if text.strip().isdigit():
                            chapter_numbers.append(int(text.strip()))
                    if chapter_numbers:
                        total_chapters = max(chapter_numbers)
            
            # Alternative method: try to find the last chapter by checking page title or breadcrumbs
            if total_chapters == 1:
                # Try to extract from page title or other elements
                title = await page.title()
                # Look for patterns like "Genesis 1 of 50" or similar
                import re
                match = re.search(r'of (\d+)', title)
                if match:
                    total_chapters = int(match.group(1))
                else:
                    # Try to find chapter selector dropdown
                    chapter_selector = await page.query_selector('select[data-testid="chapter-selector"]')
                    if chapter_selector:
                        options = await chapter_selector.query_selector_all('option')
                        if options:
                            chapter_numbers = []
                            for option in options:
                                text = await option.inner_text()
                                if text.strip().isdigit():
                                    chapter_numbers.append(int(text.strip()))
                            if chapter_numbers:
                                total_chapters = max(chapter_numbers)
        except Exception as e:
            print(f"Warning: Could not determine total chapters automatically: {e}")
            # Fallback: try to determine by attempting to access chapters
            test_chapter = 2
            while test_chapter <= 50:  # Reasonable upper limit
                test_url = f"https://www.bible.com/bible/1483/{book_name}.{test_chapter}.NNRV"
                try:
                    await page.goto(test_url, timeout=0)
                    await page.wait_for_load_state('networkidle', timeout=5000)
                    
                    # Check if chapter exists by looking for the chapter container
                    chapter_container = await page.query_selector(f'div[data-usfm="{book_name}.{test_chapter}"]')
                    if chapter_container:
                        total_chapters = test_chapter
                        test_chapter += 1
                    else:
                        break
                except:
                    break
        
        await browser.close()
        
        print(f"Found {total_chapters} chapters in {book}")
        
        # Now scrape all chapters
        for chapter_num in range(1, total_chapter + 1):
            url = f"https://www.bible.com/bible/1483/{book_name}.{chapter_num}.NNRV"
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(url, timeout=0)
            await page.wait_for_load_state('networkidle')

            current_title = None
            container = await page.query_selector(f'div[data-usfm="{book_name}.{chapter_num}"]')
            verse_texts = {}

            if container:
                # Get ALL verse elements in the chapter
                all_verse_elements = await container.query_selector_all(f'[data-usfm^="{book_name}.{chapter_num}."]')
                
                # Build a mapping of verse numbers to all their text content
                for verse_element in all_verse_elements:
                    # Get the verse number from the label
                    label_el = await verse_element.query_selector('.ChapterContent_label__R2PLt')
                    if label_el:
                        verse_text = (await label_el.inner_text()).strip()
                        if verse_text.isdigit():
                            verse_num = int(verse_text)
                            
                            # Get all content elements within this verse span
                            content_els = await verse_element.query_selector_all('.ChapterContent_content__RrUqA')
                            text_parts = []
                            for content_el in content_els:
                                # Use innerHTML to preserve formatting, then clean it up
                                html_content = await content_el.inner_html()
                                # Convert <br> tags to newlines
                                import re
                                text_with_breaks = re.sub(r'<br\s*/?>', '\n', html_content)
                                # Remove other HTML tags but keep the text
                                text_part = re.sub(r'<[^>]+>', '', text_with_breaks).strip()
                                if text_part:
                                    text_parts.append(text_part)
                            
                            if text_parts:
                                full_text = "\n".join(text_parts) if any('\n' in part for part in text_parts) else " ".join(text_parts)
                                if verse_num in verse_texts:
                                    verse_texts[verse_num] += " " + full_text
                                else:
                                    verse_texts[verse_num] = full_text

                # Also check for poetry/quote sections that might contain verse content
                poetry_sections = await container.query_selector_all('.ChapterContent_q__EZOnh')
                for poetry_el in poetry_sections:
                    verse_spans_in_poetry = await poetry_el.query_selector_all(f'[data-usfm^="{book_name}.{chapter_num}."]')
                    for verse_span in verse_spans_in_poetry:
                        # Extract verse number and text from poetry sections
                        usfm_attr = await verse_span.get_attribute('data-usfm')
                        if usfm_attr:
                            # Extract verse number from usfm attribute like "GEN.2.23"
                            parts = usfm_attr.split('.')
                            if len(parts) >= 3:
                                verse_num = int(parts[2])
                                content_els = await verse_span.query_selector_all('.ChapterContent_content__RrUqA')
                                text_parts = []
                                for content_el in content_els:
                                    # Use innerHTML to preserve formatting, then clean it up
                                    html_content = await content_el.inner_html()
                                    # Convert <br> tags to newlines
                                    import re
                                    text_with_breaks = re.sub(r'<br\s*/?>', '\n', html_content)
                                    # Remove other HTML tags but keep the text
                                    text_part = re.sub(r'<[^>]+>', '', text_with_breaks).strip()
                                    if text_part:
                                        text_parts.append(text_part)
                                
                                if text_parts:
                                    poetry_text = "\n".join(text_parts) if any('\n' in part for part in text_parts) else " ".join(text_parts)
                                    if verse_num in verse_texts:
                                        verse_texts[verse_num] += "\n" + poetry_text
                                    else:
                                        verse_texts[verse_num] = poetry_text

                # Process elements for headings
                elements = await container.query_selector_all(":scope > *")
                heading_verse_map = {}  # Map headings to the verse they precede
                
                for i, el in enumerate(elements):
                    # Check for heading
                    heading_el = await el.query_selector(".ChapterContent_heading__xBDcs")
                    if heading_el:
                        heading_text = (await heading_el.inner_text()).strip()
                        
                        # Find the next element with verses to associate the heading with
                        for j in range(i + 1, len(elements)):
                            next_el = elements[j]
                            next_verse_spans = await next_el.query_selector_all(f'[data-usfm^="{book_name}.{chapter_num}."]')
                            if next_verse_spans:
                                # Get the first verse number in the next element
                                for verse_span in next_verse_spans:
                                    label_el = await verse_span.query_selector('.ChapterContent_label__R2PLt')
                                    if label_el:
                                        verse_text = (await label_el.inner_text()).strip()
                                        if verse_text.isdigit():
                                            first_verse = int(verse_text)
                                            heading_verse_map[first_verse] = heading_text
                                            break
                                break

                # Assign accumulated verse texts to chapter with headings
                for verse_num in sorted(verse_texts.keys()):
                    text = verse_texts[verse_num]
                    verse_data = {"text": text.strip()}
                    
                    # Add heading if this verse has one
                    if verse_num in heading_verse_map:
                        verse_data["title"] = heading_verse_map[verse_num]
                    
                    if chapter_num not in chapter:
                        chapter[chapter_num] = {}
                    chapter[chapter_num][verse_num] = verse_data
                        
                print(f"Chapter {chapter_num} completed with {len(verse_texts)} verses")
            else:
                print(f"Warning: Could not find chapter container for {book_name}.{chapter_num}")
                
            await browser.close()

        output_dir = os.path.join("app", "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{book}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chapter, f, ensure_ascii=False, indent=2)
    
    return {"url": "ok", "title": "ok"}