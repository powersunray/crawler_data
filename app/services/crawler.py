#crawler.py
import time
import json
import uuid
import requests
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import create_model, BaseModel
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import google.generativeai as genai
import threading
from app import db
from app.models.sources import Source
from app.models.attributes import Attribute
from app.models.results import Result
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os
from dotenv import load_dotenv
from flask import current_app

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")
genai.configure(api_key=GOOGLE_API_KEY)

# Global stop event for thread control
stop_event = threading.Event()

def stopCrawl():
    """Set the stop event to terminate all running crawler threads"""
    stop_event.set()
    print("Stop signal received. Terminating crawler threads...")

def get_all_web_crawl() -> List[Dict]:
    """Fetch all active web crawl sources from the database"""
    with current_app.app_context():  # Sử dụng current_app
        try:
            sources = Source.query.filter_by(status='ACTIVE').all()
            return [
                {
                    'id': str(source.id),
                    'url': source.url,
                    'link_selector': source.link_selector,
                    'threads': source.threads,
                    'description': source.description,
                    'card_information': source.card_information
                }
                for source in sources
            ]
        except Exception as e:
            print(f"Error fetching web crawl sources: {e}")
            return []

def get_web_crawl_attributes_by_web_crawl_id(web_id: str) -> List[Dict]:
    """Fetch attributes for a specific web crawl source"""
    with current_app.app_context():  # Sử dụng current_app
        try:
            attributes = Attribute.query.filter_by(source_id=uuid.UUID(web_id)).all()
            return [
                {
                    'name': attr.name,
                    'type': attr.type,
                    'description': attr.description
                }
                for attr in attributes
            ]
        except Exception as e:
            print(f"Error fetching attributes for web crawl ID {web_id}: {e}")
            return []

def create_dynamic_model_from_json(attributes: List[Dict]) -> BaseModel:
    """Create a dynamic Pydantic model based on the attributes"""
    field_definitions = {}
    for attr in attributes:
        field_name = attr['name']
        field_type = None
        if attr['type'].lower() == 'string':
            field_type = (str, ...)
        elif attr['type'].lower() == 'integer':
            field_type = (int, ...)
        elif attr['type'].lower() == 'float':
            field_type = (float, ...)
        elif attr['type'].lower() == 'boolean':
            field_type = (bool, ...)
        elif attr['type'].lower() == 'array':
            field_type = (List[str], ...)
        else:
            field_type = (str, ...)
        field_definitions[field_name] = field_type
    DynamicModel = create_model('DynamicModel', **field_definitions)
    return DynamicModel

def setup_genai(api_key: str):
    """Configure the Gemini AI API"""
    return genai.GenerativeModel('models/gemini-1.5-flash-latest')

def genPageLink(base_url: str, numberofpage: int = 3) -> List[str]:
    """Generate paginated URLs using Gemini AI"""
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        prompt = f"""
        Generate a list of {numberofpage} paginated URLs for the base URL: {base_url}
        These should be valid pagination URLs typically used by e-commerce or listing websites.
        Return only the full URLs without any explanation, one URL per line.
        """
        response = model.generate_content(prompt)
        urls = [url.strip() for url in response.text.split('\n') if url.strip()]
        if not urls:
            if '?' in base_url:
                urls = [f"{base_url}&page={i+1}" for i in range(numberofpage)]
            else:
                urls = [f"{base_url}?page={i+1}" for i in range(numberofpage)]
        print(f"Generated {len(urls)} paginated URLs")
        return urls
    except Exception as e:
        print(f"Error generating paginated URLs: {e}")
        if '?' in base_url:
            return [f"{base_url}&page={i+1}" for i in range(numberofpage)]
        else:
            return [f"{base_url}?page={i+1}" for i in range(numberofpage)]

def getHtmlFile(url: str) -> tuple:
    """Load a URL with ChromeDriver and return the driver and page source"""
    try:
        service = Service('/usr/local/bin/chromedriver')  # Đường dẫn đến chromedriver
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(3)
        return driver, driver.page_source
    except Exception as e:
        print(f"Error loading URL {url}: {e}")
        return None, None

def getLinks(driver, selector: str) -> List[str]:
    """Extract links from the page based on the provided CSS selector"""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
        )
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        links = [element.get_attribute('href') for element in elements if element.get_attribute('href')]
        print(f"Found {len(links)} links using selector: {selector}")
        return links
    except Exception as e:
        print(f"Error extracting links with selector {selector}: {e}")
        return []

