from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

# --- CONFIGURATION ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Referer": "https://hdhub4u.fo/"
}

# Junk Domains jo nahi chahiye
JUNK_DOMAINS = ["catimages", "imdb.com", "googleusercontent", "instagram.com", "facebook.com", "wp-content"]

def extract_clean_links(url):
    print(f"⚡ Scanning: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        found_links = []
        capture_mode = False 
        
        # Content Area Dhundo
        content_div = soup.find('div', class_='entry-content')
        if not content_div: content_div = soup.find('main')
        if not content_div: content_div = soup.body
        
        if not content_div:
            return {"status": "error", "message": "Content div not found"}

        # Element by Element Scan
        for element in content_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'div', 'a']):
            text = element.get_text().strip().upper()
            
            # 1. START SIGNAL
            if "DOWNLOAD" in text and "LINK" in text and ":" in text:
                capture_mode = True
                continue 

            # 2. STOP SIGNAL
            if capture_mode:
                if "WATCH" in text or "PLAYER" in text or "PLAY ONLINE" in text:
                    break 

                # 3. LINK EXTRACTION
                links_in_element = []
                if element.name == 'a' and element.get('href'):
                    links_in_element.append(element)
                else:
                    links_in_element = element.find_all('a', href=True)

                for a_tag in links_in_element:
                    link = a_tag['href']
                    quality = a_tag.get_text().strip()
                    
                    # JUNK FILTER
                    if any(junk in link for junk in JUNK_DOMAINS): continue
                    if "WATCH" in quality.upper(): continue

                    # Add to list
                    if link not in [x['link'] for x in found_links]:
                        # Quality Name Fix
                        if not quality or len(quality) < 2:
                            parent = a_tag.find_parent()
                            if parent:
                                prev = parent.find_previous(['h3', 'h4', 'h5', 'strong'])
                                if prev: quality = prev.get_text().strip()
                        
                        # Clean Name
                        clean_name = quality.replace("⚡", "").strip()
                        if not clean_name: clean_name = "Download Link"

                        found_links.append({"name": clean_name, "link": link})

        if not found_links:
            return {"status": "error", "message": "No links found (Check markers)"}

        return {"status": "success", "total": len(found_links), "links": found_links}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ROUTES ---
@app.route('/')
def home():
    return "✅ Movie Extractor API is Running!"

@app.route('/extract', methods=['GET'])
def api_handler():
    url = request.args.get('url')
    if not url: return jsonify({"error": "URL missing"}), 400
    return jsonify(extract_clean_links(url))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
