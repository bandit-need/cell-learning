from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db, get_cursor

chat_bp = Blueprint('chat', __name__)


def _get_user(user_id):
    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


@chat_bp.route('/messages', methods=['GET'])
@jwt_required()
def get_messages():
    caller_id = int(get_jwt_identity())
    caller = _get_user(caller_id)
    if not caller:
        return jsonify({'error': 'ไม่พบผู้ใช้'}), 404

    if caller['role'] == 'teacher':
        student_id = request.args.get('student_id', type=int)
        if not student_id:
            return jsonify({'error': 'กรุณาระบุ student_id'}), 400
        thread_id = student_id
    else:
        thread_id = caller_id

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('''
        SELECT m.id, m.sender_id, m.content, m.created_at, m.is_read,
               u.first_name, u.role AS sender_role
        FROM messages m
        JOIN users u ON u.id = m.sender_id
        WHERE m.student_id = %s
        ORDER BY m.created_at ASC
    ''', (thread_id,))
    rows = cur.fetchall()

    # Mark incoming messages as read
    cur.execute('''
        UPDATE messages SET is_read = TRUE
        WHERE student_id = %s AND sender_id != %s AND is_read = FALSE
    ''', (thread_id, caller_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify([{
        'id':          r['id'],
        'sender_id':   r['sender_id'],
        'sender_name': r['first_name'],
        'sender_role': r['sender_role'],
        'content':     r['content'],
        'created_at':  str(r['created_at']),
        'is_mine':     r['sender_id'] == caller_id,
    } for r in rows]), 200


@chat_bp.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    caller_id = int(get_jwt_identity())
    caller = _get_user(caller_id)
    if not caller:
        return jsonify({'error': 'ไม่พบผู้ใช้'}), 404

    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'error': 'กรุณากรอกข้อความ'}), 400

    if caller['role'] == 'teacher':
        student_id = data.get('student_id')
        if not student_id:
            return jsonify({'error': 'กรุณาระบุ student_id'}), 400
    else:
        student_id = caller_id

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('''
        INSERT INTO messages (sender_id, student_id, content)
        VALUES (%s, %s, %s)
        RETURNING id, created_at
    ''', (caller_id, student_id, content))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        'id':         row['id'],
        'sender_id':  caller_id,
        'content':    content,
        'created_at': str(row['created_at']),
        'is_mine':    True,
    }), 201


@chat_bp.route('/students', methods=['GET'])
@jwt_required()
def get_chat_students():
    caller_id = int(get_jwt_identity())
    caller = _get_user(caller_id)
    if not caller or caller['role'] != 'teacher':
        return jsonify({'error': 'สิทธิ์ครูเท่านั้น'}), 403

    conn = get_db()
    cur = get_cursor(conn)
    cur.execute('''
        SELECT u.id, u.first_name, u.last_name, u.class_name, u.student_number, u.score,
               COUNT(m.id) FILTER (WHERE m.is_read = FALSE AND m.sender_id != %s) AS unread,
               MAX(m.created_at) AS last_msg
        FROM users u
        LEFT JOIN messages m ON m.student_id = u.id
        WHERE u.role = 'student'
        GROUP BY u.id
        ORDER BY unread DESC, last_msg DESC NULLS LAST, u.class_name, u.student_number
    ''', (caller_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([{
        'id':             r['id'],
        'first_name':     r['first_name'],
        'last_name':      r['last_name'],
        'class_name':     r['class_name'],
        'student_number': r['student_number'],
        'score':          r['score'],
        'unread':         int(r['unread'] or 0),
        'last_msg':       str(r['last_msg']) if r['last_msg'] else None,
    } for r in rows]), 200
