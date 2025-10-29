from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from functools import wraps
import os
from dotenv import load_dotenv
import json
import uuid
from flask_cors import CORS

# Add this after your imports in app.py
def get_locale():
    # Check if language is stored in session
    return session.get('language', 'en')

def get_text(key):
    lang = get_locale()
    file_path = f'locales/{lang}.json'
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            return translations.get(key, key)
    return key

load_dotenv()

app = Flask(__name__)

CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['WTF_CSRF_ENABLED'] = False

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@example.com')

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
csrf = CSRFProtect(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Token serializer for password reset and email verification
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    two_fa_secret = db.Column(db.String(32), nullable=True)
    two_fa_enabled = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def generate_2fa_secret(self):
        self.two_fa_secret = pyotp.random_base32()
        return self.two_fa_secret
    
    def get_totp_uri(self):
        return pyotp.totp.TOTP(self.two_fa_secret).provisioning_uri(
            name=self.email,
            issuer_name=os.getenv('issuer_name', 'Flask Auth App')
        )
    
    def verify_totp(self, token):
        totp = pyotp.TOTP(self.two_fa_secret)
        return totp.verify(token, valid_window=1)

# Project Model
class Project(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tech = db.Column(db.Text, nullable=False)  # Stored as comma-separated
    image = db.Column(db.String(500), nullable=False)
    cover = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(500), nullable=False)
    details = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'tech': [t.strip() for t in self.tech.split(',') if t.strip()],
            'image': self.image,
            'cover': self.cover,
            'source': self.source,
            'details': self.details
        }

# BlogPost Model
class BlogPost(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    excerpt = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(500), nullable=False)
    cover = db.Column(db.String(500), nullable=False)
    read_time = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'excerpt': self.excerpt,
            'date': self.date,
            'category': self.category,
            'image': self.image,
            'cover': self.cover,
            'readTime': self.read_time,
            'content': self.content
        }

# Create tables
with app.app_context():
    db.create_all()

DATA_FILE = 'data.json'

def migrate_json_to_db():
    """Migrate existing data.json to database if it exists"""
    if not os.path.exists(DATA_FILE):
        return
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Migrate projects
        for project_data in data.get('projects', []):
            # Check if project already exists
            if not Project.query.get(project_data.get('id')):
                project = Project(
                    id=project_data.get('id', str(uuid.uuid4())),
                    title=project_data['title'],
                    description=project_data['description'],
                    tech=','.join(project_data['tech']) if isinstance(project_data['tech'], list) else project_data['tech'],
                    image=project_data['image'],
                    cover=project_data['cover'],
                    source=project_data['source'],
                    details=project_data['details']
                )
                db.session.add(project)
        
        # Migrate blog posts
        for post_data in data.get('blogPosts', []):
            # Check if post already exists
            if not BlogPost.query.get(post_data.get('id')):
                post = BlogPost(
                    id=post_data.get('id', str(uuid.uuid4())),
                    title=post_data['title'],
                    excerpt=post_data['excerpt'],
                    date=post_data['date'],
                    category=post_data['category'],
                    image=post_data['image'],
                    cover=post_data['cover'],
                    read_time=post_data['readTime'],
                    content=post_data['content']
                )
                db.session.add(post)
        
        db.session.commit()
        print("Data migration completed successfully!")
    except Exception as e:
        print(f"Migration error: {e}")
        db.session.rollback()

# Run migration on startup
with app.app_context():
    migrate_json_to_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Email verification required decorator
def email_verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = User.query.get(session.get('user_id'))
        if user and not user.email_verified:
            flash('Please verify your email address to access this page.', 'warning')
            return redirect(url_for('unverified'))
        return f(*args, **kwargs)
    return decorated_function

# Add context processor to make get_text available in all templates
@app.context_processor
def utility_processor():
    return dict(get_text=get_text, current_language=get_locale())

