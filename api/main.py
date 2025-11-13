import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS # Vercel อาจจะต้องใช้ CORS

# สร้าง Flask app
app = Flask(__name__)
CORS(app) # เปิด CORS สำหรับทุก route

# ฟังก์ชันสำหรับเชื่อมต่อ Database (Neon)
# เราจะดึง Connection String จาก Environment Variable ที่ Vercel
def get_db_connection():
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# Route สำหรับการสร้างตาราง (เรียกใช้ครั้งเดียวตอน setup)
@app.route('/api/init', methods=['GET'])
def init_db():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    fname VARCHAR(100) NOT NULL,
                    lname VARCHAR(100) NOT NULL,
                    nickname VARCHAR(50),
                    phone VARCHAR(20),
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.commit()
        return jsonify({"message": "Table 'students' created successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Route สำหรับดึงข้อมูลนักเรียนทั้งหมด (GET)
@app.route('/api/students', methods=['GET'])
def get_students():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, fname, lname, nickname, phone, image_url FROM students ORDER BY fname")
            students = cur.fetchall()
        return jsonify(students), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Route สำหรับเพิ่มนักเรียนใหม่ (POST)
@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.get_json()
    if not data or not data.get('fname') or not data.get('lname'):
        return jsonify({"error": "First name and last name are required."}), 400

    fname = data.get('fname')
    lname = data.get('lname')
    nickname = data.get('nickname')
    phone = data.get('phone')
    image_url = data.get('image_url')

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO students (fname, lname, nickname, phone, image_url)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (fname, lname, nickname, phone, image_url)
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"message": "Student added successfully.", "id": new_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Vercel จะเรียกใช้ 'app' นี้
# เราไม่จำเป็นต้องใช้ app.run()