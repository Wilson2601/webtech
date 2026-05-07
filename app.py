from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename # New: For secure file uploads

app = Flask(__name__)
app.secret_key = 'uts_final_year_project_2026'

# --- Configuration for Uploads ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- JSON Paths ---
USER_DB = 'users.json'
FORUM_DB = 'forum.json'
HISTORY_DB = 'history.json'

# --- Inventory Database ---
INVENTORY = [
    {'id': 1, 'name': 'Foundations Of Computer Science', 'price': 43.00, 'cat': 'COMPUTER SCIENCE', 'cover': 'book1.jpg'},
    {'id': 2, 'name': 'Learn Python Programming', 'price': 50.00, 'cat': 'COMPUTER SCIENCE', 'cover': 'book2.jpg'},
    {'id': 3, 'name': 'Master Python', 'price': 54.00, 'cat': 'COMPUTER SCIENCE', 'cover': 'book3.jpg'},
    {'id': 4, 'name': 'Introduction to Java Programming', 'price': 41.00, 'cat': 'COMPUTER SCIENCE', 'cover': 'book4.jpg'}
]

# --- Helper Functions ---
def load_db(file, default):
    if not os.path.exists(file): return default
    with open(file, 'r') as f:
        try:
            data = json.load(f)
            return data if isinstance(data, type(default)) else default
        except: return default

def save_db(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Navigation Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portal')
def portal():
    if 'user_email' not in session:
        return render_template('login_signup.html')
    
    users = load_db(USER_DB, {})
    user_info = users.get(session['user_email'], {})
    
    # Handle user photo (defaults to default_avatar.jpg)
    user_photo = 'default_avatar.jpg'
    if isinstance(user_info, dict):
        user_photo = user_info.get('photo', 'default_avatar.jpg')

    user_name = session['user_email'].split('@')[0].upper()
    
    # Personalized Student Data for the Study Planner
    portal_data = {
        'username': user_name,
        'level': 'Level 1 Scholar',
        'xp': 45, 
        'todo': [
            {'title': 'Watch Web Tech Module 01', 'course': 'WEB TECHNOLOGY'},
            {'title': 'Complete Data Structures Quiz', 'course': 'DATA STRUCTURES'}
        ],
        'in_progress': [
            {'title': 'Draft Final Year Project Proposal', 'course': 'ASSIGNMENT'},
            {'title': 'SQL Query Optimization Lab', 'course': 'DATABASE SYSTEMS'}
        ]
    }
    return render_template('portal.html', data=portal_data, photo=user_photo)

@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    if 'user_email' not in session:
        return redirect(url_for('portal'))
    
    file = request.files.get('profile_pic')
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{session['user_email']}_profile.jpg")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        users = load_db(USER_DB, {})
        # Ensure user entry is a dictionary to store both password and photo
        if isinstance(users[session['user_email']], str):
            password = users[session['user_email']]
            users[session['user_email']] = {'password': password, 'photo': filename}
        else:
            users[session['user_email']]['photo'] = filename
            
        save_db(USER_DB, users)
        
    return redirect(url_for('portal'))

@app.route('/courses')
def courses():
    return render_template('courses.html')

# --- Forum Logic ---

@app.route('/forum')
def forum():
    posts = load_db(FORUM_DB, [])
    is_admin = session.get('user_email') == 'admin@edutech.com'
    return render_template('forum.html', posts=posts, is_admin=is_admin)

@app.route('/ask_question', methods=['POST'])
def ask_question():
    if 'user_email' not in session:
        return redirect(url_for('portal'))
    
    posts = load_db(FORUM_DB, [])
    new_post = {
        'id': len(posts) + 1,
        'author': session['user_email'].split('@')[0],
        'tag': request.form.get('tag'),
        'title': request.form.get('title'),
        'votes': 1,
        'comments': [],
        'date': datetime.now().strftime("%d/%m/%Y")
    }
    posts.insert(0, new_post)
    save_db(FORUM_DB, posts)
    return redirect(url_for('forum'))

@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_email' not in session:
        return redirect(url_for('portal'))
    
    posts = load_db(FORUM_DB, [])
    comment_text = request.form.get('comment')
    
    for post in posts:
        if post['id'] == post_id:
            post['comments'].append({
                'author': session['user_email'].split('@')[0],
                'text': comment_text,
                'date': datetime.now().strftime("%d/%m/%Y")
            })
            break
            
    save_db(FORUM_DB, posts)
    return redirect(url_for('forum'))

@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    if session.get('user_email') == 'admin@edutech.com':
        posts = load_db(FORUM_DB, [])
        posts = [p for p in posts if p['id'] != post_id]
        save_db(FORUM_DB, posts)
    return redirect(url_for('forum'))

# --- Authentication ---

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    users = load_db(USER_DB, {})
    
    user_entry = users.get(email)
    # Handle both old string passwords and new dictionary entries
    stored_password = user_entry['password'] if isinstance(user_entry, dict) else user_entry

    if user_entry and stored_password == password:
        session['user_email'] = email
        return redirect(url_for('portal'))
    return "Invalid credentials. <a href='/portal'>Try again</a>"

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    users = load_db(USER_DB, {})
    # Initialize as dictionary for future photo storage
    users[email] = {'password': password, 'photo': 'default_avatar.jpg'}
    save_db(USER_DB, users)
    session['user_email'] = email
    return redirect(url_for('portal'))

# --- Bookstore Logic ---

@app.route('/bookstore')
def bookstore():
    cart_ids = session.get('cart', [])
    bag_items = [b for b in INVENTORY if b['id'] in cart_ids]
    total = sum(item['price'] for item in bag_items)
    return render_template('bookstore.html', books=INVENTORY, bag_items=bag_items, total=total)

@app.route('/add_to_bag/<int:book_id>')
def add_to_bag(book_id):
    if 'cart' not in session: session['cart'] = []
    if book_id not in session['cart']:
        session['cart'].append(book_id)
    session.modified = True
    return redirect(url_for('bookstore'))

@app.route('/remove_from_bag/<int:book_id>')
def remove_from_bag(book_id):
    if 'cart' in session:
        if book_id in session['cart']:
            session['cart'].remove(book_id)
            session.modified = True
    return redirect(url_for('bookstore'))

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_email' not in session:
        return redirect(url_for('portal'))
    session.pop('cart', None)
    session.modified = True
    return redirect(url_for('bookstore', success='true'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portal'))

if __name__ == '__main__':
    app.run(debug=True)