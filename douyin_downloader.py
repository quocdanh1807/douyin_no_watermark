from flask import Flask, request, jsonify
import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__)

def get_real_url(share_text):
    url_pattern = re.compile(r'https?://v\.douyin\.com/[a-zA-Z0-9]+/')
    match = url_pattern.search(share_text)
    return match.group(0) if match else share_text

@app.route('/', methods=['GET'])
def download_video():
    url = request.args.get('url')
    if not url:
        return jsonify({"success": False, "error": "Vui lòng cung cấp link (url)"}), 400

    short_url = get_real_url(url)
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)'}
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        
        # 1. Lấy link dài
        resp1 = session.get(short_url, allow_redirects=False, verify=False)
        long_url = resp1.headers.get('Location', short_url)
        
        # 2. Lấy video_id
        resp2 = session.get(long_url, verify=False)
        vid_match = re.search(r'video_id=([a-zA-Z0-9]+)', resp2.text)
        if not vid_match:
            return jsonify({"success": False, "error": "Không tìm thấy video_id"}), 404
            
        video_id = vid_match.group(1)
        
        # 3. Gọi API lấy link mp4 gốc
        api_url = f"https://api.amemv.com/aweme/v1/play/?video_id={video_id}&ratio=1080p&line=0"
        resp3 = session.get(api_url, allow_redirects=False, verify=False)
        real_url = resp3.headers.get('Location')
        
        if not real_url:
            return jsonify({"success": False, "error": "Không lấy được link gốc"}), 404
            
        return jsonify({
            "success": True,
            "video_url": real_url
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Dành cho Vercel (không cần app.run)
