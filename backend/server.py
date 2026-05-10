from flask import Flask, send_from_directory, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from database import init_db
from auth import auth_bp
from data_student import student_bp
import os

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')
IMAGE_DIR    = os.path.join(os.path.dirname(__file__), '..', 'image')
VIDEO_DIR    = os.path.join(os.path.dirname(__file__), '..', 'video')

app = Flask(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
app.config['SECRET_KEY']     = os.environ.get('SECRET_KEY',     'kru-tuck-cell-learning-2026')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-kru-tuck-secret-2026')

# ── Extensions ─────────────────────────────────────────────────────────────
CORS(app, resources={r'/api/*': {'origins': '*'}})
JWTManager(app)

# ── Blueprints ─────────────────────────────────────────────────────────────
app.register_blueprint(auth_bp,    url_prefix='/api/auth')
app.register_blueprint(student_bp, url_prefix='/api/students')

# ── Init DB ────────────────────────────────────────────────────────────────
init_db()

# ── Frontend ────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    res = make_response(send_from_directory(FRONTEND_DIR, 'login.html'))
    res.headers['Content-Type'] = 'text/html; charset=utf-8'
    return res

@app.route('/image/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_DIR, filename)

@app.route('/video/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_DIR, filename, conditional=True)

@app.route('/<path:filename>')
def serve_frontend(filename):
    res = make_response(send_from_directory(FRONTEND_DIR, filename))
    if filename.endswith('.html'):
        res.headers['Content-Type'] = 'text/html; charset=utf-8'
    return res


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
