# crawl.py
from flask import jsonify, request, Blueprint, current_app
from app.services.crawler_runner import run_crawler
from app.services.crawler import stopCrawl


# Create a Blueprint for crawler API endpoints
crawler_bp = Blueprint('crawler', __name__)

@crawler_bp.route('/start', methods=['POST'])
def start_crawler():
    """Start the web crawler for all sources or a specific source"""
    with current_app.app_context():
        try:
            data = request.get_json() or {}
            web_id = data.get('web_id')
            print(f"Print web_id: {web_id}")
            success = run_crawler(web_id)
            
            if success:
                return jsonify({"status": "success", "message": "Crawler started successfully"}), 200
            else:
                return jsonify({"status": "error", "message": "Failed to start crawler"}), 500
                
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

@crawler_bp.route('/stop', methods=['POST'])
def stop_crawler():
    """Stop all running crawler threads"""
    with current_app.app_context():
        try:
            stopCrawl()
            return jsonify({"status": "success", "message": "Stop signal sent to crawler threads"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
