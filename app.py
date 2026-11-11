from datetime import datetime
import email.message
import random
import smtplib
from flask import Flask, redirect, render_template_string, request, url_for
import sqlite3
import boto3

app = Flask(__name__)
app.secret_key = 'sellandbuy_advanced_secure_key_2026'

# మీ జీమెయిల్ వివరాలు ఇక్కడ ఇవ్వండి
SENDER_EMAIL = 'mujahidsdghf@gmail.com'
SENDER_PASSWORD = 'wnvl ywns eery wvrs'

S3_BUCKET = 'sellandbuy-app-storage'
S3_REGION = 'eu-north-1'

s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id='AKIAXQ7HHUFVKYQCJIGP',
    aws_secret_access_key='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',
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
  return response


@app.route('/')
def index():
  cat_filter = request.args.get('category')
  conn = sqlite3.connect('database.db')
  cursor = conn.cursor()

  if cat_filter:
    cursor.execute(
        'SELECT id, title, model, category, price, location, description,'
        ' image_url, seller_contact, created_at FROM products WHERE category = ?'
        ' ORDER BY id DESC',
        (cat_filter,),
    )
  else:
    cursor.execute(
        'SELECT id, title, model, category, price, location, description,'
        ' image_url, seller_contact, created_at FROM products ORDER BY id DESC'
    )

  products = cursor.fetchall()

  user_contact = request.cookies.get('user_contact')
  user = None

  if user_contact:
    cursor.execute(
        'SELECT name, contact, joined_date FROM users WHERE contact = ? LIMIT'
        ' 1',
        (user_contact,),
    )
    user = cursor.fetchone()

  conn.close()

  html_content = """
    <!DOCTYPE html>
    <html lang="te">
    <head>
        <meta charset="UTF-8">
        <title>Sell & Buy Store - Advanced Marketplace</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            :root { --primary: #002f34; --accent: #ffce32; --bg: #f4f6f8; --text: #222; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background-color: var(--bg); color: var(--text); padding-bottom: 80px; }
            .header { background: var(--primary); color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .logo-text { font-size: 22px; font-weight: bold; background: linear-gradient(45deg, #ffce32, #ff5722, #00e676); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .search-container { background: white; padding: 12px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); display: flex; flex-direction: column; gap: 10px; }
            .search-bar { display: flex; gap: 10px; align-items: center; border: 2px solid var(--primary); border-radius: 6px; padding: 8px 12px; background: #fff; }
            .search-bar input { width: 100%; border: none; outline: none; font-size: 15px; }
            .top-ad-banner { background: var(--accent); color: var(--primary); padding: 12px; text-align: center; font-weight: bold; font-size: 14px; border-bottom: 1px solid #e0b825; }
            .categories { padding: 15px 20px; background: white; margin-top: 8px; }
            .categories h3 { font-size: 16px; margin-bottom: 12px; color: var(--primary); }
            .cat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; text-align: center; }
            .cat-item { background: #f1f3f5; padding: 14px 6px; border-radius: 10px; font-size: 12px; font-weight: bold; cursor: pointer; text-decoration: none; color: var(--primary); transition: 0.2s; }
            .cat-item:hover { background: var(--primary); color: white; transform: translateY(-2px); }
            .section-title { padding: 20px 20px 10px 20px; font-size: 18px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; color: var(--primary); }
            .product-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; padding: 0 15px; }
            .product-card { background: white; border: 1px solid #e5e8eb; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.04); cursor: pointer; text-decoration: none; color: inherit; display: block; transition: 0.2s; }
            .product-card:hover { transform: translateY(-3px); box-shadow: 0 6px 15px rgba(0,0,0,0.1); }
            .product-card img { width: 100%; height: 160px; object-fit: cover; background: #eee; }
            .product-info { padding: 12px; }
            .price { font-size: 19px; font-weight: bold; color: var(--primary); margin: 4px 0; }
            .title { font-size: 14px; color: #444; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .loc { font-size: 12px; color: #777; margin-top: 4px; }
            
            /* AI Voice Assistant Floating Button */
            .ai-voice-btn { position: fixed; bottom: 85px; right: 20px; background: linear-gradient(45deg, #ff416c, #ff4b2b); color: white; border-radius: 50px; padding: 12px 20px; font-weight: bold; box-shadow: 0 4px 15px rgba(255,65,108,0.4); cursor: pointer; display: flex; align-items: center; gap: 8px; z-index: 98; font-size: 14px; border: 2px solid white; animation: pulse 2s infinite; }
            @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }

            .bottom-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #ddd; box-shadow: 0 -4px 10px rgba(0,0,0,0.05); z-index: 99; }
            .nav-item { text-align: center; font-size: 11px; color: #555; text-decoration: none; cursor: pointer; font-weight: 600; }
            .sell-btn-nav { background: var(--accent); border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 26px; margin-top: -18px; border: 3px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.2); color: var(--primary); }
            
            .modal { display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); backdrop-filter: blur(3px); overflow-y: auto; }
            .modal-content { background: white; margin: 8% auto; padding: 25px; width: 90%; max-width: 420px; border-radius: 14px; position: relative; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
            .close { float: right; font-size: 24px; cursor: pointer; font-weight: bold; color: #666; }
            .modal input, .modal select, .modal textarea { width: 100%; padding: 10px 12px; margin: 8px 0 14px 0; box-sizing: border-box; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; outline: none; }
            .modal input:focus, .modal select:focus { border-color: var(--primary); }
            .modal button { background: var(--primary); color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 15px; margin-top: 5px; }
        </style>
    </head>
    <body>

        <div class="header">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 22px;">⚡</span>
                <div class="logo-text">Sell & Buy Store</div>
            </div>
            <span style="font-size: 13px; background: rgba(255,255,255,0.15); padding: 5px 10px; border-radius: 20px;">📍 Hyderabad</span>
        </div>

        <div class="search-container">
            <div class="search-bar">
                <span>🔍</span>
                <input type="text" placeholder="కార్లు, మొబైల్స్, బైకులు మరియు ఇతర వస్తువుల కోసం వెతకండి...">
            </div>
        </div>

        <div class="top-ad-banner">
            🚀 ప్రత్యేక ఆఫర్: మీ పాత వస్తువులను ఇక్కడ ఉచితంగా అమ్ముకోండి!
        </div>

        <div class="categories">
            <h3>వస్తువుల కేటగిరీలు (Categories)</h3>
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
            <span>తాజా ప్రకటనలు (Fresh Recommendations)</span>
            <a href="/" style="font-size: 13px; color: var(--primary); text-decoration: none;">అన్నీ చూడండి</a>
        </div>

        <div class="product-grid">
            {% if products %}
                {% for p in products %}
                    <a href="/product/{{ p[0] }}" class="product-card">
                        <img src="{{ p[7] }}" alt="Item" onerror="this.src='https://via.placeholder.com/300x160?text=Image+Loading';">
                        <div class="product-info">
                            <div class="price">₹ {{ p[4] }}</div>
                            <div class="title">{{ p[1] }} ({{ p[2] }})</div>
                            <div class="loc">📍 {{ p[5] }}</div>
                        </div>
                    </a>
                {% endfor %}
            {% else %}
                <div style="padding: 30px; text-align: center; color: #777; grid-column: span 2;">
                    <p style="font-size: 16px; font-weight: bold;">ఈ కేటగిరీలో ఇంకా ఎలాంటి వస్తువులు లేవు!</p>
                    <a href="/" style="color: var(--primary); text-decoration: underline;">అన్ని వస్తువులను చూడండి</a>
                </div>
            {% endif %}
        </div>

        <!-- AI Voice Assistant Floating Button -->
        <div class="ai-voice-btn" onclick="openModal('aiVoiceModal')">
            🎙️ AI Voice Help (తెలుగు / हिंदी / English)
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
                <h3 style="color: var(--primary); margin-top:0;">కొత్త ప్రకటన పోస్ట్ చేయండి (Post Ad)</h3>
                <form action="/upload" method="POST" enctype="multipart/form-data">
                    <label style="font-size: 13px; font-weight: bold;">వస్తువు పేరు:</label>
                    <input type="text" name="title" required placeholder="ఉదా: Hero Splendor Bike">
                    
                    <label style="font-size: 13px; font-weight: bold;">మోడల్ (Model):</label>
                    <input type="text" name="model" required placeholder="ఉదా: 2021 Model">

                    <label style="font-size: 13px; font-weight: bold;">కేటగిరీ:</label>
                    <select name="category">
                        <option value="Bikes">Bikes</option>
                        <option value="Cars">Cars</option>
                        <option value="Mobiles">Mobiles</option>
                        <option value="Properties">Properties</option>
                        <option value="Electronics">Electronics</option>
                        <option value="Furniture">Furniture</option>
                        <option value="Others">Others</option>
                    </select>

                    <label style="font-size: 13px; font-weight: bold;">ధర (Rs):</label>
                    <input type="text" name="price" required placeholder="ఉదా: 45000">

                    <label style="font-size: 13px; font-weight: bold;">లొకేషన్:</label>
                    <input type="text" name="location" required placeholder="ఉదా: Suraram, Hyderabad">

                    <label style="font-size: 13px; font-weight: bold;">వివరాలు (Description):</label>
                    <textarea name="description" rows="3" placeholder="వస్తువు కండిషన్ రాయండి..."></textarea>
                    
                    <label style="font-size: 13px; font-weight: bold;">ఫోటో అప్‌లోడ్:</label>
                    <input type="file" name="file" required style="border:none; padding: 0;">

                    <label style="font-size: 13px; font-weight: bold;">మొబైల్ నంబర్ / కాంటాక్ట్:</label>
                    <input type="text" name="seller_contact" value="{{ user[1] if user else '' }}" required placeholder="Contact number">
                    
                    <button type="submit">ప్రకటన లైవ్ చేయండి</button>
                </form>
            </div>
        </div>

        <!-- AI Voice Assistant Modal -->
        <div id="aiVoiceModal" class="modal">
            <div class="modal-content" style="text-align: center;">
                <span class="close" onclick="closeModal('aiVoiceModal')">&times;</span>
                <h3 style="color: var(--primary);">🤖 AI Voice Assistant</h3>
                <p style="font-size: 13px; color: #666;">మీకు ఏ భాషలో సహాయం కావాలి? (Select Language)</p>
                
                <div style="display: flex; gap: 10px; justify-content: center; margin: 15px 0;">
                    <button onclick="speakVoice('telugu')" style="background: #28a745; width: auto; padding: 8px 12px; font-size: 12px;">తెలుగు 🇮🇳</button>
                    <button onclick="speakVoice('hindi')" style="background: #ffc107; color: #000; width: auto; padding: 8px 12px; font-size: 12px;">हिंदी 🇮🇳</button>
                    <button onclick="speakVoice('english')" style="background: #007bff; width: auto; padding: 8px 12px; font-size: 12px;">English 🌐</button>
                </div>

                <div id="voiceStatusBox" style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 15px; font-size: 14px; border: 1px dashed #ccc;">
                    భాషను ఎంచుకోండి, AI వాయిస్ ఏజెంట్ మాట్లాడటం ప్రారంభిస్తుంది.
                </div>
            </div>
        </div>

        <!-- Account Modal -->
        <div id="accountModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('accountModal')">&times;</span>
                <h3>Customer Account & Profile</h3>
                {% if user %}
                    <div style="text-align: center; margin-bottom: 15px;">
                        <div style="font-size: 50px;">👤</div>
                        <h4 style="margin: 5px 0;">{{ user[0] }}</h4>
                        <p style="font-size: 12px; color: #666; margin: 0;">📧 {{ user[1] }}</p>
                        <p style="font-size: 11px; color: #888; margin-top: 5px;">జాయిన్ అయిన తేదీ: {{ user[2] }}</p>
                    </div>
                    <div style="background: #e8f5e9; color: #2e7d32; padding: 10px; border-radius: 6px; margin-bottom: 12px; font-size: 13px; text-align: center;">
                        <b>Email OTP Verified & Secured ✅</b>
                    </div>
                    <button style="background: #d9534f;" onclick="location.href='/logout'">లాగౌట్ (Logout)</button>
                {% else %}
                    <form action="/send_otp" method="POST">
                        <h4 style="margin-top: 0; color: var(--primary);">📧 Email OTP లాగిన్ / రిజిస్ట్రేషన్</h4>
                        <label style="font-size: 13px;">మీ పేరు (Name):</label>
                        <input type="text" name="name" required placeholder="మీ పూర్తి పేరు">
                        
                        <label style="font-size: 13px;">ఈమెయిల్ అడ్రస్ (Email):</label>
                        <input type="email" name="contact" required placeholder="yourname@gmail.com">
                        
                        <button type="submit" style="background: var(--primary); color: white; font-weight: bold;">ఈమెయిల్‌కు OTP పంపు</button>
                    </form>
                {% endif %}
            </div>
        </div>

        <!-- Chats Modal -->
        <div id="chatModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('chatModal')">&times;</span>
                <h3>Live Chat with Seller</h3>
                <div style="height: 160px; border: 1px solid #ddd; padding: 10px; overflow-y: auto; background: #fafafa; font-size: 13px; border-radius: 6px;" id="chatMessages">
                    <p style="color: #888;">చాటింగ్ ప్రారంభించండి...</p>
                </div>
                <input type="text" id="chatInput" placeholder="సందేశం రాయండి...">
                <button onclick="sendChatMessage()">సందేశం పంపు (Send)</button>
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
                    chatDiv.scrollTop = chatDiv.scrollHeight;
                }
            }

            function speakVoice(lang) {
                let text = "";
                let box = document.getElementById('voiceStatusBox');
                let synth = window.speechSynthesis;
                
                if(lang === 'telugu') {
                    text = "నమస్కారం! Sell & Buy స్టోర్‌కు స్వాగతం. మీరు ఇక్కడ మీ పాత వస్తువులను సులభంగా అమ్ముకోవచ్చు మరియు కొనుగోలు చేయవచ్చు.";
                    box.innerHTML = "<b>తెలుగు AI:</b> " + text;
                } else if(lang === 'hindi') {
                    text = "नमस्ते! Sell & Buy स्टोर में आपका स्वागत है। आप यहाँ अपने पुराने सामान आसानी से खरीद और बेच सकते हैं।";
                    box.innerHTML = "<b>हिंदी AI:</b> " + text;
                } else {
                    text = "Hello and welcome to Sell and Buy store. You can easily buy and sell pre-owned items here.";
                    box.innerHTML = "<b>English AI:</b> " + text;
                }

                let utterThis = new SpeechSynthesisUtterance(text);
                synth.speak(utterThis);
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
    <html lang="te">
    <head>
        <meta charset="UTF-8">
        <title>OTP Verification - Sell & Buy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #f4f6f8; color: #002f34; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .box { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.08); width: 90%; max-width: 360px; text-align: center; }
            input { width: 100%; padding: 12px; margin: 15px 0; font-size: 24px; text-align: center; letter-spacing: 8px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; outline: none; }
            input:focus { border-color: #002f34; }
            button { background: #002f34; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-weight: bold; font-size: 16px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="box">
            <h3 style="color: #002f34; margin-top: 0;">ఈమెయిల్ OTP వెరిఫికేషన్</h3>
            <p style="font-size: 13px; color: #666;">మీ ఈమెయిల్‌కు పంపబడిన 4 అంకెల కోడ్‌ని ఇక్కడ ఎంటర్ చేయండి.</p>
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

  conn = sqlite3.connect('database.db')
  cursor = conn.cursor()
  cursor.execute('SELECT otp_code FROM otps WHERE contact = ?', (contact,))
  row = cursor.fetchone()

  if row and row[0] == entered_otp:
    joined_date = datetime.now().strftime('%d-%m-%Y')
    cursor.execute(
        'INSERT OR IGNORE INTO users (name, contact, joined_date) VALUES (?, ?,'
        ' ?)',
        (name, contact, joined_date),
    )
    cursor.execute('DELETE FROM otps WHERE contact = ?', (contact,))
    conn.commit()
    conn.close()

    resp = redirect(url_for('index'))
    resp.set_cookie('user_contact', contact, max_age=60 * 60 * 24 * 30)
    return resp
  else:
    conn.close()
    return (
        "<script>alert('తప్పు OTP లేదా కాలం చెల్లిన కోడ్! దయచేసి మళ్లీ"
        " ప్రయత్నించండి.'); window.location.href='/';</script>"
    )


@app.route('/my_ads')
def my_ads_page():
  conn = sqlite3.connect('database.db')
  cursor = conn.cursor()
  cursor.execute(
      'SELECT id, title, model, category, price, location, description,'
      ' image_url, seller_contact, created_at FROM products ORDER BY id DESC'
  )
  ads = cursor.fetchall()
  conn.close()

  ads_html = """
    <!DOCTYPE html>
    <html lang="te">
    <head>
        <meta charset="UTF-8">
        <title>My Ads - Sell & Buy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; background-color: #f4f6f8; color: #002f34; }
            .header { background: #002f34; color: white; padding: 15px 20px; display: flex; align-items: center; gap: 15px; }
            .header a { color: #ffce32; text-decoration: none; font-size: 20px; }
            .container { padding: 20px; max-width: 600px; margin: auto; background: white; min-height: 100vh; box-sizing: border-box; }
            .ad-item { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e5e8eb; padding: 12px 0; }
            .ad-info { display: flex; gap: 14px; align-items: center; }
            .ad-info img { width: 55px; height: 55px; object-fit: cover; border-radius: 8px; background: #eee; }
            .delete-btn { background: #d9534f; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <a href="/">←</a>
            <h2 style="margin:0; font-size: 18px;">నా ప్రకటనలు (My Ads & Management)</h2>
        </div>

        <div class="container">
            <h3>మీరు పోస్ట్ చేసిన ప్రకటనలు:</h3>
    """

  if ads:
    for ad in ads:
      ads_html += f"""
            <div class="ad-item">
                <div class="ad-info">
                    <img src="{ad[7]}" onerror="this.src='https://via.placeholder.com/55x55?text=Img';">
                    <div>
                        <b>{ad[1]}</b><br>
                        <span style="font-size: 13px; color: #2e7d32; font-weight: bold;">₹ {ad[4]}</span><br>
                        <span style="font-size: 11px; color: #777;">Posted on: {ad[9]}</span>
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
  cursor.execute(
      'SELECT id, title, model, category, price, location, description,'
      ' image_url, seller_contact, created_at FROM products WHERE id = ?',
      (product_id,),
  )
  p = cursor.fetchone()
  conn.close()

  if not p:
    return 'ప్రొడక్ట్ కనుగొనబడలేదు!', 404

  detail_html = f"""
    <!DOCTYPE html>
    <html lang="te">
    <head>
        <meta charset="UTF-8">
        <title>{p[1]} - Sell & Buy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; background-color: #f4f6f8; color: #002f34; }}
            .header {{ background: #002f34; color: white; padding: 15px 20px; display: flex; align-items: center; gap: 15px; }}
            .header a {{ color: #ffce32; text-decoration: none; font-size: 20px; }}
            .container {{ padding: 20px; max-width: 600px; margin: auto; background: white; min-height: 100vh; box-sizing: border-box; }}
            .prod-img {{ width: 100%; height: 300px; object-fit: cover; border-radius: 10px; background: #eee; }}
            .price {{ font-size: 26px; font-weight: bold; color: #002f34; margin: 12px 0; }}
            .title {{ font-size: 22px; font-weight: bold; margin: 5px 0; }}
            .details-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 18px 0; border: 1px solid #e5e8eb; }}
            .action-btns {{ display: flex; gap: 12px; margin-top: 25px; }}
            .action-btns a {{ flex: 1; padding: 14px; border-radius: 8px; font-weight: bold; color: white; font-size: 15px; text-align: center; text-decoration: none; display: block; }}
        </style>
    </head>
    <body>
        <div class="header">
            <a href="/">←</a>
            <h2 style="margin:0; font-size: 18px;">ప్రొడక్ట్ వివరాలు</h2>
        </div>

        <div class="container">
            <img src="{p[7]}" class="prod-img" onerror="this.src='https://via.placeholder.com/400x300?text=No+Image';">
            <div class="price">₹ {p[4]}</div>
            <div class="title">{p[1]}</div>
            
            <div class="details-box">
                <p><b>మోడల్:</b> {p[2]}</p>
                <p><b>కేటగిరీ:</b> {p[3]}</p>
                <p><b>లొకేషన్ & టైమ్:</b> 📍 {p[5]} &nbsp;|&nbsp; 🕒 {p[9]}</p>
                <p><b>వివరాలు:</b> {p[6]}</p>
            </div>

            <div style="width: 100%; height: 180px; margin: 15px 0; border-radius: 8px; overflow: hidden; border: 1px solid #ccc;">
                <iframe width="100%" height="180" style="border:0;" loading="lazy" src="https://maps.google.com/maps?q={p[5]}&t=&z=13&ie=UTF8&iwloc=&output=embed"></iframe>
            </div>

            <div class="action-btns">
                <a href="tel:{p[8]}" style="background: #28a745;">📞 డైరెక్ట్ కాల్</a>
                <a href="#" onclick="alert('చాట్ బాక్స్ ఓపెన్ అయింది!');" style="background: #007bff;">💬 చాట్ చేయండి</a>
            </div>
        </div>
    </body>
    </html>
    """
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
  created_at = datetime.now().strftime('%d-%m-%Y %H:%M')

  if file.filename == '':
    return 'ఫైల్ సెలెక్ట్ చేయలేదు'

  try:
    s3_client.upload_fileobj(
        file, S3_BUCKET, file.filename, ExtraArgs={'ContentType': file.content_type}
    )
    image_url = (
        f'https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file.filename}'
    )

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO products (title, model, category, price, location,'
        ' description, image_url, seller_contact, created_at) VALUES (?, ?, ?,'
        ' ?, ?, ?, ?, ?, ?)',
        (
            title,
            model,
            category,
            price,
            location,
            description,
            image_url,
            seller_contact,
            created_at,
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for('index'))
  except Exception as e:
    return f'ఎర్రర్ వచ్చింది: {str(e)}'


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
  email = request.form.get('contact').strip()

  otp_code = str(random.randint(1000, 9999))

  conn = sqlite3.connect('database.db')
  cursor = conn.cursor()
  cursor.execute(
      'INSERT OR REPLACE INTO otps (contact, otp_code) VALUES (?, ?)',
      (email, otp_code),
  )
  conn.commit()
  conn.close()

  try:
    msg = email.message.EmailMessage()
    msg.set_content(
        f'హలో {name},\n\nమీ Sell & Buy Store వెరిఫికేషన్ కోడ్ (OTP):'
        f' {otp_code}\n\nధన్యవాదాలు!'
    )
    msg['Subject'] = 'Sell & Buy Store - Login OTP Code'
    msg['From'] = SENDER_EMAIL
    msg['To'] = email

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()
  except Exception as e:
    print(f'Email Error: {e}')

  resp = redirect(url_for('verify_otp_page'))
  resp.set_cookie('temp_name', name, max_age=300)
  resp.set_cookie('temp_contact', email, max_age=300)
  return resp


@app.route('/logout')
def logout():
  resp = redirect(url_for('index'))
  resp.delete_cookie('user_contact')
  return resp


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8000, debug=True)
