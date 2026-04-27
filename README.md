# ComplaintFlow: Autonomous AI Complaint System

ComplaintFlow is an intelligent "Automated Registrar" built to manage, categorize, and route campus complaints. It uses AI to strip away emotional hyperbole from student complaints, extract objective facts, and dynamically route the issue to the appropriate department based on urgency and time constraints.

## 🎯 Problem Statement
Campus administrations receive a massive volume of student complaints daily. These complaints are often highly emotional, exaggerated, and sent to the wrong department, causing severe bottlenecks in resolution. Critical issues (like blocked fees before an exam) frequently get buried under minor complaints (like a squeaky chair). There is a need for a system that can instantly triage, prioritize, and route complaints objectively.

## 💡 How We Solve It
ComplaintFlow acts as a high-speed, objective triage agent:
1. **Fact-First Triage**: Uses the Gemini API to analyze the complaint, strip away all emotional language, and extract the objective facts ("Agent Interpretation").
2. **Contextual Urgency Scoring**: Prioritizes complaints based on a strict objective rubric (Urgent, High, Low) and identifies explicit time constraints or deadlines.
3. **Hierarchical Routing Matrix**: Conditionally routes emails based on severity. High/Urgent issues are escalated directly to Department Heads (HODs), while Low-priority issues go to the general department inbox.
4. **FIFO Queue Architecture**: Enforces chronological fairness by fetching and processing complaints based on the timestamp they were submitted.
5. **Real-Time Transparency**: Provides an interactive terminal UI that streams the AI's "thinking process" directly to the student, increasing trust and engagement.

## 🛠️ Tech Stack
- **Backend Core**: Python, Flask
- **AI/Intelligence**: Google GenAI SDK (Gemini 2.5 Flash)
- **Database**: SQLite (for persistent FIFO queue storage)
- **Frontend UI**: HTML5, Vanilla CSS (Modern Glassmorphism Design), JavaScript (Server-Sent Events / Fetch API for streaming)
- **Email Delivery**: Python `smtplib` (SMTP protocol)

## 🚀 Key Features
- **Emotion De-Noising**: Converts a 500-word angry rant into a 1-sentence factual problem statement.
- **Keyword Extraction**: Automatically tags complaints with core topics for database searchability.
- **Dynamic Escalation**: `get_recipient()` logic routes to `head_accounts@...` if High priority, but `accounts_dept@...` if Low priority.
- **Streaming Terminal UI**: Users see exactly how the AI is interpreting their problem in real-time.

## ⚙️ Setup & Installation
1. Clone the repository.
2. Ensure you have Python installed.
3. Rename `config_example.py` to `config.py` and add your Gemini API Key and SMTP credentials.
4. Run the application:
   ```bash
   python agent.py
   ```
5. Open `http://127.0.0.1:5000` in your browser.
