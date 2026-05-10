import psycopg2
import psycopg2.extras
import os


def _get_url():
    url = os.environ.get('DATABASE_URL', '')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


def get_db():
    return psycopg2.connect(_get_url())


def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def init_db():
    conn = get_db()
    cur = get_cursor(conn)

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id               SERIAL PRIMARY KEY,
            username         TEXT    UNIQUE NOT NULL,
            password_hash    TEXT    NOT NULL,
            first_name       TEXT    NOT NULL,
            last_name        TEXT    NOT NULL,
            class_name       TEXT    NOT NULL,
            student_number   INTEGER NOT NULL,
            gender           TEXT    NOT NULL CHECK(gender IN ('ชาย', 'หญิง', 'อื่นๆ')),
            age              INTEGER NOT NULL CHECK(age > 0 AND age < 100),
            role             TEXT    NOT NULL DEFAULT 'student'
                                    CHECK(role IN ('student', 'teacher')),
            score            INTEGER NOT NULL DEFAULT 0,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id         SERIAL PRIMARY KEY,
            sender_id  INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            student_id INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            content    TEXT      NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read    BOOLEAN   DEFAULT FALSE
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            user_id      INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            stage        TEXT      NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, stage)
        )
    ''')

    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized")
