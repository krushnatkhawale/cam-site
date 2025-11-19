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

CSS = """
<style>
    body{font-family:system-ui,sans-serif;margin:0;background:#fafafa;color:#222;line-height:1.6}
    nav{background:white;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.1);position:sticky;top:0}
    nav a{margin:0 1rem;color:#0066ff;text-decoration:none;font-weight:600}
    main{max-width:1100px;margin:2rem auto;padding:0 1rem}
    h1{color:#0066ff}
    .gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.5rem;padding:2rem 0}
    .gallery img{width:100%;height:260px;object-fit:cover;border-radius:12px;
                 box-shadow:0 4px 20px rgba(0,0,0,.15);transition:.4s;loading:lazy}
    .gallery img:hover{transform:scale(1.06);box-shadow:0 20px 40px rgba(0,0,0,.25)}
    footer{text-align:center;padding:3rem;color:#777}
</style>
"""

layout = lambda title, body: f"""
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>{CSS}</head>
<body>
<nav><a href="/">Home</a> <a href="/gallery">Gallery</a> <a href="/about">About</a></nav>
<main>{body}</main>
<footer>© 2025 • Raspberry Pi + Flask • {len(images)} photos</footer>
</body></html>
"""

@app.route("/")
def home():
    body = "<h1>Hello from Raspberry Pi!</h1><p>Your Flask site is running perfectly.</p>"
    body += "<p><button id=\"capture-btn\">Capture current</button> <span id=\"capture-msg\"></span></p>"
    body += "<script>document.getElementById('capture-btn').addEventListener('click',async()=>{const btn=document.getElementById('capture-btn');btn.disabled=true;document.getElementById('capture-msg').textContent='Capturing...';try{const res=await fetch('/capture',{method:'POST'});const j=await res.json();if(res.ok){document.getElementById('capture-msg').textContent='Done';setTimeout(()=>{document.getElementById('capture-msg').textContent='';btn.disabled=false;},700);}else{document.getElementById('capture-msg').textContent='Error: '+(j.error||res.statusText);btn.disabled=false;}}catch(e){document.getElementById('capture-msg').textContent='Error: '+e;btn.disabled=false;}});</script>"
    return render_template_string(layout("Home", body))

@app.route("/gallery")
def gallery():
    images = get_images()
    imgs = "".join(f'<img src="/img/{f}" alt="{f}" data-fname="{f}">' for f in images)
    # Capture button for gallery page
    capture_button = "<p><button id=\"capture-btn\">Capture current</button> <span id=\"capture-msg\"></span></p>"
    # JS for capture action (triggers fetchImages when capture succeeds)
    capture_js = """
    <script>
    document.getElementById('capture-btn').addEventListener('click',async()=>{
        const btn=document.getElementById('capture-btn');
        btn.disabled=true;document.getElementById('capture-msg').textContent='Capturing...';
        try{
            const res=await fetch('/capture',{method:'POST'});
            const j=await res.json();
            if(res.ok){
                document.getElementById('capture-msg').textContent='Done';
                if(window.fetchImages) await window.fetchImages();
                setTimeout(()=>{document.getElementById('capture-msg').textContent='';btn.disabled=false;},700);
            }
            else{document.getElementById('capture-msg').textContent='Error: '+(j.error||res.statusText);btn.disabled=false;}
        }catch(e){document.getElementById('capture-msg').textContent='Error: '+e;btn.disabled=false;}
    });
    </script>
    """
    infinite_js = """
    <script>
    let i=12; const imgs = document.querySelectorAll('.gallery img');
    window.addEventListener('scroll',()=>{
        if(window.innerHeight + window.scrollY >= document.body.offsetHeight - 800 && i<imgs.length){
            for(let j=0;j<12 && i<imgs.length;j++,i++) imgs[i].style.opacity=1;
        }
    });
    </script>
    """ if len(images)>12 else ""

    # Polling JS to fetch new images and append them without reloading
    poll_js = """
    <script>
    window.fetchImages = async function(){
        try{
            const res = await fetch('/images');
            if(!res.ok) return;
            const data = await res.json();
            const gallery = document.getElementById('gallery');
            if(!gallery) return;
            const existing = new Set(Array.from(gallery.querySelectorAll('img')).map(i=>i.getAttribute('data-fname')));
            data.images.forEach(fname=>{
                if(!existing.has(fname)){
                    const html = `<img src="/img/${fname}" alt="${fname}" data-fname="${fname}">`;
                    gallery.insertAdjacentHTML('afterbegin', html);
                }
            });
        }catch(e){console.log('fetchImages error', e)}
    }
    // fetchImages will be invoked only when a capture completes successfully
    </script>
    """

    body = f"<h1>Gallery ({len(images)})</h1>{capture_button}<div id='gallery' class='gallery'>{imgs}</div>{infinite_js}{capture_js}{poll_js}"
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