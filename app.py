import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "sellandbuy_super_secret_key_2026"

# SQLite డేటాబేస్ సెటప్
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sellandbuy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ప్రొఫైల్ పిక్చర్స్ అప్‌లోడ్ ఫోల్డర్
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# Brevo API Key (Render Environment Variable నుంచి)
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL = "mujahidsdghf@gmail.com"

# --- డేటాబేస్ టేబుల్స్ (Models) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default="Customer")
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    profile_pic = db.Column(db.String(255), default="default.png")
    referral_code = db.Column(db.String(20), unique=True)
    referred_by = db.Column(db.String(20), nullable=True)
    is_premium = db.Column(db.Boolean, default=False)
    free_ads_count = db.Column(db.Integer, default=2)  # మొదటి 2 యాడ్స్ ఫ్రీ
    free_chats_count = db.Column(db.Integer, default=5) # మొదటి 5 చాట్లు ఫ్రీ
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(100), default="Suraram, Hyderabad")
    image_url = db.Column(db.String(255), default="default_item.jpg")
    user_email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default="Active") # Active, Sold, Expired, Deleted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    sender_email = db.Column(db.String(120), nullable=False)
    receiver_email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    # అడ్మిన్ ఈమెయిల్ సెట్ చేయడం
    admin_user = User.query.filter_by(email="mujahidsdghf@gmail.com").first()
    if not admin_user:
        admin = User(name="Syed Mujahid", email="mujahidsdghf@gmail.com", is_admin=True, referral_code="MUJAHIDADMIN")
        db.session.add(admin)
        db.session.commit()

# --- 1. హోమ్ పేజీ & కేటగిరీలు ---
@app.route('/')
def home():
    category = request.args.get('category')
    search_query = request.args.get('q')
    
    query = Product.query.filter_by(status="Active")
    if category:
        query = query.filter_by(category=category)
    if search_query:
        query = query.filter(Product.title.ilike(f"%{search_query}%"))
        
    products = query.order_by(Product.id.desc()).all()
    return render_template('home.html', products=products)

