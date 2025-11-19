# 1. Update system (always first)
#sudo apt update && sudo apt upgrade -y
# 2. Install Python + venv + git
#sudo apt install python3 python3-venv python3-pip git -y
# 3. Create project folder and enter it
#mkdir ~/flask-site && cd ~/flask-site
# 4. Create virtual environment and activate
#python3 -m venv venv
#source venv/bin/activate
# 5. Install Flask + extras you'll actually want
#pip install --upgrade pip
#pip install flask gunicorn pillow   # pillow = for image thumbnails later
# 6. Create the complete single-file site (with gallery from local folder)
#cat > app.py << 'EOF'
try:
    from flask import Flask, render_template_string, send_from_directory, request, jsonify
except ImportError:
    import sys
    print("Missing dependency: Flask")
    print("")
    print("To install Flask and required packages, run:")
    print("  python3 -m venv venv                # create a virtualenv (optional)")
    print("  source venv/bin/activate            # activate virtualenv (macOS/Linux)")
    print("  pip install --upgrade pip")
    print("  pip install -r requirements.txt    # or 'pip install flask gunicorn pillow'")
    print("")
    sys.exit(1)

import os
import subprocess
import datetime

app = Flask(__name__, static_folder=None)
IMAGE_DIR = "static/gallery"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Auto-discover images
def get_images():
    if not os.path.exists(IMAGE_DIR):
        return []
    return sorted([f for f in os.listdir(IMAGE_DIR)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))])

images = get_images()

layout = lambda title, body: f"""
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
<nav><a href="/">Home</a> <a href="/gallery">Gallery</a> <a href="/about">About</a></nav>
<main>{body}</main>
<footer>© 2025 • Raspberry Pi + Flask • {len(images)} photos</footer>
<script src="/static/js/app.js"></script>
</body></html>
"""

# Serve static files from the local static/ folder
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route("/")
def home():
    body = "<h1>Hello from Raspberry Pi!</h1><p>Your Flask site is running perfectly.</p>"
    # simple button and message span; JS lives in static/js/app.js
    body += "<p><button id=\"capture-btn\">Capture current</button> <span id=\"capture-msg\"></span></p>"
    return render_template_string(layout("Home", body))

@app.route("/gallery")
def gallery():
    images = get_images()
    imgs = "".join(f'<img src="/img/{f}" alt="{f}" data-fname="{f}">' for f in images)
    # Capture button for gallery page; JS handles capture and dynamic updates
    capture_button = "<p><button id=\"capture-btn\">Capture current</button> <span id=\"capture-msg\"></span></p>"
    body = f"<h1>Gallery ({len(images)})</h1>{capture_button}<div id='gallery' class='gallery'>{imgs}</div>"
    return render_template_string(layout("Gallery", body))

@app.route("/about")
def about():
    return render_template_string(layout("About", "<h1>About</h1><p>Running on Raspberry Pi with pure Flask. Zero bloat.</p>"))

@app.route('/img/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_DIR, filename)

# Capture endpoint that runs rpicam-still and saves to a timestamped filename
@app.route('/capture', methods=['POST'])
def capture():
    global images
    try:
        os.makedirs(IMAGE_DIR, exist_ok=True)
        # create a unique filename using current timestamp
        filename = datetime.datetime.now().strftime('img_%Y%m%d_%H%M%S.jpg')
        target = os.path.join(IMAGE_DIR, filename)
        # Run the rpicam-still command to capture an image
        res = subprocess.run(['rpicam-still', '-o', target], capture_output=True, text=True, timeout=30)
        if res.returncode != 0:
            return jsonify({'ok': False, 'error': res.stderr.strip() or 'rpicam-still failed'}), 500
        images = get_images()
        return jsonify({'ok': True, 'path': f'/img/{filename}', 'filename': filename})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# JSON endpoint returning list of images
@app.route('/images')
def images_api():
    return jsonify({'images': get_images()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
#EOF

# 7. Create folder for your photos
#mkdir -p static/gallery
#echo "Drop your photos into ~/flask-site/static/gallery/ and refresh the page!"