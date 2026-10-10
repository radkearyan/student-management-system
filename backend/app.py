import os
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load configurations from .env
load_dotenv()

app = Flask(
    __name__, 
    static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend')),
    static_url_path='',
    template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
)

from datetime import timedelta

app.secret_key = os.environ.get('SECRET_KEY', 'smart_sms_secure_secret_key_192837')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

CORS(app, supports_credentials=True)

@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


# UPLOAD_FOLDER Configuration
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Register Blueprints
from backend.routes.auth import auth_bp
from backend.routes.admin import admin_bp
from backend.routes.student import student_bp
from backend.routes.attendance import attendance_bp
from backend.routes.examination import exams_bp
from backend.routes.fees import fees_bp
from backend.routes.notification import notification_bp
from backend.routes.reports import reports_bp
from backend.routes.faculty import faculty_bp
from backend.routes.parent import parent_bp
from backend.routes.timetable import timetable_bp
from backend.routes.courses import courses_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api')
app.register_blueprint(student_bp, url_prefix='/api/students')
app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
app.register_blueprint(exams_bp, url_prefix='/api')
app.register_blueprint(fees_bp, url_prefix='/api/fees')
app.register_blueprint(notification_bp, url_prefix='/api/ai')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(faculty_bp, url_prefix='/api/faculty')
app.register_blueprint(parent_bp, url_prefix='/api/parent')
app.register_blueprint(timetable_bp, url_prefix='/api/timetable')
app.register_blueprint(courses_bp, url_prefix='/api')


# Route to serve uploads
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Root route serves index.html
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    from backend.config.database import init_db
    init_db()
    
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=True)
