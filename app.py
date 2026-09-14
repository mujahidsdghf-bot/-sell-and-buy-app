from flask import Flask, render_template_string, request, redirect, url_for, session
import boto3
import sqlite3
from datetime import datetime
import random
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = 'sellandbuy_ultra_secure_cyber_key_2026_production'

# మీ Twilio క్రెడెన్షియల్స్
TWILIO_ACCOUNT_SID = 'AC2f4c5f7922c852e68b8eeaac4f5dd03a'
TWILIO_AUTH_TOKEN = '2b6d6eed8daf347db44006f36571d7a8'
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'

S3_BUCKET = 'sellandbuy-app-storage'
S3_REGION = 'eu-north-1'

s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id='AKIAXQ7HHUFVKYQCJIGP',
    aws_secret_access_key='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'
)

def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            model TEXT,
            category TEXT NOT NULL,
            price TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            image_url TEXT NOT NULL,
            seller_contact TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            contact TEXT,
            joined_date TEXT
        )
    ''')
    # OTP డేటాబేస్ టేబుల్ (సెక్యూరిటీ కోసం)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otps (
            contact TEXT PRIMARY KEY,
            otp_code TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self' https: 'unsafe-inline' 'unsafe-eval';"
    return response

@app.route('/')
def index():
    cat_filter = request.args.get('category')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if cat_filter:
        cursor.execute('SELECT id, title, model, category, price, location, description, image_url, seller_contact, created_at FROM products WHERE category = ? ORDER BY id DESC', (cat_filter,))
    else:
        cursor.execute('SELECT id, title, model, category, price, location, description, image_url, seller_contact, created_at FROM products ORDER BY id DESC')
    
    products = cursor.fetchall()
    
    user_contact = request.cookies.get('user_contact')
    user = None
    
    if user_contact:
        cursor.execute('SELECT name, contact, joined_date FROM users WHERE contact = ? LIMIT 1', (user_contact,))
        user = cursor.fetchone()

    conn.close()

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sell & Buy - OLX Style</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; background-color: #f7f8f9; color: #002f34; padding-bottom: 70px; }
            .header { background: #002f34; color: white; padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; }
            .logo-container { display: flex; align-items: center; gap: 8px; }
            .logo-text { font-size: 20px; font-weight: bold; background: linear-gradient(45deg, #ffce32, #ff5722, #00e676, #00bcd4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }
            .search-container { background: white; padding: 10px 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; gap: 8px; }
            .location-bar, .search-bar { display: flex; gap: 8px; align-items: center; border: 2px solid #002f34; border-radius: 4px; padding: 8px; }
            .location-bar input, .search-bar input { width: 100%; border: none; outline: none; font-size: 14px; }
            .top-ad-banner { background: #ffce32; color: #002f34; padding: 10px; text-align: center; font-weight: bold; font-size: 13px; border-bottom: 1px solid #e0b825; }
            .categories { padding: 15px; background: white; margin-top: 5px; }
            .categories h3 { font-size: 16px; margin-bottom: 10px; }
            .cat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; text-align: center; }
            .cat-item { background: #ebeeef; padding: 12px 5px; border-radius: 8px; font-size: 12px; font-weight: bold; cursor: pointer; text-decoration: none; color: #002f34; display: block; }
            .cat-item:hover { background: #002f34; color: white; }
            .section-title { padding: 15px 15px 5px 15px; font-size: 16px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; }
            .product-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 10px 15px; }
            .product-card { background: white; border: 1px solid #ebeeef; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); cursor: pointer; text-decoration: none; color: inherit; display: block; }
            .product-card img { width: 100%; height: 150px; object-fit: cover; background: #eee; }
            .product-info { padding: 10px; }
            .price { font-size: 18px; font-weight: bold; color: #002f34; margin: 4px 0; }
            .title { font-size: 14px; color: #333; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .loc { font-size: 11px; color: #777; margin-top: 3px; }
            .ad-banner-box { grid-column: span 2; background: #002f34; color: #ffce32; padding: 15px; text-align: center; font-weight: bold; border-radius: 6px; margin: 5px 0; border: 1px dashed #ffce32; }
            .bottom-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 8px 0; border-top: 1px solid #ddd; box-shadow: 0 -2px 5px rgba(0,0,0,0.05); z-index: 99; }
            .nav-item { text-align: center; font-size: 11px; color: #555; text-decoration: none; cursor: pointer; }
            .sell-btn-nav { background: #ffce32; border-radius: 50%; width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 24px; margin-top: -15px; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.2); color: #002f34; }
            .modal { display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); overflow-y: auto; }
            .modal-content { background: white; margin: 10% auto; padding: 20px; width: 85%; max-width: 400px; border-radius: 8px; position: relative; }
            .close { float: right; font-size: 22px; cursor: pointer; font-weight: bold; color: #333; }
            .modal input, .modal select, .modal textarea { width: 100%; padding: 8px; margin: 5px 0 10px 0; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
            .modal button { background: #002f34; color: white; border: none; padding: 10px; width: 100%; border-radius: 4px; font-weight: bold; cursor: pointer; margin-top: 5px; }
        </style>
    </head>
    <body>

        <div class="header">
            <div class="logo-container">
                <span style="font-size: 20px;">⚡</span>
                <div class="logo-text">Sell & Buy 🚀</div>
            </div>
            <span style="font-size: 13px;">📍 Hyderabad</span>
        </div>

        <div class="search-container">
            <div class="location-bar">
                <span>📍</span>
                <input type="text" placeholder="మీ ఊరు / లొకేషన్ రాయండి (ఉదా: Suraram, Hyderabad)">
            </div>
            <div class="search-bar">
                <span>🔍</span>
                <input type="text" placeholder="Find Cars, Bikes, Mobile Phones and more...">
            </div>
        </div>

        <div class="top-ad-banner">
            🚀 ప్రత్యేక ప్రకటన: మీ పాత వస్తువులను ఇక్కడ ఉచితంగా అమ్ముకోండి!
        </div>

        <div class="categories">
            <h3>Browse Categories</h3>
            <div class="cat-grid">
                <a href="/?category=Cars" class="cat-item">🚗 Cars</a>
                <a href="/?category=Mobiles" class="cat-item">📱 Mobiles</a>
                <a href="/?category=Bikes" class="cat-item">🏍️ Bikes</a>
                <a href="/?category=Properties" class="cat-item">🏠 Properties</a>
                <a href="/?category=Electronics" class="cat-item">💻 Electronics</a>
                <a href="/?category=Furniture" class="cat-item">🛋️ Furniture</a>
                <a href="/?category=Jobs" class="cat-item">💼 Jobs</a>
                <a href="/?category=Others" class="cat-item">📦 Others</a>
            </div>
        </div>

        <div class="section-title">
            <span>Fresh Recommendations</span>
            <a href="/" style="font-size: 12px; color: #002f34; text-decoration: none;">View All</a>
        </div>

        <div class="product-grid">
            {% if products %}
                {% for p in products %}
                    <a href="/product/{{ p[0] }}" class="product-card">
                        <img src="{{ p[7] }}" alt="Item" onerror="this.src='https://via.placeholder.com/300x150?text=Image+Loading';">
                        <div class="product-info">
                            <div class="price">₹ {{ p[4] }}</div>
                            <div class="title">{{ p[1] }} ({{ p[2] }})</div>
                            <div class="loc">📍 {{ p[5] }}</div>
                        </div>
                    </a>

                    {% if loop.index % 3 == 0 %}
                        <div class="ad-banner-box">
                            📢 Sponsored Ad: మీ వ్యాపారాన్ని ఇక్కడ ప్రమోట్ చేసుకోండి!
                        </div>
                    {% endif %}
                {% endfor %}
            {% else %}
                <div style="padding: 20px; text-align: center; color: #777; grid-column: span 2;">
                    <p style="font-size: 15px; font-weight: bold;">ఈ కేటగిరీలో ఇంకా ఎలాంటి వస్తువులు లేవు!</p>
                    <a href="/" style="color: #002f34; text-decoration: underline;">అన్ని వస్తువులను చూడండి</a>
                </div>
            {% endif %}
        </div>

        <div class="bottom-nav">
            <a href="/" class="nav-item">🏠<br>Home</a>
            <a href="#" onclick="openModal('chatModal')" class="nav-item">💬<br>Chats</a>
            <a href="#" onclick="openModal('sellModal')" class="sell-btn-nav">+</a>
            <a href="/my_ads" class="nav-item">📋<br>My Ads</a>
            <a href="#" onclick="openModal('accountModal')" class="nav-item">👤<br>Account</a>
        </div>

        <!-- Sell Modal -->
        <div id="sellModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('sellModal')">&times;</span>
                <h3>Post New Ad</h3>
                <form action="/upload" method="POST" enctype="multipart/form-data">
                    <label style="font-size: 12px; font-weight: bold;">వస్తువు పేరు:</label>
                    <input type="text" name="title" required placeholder="ఉదా: Bike">
                    
                    <label style="font-size: 12px; font-weight: bold;">మోడల్ (Model):</label>
                    <input type="text" name="model" required placeholder="ఉదా: Bajaj Pulsar 2013">

                    <label style="font-size: 12px; font-weight: bold;">కేటగిరీ:</label>
                    <select name="category">
                        <option value="Bikes">Bikes</option>
                        <option value="Cars">Cars</option>
                        <option value="Mobiles">Mobiles</option>
                        <option value="Properties">Properties</option>
                        <option value="Electronics">Electronics</option>
                        <option value="Furniture">Furniture</option>
                        <option value="Others">Others</option>
                    </select>

                    <label style="font-size: 12px; font-weight: bold;">ధర (Rs):</label>
                    <input type="text" name="price" required placeholder="ఉదా: 29000">

                    <label style="font-size: 12px; font-weight: bold;">లొకేషన్:</label>
                    <input type="text" name="location" required placeholder="ఉదా: Khammam">

                    <label style="font-size: 12px; font-weight: bold;">వివరాలు (Description):</label>
                    <textarea name="description" rows="3" placeholder="కండిషన్ రాయండి..."></textarea>
                    
                    <label style="font-size: 12px; font-weight: bold;">ఫోటో:</label>
                    <input type="file" name="file" required style="border:none;">

                    <label style="font-size: 12px; font-weight: bold;">మొబైల్ నంబర్:</label>
                    <input type="text" name="seller_contact" value="{{ user[1] if user else '' }}" required placeholder="Mobile Number">
                    
                    <button type="submit">పోస్ట్ చేయండి</button>
                </form>
            </div>
        </div>

        <!-- Chats Modal -->
        <div id="chatModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('chatModal')">&times;</span>
                <h3>Live Chat with Seller</h3>
                <div style="height: 150px; border: 1px solid #ddd; padding: 8px; overflow-y: auto; background: #fafafa; font-size: 13px;" id="chatMessages">
                    <p style="color: #888;">చాటింగ్ ప్రారంభించండి...</p>
                </div>
                <input type="text" id="chatInput" placeholder="సందేశం రాయండి...">
                <button onclick="sendChatMessage()">సందేశం పంపు (Send)</button>
            </div>
        </div>

        <!-- Account Modal -->
        <div id="accountModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('accountModal')">&times;</span>
                <h3>Customer Profile & Settings</h3>
                {% if user %}
                    <div style="text-align: center; margin-bottom: 15px;">
                        <div style="font-size: 50px;">👤</div>
                        <h4 style="margin: 5px 0;">{{ user[0] }}</h4>
                        <p style="font-size: 12px; color: #666; margin: 0;">📱/✉️ {{ user[1] }}</p>
                        <p style="font-size: 11px; color: #888; margin-top: 5px;">జాయిన్ అయిన తేదీ: {{ user[2] }}</p>
                    </div>
                    <div style="background: #f1f1f1; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 13px;">
                        <b>⚙️ అకౌంట్ సెట్టింగ్స్:</b><br>
                        - Twilio Secure WhatsApp OTP ✅<br>
                        - సైబర్ సెక్యూరిటీ ప్రొటెక్షన్: ఆక్టివ్ 🔒
                    </div>
                    <button style="background: #d9534f;" onclick="location.href='/logout'">లాగౌట్ (Logout)</button>
                {% else %}
                    <form action="/send_otp" method="POST">
                        <h4 style="margin-top: 0; color: #075e54;">🟢 WhatsApp Secure OTP లాగిన్</h4>
                        <label style="font-size: 12px;">పేరు (Name):</label>
                        <input type="text" name="name" required placeholder="మీ పేరు">
                        
                        <label style="font-size: 12px;">10 అంకెల మొబైల్ నంబర్:</label>
                        <input type="text" name="contact" required placeholder="ఉదా: 9177411712" maxlength="10">
                        
                        <button type="submit" style="background: #25d366; color: white; font-weight: bold;">WhatsApp కి OTP పంపు</button>
                    </form>
                {% endif %}
            </div>
        </div>

        <script>
            function openModal(id) { document.getElementById(id).style.display = 'block'; }
            function closeModal(id) { document.getElementById(id).style.display = 'none'; }
            
            function sendChatMessage() {
                let msg = document.getElementById('chatInput').value;
                if(msg.trim() !== "") {
                    let chatDiv = document.getElementById('chatMessages');
                    chatDiv.innerHTML += "<p><b>మీరు:</b> " + msg + "</p>";
                    document.getElementById('chatInput').value = "";
                    alert("మెసేజ్ విజయవంతంగా పంపబడింది!");
                }
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content, products=products, user=user)

@app.route('/verify_otp_page')
def verify_otp_page():
    verify_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OTP Verification - Sell & Buy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; background-color: #f7f8f9; color: #002f34; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .box { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 90%; max-width: 350px; text-align: center; }
            input { width: 100%; padding: 10px; margin: 10px 0; font-size: 20px; text-align: center; letter-spacing: 5px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            button { background: #25d366; color: white; border: none; padding: 12px; width: 100%; border-radius: 4px; font-weight: bold; font-size: 15px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="box">
            <h3 style="color: #075e54; margin-top: 0;">WhatsApp OTP వెరిఫికేషన్</h3>
            <p style="font-size: 13px; color: #666;">మీ WhatsApp నంబర్‌కు పంపబడిన 4 అంకెల కోడ్‌ని ఇక్కడ ఎంటర్ చేయండి.</p>
            <form action="/verify_otp" method="POST">
                <input type="text" name="entered_otp" required placeholder="XXXX" maxlength="4">
                <button type="submit">వెరిఫై చేసి లాగిన్ అవ్వండి</button>
            </form>
        </div>
    </body>
    </html>
    """
    return verify_html

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    entered_otp = request.form.get('entered_otp').strip()
    contact = request.cookies.get('temp_contact')
    name = request.cookies.get('temp_name')

    # సర్వర్ డేటాబేస్ నుండి OTP ని చెక్ చేయడం (సెక్యూర్ వే)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT otp_code FROM otps WHERE contact = ?', (contact,))
    row = cursor.fetchone()

    if row and row[0] == entered_otp:
        joined_date = datetime.now().strftime("%d-%m-%Y")
        cursor.execute('INSERT OR IGNORE INTO users (name, contact, joined_date) VALUES (?, ?, ?)', (name, contact, joined_date))
        cursor.execute('DELETE FROM otps WHERE contact = ?', (contact,)) # వాడుకున్న OTP డిలీట్ అవుతుంది
        conn.commit()
        conn.close()

        resp = redirect(url_for('index'))
        resp.set_cookie('user_contact', contact, max_age=60*60*24*30)
        return resp
    else:
        conn.close()
        return "<script>alert('తప్పు OTP లేదా కాలం చెల్లిన కోడ్! దయచేసి మళ్లీ ప్రయత్నించండి.'); window.location.href='/';</script>"

@app.route('/my_ads')
def my_ads_page():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, price, image_url, seller_contact, created_at FROM products ORDER BY id DESC')
    ads = cursor.fetchall()
    conn.close()

    ads_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Ads - Sell & Buy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; background-color: #f7f8f9; color: #002f34; }
            .header { background: #002f34; color: white; padding: 12px 15px; display: flex; align-items: center; gap: 15px; }
            .header a { color: #ffce32; text-decoration: none; font-size: 20px; }
            .container { padding: 15px; max-width: 600px; margin: auto; background: white; min-height: 100vh; box-sizing: border-box; }
            .ad-item { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #ddd; padding: 10px 0; }
            .ad-info { display: flex; gap: 12px; align-items: center; }
            .ad-info img { width: 50px; height: 50px; object-fit: cover; border-radius: 6px; background: #eee; }
            .delete-btn { background: #d9534f; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 13px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <a href="/">← వెనుకకు</a>
            <h2 style="margin:0; font-size: 18px;">My Ads & Delete Options</h2>
        </div>

        <div class="container">
            <h3>మీరు పోస్ట్ చేసిన ప్రకటనలు:</h3>
    """

    if ads:
        for ad in ads:
            ads_html += f"""
            <div class="ad-item">
                <div class="ad-info">
                    <img src="{ad[3]}" onerror="this.src='https://via.placeholder.com/50x50?text=Img';">
                    <div>
                        <b>{ad[1]}</b><br>
                        <span style="font-size: 13px; color: green; font-weight: bold;">₹ {ad[2]}</span><br>
                        <span style="font-size: 11px; color: #777;">Posted on: {ad[5]}</span>
                    </div>
                </div>
                <a href="/delete_ad/{ad[0]}" class="delete-btn" onclick="return confirm('మీరు ఈ యాడ్ ని డిలీట్ చేయాలనుకుంటున్నారా?');">Delete</a>
            </div>
            """
    else:
        ads_html += "<p style='color: #777;'>ఇక్కడ ఎలాంటి యాడ్స్ లేవు.</p>"

    ads_html += """
        </div>
    </body>
    </html>
    """
    return ads_html

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, model, category, price, location, description, image_url, seller_contact, created_at FROM products WHERE id = ?', (product_id,))
    p = cursor.fetchone()
    conn.close()

    if not p:
        return "ప్రొడక్ట్ కనుగొనబడలేదు!", 404

    detail_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{p[1]} - Sell & Buy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; background-color: #f7f8f9; color: #002f34; }}
            .header {{ background: #002f34; color: white; padding: 12px 15px; display: flex; align-items: center; gap: 15px; }}
            .header a {{ color: #ffce32; text-decoration: none; font-size: 20px; }}
            .container {{ padding: 15px; max-width: 600px; margin: auto; background: white; min-height: 100vh; box-sizing: border-box; }}
            .prod-img {{ width: 100%; height: 280px; object-fit: cover; border-radius: 8px; background: #eee; }}
            .price {{ font-size: 24px; font-weight: bold; color: #002f34; margin: 10px 0; }}
            .title {{ font-size: 20px; font-weight: bold; margin: 5px 0; }}
            .details-box {{ background: #f9f9f9; padding: 12px; border-radius: 6px; margin: 15px 0; border: 1px solid #eee; }}
            .action-btns {{ display: flex; gap: 10px; margin-top: 20px; }}
            .action-btns button {{ flex: 1; padding: 12px; border: none; border-radius: 6px; font-weight: bold; color: white; font-size: 15px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="header">
            <a href="/">← వెనుకకు</a>
            <h2 style="margin:0; font-size: 18px;">ప్రొడక్ట్ వివరాలు</h2>
        </div>

        <div class="container">
            <img src="{p[7]}" class="prod-img" onerror="this.src='https://via.placeholder.com/400x280?text=No+Image';">
            <div class="price">₹ {p[4]}</div>
            <div class="title">{p[1]}</div>
            
            <div class="details-box">
                <p><b>మోడల్:</b> {p[2]}</p>
                <p><b>కేటగిరీ:</b> {p[3]}</p>
                <p><b>లొకేషన్ & టైమ్:</b> 📍 {p[5]} &nbsp;|&nbsp; 🕒 {p[9]}</p>
                <p><b>వివరాలు:</b> {p[6]}</p>
            </div>

            <div style="width: 100%; height: 160px; margin: 15px 0; border-radius: 6px; overflow: hidden; border: 1px solid #ccc;">
                <iframe width="100%" height="160" style="border:0;" loading="lazy" src="https://maps.google.com/maps?q={p[5]}&t=&z=13&ie=UTF8&iwloc=&output=embed"></iframe>
            </div>

            <div class="action-btns">
                <button style="background: #28a745;" onclick="makeCall('{p[8]}')">📞 Call (4 Free)</button>
                <button style="background: #007bff;" onclick="alert('చాట్ బాక్స్ ఓపెన్ అయింది!')">💬 Chat (Free)</button>
            </div>
        </div>

        <script>
            let callCount = 0;
            function makeCall(phone) {{
                callCount++;
                if (callCount <= 4) {{
                    alert("ఫ్రీ కాల్స్ మిగిలి ఉన్నాయి (" + callCount + "/4). డైరెక్ట్ నెంబర్: " + phone);
                }} else {{
                    alert("మీ 4 ఫ్రీ కాల్స్ పూర్తయ్యాయి! ఛార్జ్ వర్తిస్తుంది.");
                    window.location.href = "tel:" + phone;
                }}
            }}
        </script>
    </body>
    </html>
    '''
    return detail_html

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'ఫైల్ లేదు!'
    file = request.files['file']
    title = request.form.get('title')
    model = request.form.get('model')
    category = request.form.get('category')
    price = request.form.get('price')
    location = request.form.get('location')
    description = request.form.get('description')
    seller_contact = request.form.get('seller_contact')
    created_at = datetime.now().strftime("%d-%m-%Y %H:%M")
    
    if file.filename == '':
        return 'ఫైల్ సెలెక్ట్ చేయలేదు'

    try:
        s3_client.upload_fileobj(
            file,
            S3_BUCKET,
            file.filename,
            ExtraArgs={"ContentType": file.content_type}
        )
        image_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file.filename}"
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO products (title, model, category, price, location, description, image_url, seller_contact, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                       (title, model, category, price, location, description, image_url, seller_contact, created_at))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    except Exception as e:
        return f"ఎర్రర్ వచ్చింది: {str(e)}"