# --- Brevo OTP ఫంక్షన్ ---
def send_otp_via_brevo(to_email, otp_code):
    if not BREVO_API_KEY:
        return True 
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {"accept": "application/json", "api-key": BREVO_API_KEY, "content-type": "application/json"}
    payload = {
        "sender": {"name": "Sell & Buy Store", "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": "Sell & Buy Store - Login OTP Code",
        "htmlContent": f"<p>హలో,</p><p>మీ Sell & Buy Store వెరిఫికేషన్ కోడ్ (OTP): <b>{otp_code}</b></p><p>ధన్యవాదాలు!</p>"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code == 201
    except Exception as e:
        print(f"Brevo API Error: {e}")
        return False

# --- లాగిన్ & OTP రూట్స్ (2FA Security) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        ref_code_input = request.form.get('ref_code')
        otp = str(random.randint(1000, 9999))
        session['pending_email'] = email
        session['saved_otp'] = otp
        session['pending_ref'] = ref_code_input
        
        success = send_otp_via_brevo(email, otp)
        if success:
            return redirect(url_for('verify_otp'))
        else:
            return "Brevo API Error: Could not send OTP."
    return render_template('login.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        if user_otp == session.get('saved_otp'):
            email = session.get('pending_email')
            ref_code_input = session.get('pending_ref')
            session['user_email'] = email
            
            user = User.query.filter_by(email=email).first()
            if not user:
                new_ref = f"REF{random.randint(10000,99999)}"
                new_user = User(name="Customer", email=email, referral_code=new_ref, referred_by=ref_code_input)
                db.session.add(new_user)
                db.session.commit()
                
            return redirect(url_for('home'))
        else:
            return "Invalid OTP. Please try again."
    return render_template('verify_otp.html')

# --- 2. ప్రొడక్ట్ డీటెయిల్స్ పేజీ ---
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        return "Product not found", 404
        
    return render_template('product_detail.html', product=product)

# --- 3. యాడ్ పోస్ట్ చేయడం & సబ్‌స్క్రిప్షన్ లిమిట్ చెక్ ---
@app.route('/post-ad', methods=['GET', 'POST'])
def post_ad():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(email=session['user_email']).first()
    
    if request.method == 'POST':
        if user.free_ads_count <= 0 and not user.is_premium:
            return redirect(url_for('subscription'))
            
        title = request.form.get('title')
        category = request.form.get('category')
        price = float(request.form.get('price', 0))
        description = request.form.get('description')
        location = request.form.get('location', 'Suraram, Hyderabad')
        
        new_product = Product(title=title, category=category, price=price, description=description, location=location, user_email=user.email)
        db.session.add(new_product)
        
        if user.free_ads_count > 0:
            user.free_ads_count -= 1
            
        db.session.commit()
        return redirect(url_for('my_ads'))
        
    return render_template('post_ad.html', user=user)

# --- సబ్‌స్క్రిప్షన్ పేజీ (₹100/mo లేదా ₹599/yr) ---
@app.route('/subscription')
def subscription():
    return render_template('subscription.html')

# --- 4. మై యాడ్స్ పేజీ & మేనేజ్‌మెంట్ ---
@app.route('/my-ads')
def my_ads():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user_email = session['user_email']
    products = Product.query.filter_by(user_email=user_email).all()
    return render_template('my_ads.html', products=products)

@app.route('/update-ad/<int:ad_id>/<status>')
def update_ad(ad_id, status):
    if 'user_email' not in session:
        return redirect(url_for('login'))
    product = Product.query.get_or_404(ad_id)
    if product.user_email == session['user_email']:
        product.status = status # Active, Sold, Deleted
        db.session.commit()
    return redirect(url_for('my_ads'))

@app.route('/chats-list')
def chats_list():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    return render_template('chats.html')
    
    user = User.query.filter_by(email=session['user_email']).first()
    product = Product.query.get_or_404(product_id)
    
    if user.free_chats_count <= 0 and not user.is_premium:
        return render_template('subscription.html', message="మీ ఉచిత చాట్లు ముగిశాయి. అన్లిమిటెడ్ చాట్స్ కోసం సబ్‌స్క్రిప్షన్ తీసుకోండి.")

    if request.method == 'POST':
        msg_text = request.form.get('message')
        receiver = product.user_email
        new_chat = Chat(product_id=product_id, sender_email=user.email, receiver_email=receiver, message=msg_text)
        db.session.add(new_chat)
        
        if user.free_chats_count > 0 and user.email != product.user_email:
            user.free_chats_count -= 1
            
        db.session.commit()
        return redirect(url_for('chat', product_id=product_id))

    chats = Chat.query.filter_by(product_id=product_id).all()
    return render_template('chat.html', product=product, chats=chats)

# --- 2 & 8. కస్టమర్ అకౌంట్, ప్రొఫైల్ పిక్చర్ & రెఫరల్ ---
@app.route('/account')
def account():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(email=session['user_email']).first()
    return render_template('account.html', user=user)

@app.route('/update-profile-pic', methods=['POST'])
def update_profile_pic():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=session['user_email']).first()
    file = request.files.get('profile_pic')
    
    if file and file.filename != '':
        filename = secure_filename(f"user_{user.id}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        user.profile_pic = filename
        db.session.commit()
        
    return redirect(url_for('account'))

# --- 9. సెక్యూరిటీ & సెట్టింగ్స్ పేజీ ---
@app.route('/settings')
def settings():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(email=session['user_email']).first()
    return render_template('settings.html', user=user)

# --- 10. సీక్రెట్ అడ్మిన్ ప్యానెల్ (కేవలం మీకు మాత్రమే) ---
@app.route('/admin_secure_portal_786')
def admin_portal():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(email=session['user_email']).first()
    
    # కేవలం మీ ఈమెయిల్ మరియు అడ్మిన్ పర్మిషన్ ఉన్నవారికే
    if not user or not user.is_admin or user.email != "mujahidsdghf@gmail.com":
        return "404 Page Not Found", 404
        
    users = User.query.all()
    products = Product.query.all()
    return render_template('admin.html', users=users, products=products)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
