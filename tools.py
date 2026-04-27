import smtplib
from email.mime.text import MIMEText
from config import SENDER_EMAIL, SENDER_PASSWORD
import sqlite3
import datetime

def send_email(to_email, subject, body):
    """Tool: Sends a formal email via SMTP."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    try:
        # Check if dummy config is used to avoid hanging or failing locally without creds
        if SENDER_EMAIL == "namrata21social@gmail.com":
            print(f"Skipping actual email send (dummy config). To: {to_email}, Subject: {subject}")
            return "✅ Email sent successfully (Simulated)"
            
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return "✅ Email sent successfully"
    except Exception as e:
        print(f"Email Error: {e}")
        return f"❌ Email failed: {e}"

def mark_urgent(complaint):
    """Tool: Heuristic check for urgency keywords."""
    keywords = ["urgent", "immediately", "asap", "not working", "emergency", "broken", "fast", "safety", "health"]
    for word in keywords:
        if word in complaint.lower():
            return True
    return False

def init_db():
    """Initializes the SQLite database and creates the complaints table."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            enrollment_no TEXT,
            year TEXT,
            original_complaint TEXT,
            summary TEXT,
            department TEXT,
            urgency_level TEXT,
            status TEXT DEFAULT 'Pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def store_db(data):
    """Tool: Persists data to SQLite database."""
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO complaints (student_name, enrollment_no, year, original_complaint, summary, department, urgency_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get("name", "Unknown"),
            data.get("enrollment_no", "Unknown"),
            data.get("year", "Unknown"),
            data.get("complaint", "Unknown"),
            data.get("summary", "No summary"),
            data.get("department", "Admin"),
            data.get("urgency", "Low")
        ))
        
        conn.commit()
        conn.close()
        return "✅ Stored in database"
    except Exception as e:
        print(f"DB Error: {e}")
        return f"❌ DB Error: {e}"

def get_next_task():
    """Tool: Fetches the oldest pending complaint from the database (FIFO)."""
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        # ASC ensures the oldest dates come first for chronological fairness
        cursor.execute("SELECT * FROM complaints WHERE status = 'Pending' ORDER BY timestamp ASC LIMIT 1")
        task = cursor.fetchone()
        conn.close()
        return task
    except Exception as e:
        print(f"DB Fetch Error: {e}")
        return None
