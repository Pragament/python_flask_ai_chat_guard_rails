# ✅ Updated ollama_api.py with log detail API
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import sqlite3
import datetime
import socket
import os

app = Flask(__name__)
CORS(app)

# ✅ Initialize SQLite DB
def init_db():
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            computer_id TEXT,
            prompt TEXT,
            code TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return jsonify({"message": "Flask API is running! Use /api/ask for queries."})

@app.route("/logs")
def serve_logs_page():
    return send_from_directory(os.getcwd(), "logs.html")

# ✅ Ask route
@app.route("/api/ask", methods=["POST"])
def ask():
    print("\n📩 Received POST /api/ask")
    data = request.get_json()
    prompt = data.get("prompt", "")
    code = data.get("code", "")
    combined_prompt = f"{prompt}\n\n[CODE]\n{code}\n[/CODE]"

    try:
        res = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "tinyllama",
                "messages": [{"role": "user", "content": combined_prompt}],
                "stream": False
            },
            timeout=500
        )
        response_json = json.loads(res.text.strip().splitlines()[0])
        answer = response_json["message"]["content"]

        # ✅ Save to DB
        conn = sqlite3.connect("logs.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO logs (computer_id, prompt, code, response, timestamp) VALUES (?, ?, ?, ?, ?)",
            (socket.gethostname(), prompt, code, answer, datetime.datetime.now())
        )
        conn.commit()
        conn.close()

        return jsonify({"response": answer})

    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return jsonify({"error": "Failed to get response from Ollama"}), 500

# ✅ Logs list
@app.route("/api/logs", methods=["GET"])
def get_logs():
    computer_id = request.args.get("computer_id")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    search = request.args.get("search")

    query = "SELECT id, computer_id, prompt, response, timestamp FROM logs WHERE 1=1"
    params = []

    if computer_id:
        query += " AND computer_id = ?"
        params.append(computer_id)
    if start_date:
        query += " AND DATE(timestamp) >= DATE(?)"
        params.append(start_date)
    if end_date:
        query += " AND DATE(timestamp) <= DATE(?)"
        params.append(end_date)
    if search:
        query += " AND (prompt LIKE ? OR response LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY timestamp DESC"

    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    logs = [{
        "id": row[0],
        "computer_id": row[1],
        "prompt": row[2],
        "response": row[3],
        "timestamp": row[4]
    } for row in rows]

    return jsonify(logs)

# ✅ Log detail API
@app.route("/api/log/<int:log_id>")
def get_log(log_id):
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("SELECT prompt, response FROM logs WHERE id = ?", (log_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({"prompt": row[0], "response": row[1]})
    else:
        return jsonify({"error": "Log not found"}), 404

# ✅ Bulk delete
@app.route("/api/logs/delete", methods=["POST"])
def delete_logs():
    data = request.get_json()
    ids = data.get("ids", [])
    if not ids or not isinstance(ids, list):
        return jsonify({"error": "Invalid ID list"}), 400

    placeholders = ",".join("?" for _ in ids)
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute(f"DELETE FROM logs WHERE id IN ({placeholders})", ids)
    conn.commit()
    deleted_count = c.rowcount
    conn.close()

    return jsonify({"message": f"✅ Deleted {deleted_count} log(s)."})

if __name__ == "__main__":
    print("\n🚀 Starting Ollama API Flask server on http://localhost:5001")
    app.run(host="0.0.0.0", port=5001)