def extract_images(soup) -> List[str]:
    """Extract image URLs from the page"""
    image_urls = []
    try:
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and (src.startswith('http') or src.startswith('//')):
                image_urls.append(src if src.startswith('http') else f"https:{src}")
        return image_urls[:5]
    except Exception as e:
        print(f"Error extracting images: {e}")
        return []

def add_web_page_content(source_id: str, url: str, content: Dict, ctx):
    """Save the extracted content to the database"""
    try:
        result = Result(
            source_id=uuid.UUID(source_id),
            url=url,
            contents=content,
            time_stamp=datetime.now()
        )
        db.session.add(result)
        db.session.commit()
        print(f"Saved content from {url} to database")
    except Exception as e:
        db.session.rollback()
        print(f"Error saving content to database: {e}")

def getObject(driver, url: str, api_key: str, pydantic_model: BaseModel, source_id: str, ctx) -> Dict:
    """Extract structured data from a detail page using Gemini AI"""
    try:
        if stop_event.is_set():
            return None
            
        logger.info(f"Processing URL: {url}")
        driver.get(url)
        time.sleep(3)
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        text_content = soup.get_text(separator='\n', strip=True)
        image_urls = extract_images(soup)
        
        model = setup_genai(api_key)
        
        max_retries = 5
        base_delay = 5
        
        for attempt in range(max_retries):
            try:
                prompt = f"""
                Extract the following information from this webpage about a product or listing:
                {[attr for attr in pydantic_model.__annotations__]}
                Return the data in valid JSON format with these fields.
                """
                
                content_parts = [prompt, text_content]
                
                # Giới hạn số lượng ảnh xuống 1 ảnh
                for img_url in image_urls[:1]:
                    try:
                        img_response = requests.get(img_url)
                        if img_response.status_code == 200:
                            content_parts.append({
                                "mime_type": img_response.headers.get('content-type', 'image/jpeg'),
                                "data": img_response.content
                            })
                    except Exception as e:
                        logger.error(f"Error processing image {img_url}: {e}")
                        continue
                
                response = model.generate_content(content_parts)
                
                # Xử lý response text cẩn thận hơn
                json_string = response.text
                
                try:
                    if not json_string or json_string.isspace():
                        raise ValueError("Empty JSON response")
                    
                    # Thử cleanup JSON string
                    json_string = json_string.strip()
                    if json_string.startswith("```") and json_string.endswith("```"):
                        json_string = json_string[3:-3]
                    elif '```json' in json_string:
                        json_string = json_string.split('```json')[1].split('```')[0].strip()
                    elif '```' in json_string:
                        json_string = json_string.split('```')[1].strip()
                    
                    extracted_data = json.loads(json_string)
                    
                    if not isinstance(extracted_data, dict):
                        raise ValueError("Extracted data is not a dictionary")
                    
                    add_web_page_content(source_id, url, extracted_data, ctx)
                    logger.info(f"Successfully processed: {url}")
                    
                    return extracted_data
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON format for {url}")
                    return None
                    
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    retry_delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Error extracting data from {url}: {e}")
                    return None
        
    except Exception as e:
        logger.error(f"Error extracting data from {url}: {e}")
        return None

def crawlThread(urls: List[str], config: Dict, api_key: str, pydantic_model: BaseModel, source_id: str, ctx):
    """Process a subset of URLs in a separate thread"""
    try:
        print(f"Starting crawler thread for {len(urls)} URLs")
        ctx.push()  # Push context khi thread bắt đầu
        
        try:
            for url in urls:
                if stop_event.is_set():
                    print("Stop event detected. Terminating thread.")
                    break
                    
                try:
                    driver, _ = getHtmlFile(url)
                    if not driver:
                        continue
                    
                    product_links = getLinks(driver, config['link_selector'])
                    print(f"Found {len(product_links)} links using selector: {config['link_selector']}")
                    
                    for link in product_links:
                        if stop_event.is_set():
                            break
                        
                        try:
                            getObject(driver, link, api_key, pydantic_model, source_id, ctx)
                            time.sleep(3)  # Tăng delay giữa các request
                        except Exception as e:
                            print(f"Error processing product {link}: {e}")
                    
                    driver.quit()
                
                except Exception as e:
                    print(f"Error processing URL {url}: {e}")
        
        finally:
            ctx.pop()  # Ensure context is always popped
    
    except Exception as e:
        print(f"Thread execution error: {e}")