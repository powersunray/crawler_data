#crawler_runner.py
import os
from typing import List, Dict
import threading
from app.services.crawler import (
    get_all_web_crawl,
    get_web_crawl_attributes_by_web_crawl_id,
    create_dynamic_model_from_json,
    genPageLink,
    crawlThread,
    stop_event
)

def run_crawler(web_id: str, app):
    try:
        stop_event.clear()
        api_key = os.getenv("GOOGLE_API_KEY")
        print(f"API KEY: {api_key}")
        if not api_key:
            print("No GOOGLE_API_KEY found in environment variables")
            return False
        
        # Get web crawl sources
        with app.app_context():
            sources = get_all_web_crawl()
            if web_id:
                sources = [s for s in sources if s['id'] == web_id]
            
            if not sources:
                print(f"No active web crawl sources found{' for ID ' + web_id if web_id else ''}")
                return False
            
            # Process each source
            for source in sources:
                print(f"Processing web crawl source: {source['url']}")
                
                attributes = get_web_crawl_attributes_by_web_crawl_id(source['id'])
                if not attributes:
                    print(f"No attributes defined for source {source['id']}")
                    continue
                
                pydantic_model = create_dynamic_model_from_json(attributes)
                page_urls = genPageLink(source['url'], numberofpage=3)
                num_threads = min(source['threads'], 3)
                
                # Split URLs among threads
                url_chunks = [[] for _ in range(num_threads)]
                for i, url in enumerate(page_urls):
                    url_chunks[i % num_threads].append(url)
                
                # Create and start threads
                threads = []
                for i in range(num_threads):
                    # Tạo một bản sao của app context cho mỗi thread
                    ctx = app.app_context()
                    thread = threading.Thread(
                        target=crawlThread,
                        args=(url_chunks[i], source, api_key, pydantic_model, source['id'], ctx)
                    )
                    thread.start()
                    threads.append(thread)
                
                for thread in threads:
                    thread.join()
                
                print(f"Completed processing source: {source['url']}")
            
            return True
    
    except Exception as e:
        print(f"Error in run_crawler: {e}")
        return False