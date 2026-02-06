from flask import Flask, request, jsonify
import cloudscraper
import re
import time
import os

app = Flask(__name__)

# --- CONFIGURATION FOR RENDER ---
def get_scraper():
    # Render Server par 'Windows/Chrome' banna jyada safe hai
    return cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

def solve_hubcloud(url):
    print(f"⚡ Processing Cloud Request: {url}")
    scraper = get_scraper()
    
    try:
        # --- STEP 1: Main Page Visit ---
        # Headers lagana jaruri hai taki asli user lage
        headers_fake = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        
        resp1 = scraper.get(url, headers=headers_fake, timeout=15)
        
        # Check Cloudflare Block
        if "Just a moment" in resp1.text:
            return {"status": "error", "message": "Blocked by Cloudflare (Challenge Page)"}

        # Redirect Link Dhundo
        redirect_match = re.search(r'href="([^"]+hubcloud\.php\?[^"]+)"', resp1.text)
        if not redirect_match:
            # Backup Pattern
            redirect_match = re.search(r'id="download"[^>]+href="([^"]+)"', resp1.text)
            
        if not redirect_match:
            return {"status": "error", "message": "Redirect Link Not Found"}

        next_url = redirect_match.group(1).replace("&amp;", "&")
        
        # --- STEP 2: Final Page Visit ---
        # Thoda wait karo (Render fast hota hai, HubCloud pakad leta hai)
        time.sleep(2) 
        
        # Referer HEADER ke bina link nahi milega
        headers_final = {
            "Referer": url,
            "User-Agent": headers_fake["User-Agent"]
        }
        
        resp2 = scraper.get(next_url, headers=headers_final, timeout=15)
        
        # --- STEP 3: Link Extraction ---
        content = resp2.text
        links = []
        
        # Regex Patterns
        links.extend(re.findall(r'(https?://[^"\s\'>]+token=[^"\s\'>]+)', content))
        links.extend(re.findall(r'(https?://[^"\s\'>]+\.(?:mkv|mp4)[^"\s\'>]*)', content))
        
        # Duplicate hatao
        final_links = list(set([l.strip('"').strip("'") for l in links]))
        
        if not final_links:
            return {"status": "error", "message": "No links found inside page"}
            
        return {"status": "success", "total": len(final_links), "links": final_links}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ROUTES ---
@app.route('/')
def home():
    return "✅ HubCloud Solver is LIVE on Render!"

@app.route('/solve', methods=['GET'])
def api_handler():
    url = request.args.get('url')
    if not url: return jsonify({"error": "URL missing"}), 400
    return jsonify(solve_hubcloud(url))

# --- SERVER START ---
if __name__ == '__main__':
    # Render apna PORT khud deta hai (Environment Variable se)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
