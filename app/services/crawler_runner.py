# crawler_runner.py
import os
from typing import List, Dict
import threading
# from app.logger import logger
from app import create_app
from app.services.crawler import (
    get_all_web_crawl,
    get_web_crawl_attributes_by_web_crawl_id,
    create_dynamic_model_from_json,
    genPageLink,
    crawlThread,
    stop_event
)

def run_crawler(web_id: str):
    """
    Run the web crawler for all active sources or a specific source if web_id is provided
    """
    try:
        # Reset the stop event
        stop_event.clear()
        
        # Get API keys from environment
        api_keys = [
            os.getenv('GEMINI_API_KEY_1'),
            os.getenv('GEMINI_API_KEY_2'),
            os.getenv('GEMINI_API_KEY_3')
        ]
        print(f"API KEY 1: {api_keys[0]}")
        
        # Ensure we have at least one API key
        if not api_keys[0]:
            print("No Gemini API keys found in environment variables")
            return False
            
        # Get web crawl sources
        sources = get_all_web_crawl()
        if web_id:
            sources = [s for s in sources if s['id'] == web_id]
            
        if not sources:
            print(f"No active web crawl sources found{' for ID ' + web_id if web_id else ''}")
            return False
            
        # Process each source
        for source in sources:
            print(f"Processing web crawl source: {source['url']}")
            
            # Get attributes for this source
            attributes = get_web_crawl_attributes_by_web_crawl_id(source['id'])
            if not attributes:
                print(f"No attributes defined for source {source['id']}")
                continue
                
            # Create dynamic Pydantic model
            pydantic_model = create_dynamic_model_from_json(attributes)
            
            # Generate paginated URLs
            page_urls = genPageLink(source['url'], numberofpage=3)
            
            # Determine number of threads to use
            num_threads = min(source['threads'], 3)  # Cap at 3 threads
            
            # Split URLs among threads
            # url_chunks = [[] for _ in range(num_threads)]
            # for i, url in enumerate(page_urls):
            #     url_chunks[i % num_threads].append(url)
            url_chunks: List[List[str]] = [[] for _ in range(num_threads)]
            for i, url in enumerate(page_urls):
                url_chunks[i % num_threads].append(url)
                
            # Create and start threads
            threads = []
            for i in range(num_threads):
                # Use different API key for each thread if available
                api_key = api_keys[i] if i < len(api_keys) else api_keys[0]
                
                thread = threading.Thread(
                    target=crawlThread,
                    args=(url_chunks[i], source, api_key, pydantic_model, source['id'])
                )
                thread.start()
                threads.append(thread)
                
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
                
            print(f"Completed processing source: {source['url']}")
            
        return True
        
    except Exception as e:
        print(f"Error in run_crawler: {e}")
        return False