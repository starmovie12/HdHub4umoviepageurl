from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/', methods=['GET'])
def get_movie_links():
    # URL parameter se target link lena
    target_url = request.args.get('url')
    
    if not target_url:
        return jsonify({
            "status": "error",
            "message": "Please provide a url. Usage: /?url=https://example.com/movie-page"
        }), 400

    try:
        # Website ko access karne ke liye headers (fake browser)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(target_url, headers=headers)
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch the website. Status code: " + str(response.status_code)}), 400

        soup = BeautifulSoup(response.text, 'html.parser')
        
        download_list = []
        start_extraction = False
        
        # HTML elements ko scan karna (Wahi logic jo pehle tha)
        # Hum zyada tags cover kar rahe hain taaki miss na ho
        for element in soup.find_all(['h2', 'h3', 'h4', 'h5', 'p', 'div', 'span', 'center']):
            text = element.get_text(strip=True)
            
            # Start Condition
            if ": DOWNLOAD LINKS :" in text:
                start_extraction = True
                continue

            # Stop Condition
            if start_extraction and "WATCH" in text and "PLAYER-2" in text:
                break
            
            # Link Extraction
            if start_extraction:
                links = element.find_all('a')
                for link in links:
                    name = link.get_text(strip=True)
                    url = link.get('href')
                    
                    # Sirf valid links aur naam add karein
                    if name and url and "http" in url:
                        # Purane duplicates hatane ke liye check kar sakte hain, par abhi direct add kar rahe hain
                        download_list.append({
                            "name": name,
                            "link": url
                        })

        return jsonify(download_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
          
