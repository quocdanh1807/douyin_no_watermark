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
    # Dùng User-Agent của máy tính để Douyin trả về URL dễ bóc ID hơn
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        
        # 1. Truy cập link ngắn và cho phép tự động chuyển hướng sang link dài
        resp = session.get(short_url, allow_redirects=True, verify=False)
        long_url = resp.url
        
        # 2. Tìm đoạn mã 19 chữ số (video_id) nằm trực tiếp trong link dài
        vid_match = re.search(r'(?:/video/|/note/|/share/video/|video_id=)(\d+)', long_url)
        
        if not vid_match:
            return jsonify({"success": False, "error": "Không tìm thấy video_id", "url_thuc_te": long_url}), 404
            
        video_id = vid_match.group(1)
        
        # 3. Gọi API nội bộ của Douyin để lấy link mp4 không logo
        api_url = f"https://api.amemv.com/aweme/v1/play/?video_id={video_id}&ratio=1080p&line=0"
        resp_api = session.get(api_url, allow_redirects=False, verify=False)
        real_url = resp_api.headers.get('Location')
        
        if not real_url:
            return jsonify({"success": False, "error": "Không lấy được link gốc"}), 404
            
        return jsonify({
            "success": True,
            "video_url": real_url
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Dành cho Vercel (không cần app.run)
