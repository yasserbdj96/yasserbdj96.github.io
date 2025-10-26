# Flask Authentication App

A production-ready Flask application with comprehensive user authentication features including Two-Factor Authentication (2FA), password reset, and secure account management.

## Features

- ✅ User Registration & Login
- ✅ Secure Password Hashing (bcrypt)
- ✅ Session-based Authentication
- ✅ Two-Factor Authentication (TOTP/Google Authenticator)
- ✅ Email-based Password Reset
- ✅ CSRF Protection
- ✅ Rate Limiting (brute-force protection)
- ✅ Remember Me functionality
- ✅ Clean, responsive UI
- ✅ External CSS styling

## Project Structure

```
flask-auth-app/
│
├── app.py                         # Main application file (Flask backend)
├── .env                           # Environment variables (create from .env.example)
├── .env.example                   # Environment variables template
├── requirements.txt               # Python dependencies
├── README.md                      # Project documentation
│
├── locales
│   ├── en.json
│   └── ar.json
│
├── static/                        # Static files (CSS, JS, images)
│   └── css/
│       └── style.css              # Main stylesheet
│
└── templates/                     # HTML templates (Jinja2)
    ├── base.html                  # Base template with navigation
    ├── index.html                 # Home page
    ├── register.html              # User registration
    ├── login.html                 # User login
    ├── verify_2fa.html            # 2FA code verification
    ├── dashboard.html             # User dashboard (protected)
    ├── enable_2fa.html            # Enable 2FA setup
    ├── unverified.html
    ├── resend_verification.html
    ├── forgot_password.html       # Request password reset
    └── reset_password.html        # Reset password with token
```

## Installation

### 1. Clone or Download the Project

```bash
# Create project directory
mkdir flask-auth-app
cd flask-auth-app
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your settings
```

**Important:** Update the following in your `.env` file:

- `SECRET_KEY`: Generate a secure random key
- `MAIL_USERNAME`: Your email address
- `MAIL_PASSWORD`: Your email app password (for Gmail, use App Password)
- `MAIL_DEFAULT_SENDER`: Sender email address

#### Generate a Secure Secret Key:

```python
python -c "import secrets; print(secrets.token_hex(32))"
```

#### Gmail Setup:

1. Enable 2-Step Verification on your Google Account
2. Go to: https://myaccount.google.com/apppasswords
3. Generate an App Password for "Mail"
4. Use this App Password in your `.env` file

### 5. Initialize Database

The database will be created automatically when you run the app for the first time.

### 6. Run the Application

```bash
python app.py
```

The application will be available at: http://127.0.0.1:5000

## Usage

### User Registration

1. Navigate to the Register page
2. Fill in username, email, and password (minimum 8 characters)
3. Click "Register"
4. Check your inbox for a verification message and follow the link to confirm your email address

### User Login

1. Navigate to the Login page
2. Enter your email and password
3. Optionally check "Remember me" for persistent sessions
4. If 2FA is enabled, you'll be prompted for the code

### Enable Two-Factor Authentication

1. Log in to your account
2. Go to the Dashboard
3. Click "Enable 2FA"
4. Scan the QR code with Google Authenticator or enter the key manually
5. Enter the 6-digit code to confirm

### Password Reset

1. Click "Forgot password?" on the login page
2. Enter your email address
3. Check your email for the reset link
4. Click the link and enter your new password

## Security Features

### Password Security
- Bcrypt hashing with salt
- Minimum 8-character requirement
- Server-side validation

### Session Security
- Secure session cookies
- CSRF protection on all forms
- Session expiration

### Rate Limiting
- 5 login attempts per minute
- 200 requests per day per IP
- 50 requests per hour per IP

### 2FA Security
- Time-based One-Time Passwords (TOTP)
- Compatible with Google Authenticator, Authy, etc.
- Optional per-user basis

### Password Reset Security
- Time-limited tokens (1 hour expiration)
- Single-use tokens
- Secure token generation

## API Routes

- `GET/POST /register` - User registration
- `GET/POST /login` - User login
- `GET/POST /verify-2fa` - 2FA verification
- `GET /dashboard` - User dashboard (protected)
- `GET/POST /enable-2fa` - Enable 2FA
- `POST /disable-2fa` - Disable 2FA
- `GET/POST /forgot-password` - Request password reset
- `GET/POST /reset-password/<token>` - Reset password with token
- `GET /logout` - User logout

## Testing

### Manual Testing Checklist

- [ ] User can register with valid credentials
- [ ] User cannot register with existing email/username
- [ ] User can log in with correct credentials
- [ ] User cannot log in with incorrect credentials
- [ ] Rate limiting works after 5 failed login attempts
- [ ] User can enable 2FA
- [ ] 2FA verification works during login
- [ ] User can disable 2FA
- [ ] Password reset email is sent
- [ ] Password reset token works
- [ ] Expired tokens are rejected
- [ ] Remember me checkbox persists session
- [ ] Logout clears session
- [ ] Protected routes redirect to login

## Production Deployment Checklist

- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Set `DEBUG = False` in production
- [ ] Use PostgreSQL instead of SQLite
- [ ] Use a production WSGI server (Gunicorn, uWSGI)
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure proper email service (SendGrid, AWS SES, etc.)
- [ ] Enable logging and monitoring
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Use environment-specific configuration
- [ ] Implement proper secret management
- [ ] Set up rate limiting with Redis backend

### Example Production Server Setup (Gunicorn)

```bash
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Troubleshooting

### Email Not Sending

- Verify SMTP credentials in `.env`
- For Gmail, ensure you're using an App Password, not your regular password
- Check firewall rules allow SMTP connections
- Try port 465 with SSL instead of 587 with TLS

### Database Locked Error

- SQLite is not suitable for high-concurrency production use
- Switch to PostgreSQL for production

### 2FA QR Code Not Displaying

- Ensure Pillow is installed: `pip install Pillow`
- Check browser console for errors

### Rate Limit Issues

- Rate limits are stored in memory by default
- For production, use Redis: `pip install redis`
- Update limiter configuration to use Redis

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.