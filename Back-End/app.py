# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message  # Add this import
import json
import uuid
from functools import wraps
import os
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
app.secret_key = 'your_very_secret_key_here'  # Change this in production!

DATA_FILE = 'data.json'

# Hardcoded credentials (for simplicity - consider using environment variables or a database in production)
VALID_USERNAME = 'your_username_here'
VALID_PASSWORD = 'your_password_here'

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.your-email-provider.com'  # e.g., 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@example.com'

mail = Mail(app)

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            # Add IDs to existing entries if missing
            for project in data['projects']:
                if 'id' not in project:
                    project['id'] = str(uuid.uuid4())
            for post in data['blogPosts']:
                if 'id' not in post:
                    post['id'] = str(uuid.uuid4())
            return data
    except FileNotFoundError:
        return {'projects': [], 'blogPosts': []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    data = load_data()
    return render_template('dashboard.html', 
                         projects=data['projects'], 
                         blog_posts=data['blogPosts'])

@app.route('/add/<content_type>', methods=['GET', 'POST'])
@login_required
def add_content(content_type):
    if content_type not in ['project', 'blog']:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        data = load_data()
        new_entry = { 'id': str(uuid.uuid4()) }

        if content_type == 'project':
            new_entry.update({
                'title': request.form['title'],
                'description': request.form['description'],
                'tech': [t.strip() for t in request.form['tech'].split(',')],
                'image': request.form['image'],
                'cover': request.form['cover'],
                'source': request.form['source'],
                'details': request.form['details']
            })
            data['projects'].append(new_entry)
        else:
            new_entry.update({
                'title': request.form['title'],
                'excerpt': request.form['excerpt'],
                'date': request.form['date'],
                'category': request.form['category'],
                'image': request.form['image'],
                'cover': request.form['cover'],
                'readTime': request.form['readTime'],
                'content': request.form['content']
            })
            data['blogPosts'].append(new_entry)

        save_data(data)
        flash(f'{content_type.capitalize()} added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_edit.html', content_type=content_type)

@app.route('/edit/<content_type>/<entry_id>', methods=['GET', 'POST'])
@login_required
def edit_content(content_type, entry_id):
    data = load_data()
    entries = data['projects'] if content_type == 'project' else data['blogPosts']
    entry = next((e for e in entries if e['id'] == entry_id), None)

    if not entry:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        if content_type == 'project':
            entry.update({
                'title': request.form['title'],
                'description': request.form['description'],
                'tech': [t.strip() for t in request.form['tech'].split(',')],
                'image': request.form['image'],
                'cover': request.form['cover'],
                'source': request.form['source'],
                'details': request.form['details']
            })
        else:
            entry.update({
                'title': request.form['title'],
                'excerpt': request.form['excerpt'],
                'date': request.form['date'],
                'category': request.form['category'],
                'image': request.form['image'],
                'cover': request.form['cover'],
                'readTime': request.form['readTime'],
                'content': request.form['content']
            })

        save_data(data)
        flash(f'{content_type.capitalize()} updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_edit.html', 
                          content_type=content_type, 
                          entry=entry)

@app.route('/delete/<content_type>/<entry_id>', methods=['POST'])
@login_required
def delete_content(content_type, entry_id):
    data = load_data()
    entries = data['projects'] if content_type == 'project' else data['blogPosts']
    data[content_type + 's' if content_type == 'project' else 'blogPosts'] = [e for e in entries if e['id'] != entry_id]
    save_data(data)
    flash(f'{content_type.capitalize()} deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/data.json')
def serve_data():
    """Serve the data.json file publicly as a proper JSON response"""
    try:
        with open(os.path.join(os.getcwd(), DATA_FILE), 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "data.json not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format"}), 500

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    try:
        data = request.json  # For JSON requests
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')
    except:
        # Fallback to form data if JSON parsing fails
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

    if not all([name, email, message]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    try:
        # Send email
        msg = Message(
            subject=f"New contact form submission from {name}",
            recipients=['your-receiving-email@example.com'],  # Where you want to receive messages
            body=f"""
Name: {name}
Email: {email}
Message: {message}
"""
        )
        mail.send(msg)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port=8080
    ip='0.0.0.0'
    app.run(host=ip, port=port, debug=True)