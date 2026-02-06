from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/', methods=['GET'])
def get_movie_links():
    target_url = request.args.get('url')
    
    if not target_url:
        return jsonify({"error": "Please provide a url"}), 400

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(target_url, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch website"}), 400

        soup = BeautifulSoup(response.text, 'html.parser')
        
        download_list = []
        start_extraction = False
        
        # HTML ke saare relevant tags ko scan karte hain
        # 'hr' bhi add kiya hai kyunki sections aksar hr se separate hote hain
        all_tags = soup.find_all(['h2', 'h3', 'h4', 'h5', 'p', 'div', 'span', 'center', 'hr'])

        for element in all_tags:
            text = element.get_text(strip=True)
            
            # --- 1. START Condition ---
            if ": DOWNLOAD LINKS :" in text:
                start_extraction = True
                continue # Header ko list mein add nahi karna

            # --- 2. STOP Condition ---
            if start_extraction and "WATCH" in text and "PLAYER-2" in text:
                break # Loop yahin rok do
            
            # --- 3. EXTRACTION Logic ---
            if start_extraction:
                links = element.find_all('a')
                for link in links:
                    name = link.get_text(strip=True)
                    href = link.get('href')
                    
                    # --- STRICT FILTERS (Yahan Gadbad Hoti Thi) ---
                    
                    # Filter 1: Link aur Name hona zaroori hai
                    if not name or not href:
                        continue
                        
                    # Filter 2: IMDB aur Rating wale links ko hatao
                    if "imdb.com" in href or "/10" in name:
                        continue

                    # Filter 3: Valid Keywords check karo (Sirf wahi lo jo kaam ka ho)
                    # Agar naam mein inme se kuch nahi hai, to wo download link nahi hai
                    valid_keywords = ["480p", "720p", "1080p", "2160p", "4k", "hevc", "x264", "web-dl", "mb", "gb"]
                    
                    is_valid = any(key in name.lower() for key in valid_keywords)
                    
                    if is_valid:
                        # Duplicate se bachne ke liye check
                        if not any(d['link'] == href for d in download_list):
                            download_list.append({
                                "name": name,
                                "link": href
                            })

        return jsonify(download_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
