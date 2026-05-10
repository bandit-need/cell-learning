from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, get_cursor
import os

auth_bp = Blueprint('auth', __name__)

REQUIRED_FIELDS = {
    'username':       'ชื่อผู้ใช้',
    'password':       'รหัสผ่าน',
    'first_name':     'ชื่อ',
    'last_name':      'นามสกุล',
    'class_name':     'ชั้น',
    'student_number': 'เลขที่',
    'gender':         'เพศ',
    'age':            'อายุ',
}


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}

    for field, label in REQUIRED_FIELDS.items():
        if not data.get(field) and data.get(field) != 0:
            return jsonify({'error': f'กรุณากรอก{label}'}), 400

    gender = data['gender']
    if gender not in ('ชาย', 'หญิง', 'อื่นๆ'):
        return jsonify({'error': 'เพศต้องเป็น ชาย / หญิง / อื่นๆ'}), 400

    try:
        age = int(data['age'])
        student_number = int(data['student_number'])
    except (ValueError, TypeError):
        return jsonify({'error': 'อายุและเลขที่ต้องเป็นตัวเลข'}), 400

    password_hash = generate_password_hash(data['password'])

    teacher_code = data.get('teacher_code', '').strip()
    role = 'teacher' if teacher_code == os.environ.get('TEACHER_CODE', 'KRUTHAK2026') else 'student'

    try:
        conn = get_db()
        cur = get_cursor(conn)
        cur.execute(
            '''INSERT INTO users
               (username, password_hash, first_name, last_name,
                class_name, student_number, gender, age, role)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
            (data['username'], password_hash, data['first_name'], data['last_name'],
             data['class_name'], student_number, gender, age, role)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'สมัครสมาชิกสำเร็จ'}), 201
    except Exception as e:
        if 'unique' in str(e).lower() or 'duplicate key' in str(e).lower():
            return jsonify({'error': 'ชื่อผู้ใช้นี้มีอยู่แล้ว'}), 409
        return jsonify({'error': 'เกิดข้อผิดพลาด กรุณาลองใหม่'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'กรุณากรอกชื่อผู้ใช้และรหัสผ่าน'}), 400

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'}), 401

    token = create_access_token(identity=str(user['id']))
    return jsonify({
        'token': token,
        'user': _serialize_user(user)
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({'error': 'ไม่พบผู้ใช้'}), 404
    return jsonify(_serialize_user(user)), 200


def _serialize_user(user):
    return {
        'id':             user['id'],
        'username':       user['username'],
        'first_name':     user['first_name'],
        'last_name':      user['last_name'],
        'class_name':     user['class_name'],
        'student_number': user['student_number'],
        'gender':         user['gender'],
        'age':            user['age'],
        'role':           user['role'],
        'score':          user['score'],
        'created_at':     str(user['created_at']),
    }