@app.route('/delete_ad/<int:ad_id>')
def delete_ad(ad_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (ad_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('my_ads_page'))

@app.route('/send_otp', methods=['POST'])
def send_otp():
    name = request.form.get('name')
    raw_contact = request.form.get('contact').strip()
    
    if len(raw_contact) == 10:
        contact = "+91" + raw_contact
    else:
        contact = raw_contact if raw_contact.startswith("+") else "+91" + raw_contact

    # 1. సర్వర్ సైడ్ రాండమ్ OTP జనరేట్ చేయడం
    otp_code = str(random.randint(1000, 9999))
    
    # 2. డేటాబేస్‌లో ఈ నంబర్‌కు సంబంధించిన OTP ని భద్రపరచడం (హ్యాక్ కాకుండా సెక్యూరిటీ కోసం)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO otps (contact, otp_code) VALUES (?, ?)', (contact, otp_code))
    conn.commit()
    conn.close()

    # 3. ట్వీలియో ద్వారా వాట్సాప్‌కు మెసేజ్ పంపడం
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=f"హలో {name}! Sell & Buy యాప్ సురక్షితమైన వెరిఫికేషన్ కోడ్ (OTP): *{otp_code}*",
            to=f"whatsapp:{contact}"
        )
    except Exception as e:
        print(f"Twilio ఎర్రర్: {e}")

    resp = redirect(url_for('verify_otp_page'))
    resp.set_cookie('temp_name', name, max_age=300)
    resp.set_cookie('temp_contact', contact, max_age=300)
    return resp

@app.route('/logout')
def logout():
    resp = redirect(url_for('index'))
    resp.delete_cookie('user_contact')
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
