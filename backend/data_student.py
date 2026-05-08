from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db, get_cursor

student_bp = Blueprint('students', __name__)

EDITABLE_FIELDS = {'first_name', 'last_name', 'class_name', 'student_number', 'gender', 'age'}
TEACHER_ONLY_FIELDS = {'score', 'role'}


def _get_user(user_id):
    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


def _serialize(row):
    return {
        'id':             row['id'],
        'username':       row['username'],
        'first_name':     row['first_name'],
        'last_name':      row['last_name'],
        'class_name':     row['class_name'],
        'student_number': row['student_number'],
        'gender':         row['gender'],
        'age':            row['age'],
        'role':           row['role'],
        'score':          row['score'],
        'created_at':     str(row['created_at']),
    }


@student_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_students():
    caller = _get_user(get_jwt_identity())
    if not caller or caller['role'] != 'teacher':
        return jsonify({'error': 'สิทธิ์ครูเท่านั้น'}), 403

    class_filter = request.args.get('class')
    conn = get_db()
    cur = get_cursor(conn)
    if class_filter:
        cur.execute(
            "SELECT * FROM users WHERE role='student' AND class_name=%s ORDER BY student_number",
            (class_filter,)
        )
    else:
        cur.execute(
            "SELECT * FROM users WHERE role='student' ORDER BY class_name, student_number"
        )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([_serialize(r) for r in rows]), 200


@student_bp.route('/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student(student_id):
    caller = _get_user(get_jwt_identity())
    if not caller:
        return jsonify({'error': 'ไม่พบผู้ใช้'}), 404
    if caller['role'] != 'teacher' and caller['id'] != student_id:
        return jsonify({'error': 'ไม่มีสิทธิ์เข้าถึงข้อมูลนี้'}), 403

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM users WHERE id = %s', (student_id,))
    student = cur.fetchone()
    cur.close()
    conn.close()

    if not student:
        return jsonify({'error': 'ไม่พบนักเรียน'}), 404
    return jsonify(_serialize(student)), 200


@student_bp.route('/<int:student_id>', methods=['PUT'])
@jwt_required()
def update_student(student_id):
    caller = _get_user(get_jwt_identity())
    if not caller:
        return jsonify({'error': 'ไม่พบผู้ใช้'}), 404
    if caller['role'] != 'teacher' and caller['id'] != student_id:
        return jsonify({'error': 'ไม่มีสิทธิ์แก้ไขข้อมูลนี้'}), 403

    data = request.get_json(silent=True) or {}
    allowed = EDITABLE_FIELDS | (TEACHER_ONLY_FIELDS if caller['role'] == 'teacher' else set())
    updates = {k: v for k, v in data.items() if k in allowed}

    if not updates:
        return jsonify({'error': 'ไม่มีฟิลด์ที่แก้ไขได้'}), 400

    set_clause = ', '.join(f'{k} = %s' for k in updates)
    values = list(updates.values()) + [student_id]

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute(f'UPDATE users SET {set_clause} WHERE id = %s', values)
    conn.commit()
    cur.execute('SELECT * FROM users WHERE id = %s', (student_id,))
    updated = cur.fetchone()
    cur.close()
    conn.close()

    return jsonify({'message': 'อัพเดตข้อมูลสำเร็จ', 'user': _serialize(updated)}), 200


@student_bp.route('/<int:student_id>', methods=['DELETE'])
@jwt_required()
def delete_student(student_id):
    caller = _get_user(get_jwt_identity())
    if not caller or caller['role'] != 'teacher':
        return jsonify({'error': 'สิทธิ์ครูเท่านั้น'}), 403

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute(
        "DELETE FROM users WHERE id = %s AND role = 'student'", (student_id,)
    )
    conn.commit()
    rowcount = cur.rowcount
    cur.close()
    conn.close()

    if rowcount == 0:
        return jsonify({'error': 'ไม่พบนักเรียนที่จะลบ'}), 404
    return jsonify({'message': 'ลบข้อมูลนักเรียนสำเร็จ'}), 200


@student_bp.route('/score', methods=['POST'])
@jwt_required()
def add_score():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    points = data.get('points')

    if points is None:
        return jsonify({'error': 'กรุณาระบุคะแนน'}), 400
    try:
        points = int(points)
    except (ValueError, TypeError):
        return jsonify({'error': 'คะแนนต้องเป็นตัวเลข'}), 400

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('UPDATE users SET score = score + %s WHERE id = %s', (points, user_id))
    conn.commit()
    cur.execute('SELECT score FROM users WHERE id = %s', (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    return jsonify({'message': 'บันทึกคะแนนสำเร็จ', 'total_score': row['score']}), 200
