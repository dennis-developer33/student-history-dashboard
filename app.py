# app.py (Sprint 5 - Pagination for History and Summary)
from flask import Flask, request, jsonify, render_template, redirect, url_for
import psycopg2
import psycopg2.extras
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT", 5432)
    )

# --- Landing page ---
@app.route("/landing")
def landing():
    return render_template("landing.html")

# --- Dashboard ---
@app.route("/dashboard")
def dashboard():
    return render_template("index.html")

# Redirect root to landing page
@app.route("/")
def home():
    return redirect(url_for('landing'))

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return None

# --- API: Raw history data with pagination ---
@app.route("/api/history")
def get_history():
    trno = request.args.get("trno")
    student_class = request.args.get("class")
    from_date = parse_date(request.args.get("from_date"))
    to_date = parse_date(request.args.get("to_date"))

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    offset = (page - 1) * per_page

    query = """
        SELECT id, trno, fullname, class, website, visit_date
        FROM history
        WHERE 1=1
    """
    params = []
    if trno:
        query += " AND trno = %s"
        params.append(trno)
    if student_class:
        query += " AND class = %s"
        params.append(student_class)
    if from_date:
        query += " AND visit_date >= %s"
        params.append(from_date)
    if to_date:
        query += " AND visit_date <= %s"
        params.append(to_date)

    query += " ORDER BY visit_date DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([dict(r) for r in rows])

# --- API: Daily summary with pagination ---
@app.route("/api/summary")
def get_summary():
    trno = request.args.get("trno")
    from_date = parse_date(request.args.get("from_date"))
    to_date = parse_date(request.args.get("to_date"))

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    offset = (page - 1) * per_page

    query = """
        SELECT trno, fullname, class, website, visit_date, visit_count
        FROM daily_summary
        WHERE 1=1
    """
    params = []
    if trno:
        query += " AND trno = %s"
        params.append(trno)
    if from_date:
        query += " AND visit_date >= %s"
        params.append(from_date)
    if to_date:
        query += " AND visit_date <= %s"
        params.append(to_date)

    query += " ORDER BY visit_date DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([dict(r) for r in rows])

# --- API: Summary stats for dashboard ---
@app.route("/api/summary_stats")
def get_summary_stats():
    trno = request.args.get("trno")
    student_class = request.args.get("class")
    from_date = parse_date(request.args.get("from_date"))
    to_date = parse_date(request.args.get("to_date"))

    query = """
        SELECT COUNT(*) AS total_visits,
               COUNT(DISTINCT website) AS unique_sites
        FROM history
        WHERE 1=1
    """
    params = []
    if trno:
        query += " AND trno = %s"
        params.append(trno)
    if student_class:
        query += " AND class = %s"
        params.append(student_class)
    if from_date:
        query += " AND visit_date >= %s"
        params.append(from_date)
    if to_date:
        query += " AND visit_date <= %s"
        params.append(to_date)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    result = cur.fetchone()
    cur.close()
    conn.close()

    return jsonify({
        "total_visits": result[0] or 0,
        "unique_sites": result[1] or 0
    })

if __name__ == "__main__":
    # Use host='0.0.0.0' for deployment (Render, Heroku, etc.)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
