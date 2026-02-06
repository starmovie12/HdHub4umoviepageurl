from flask import Flask, request
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)
app.json.sort_keys = False

@app.route('/', methods=['GET'])
def get_movie_links():
    target_url = request.args.get('url')
    
    if not target_url:
        return app.response_class(
            response=json.dumps({"error": "Please provide a url"}, indent=4),
            status=400,
            mimetype='application/json'
        )

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(target_url, headers=headers)
        if response.status_code != 200:
            return app.response_class(
                response=json.dumps({"error": "Failed to fetch website"}, indent=4),
                status=400,
                mimetype='application/json'
            )

        soup = BeautifulSoup(response.text, 'html.parser')
        
        download_list = []
        start_extraction = False
        
        all_tags = soup.find_all(['h2', 'h3', 'h4', 'h5', 'p', 'div', 'span', 'center', 'hr'])

        for element in all_tags:
            text = element.get_text(strip=True)
            
            # --- START POINT ---
            if ": DOWNLOAD LINKS :" in text:
                start_extraction = True
                continue 

            # --- STOP POINT ---
            if start_extraction and "WATCH" in text and "PLAYER-2" in text:
                break 
            
            # --- EXTRACTION ---
            if start_extraction:
                links = element.find_all('a')
                for link in links:
                    name = link.get_text(strip=True)
                    href = link.get('href')
                    
                    # --- STRICT FILTERS (Updated) ---
                    
                    # 1. Basic Check
                    if not name or not href:
                        continue

                    # 2. HTTP Check (Sabse Important Fix)
                    # "300MB Movies" wala link '/category/...' se shuru hota hai (http nahi hota).
                    # Ye line use turant hata degi.
                    if not href.startswith("http"):
                        continue

                    # 3. Explicit Block
                    # Agar galti se http wala category link bhi aa gaya, to ye use rok lega.
                    if "/category/" in href or "/tag/" in href:
                        continue
                        
                    # 4. IMDb Check
                    if "imdb.com" in href or "/10" in name:
                        continue

                    # 5. Valid Keywords Check
                    valid_keywords = ["480p", "720p", "1080p", "2160p", "4k", "hevc", "x264", "web-dl", "mb", "gb"]
                    is_valid = any(key in name.lower() for key in valid_keywords)
                    
                    if is_valid:
                        # Duplicate check
                        if not any(d['link'] == href for d in download_list):
                            download_list.append({
                                "name": name,
                                "link": href
                            })

        return app.response_class(
            response=json.dumps(download_list, indent=4, ensure_ascii=False),
            mimetype='application/json'
        )

    except Exception as e:
        return app.response_class(
            response=json.dumps({"error": str(e)}, indent=4),
            status=500,
            mimetype='application/json'
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