# Add language switching route
@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in ['en', 'ar']:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long.', 'error')
            return render_template('register.html')
        
        if not email or '@' not in email:
            flash('Please provide a valid email address.', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        try:
            token = serializer.dumps(email, salt='email-verification-salt')
            verify_url = url_for('verify_email', token=token, _external=True)
            
            msg = Message('Verify Your Email Address',
                        recipients=[email])
            msg.body = f'''Hello {username},

Thank you for registering! Please verify your email address by clicking the link below:

{verify_url}

This link will expire in 24 hours.

If you did not create an account, please ignore this email.

Best regards,
Flask Auth App Team
'''
            mail.send(msg)
            flash('Registration successful! Please check your email to verify your account.', 'success')
        except Exception as e:
            flash('Registration successful! However, we could not send the verification email. Please contact support.', 'warning')
            print(f"Mail error: {e}")
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/verify-email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verification-salt', max_age=86400)  # 24 hours
    except SignatureExpired:
        flash('The verification link has expired. Please request a new one.', 'error')
        return redirect(url_for('resend_verification'))
    except BadSignature:
        flash('The verification link is invalid.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        if user.email_verified:
            flash('Email already verified. Please log in.', 'info')
        else:
            user.email_verified = True
            db.session.commit()
            flash('Your email has been verified successfully! You can now log in.', 'success')
    else:
        flash('User not found.', 'error')
    
    return redirect(url_for('login'))

@app.route('/unverified')
@login_required
def unverified():
    user = User.query.get(session['user_id'])
    if user and user.email_verified:
        return redirect(url_for('dashboard'))
    return render_template('unverified.html')

@app.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        
        if user:
            if user.email_verified:
                flash('This email is already verified. Please log in.', 'info')
                return redirect(url_for('login'))
            
            try:
                token = serializer.dumps(email, salt='email-verification-salt')
                verify_url = url_for('verify_email', token=token, _external=True)
                
                msg = Message('Verify Your Email Address',
                            recipients=[email])
                msg.body = f'''Hello {user.username},

Please verify your email address by clicking the link below:

{verify_url}

This link will expire in 24 hours.

If you did not create an account, please ignore this email.

Best regards,
Flask Auth App Team
'''
                mail.send(msg)
                flash('Verification email has been sent. Please check your inbox.', 'success')
            except Exception as e:
                flash('Error sending email. Please try again later.', 'error')
                print(f"Mail error: {e}")
        else:
            flash('If that email exists, a verification email has been sent.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('resend_verification.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.email_verified:
                flash('Please verify your email address before logging in. Check your inbox for the verification link.', 'warning')
                return render_template('login.html')
            
            if user.two_fa_enabled:
                # Store user_id temporarily for 2FA verification
                session['2fa_user_id'] = user.id
                return redirect(url_for('verify_2fa'))
            
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = remember
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    if '2fa_user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        user = User.query.get(session['2fa_user_id'])
        
        if user and user.verify_totp(token):
            session['user_id'] = user.id
            session['username'] = user.username
            session.pop('2fa_user_id', None)
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid 2FA code. Please try again.', 'error')
    
    return render_template('verify_2fa.html')

@app.route('/enable-2fa', methods=['GET', 'POST'])
@login_required
@email_verified_required
def enable_2fa():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        
        if user.verify_totp(token):
            user.two_fa_enabled = True
            db.session.commit()
            flash('2FA has been enabled successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid code. Please try again.', 'error')
    
    # Generate 2FA secret if not exists
    if not user.two_fa_secret:
        user.generate_2fa_secret()
        db.session.commit()
    
    # Generate QR code
    qr_uri = user.get_totp_uri()
    qr = qrcode.make(qr_uri)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)
    qr_code_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return render_template('enable_2fa.html', 
                         qr_code=qr_code_base64, 
                         secret=user.two_fa_secret)

@app.route('/disable-2fa', methods=['POST'])
@login_required
@email_verified_required
def disable_2fa():
    user = User.query.get(session['user_id'])
    user.two_fa_enabled = False
    user.two_fa_secret = None
    db.session.commit()
    flash('2FA has been disabled.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        
        if user:
            if not user.email_verified:
                flash('Please verify your email address first.', 'warning')
                return redirect(url_for('resend_verification'))
            
            token = serializer.dumps(email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Send email
            try:
                msg = Message('Password Reset Request',
                            recipients=[email])
                msg.body = f'''To reset your password, visit the following link:
{reset_url}

This link will expire in 1 hour.

If you did not make this request, please ignore this email.
'''
                mail.send(msg)
                flash('Password reset instructions have been sent to your email.', 'info')
            except Exception as e:
                flash('Error sending email. Please try again later.', 'error')
                print(f"Mail error: {e}")
        else:
            # Don't reveal if email exists
            flash('If that email exists, password reset instructions have been sent.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            flash('Your password has been reset successfully!', 'success')
            return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/publish')
@login_required
@email_verified_required
def publish():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    blog_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('publish.html', 
                         projects=projects, 
                         blog_posts=blog_posts)

@app.route('/add/<content_type>', methods=['GET', 'POST'])
@login_required
@email_verified_required
def add_content(content_type):
    if content_type not in ['project', 'blog']:
        return redirect(url_for('publish'))

    if request.method == 'POST':
        try:
            if content_type == 'project':
                project = Project(
                    title=request.form['title'],
                    description=request.form['description'],
                    tech=request.form['tech'],
                    image=request.form['image'],
                    cover=request.form['cover'],
                    source=request.form['source'],
                    details=request.form['details']
                )
                db.session.add(project)
                db.session.commit()
            else:
                blog_post = BlogPost(
                    title=request.form['title'],
                    excerpt=request.form['excerpt'],
                    date=request.form['date'],
                    category=request.form['category'],
                    image=request.form['image'],
                    cover=request.form['cover'],
                    read_time=request.form['readTime'],
                    content=request.form['content']
                )
                db.session.add(blog_post)
                db.session.commit()

            flash(f'{content_type.capitalize()} added successfully!', 'success')
            return redirect(url_for('publish'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding {content_type}: {str(e)}', 'error')

    return render_template('add_edit.html', content_type=content_type)

@app.route('/edit/<content_type>/<entry_id>', methods=['GET', 'POST'])
@login_required
@email_verified_required
def edit_content(content_type, entry_id):
    if content_type == 'project':
        entry = Project.query.get_or_404(entry_id)
    else:
        entry = BlogPost.query.get_or_404(entry_id)

    if request.method == 'POST':
        try:
            if content_type == 'project':
                entry.title = request.form['title']
                entry.description = request.form['description']
                entry.tech = request.form['tech']
                entry.image = request.form['image']
                entry.cover = request.form['cover']
                entry.source = request.form['source']
                entry.details = request.form['details']
            else:
                entry.title = request.form['title']
                entry.excerpt = request.form['excerpt']
                entry.date = request.form['date']
                entry.category = request.form['category']
                entry.image = request.form['image']
                entry.cover = request.form['cover']
                entry.read_time = request.form['readTime']
                entry.content = request.form['content']

            db.session.commit()
            flash(f'{content_type.capitalize()} updated successfully!', 'success')
            return redirect(url_for('publish'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating {content_type}: {str(e)}', 'error')

    return render_template('add_edit.html', 
                          content_type=content_type, 
                          entry=entry)

@app.route('/delete/<content_type>/<entry_id>', methods=['POST'])
@login_required
@email_verified_required
def delete_content(content_type, entry_id):
    try:
        if content_type == 'project':
            entry = Project.query.get_or_404(entry_id)
        else:
            entry = BlogPost.query.get_or_404(entry_id)
        
        db.session.delete(entry)
        db.session.commit()
        flash(f'{content_type.capitalize()} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting {content_type}: {str(e)}', 'error')
    
    return redirect(url_for('publish'))

@app.route('/data.json')
def serve_data():
    """Serve data from database as JSON (maintains compatibility with existing endpoint)"""
    try:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        blog_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
        
        data = {
            'projects': [project.to_dict() for project in projects],
            'blogPosts': [post.to_dict() for post in blog_posts]
        }
        
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

@app.route('/dashboard')
@login_required
@email_verified_required
def dashboard():
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

# API Routes
@app.route('/api/project', methods=['POST'])
@login_required
@email_verified_required
def create_project():
    try:
        data = request.get_json()
        project = Project(
            title=data['title'],
            description=data['description'],
            tech=data['tech'],
            image=data['image'],
            cover=data['cover'],
            source=data['source'],
            details=data['details']
        )
        db.session.add(project)
        db.session.commit()
        return jsonify(project.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/project/<project_id>', methods=['GET'])
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())

@app.route('/api/project/<project_id>', methods=['PUT'])
@login_required
@email_verified_required
def update_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        project.title = data.get('title', project.title)
        project.description = data.get('description', project.description)
        project.tech = data.get('tech', project.tech)
        project.image = data.get('image', project.image)
        project.cover = data.get('cover', project.cover)
        project.source = data.get('source', project.source)
        project.details = data.get('details', project.details)
        
        db.session.commit()
        return jsonify(project.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/project/<project_id>', methods=['DELETE'])
@login_required
@email_verified_required
def delete_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/blog', methods=['POST'])
@login_required
@email_verified_required
def create_blog():
    try:
        data = request.get_json()
        blog = BlogPost(
            title=data['title'],
            excerpt=data['excerpt'],
            date=data['date'],
            category=data['category'],
            image=data['image'],
            cover=data['cover'],
            read_time=data['readTime'],
            content=data['content']
        )
        db.session.add(blog)
        db.session.commit()
        return jsonify(blog.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/blog/<blog_id>', methods=['GET'])
def get_blog(blog_id):
    blog = BlogPost.query.get_or_404(blog_id)
    return jsonify(blog.to_dict())

@app.route('/api/blog/<blog_id>', methods=['PUT'])
@login_required
@email_verified_required
def update_blog(blog_id):
    try:
        blog = BlogPost.query.get_or_404(blog_id)
        data = request.get_json()
        
        blog.title = data.get('title', blog.title)
        blog.excerpt = data.get('excerpt', blog.excerpt)
        blog.date = data.get('date', blog.date)
        blog.category = data.get('category', blog.category)
        blog.image = data.get('image', blog.image)
        blog.cover = data.get('cover', blog.cover)
        blog.read_time = data.get('readTime', blog.read_time)
        blog.content = data.get('content', blog.content)
        
        db.session.commit()
        return jsonify(blog.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/blog/<blog_id>', methods=['DELETE'])
@login_required
@email_verified_required
def delete_blog(blog_id):
    try:
        blog = BlogPost.query.get_or_404(blog_id)
        db.session.delete(blog)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)