#crawler.py
import undetected_chromedriver as uc
import time
import json
import uuid
from httpx import TimeoutException
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
import instructor


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






# def getHtmlFile(url: str) -> tuple:
#     try:
#         options = uc.ChromeOptions()
#         options.add_argument('--no-sandbox')
#         options.add_argument('--disable-dev-shm-usage')
#         options.add_argument('--disable-blink-features=AutomationControlled')  # Ẩn dấu hiệu tự động hóa
#         options.add_experimental_option('excludeSwitches', ['enable-automation'])  # Loại bỏ cờ automation
#         options.add_experimental_option('useAutomationExtension', False)  # Tắt extension automation
#         driver = uc.Chrome(options=options)
#         driver.get(url)
#         time.sleep(5)  # Tăng thời gian chờ để trang tải hoàn toàn
#         return driver, driver.page_source
#     except Exception as e:
#         print(f"Error loading URL {url}: {e}")
#         return None, None




def getHtmlFile(url: str) -> tuple:
    """Load a URL with undetected-chromedriver and return the driver and page source"""
    try:
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
       
        # Khởi tạo undetected-chromedriver
        driver = uc.Chrome(options=options)
       
        # Tải URL
        driver.get(url)
       
        # Chờ trang tải hoàn tất
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
       
        page_source = driver.page_source
        return driver, page_source
   
    except Exception as e:
        print(f"Error loading URL {url}: {e}")
        return None, None








   
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


#this will return list of links
def getLinks(driver, className):
    #sleep to wait for page to load
    time.sleep(3)
    elements=driver.find_elements(By.CSS_SELECTOR,className)
    links = []
    print(len(elements))
    #get href of all elements
    for element in elements:
        #print(element.get_attribute("href"))
        links.append(element.get_attribute("href"))
    return links
stop_event = threading.Event()
def getObject(driver, link, apikey,pydanticClass,id):
    while not stop_event.is_set():
        try:
            print(id)
            start_time = time.time()
            driver.set_page_load_timeout(15)
            try:
                driver.get(link)
                #sleep to wait for page to load
               
               
            except TimeoutException:
                driver.execute_script("window.stop();")
            html=driver.page_source
            #get all image source as string
            images = driver.find_elements(By.CSS_SELECTOR, "img")         
            soup = BeautifulSoup(html, 'html.parser')
            html = soup.get_text()
           
            for image in images:
                if image.get_attribute("src") is not None:
                    html += " "+image.get_attribute("src")
           
            # print(f"html: {html}")
       
            try:
                genai.configure(api_key=apikey) # alternative API key configuration
                client = instructor.from_gemini(
                    client=genai.GenerativeModel(
                        model_name="models/gemini-1.5-flash-latest",  
                    ),
                    mode=instructor.Mode.GEMINI_JSON,
                )

                resp = client.chat.completions.create(
                   
                    # max_tokens=1024,
                    messages=[
                        {
                            "role": "user",
                            "content": html}
                    ],
                    response_model=pydanticClass,
                )
                print(resp)
                jsonObject=resp.dict()
                #! Luu cai nay
                print(jsonObject)
                #convert any datetime object to string
                for key in jsonObject:
                    if isinstance(jsonObject[key], datetime.date):
                        jsonObject[key]=jsonObject[key].strftime("%Y-%m-%d")
                       
                jsonObject['url']=link
                add_web_page_content(id, link, jsonObject)
            except Exception as e:
                print("exception: ",e)
                jsonObject= {
                    "url": link,
                    "name": "N/A",
                    "price": "N/A",
                    "area": "N/A",
                    "legal": "N/A",
                    "address": "N/A",
                    "province": "N/A",
                    "district": "N/A",
                    "img": "N/A",}
            return jsonObject
        finally:
            #driver.quit()
            print("Got object")


def genPageLink(url, numberofpage=5):
    class Link(BaseModel):
        link: List[str]
    genai.configure(api_key=os.getenv('API_KEY')) # alternative API key configuration
    client = instructor.from_gemini(
        client=genai.GenerativeModel(
            model_name="models/gemini-1.5-flash-latest",  
        ),
        mode=instructor.Mode.GEMINI_JSON,
    )
    prompt="be awared of trailing character,create links for "+url +" with page number from current page to  "+str(numberofpage)+"example: https://vnexpress.net/the-thao-p2 -> https://vnexpress.net/the-thao-p2, https://vnexpress.net/the-thao-p3, https://vnexpress.net/the-thao-p4, https://vnexpress.net/the-thao-p5"
   
    #print(prompt)


    resp=client.chat.completions.create(
        # max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": prompt}
        ],
        response_model=Link,
    )
    print(resp.link)
    return resp.link


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
                            getObject(driver, link, api_key, pydantic_model, source_id)
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
