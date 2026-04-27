from flask import Flask, render_template, request, Response, stream_with_context
from google import genai
import json
import re
import sqlite3

from config import GEMINI_API_KEY, DEPARTMENT_EMAILS, DEPARTMENT_HEAD_EMAILS
from tools import send_email, mark_urgent, store_db, init_db

app = Flask(__name__)

# Initialize database on startup
init_db()

# Configure Gemini is now done per client instance in google.genai
    
def analyze_complaint(complaint_text):
    """
    Uses Gemini API to analyze the complaint and extract structured information.
    """
    if GEMINI_API_KEY == "your_gemini_key":
        # Fallback for when API key is not set (for local testing without key)
        is_urg = mark_urgent(complaint_text)
        return {
            "summary": "Simulated summary of the problem: " + complaint_text[:50] + "...",
            "department": "Admin",
            "urgency": "High" if is_urg else "Medium",
            "action_steps": "Investigate the issue and contact the student."
        }

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""
        Perform an objective triage on the following student input:
        "{complaint_text}"

        Step 1: Split the input into distinct, objective problems.
        Step 2: Strip away all emotional language, adjectives, and exaggeration. Extract only facts.
        Step 3: Assign a Priority (Urgent, High, Low) based on this RUBRIC:
        - Urgent: Immediate safety/security threat, data breach, or active physical danger.
        - High: Direct academic/financial blocker (deadline < 24h) or significant service disruption.
        - Low: General feedback, minor inconvenience, aesthetic complaints, or no immediate deadline.
        
        Step 4: Target Department based on the highest priority issue:
        - Technical: WiFi, systems, equipment, portal login issues.
        - Finance: Fees, refunds, scholarships, payments, bank drafts.
        - Academics: Grades, exams, courses, faculty issues.
        - Admin: Hostel, policies, campus facilities, general inquiries.

        You must output ONLY a valid JSON object with the following structure:
        {{
            "agent_interpretation": "A clear statement of the facts stripped of all emotions.",
            "summary": "A concise 1-sentence summary combining all distinct problems found.",
            "keywords": ["list", "of", "3-5", "core", "keywords"],
            "time_constraint": "Explicit dates, deadlines, or waiting periods mentioned (e.g. '1st May', '< 24h', or 'None')",
            "department": "One of: Technical, Finance, Admin, Academics",
            "urgency": "One of: Urgent, High, Low",
            "action_steps": "A short suggested action step based on the facts."
        }}
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        
        # Clean up potential markdown formatting around the JSON
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        result = json.loads(text)
        
        # Ensure fallback for department
        if result.get("department") not in DEPARTMENT_EMAILS:
            result["department"] = "Admin"
            
        return result
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Fallback
        is_urg = mark_urgent(complaint_text)
        return {
            "agent_interpretation": "N/A",
            "summary": f"Failed to analyze. Original: {complaint_text[:50]}",
            "department": "Admin",
            "urgency": "High" if is_urg else "Low",
            "action_steps": "Manual review required."
        }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    is_stream = request.headers.get("X-Requested-With") == "Fetch"
    
    student_name = request.form.get("name")
    enrollment_no = request.form.get("enrollment_no")
    student_email = request.form.get("email")
    year = request.form.get("year")
    complaint_text = request.form.get("complaint")
    
    def get_recipient(category, priority):
        category = str(category).strip().lower()
        priority = str(priority).strip().lower()
        if "academic" in category:
            return DEPARTMENT_HEAD_EMAILS.get("Academics") if priority in ["high", "urgent"] else DEPARTMENT_EMAILS.get("Academics")
        elif "finance" in category or "account" in category:
            return DEPARTMENT_HEAD_EMAILS.get("Accounts") if priority in ["high", "urgent"] else DEPARTMENT_EMAILS.get("Accounts")
        elif "tech" in category:
            return DEPARTMENT_HEAD_EMAILS.get("Technical") if priority in ["high", "urgent"] else DEPARTMENT_EMAILS.get("Technical")
        else:
            return DEPARTMENT_EMAILS.get("Admin")
    
    def generate():
        yield json.dumps({"step": "Agent is thinking..."}) + "\n"
        
        # 1. THINK & ANALYZE (Gemini API)
        analysis = analyze_complaint(complaint_text)
        
        # Check manual urgency heuristic to bump urgency if Gemini missed it
        if mark_urgent(complaint_text) and analysis["urgency"] in ["Medium", "Low"]:
            analysis["urgency"] = "High"
            
        department = analysis["department"]
        dept_email = get_recipient(department, analysis["urgency"])
        
        yield json.dumps({"step": f"Agent Interpretation: {analysis.get('agent_interpretation', 'Analyzing...')}"}) + "\n"
        yield json.dumps({"step": f"Identified Priority: {analysis['urgency']}"}) + "\n"
        yield json.dumps({"step": f"Time Constraint Check: {analysis.get('time_constraint', 'None')}"}) + "\n"
        
        # Display routing logic in terminal
        recipient_type = "Head of Department" if analysis["urgency"] in ["Urgent", "High"] else "General Department"
        yield json.dumps({"step": f"Routing Matrix: Priority {analysis['urgency']} -> Routing to {recipient_type} ({dept_email})"}) + "\n"
        
        # 2. PLAN & ACT: Create Email
        email_subject = f"[{analysis['urgency'].upper()}] Complaint from {student_name} ({enrollment_no})"
        email_body = f"""
New Student Complaint Received

Student Details:
- Name: {student_name}
- Enrollment No: {enrollment_no}
- Year: {year}

Complaint Analysis:
- Department Routed: {department}
- Urgency Level: {analysis['urgency']}

AI Interpreted Problem (Fact-based):
{analysis.get('agent_interpretation', 'N/A')}

Original Human-Written Problem:
"{complaint_text}"

Suggested Action:
{analysis['action_steps']}

---
This email was generated by the ComplaintFlow Autonomous AI Agent.
"""
        
        # 3. Send Email
        email_status = send_email(dept_email, email_subject, email_body)
        print(email_status)
        
        yield json.dumps({"step": "Finalizing result..."}) + "\n"
        
        # 4. Persist to Database
        db_data = {
            "name": student_name,
            "enrollment_no": enrollment_no,
            "year": year,
            "complaint": complaint_text,
            "summary": analysis["summary"],
            "department": department,
            "urgency": analysis["urgency"]
        }
        db_status = store_db(db_data)
        print(db_status)
        
        # Expected Resolution based on urgency
        resolution_map = {
            "Urgent": "Under 4 Hours",
            "High": "Within 24 Hours",
            "Low": "Up to 7 Days"
        }
        timeline = resolution_map.get(analysis["urgency"], "Within 24 Hours")
        
        # Render Result
        final_html = render_template("result.html", 
                               agent_interpretation=analysis.get("agent_interpretation", ""),
                               summary=analysis["summary"],
                               keywords=", ".join(analysis.get("keywords", [])),
                               time_constraint=analysis.get("time_constraint", "None"),
                               department_email=dept_email,
                               urgency=analysis["urgency"],
                               timeline=timeline)
                               
        yield json.dumps({"final_html": final_html}) + "\n"

    if is_stream:
        return Response(stream_with_context(generate()), mimetype="application/x-ndjson")
    else:
        # Fallback for standard form submission
        gen = list(generate())
        last_json = json.loads(gen[-1])
        return last_json["final_html"]

@app.route("/check-followup", methods=["GET"])
def check_followup():
    """
    Endpoint intended to be called by a cron job every hour.
    Checks the database for complaints older than 24 hours that are still 'Pending'.
    """
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # In SQLite, we can use datetime functions to find rows older than 24 hours
        # For simplicity in this demo, let's just query Pending complaints
        cursor.execute('''
            SELECT id, student_name, department, summary 
            FROM complaints 
            WHERE status = 'Pending' AND timestamp <= datetime('now', '-1 day')
        ''')
        pending_issues = cursor.fetchall()
        
        count = 0
        for issue in pending_issues:
            issue_id, name, dept, summary = issue
            dept_email = DEPARTMENT_EMAILS.get(dept, DEPARTMENT_EMAILS["Admin"])
            
            # Send reminder email
            subject = f"[REMINDER] Unresolved Complaint #{issue_id} from {name}"
            body = f"This is an automated 24-hour reminder.\n\nIssue Summary:\n{summary}\n\nPlease update the status of this complaint."
            send_email(dept_email, subject, body)
            count += 1
            
        conn.close()
        return {"status": "success", "reminders_sent": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
