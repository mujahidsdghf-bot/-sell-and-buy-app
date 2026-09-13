from flask import Flask, render_template_string, request, redirect, url_for
import boto3
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sellandbuy_super_secure_cyber_key_2026'

# AWS S3 సెటప్ (మీరు ఇచ్చిన ఒరిజినల్ కీస్)
S3_BUCKET = 'sellandbuy-app-storage'
S3_REGION = 'eu-north-1'

s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id='AKIAXQ7HHUFVKYQCJIGP',
    aws_secret_access_key='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'
)

def init_db():
    conn = sqlite3.connect('database.db')
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
    conn.commit()
    conn.close()

init_db()

@app.after_request
def add_security_headers(response):
    # సైబర్ సెక్యూరిటీ హెడర్స్
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
        cursor.execute('SELECT id, title, model, category, price, location, description, image_url, seller_contact, created_at FROM products WHERE category = ? ORDER BY id DESC', (cat_filter,))
    else:
        cursor.execute('SELECT id, title, model, category, price, location, description, image_url, seller_contact, created_at FROM products ORDER BY id DESC')
    
    products = cursor.fetchall()
    
    cursor.execute('SELECT name, contact, joined_date FROM users LIMIT 1')
    user = cursor.fetchone()
    conn.close()

    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sell & Buy - OLX Style</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; background-color: #f7f8f9; color: #002f34; padding-bottom: 70px; }
            .header { background: #002f34; color: white; padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; }
            .header h2 { margin: 0; font-size: 20px; color: #ffce32; }
            
            .search-container { background: white; padding: 10px 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; gap: 8px; }
            .location-bar, .search-bar { display: flex; gap: 8px; align-items: center; border: 2px solid #002f34; border-radius: 4px; padding: 8px; }
            .location-bar input, .search-bar input { width: 100%; border: none; outline: none; font-size: 14px; }
            
            /* సెర్చ్ బార్ కింద యాడ్ బాక్స్ */
            .top-ad-banner { background: #ffce32; color: #002f34; padding: 10px; text-align: center; font-weight: bold; font-size: 13px; border-bottom: 1px solid #e0b825; }

            .categories { padding: 15px; background: white; margin-top: 5px; }
            .categories h3 { font-size: 16px; margin-bottom: 10px; }
            .cat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; text-align: center; }
            .cat-item { background: #ebeeef; padding: 12px 5px; border-radius: 8px; font-size: 12px; font-weight: bold; cursor: pointer; text-decoration: none; color: #002f34; display: block; }
            .cat-item:hover { background: #002f34; color: white; }
            
            .section-title { padding: 15px 15px 5px 15px; font-size: 16px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; }
            
            /* పెద్ద ఫోటోలతో కూడిన ప్రొడక్ట్ గ్రిడ్ */
            .product-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 10px 15px; }
            .product-card { background: white; border: 1px solid #ebeeef; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); cursor: pointer; }
            .product-card img { width: 100%; height: 150px; object-fit: cover; }
            .product-info { padding: 10px; }
            .price { font-size: 18px; font-weight: bold; color: #002f34; margin: 4px 0; }
            .title { font-size: 14px; color: #333; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .loc { font-size: 11px; color: #777; margin-top: 3px; }

            .ad-banner-box { grid-column: span 2; background: #002f34; color: #ffce32; padding: 15px; text-align: center; font-weight: bold; border-radius: 6px; margin: 5px 0; border: 1px dashed #ffce32; }

            .bottom-nav { position: fixed; bottom: 0; width: 100%; background: white; display: flex; justify-content: space-around; padding: 8px 0; border-top: 1px solid #ddd; box-shadow: 0 -2px 5px rgba(0,0,0,0.05); z-index: 99; }
            .nav-item { text-align: center; font-size: 11px; color: #555; text-decoration: none; cursor: pointer; }
            .sell-btn-nav { background: #ffce32; border-radius: 50%; width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 24px; margin-top: -15px; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.2); color: #002f34; }

            .modal { display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); overflow-y: auto; }
            .modal-content { background: white; margin: 8% auto; padding: 20px; width: 85%; max-width: 400px; border-radius: 8px; position: relative; }
            .close { float: right; font-size: 22px; cursor: pointer; font-weight: bold; color: #333; }
            .modal input, .modal select, .modal textarea { width: 100%; padding: 8px; margin: 5px 0 10px 0; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
            .modal button { background: #002f34; color: white; border: none; padding: 10px; width: 100%; border-radius: 4px; font-weight: bold; cursor: pointer; margin-top: 5px; }
        </style>
    </head>
    <body>

        <div class="header">
            <h2>Sell & Buy</h2>
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

        <!-- సెర్చ్ బార్ కింద యాడ్ బాక్స్ -->
        <div class="top-ad-banner">
            🚀 ప్రత్యేక ప్రకటన: మీ పాత వస్తువులను ఇక్కడ ఉచితంగా అమ్ముకోండి!
        </div>

        <!-- కేటగిరీలు -->
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
                    <div class="product-card" onclick="openDetails('{{ p[1] }}', '{{ p[2] }}', '{{ p[4] }}', '{{ p[5] }}', '{{ p[6] }}', '{{ p[7] }}', '{{ p[8] }}')">
                        <img src="{{ p[7] }}" alt="Item">
                        <div class="product-info">
                            <div class="price">₹ {{ p[4] }}</div>
                            <div class="title">{{ p[1] }} ({{ p[2] }})</div>
                            <div class="loc">📍 {{ p[5] }}</div>
                        </div>
                    </div>

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
            <a href="#" onclick="openModal('adsModal')" class="nav-item">📋<br>My Ads</a>
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
                    <input type="text" name="seller_contact" required placeholder="Mobile Number">
                    
                    <button type="submit">పోస్ట్ చేయండి</button>
                </form>
            </div>
        </div>

        <!-- Product Details Modal (మ్యాప్స్ మరియు పెద్ద ఫోటోతో సహా) -->
        <div id="detailsModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('detailsModal')">&times;</span>
                <img id="detImg" src="" style="width: 100%; height: 200px; object-fit: cover; border-radius: 6px;">
                <h3 id="detTitle" style="margin: 10px 0 5px 0;"></h3>
                <p><b>మోడల్:</b> <span id="detModel"></span></p>
                <p><b>ధర:</b> ₹ <span id="detPrice" style="color: green; font-weight: bold; font-size: 16px;"></span></p>
                <p><b>లొకేషన్:</b> 📍 <span id="detLoc"></span></p>
                
                <!-- గూగుల్ మ్యాప్ లొకేషన్ బాక్స్ -->
                <div style="width: 100%; height: 110px; margin: 8px 0; border-radius: 4px; overflow: hidden; border: 1px solid #ccc;">
                    <iframe id="mapFrame" width="100%" height="110" style="border:0;" loading="lazy" src=""></iframe>
                </div>

                <p><b>వివరాలు:</b> <span id="detDesc"></span></p>
                <hr>
                <div style="display: flex; gap: 10px;">
                    <button onclick="makeCall()" style="background: #28a745;">📞 Call (4 Free)</button>
                    <button onclick="openChatBox()" style="background: #007bff;">💬 Chat (Free)</button>
                </div>
            </div>
        </div>

        <!-- Chat Box Modal -->
        <div id="chatBoxModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('chatBoxModal')">&times;</span>
                <h3>Live Chat with Seller</h3>
                <div style="height: 150px; border: 1px solid #ddd; padding: 8px; overflow-y: auto; background: #fafafa; font-size: 13px;" id="chatMessages">
                    <p style="color: #888;">చాటింగ్ ప్రారంభించండి...</p>
                </div>
                <input type="text" id="chatInput" placeholder="సందేశం రాయండి...">
                <button onclick="sendChatMessage()">సందేశం పంపు (Send)</button>
            </div>
        </div>

        <!-- Chats Modal -->
        <div id="chatModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('chatModal')">&times;</span>
                <h3>Chats & Notifications</h3>
                <p style="color: #666; font-size: 14px;">🔔 చాట్ నోటిఫికేషన్‌లు మరియు మెసేజ్‌లు ఇక్కడ కనిపిస్తాయి.</p>
            </div>
        </div>

        <!-- My Ads Modal -->
        <div id="adsModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('adsModal')">&times;</span>
                <h3>My Ads</h3>
                <p style="color: #666; font-size: 14px;">మీరు పోస్ట్ చేసిన ప్రకటనలు మరియు హిస్టరీ ఇక్కడ ఉంటుంది.</p>
            </div>
        </div>

        <!-- Account Modal (WhatsApp OTP Login) -->
        <div id="accountModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('accountModal')">&times;</span>
                <h3>Customer Profile & Account</h3>
                {% if user %}
                    <div style="text-align: center; margin-bottom: 15px;">
                        <div style="font-size: 50px;">👤</div>
                        <h4 style="margin: 5px 0;">{{ user[0] }}</h4>
                        <p style="font-size: 12px; color: #666; margin: 0;">📱/✉️ {{ user[1] }}</p>
                        <p style="font-size: 11px; color: #888; margin-top: 5px;">జాయిన్ అయిన తేదీ: {{ user[2] }}</p>
                    </div>
                    <button style="background: #d9534f;" onclick="location.href='/logout'">లాగౌట్ (Logout)</button>
                {% else %}
                    <form action="/send_otp" method="POST">
                        <h4 style="margin-top: 0;">WhatsApp OTP / Email లాగిన్</h4>
                        <label style="font-size: 12px;">పేరు (Name):</label>
                        <input type="text" name="name" required>
                        
                        <label style="font-size: 12px;">WhatsApp నంబర్ లేదా Email:</label>
                        <input type="text" name="contact" required placeholder="Mobile / Email">
                        
                        <button type="submit">WhatsApp కి OTP పంపు</button>
                    </form>
                {% endif %}
            </div>
        </div>

        <script>
            let callCount = 0;
            let sellerPhone = "";

            function openModal(id) { document.getElementById(id).style.display = 'block'; }
            function closeModal(id) { document.getElementById(id).style.display = 'none'; }
            
            function openDetails(title, model, price, loc, desc, img, contact) {
                document.getElementById('detTitle').innerText = title;
                document.getElementById('detModel').innerText = model;
                document.getElementById('detPrice').innerText = price;
                document.getElementById('detLoc').innerText = loc;
                document.getElementById('detDesc').innerText = desc;
                document.getElementById('detImg').src = img;
                sellerPhone = contact;
                
                // గూగుల్ మ్యాప్స్‌లో లొకేషన్ లోడ్ చేయడం
                let mapSrc = "https://maps.google.com/maps?q=" + encodeURIComponent(loc) + "&t=&z=13&ie=UTF8&iwloc=&output=embed";
                document.getElementById('mapFrame').src = mapSrc;

                document.getElementById('detailsModal').style.display = 'block';
            }

            function makeCall() {
                callCount++;
                if (callCount <= 4) {
                    alert("ఫ్రీ కాల్స్ మిగిలి ఉన్నాయి (" + callCount + "/4). డైరెక్ట్ నెంబర్: " + sellerPhone);
                } else {
                    alert("మీ 4 ఫ్రీ కాల్స్ పూర్తయ్యాయి! ఛార్జ్ వర్తిస్తుంది.");
                    window.location.href = "tel:" + sellerPhone;
                }
            }

            function openChatBox() {
                closeModal('detailsModal');
                document.getElementById('chatBoxModal').style.display = 'block';
            }

            function sendChatMessage() {
                let msg = document.getElementById('chatInput').value;
                if(msg.trim() !== "") {
                    let chatDiv = document.getElementById('chatMessages');
                    chatDiv.innerHTML += "<p><b>మీరు:</b> " + msg + "</p>";
                    document.getElementById('chatInput').value = "";
                    alert("మెసేజ్ పంపబడింది మరియు అమ్మకందారునికి నోటిఫికేషన్ వెళ్ళింది!");
                }
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_content, products=products, user=user)

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
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    
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

@app.route('/send_otp', methods=['POST'])
def send_otp():
    name = request.form.get('name')
    contact = request.form.get('contact')
    joined_date = datetime.now().strftime("%d-%m-%Y")
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (name, contact, joined_date) VALUES (?, ?, ?)', (name, contact, joined_date))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users')
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
