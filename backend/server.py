from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from database import init_db
from auth import auth_bp
from data_student import student_bp
import os

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')

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

# ── Frontend ────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'login.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    return send_from_directory(FRONTEND_DIR, filename)


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
