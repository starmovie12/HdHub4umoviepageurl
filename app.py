from flask import Flask, request, jsonify
import cloudscraper
import re
import time
import os

app = Flask(__name__)

# --- CONFIGURATION ---
def get_scraper():
    # Render par Cloudflare ko dhokha dene ke liye settings
    return cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'android', 'desktop': False}
    )

def solve_hubcloud(url):
    print(f"⚡ Processing on Cloud: {url}")
    scraper = get_scraper()
    
    try:
        # STEP 1: Main Page
        resp1 = scraper.get(url, timeout=15)
        
        # Redirect Link Dhundo
        redirect_match = re.search(r'href="([^"]+hubcloud\.php\?[^"]+)"', resp1.text)
        if not redirect_match:
            redirect_match = re.search(r'id="download"[^>]+href="([^"]+)"', resp1.text)
            
        if not redirect_match:
            return {"status": "error", "message": "Redirect Link Not Found"}

        next_url = redirect_match.group(1).replace("&amp;", "&")
        
        # STEP 2: Final Page with Referer
        time.sleep(1) # Thoda wait taki block na ho
        headers = {"Referer": url}
        resp2 = scraper.get(next_url, headers=headers)
        
        # STEP 3: Link Extraction
        content = resp2.text
        links = []
        
        # Regex Patterns
        links.extend(re.findall(r'(https?://[^"\s\'>]+token=[^"\s\'>]+)', content))
        links.extend(re.findall(r'(https?://[^"\s\'>]+\.(?:mkv|mp4)[^"\s\'>]*)', content))
        
        final_links = list(set([l.strip('"').strip("'") for l in links]))
        
        if not final_links:
            return {"status": "error", "message": "No links found inside page"}
            
        return {"status": "success", "total": len(final_links), "links": final_links}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/')
def home():
    return "✅ HubCloud Solver API is Running on Render!"

@app.route('/solve', methods=['GET'])
def api_handler():
    url = request.args.get('url')
    if not url: return jsonify({"error": "URL missing"}), 400
    return jsonify(solve_hubcloud(url))

if __name__ == '__main__':
    # Local testing ke liye
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
